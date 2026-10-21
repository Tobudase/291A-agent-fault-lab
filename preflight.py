"""Check that the configured model can run our workflow (a few calls, ~1 minute), before the long run.

  python preflight.py            # uses LLM_MODEL / LLM_BASE_URL (phase1_local.py sets them)

Tests: plain reply, a tool call, the tool-result round trip (the format our agents use) and JSON-only output.
Prints the time per call so you can estimate how long the full Phase 1 run will take.
"""
import json
import sys
import time

from mas import llm

TOOL = [{"type": "function", "function": {
    "name": "lookup_stock", "description": "Look up price, sector and rating of a ticker.",
    "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}}}]
CALLS_PER_RUN = 3000  # one full Phase 1 pass (138 episodes) is ~2,800-3,200 LLM calls


def timed(messages, tools=None):
    t0 = time.time()
    msg, u = llm.chat(messages, tools, retries=2)
    return msg, u, time.time() - t0


def main():
    print(llm.describe())
    res, secs = {}, []
    try:
        m, u, s = timed([{"role": "user", "content": "Reply with the single word OK."}])
        secs.append(s)
        res["plain"] = bool((m.content or "").strip())
        if u["completion_tokens"] > 60:  # "OK" is 1-2 tokens; hundreds means hidden reasoning is on
            res["thinking_off"] = False
            print(f"   'Reply OK' used {u['completion_tokens']} output tokens: the model is THINKING on every call "
                  f"(slow, and replies get cut off). For Qwen3 hybrid models set LLM_NO_THINK=1 (presets do).")
        sys_msg = {"role": "system", "content": "You are the Researcher agent. Use your tools."}
        ask = {"role": "user", "content": "Research stock AAPL: call lookup_stock, then reply with ONLY JSON "
                                          '{"ticker": str, "rating": "buy"|"hold"|"sell"}.'}
        m, u, s = timed([sys_msg, ask], TOOL)
        secs.append(s)
        tc = (m.tool_calls or [None])[0]
        try:
            args = json.loads(tc.function.arguments) if tc else None
        except json.JSONDecodeError:
            args = None
        res["tool_call"] = bool(tc and tc.function.name == "lookup_stock" and isinstance(args, dict) and "ticker" in args)
        res["json_roundtrip"] = False
        if res["tool_call"]:
            msgs = [sys_msg, ask,
                    {"role": "assistant", "content": m.content or "", "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name,
                                                                      "arguments": tc.function.arguments}}]},
                    {"role": "tool", "tool_call_id": tc.id,
                     "content": json.dumps({"ticker": "AAPL", "price": 190, "sector": "technology", "rating": "buy"})}]
            m2, u, s = timed(msgs, TOOL)
            secs.append(s)
            txt = m2.content or ""
            i, j = txt.find("{"), txt.rfind("}")
            try:
                res["json_roundtrip"] = json.loads(txt[i:j + 1]).get("rating") == "buy"
            except Exception:
                pass
            if not res["json_roundtrip"]:
                print("   model reply after the tool result:", repr(txt[:300]))
        else:
            print("   model did not call the tool; reply was:", repr((m.content or "")[:300]))
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    ok = res.get("plain") and res.get("tool_call") and res.get("json_roundtrip") and res.get("thinking_off", True)
    print(f"\n{llm.MODEL}: {'PASS' if ok else 'FAIL'}  {res}")
    if secs:
        per = sum(secs[1:] or secs) / len(secs[1:] or secs)  # first call includes model loading
        print(f"   time per call ~{per:.1f}s (first call {secs[0]:.1f}s incl. loading). "
              f"Rough full Phase 1 time at 1 worker: ~{per * CALLS_PER_RUN / 3600:.1f} h "
              f"(real calls are longer: bigger prompts; parallel workers on a GPU cut this ~2-3x).")
    if "error" in res:
        print("   Is the server running? For Ollama: `ollama serve` and `ollama pull <model>` "
              "(phase1_local.py does both).")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
