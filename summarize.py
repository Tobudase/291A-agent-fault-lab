"""Aggregate runs/<exp>/results.jsonl into a markdown table (also written to summary.md).

  python summarize.py runs/<exp>
"""
import json
import os
import sys
from collections import Counter, defaultdict

COLS = ["correct", "safe_success", "unauthorized", "affected", "wasted_tokens", "latency", "tokens",
        "verify_tokens", "detected", "false_alarms", "recomputed", "retained", "recovery_latency", "unrecoverable"]


def main(exp):
    rows = [json.loads(l) for l in open(os.path.join(exp, "results.jsonl"))]
    groups = defaultdict(list)
    for r in rows:
        groups[(r["fault"], r["category"], r["method"])].append(r)
    cols = [c for c in COLS if any(c in r for r in rows)]
    lines = ["| fault | category | method | n | outcome | " + " | ".join(cols) + " |",
             "|" + "---|" * (5 + len(cols))]
    for (fault, cat, method), rs in groups.items():
        outcomes = Counter(r.get("outcome") or r.get("fault_outcome") or "-" for r in rs)
        cells = []
        for c in cols:
            vals = [float(r[c]) for r in rs if r.get(c) is not None]
            cells.append(f"{sum(vals) / len(vals):.2f}" if vals else "")
        oc = ", ".join(f"{k}:{v}" for k, v in outcomes.items())
        lines.append(f"| {fault} | {cat} | {method} | {len(rs)} | {oc} | " + " | ".join(cells) + " |")
    table = "\n".join(lines)
    print(table)
    with open(os.path.join(exp, "summary.md"), "w") as f:
        f.write(table + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
