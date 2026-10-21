"""Thin wrapper around any OpenAI-compatible chat endpoint (local vLLM or UCSD TritonAI).

Environment variables (LLM_* wins, OPENAI_* is the fallback, so it works out of the box in UCSD DataHub):
  LLM_BASE_URL / OPENAI_BASE_URL   endpoint, default http://localhost:8001/v1
  LLM_API_KEY  / OPENAI_API_KEY    key, default EMPTY
  LLM_MODEL                        model id, e.g. api-glm-5.3
  LLM_TEMPERATURE                  default 0
  LLM_REASONING_EFFORT             optional: low | high | max (reasoning models such as GLM-5.3)
  LLM_EXTRA_BODY                   optional JSON merged into the request body (e.g. chat_template_kwargs)
  LLM_TIMEOUT / LLM_RETRIES        per-call timeout in s (default 300) / max attempts (default 6)
"""
import json
import os
import random
import re
import threading
import time

import openai
from openai import OpenAI

BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "http://localhost:8001/v1"
MODEL = os.getenv("LLM_MODEL") or "qwen3.8-27b"
API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "EMPTY"
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
NO_THINK = os.getenv("LLM_NO_THINK", "0") == "1"
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "0"))
REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT") or None
EXTRA_BODY = json.loads(os.getenv("LLM_EXTRA_BODY") or "null")
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "600"))
RETRIES = int(os.getenv("LLM_RETRIES", "6"))
 
# USD per 1M tokens (input, output), from the public TritonAI model catalog. Local models cost $0.
PRICES = {"api-glm-5.3": (1.2, 3.25), "api-glm-5.3-flash": (0.15, 0.5), "api-muse-glimmer-30b": (0.2, 0.4)}
 
_client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=TIMEOUT, max_retries=0)
_THINK = re.compile(r"<think>.*?</think>", re.S)
_OPEN_THINK = re.compile(r"^.*?</think>", re.S)  # template already opened <think>, model closed it
 
# Running totals for this process (guarded by a lock).
STATS = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "retries": 0,
         "truncated": 0}  # truncated = replies cut off at the token limit (finish_reason == "length")
_lock = threading.Lock()
 
 
def estimate_cost(stats=None):
    s = stats or STATS
    pin, pout = PRICES.get(MODEL, (0.0, 0.0))
    return (s["prompt_tokens"] * pin + s["completion_tokens"] * pout) / 1e6
 
 
def describe():
    return f"model={MODEL} endpoint={BASE_URL} no_think={NO_THINK} max_tokens={MAX_TOKENS or 'server default'}"
 
 
def strip_think(text):
    text = _THINK.sub("", text)
    if "</think>" in text:
        text = _OPEN_THINK.sub("", text)
    return text.replace("<think>", "").strip()
 
 
def _with_no_think(messages):
    if not NO_THINK:
        return messages
    out = []
    for m in messages:
        if m.get("role") == "system" and "/no_think" not in (m.get("content") or ""):
            m = {**m, "content": (m.get("content") or "") + "\n/no_think"}
        out.append(m)
    if not any(m.get("role") == "system" for m in out):
        out.insert(0, {"role": "system", "content": "/no_think"})
    return out
 
 
def _retryable(e):
    if isinstance(e, (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError,
                      openai.InternalServerError)):
        return "budget" not in str(e).lower()  # an exhausted budget will not fix itself
    return isinstance(e, openai.APIStatusError) and e.status_code in (408, 409, 429, 500, 502, 503, 504)
 
 
def chat(messages, tools=None, retries=None):
    """One chat completion. Returns (message, usage). Retries 429/5xx/timeouts with backoff."""
    kwargs = dict(model=MODEL, messages=_with_no_think(messages), temperature=TEMPERATURE)
    if tools:
        kwargs["tools"] = tools
    if MAX_TOKENS > 0:
        kwargs["max_tokens"] = MAX_TOKENS
    if REASONING_EFFORT:
        kwargs["reasoning_effort"] = REASONING_EFFORT
    elif NO_THINK:
        # Ollama ignores the "/no_think" text; thinking is switched off only through the API field
        kwargs["reasoning_effort"] = "none"
    if EXTRA_BODY:
        kwargs["extra_body"] = EXTRA_BODY
    attempts = retries or RETRIES
    for attempt in range(attempts):
        try:
            r = _client.chat.completions.create(**kwargs)
            break
        except Exception as e:
            if attempt == attempts - 1 or not _retryable(e):
                raise
            wait = min(60, 2 ** attempt) * (0.5 + random.random())
            ra = getattr(getattr(e, "response", None), "headers", {}).get("retry-after")
            if ra and str(ra).replace(".", "", 1).isdigit():
                wait = max(wait, float(ra))
            with _lock:
                STATS["retries"] += 1
            time.sleep(wait)
    msg, u = r.choices[0].message, r.usage
    if msg.content and "think>" in msg.content:  # some servers leave the reasoning in the content
        try:
            msg.content = strip_think(msg.content)
        except Exception:
            pass
    pt = getattr(u, "prompt_tokens", 0) or 0
    ct = getattr(u, "completion_tokens", 0) or 0
    rt = getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", 0) or 0
    with _lock:
        STATS["calls"] += 1
        STATS["prompt_tokens"] += pt
        STATS["completion_tokens"] += ct
        STATS["reasoning_tokens"] += rt
        if getattr(r.choices[0], "finish_reason", None) == "length":
            STATS["truncated"] += 1
    return msg, {"calls": 1, "prompt_tokens": pt, "completion_tokens": ct}