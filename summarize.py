"""Aggregate runs/<exp>/results.jsonl into summary.md (Phase 1 tables).

  python summarize.py runs/<exp>

Tables (match OUTLINE.md section 5/6):
  Table 1   clean baseline per task (+ verify on clean input = false-alarm cost)
  Table 2a  propagation, ACCIDENTAL faults   (method = none)
  Table 2b  propagation, ADVERSARIAL faults  (method = none)
  Table 3a/b recovery baselines per fault: none vs restart vs verify, END-TO-END cost (fault run + recovery)
"""
import os
import sys

from analysis import ACCIDENTAL, ADVERSARIAL, METHOD_ORDER, OUTCOMES, faults_in, group, load, mean, outcome_counts


def f(v, nd=2):
    return "" if v is None else f"{v:.{nd}f}"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def fmt_outcomes(rs):
    c = outcome_counts(rs)
    return ", ".join(f"{k}:{c[k]}" for k in OUTCOMES + ["not_fired", "clean_failed", "-"] if c.get(k))


def main(exp):
    rows = load(exp)
    model = rows[0].get("model", "unknown (run predates the model field)")
    parts = [f"# Phase 1 summary: `{exp}` (model `{model}`, {len(rows)} episodes)\n"]

    # Table 1: clean baseline
    clean = [r for r in rows if r["fault"] == "clean"]
    t1 = []
    for task, rs in sorted(group([r for r in clean if r["method"] == "none"], "task").items()):
        r = rs[0]
        t1.append([task[0], int(r["correct"]), r["llm_calls"], r["tokens"], f(r["latency"], 1)])
    all_none = [r for r in clean if r["method"] == "none"]
    t1.append(["**mean**", f(mean(r["correct"] for r in all_none)), f(mean(r["llm_calls"] for r in all_none), 1),
               f(mean(r["tokens"] for r in all_none), 0), f(mean(r["latency"] for r in all_none), 1)])
    parts.append("## Table 1: clean baseline\n\n" + table(["task", "correct", "llm_calls", "tokens", "latency_s"], t1))
    v = [r for r in clean if r["method"] == "verify"]
    if v:
        parts.append(f"\nAlways-verify on clean input: tokens {f(mean(r['tokens'] for r in v), 0)} "
                     f"(+{f(100 * (mean(r['tokens'] for r in v) / mean(r['tokens'] for r in all_none) - 1), 0)}%), "
                     f"latency {f(mean(r['latency'] for r in v), 1)} s, "
                     f"false alarms per run {f(mean(r.get('false_alarms') for r in v))}.")
    n_bad = sum(1 for r in all_none if not r["correct"])
    if n_bad:
        parts.append(f"\n**Warning:** the clean run failed on {n_bad} task(s); fault outcomes there are `clean_failed`.")

    # Table 2: propagation
    for title, names in (("2a: accidental faults", ACCIDENTAL), ("2b: adversarial faults", ADVERSARIAL)):
        present = [x for x in faults_in(rows) if x in names]
        if not present:
            continue
        t = []
        for fault in present:
            rs = [r for r in rows if r["fault"] == fault and r["method"] == "none"]
            t.append([fault, len(rs), fmt_outcomes(rs), f(mean(r["safe_success"] for r in rs)),
                      f(mean(r["unauthorized"] for r in rs)), f(mean(r.get("downstream") for r in rs), 1),
                      f(mean(r.get("affected") for r in rs), 1),
                      "/".join(f(mean(r[f"aff_{s}"] for r in rs), 1) for s in ("research", "plan", "exec")),
                      f(mean(r.get("wasted_tokens") for r in rs), 0)])
        parts.append(f"\n## Table {title} (no recovery)\n\n" + table(
            ["fault", "n", "outcome", "safe_success", "unauthorized", "downstream", "affected",
             "affected R/P/E", "wasted_tokens"], t))
    parts.append("\n`downstream` = nodes the dependency graph marks as depending on the fault; `affected` = those whose "
                 "decision really changed vs the clean run. `ignored` means nothing downstream changed; it is not "
                 "evidence of robustness.")

    # Table 3: recovery baselines, end-to-end
    for title, names in (("3a: accidental faults", ACCIDENTAL), ("3b: adversarial faults", ADVERSARIAL)):
        present = [x for x in faults_in(rows) if x in names]
        t = []
        for fault in present:
            for m in METHOD_ORDER:
                rs = [r for r in rows if r["fault"] == fault and r["method"] == m]
                if not rs:
                    continue
                t.append([fault, m, len(rs), fmt_outcomes(rs), f(mean(r["safe_success"] for r in rs)),
                          f(mean(r["unauthorized"] for r in rs)), f(mean(r["total_tokens"] for r in rs), 0),
                          f(mean(r["total_latency"] for r in rs), 1), f(mean(r.get("recomputed") for r in rs), 1),
                          f(mean(r.get("unrecoverable") for r in rs)), f(mean(r.get("detected") for r in rs)),
                          f(mean(r.get("false_alarms") for r in rs))])
        if t:
            parts.append(f"\n## Table {title}: recovery baselines (end-to-end)\n\n" + table(
                ["fault", "method", "n", "outcome", "safe_success", "unauthorized", "total_tokens", "total_latency_s",
                 "recomputed", "unrecoverable", "detected", "false_alarms"], t))
    parts.append("\n`total_*` = faulty run + recovery for restart (the raw rows only hold the rerun); for verify it is the "
                 "single run including verification. `detected`/`false_alarms` are only defined for verify. "
                 "`unrecoverable` = irreversible actions (e.g. an emailed statement) that a rollback cannot undo.")

    text = "\n".join(parts) + "\n"
    print(text)
    with open(os.path.join(exp, "summary.md"), "w") as fh:
        fh.write(text)


if __name__ == "__main__":
    main(sys.argv[1])
