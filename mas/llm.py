"""Thin wrapper around any OpenAI-compatible chat endpoint (local vLLM by default)."""
import os
import time

from openai import OpenAI

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
MODEL = os.getenv("LLM_MODEL", "qwen3.8-27b")
API_KEY = os.getenv("LLM_API_KEY", "EMPTY")

_client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=180)


def chat(messages, tools=None, retries=3):
    """One chat completion at temperature 0. Returns (message, usage)."""
    kwargs = dict(model=MODEL, messages=messages, temperature=0)
    if tools:
        kwargs["tools"] = tools
    for attempt in range(retries):
        try:
            r = _client.chat.completions.create(**kwargs)
            break
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    u = r.usage
    return r.choices[0].message, {"calls": 1, "prompt_tokens": u.prompt_tokens,
                                  "completion_tokens": u.completion_tokens}
