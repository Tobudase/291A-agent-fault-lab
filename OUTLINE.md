# Project Outline (living document)

How to use this file: it is the skeleton of both reports. Fill each `[TODO]` with bullets, numbers or
figure paths as the work lands. When the content is complete, hand this file plus `runs/*/summary.md`
to an agent or writer to produce the final PDFs. Keep bullets short and factual.

**Deadlines.** Phase 1 code + 1–2 page report (with a timeline appendix): **Oct 28, 2026**.
Phase 2 code + final report (4–6 pages, two-column, 10pt, PDF): **Dec 10, 2026**.

**Grading reminders (from the spec).** Distinguish detection from recovery. Show meaningful propagation
paths. Handle shared-state dependencies. Explain the trade-off between recovery precision and bookkeeping
overhead. Keep accidental and adversarial faults separate. Report irreversible actions instead of counting
recomputation as full recovery.

---

## Storyline (one paragraph)

Multi-agent LLM systems pass results through messages and shared state, so one bad result
(a wrong fact, a stale value, an injected instruction) can silently steer later agents into wrong or
unsafe actions. We build a small researcher–planner–executor workflow with programmatically checkable
outcomes and measure how injected faults propagate (Phase 1). We then show that tracking provenance,
including shared-state reads and writes, lets the system recover by recomputing only the affected steps.
This is cheaper than a full restart and safer than verifying everything, but some actions cannot be undone (Phase 2).

---

## 1. Introduction / Motivation
- Problem: failure propagation in MAS; the motivating example of a fabricated fact leading to a wrong plan and then a wrong trade.
- Core question: can dependency tracking support efficient recovery while preserving correct and safe execution?
- Contributions (3 bullets): workflow + injection harness; propagation measurement; selective recovery vs. baselines. [TODO: final numbers in 1 line each]

## 2. Background & Related Work
- TAMAS (Kavathekar et al., 2025): adversarial MAS benchmark (DPI, IPI, Byzantine, …). We reuse its finance scenario and attack styles.
- A2ASecBench (ICLR 2026): A2A protocol attacks. It is out of scope here, but cite it as an orthogonal threat surface.
- Provenance and lineage-based recovery (databases, Spark RDD lineage, build systems such as Make and Bazel), plus checkpoint/rollback and compensating transactions (sagas). [TODO: 3–5 citations]
- Prompt injection and MAS failure taxonomies. [TODO]

## 3. System Design (Method)
- 3.1 Workflow: researcher (one per ticker) → planner (JSON steps with `uses`) → executor (one call per step). Figure 1: architecture plus one example trace.
- 3.2 Environment and shared state: account, files, `external` effects; tools log reads/writes; harmful tools are visible but unauthorized and irreversible.
- 3.3 Tasks and checker: 6 tasks, ground truth computed from market data, 6 state checks, `safe_success`.
- 3.4 Provenance tracking: Node = result plus sources. Three edge types: message, declared `uses`, shared-state read-after-write.
- 3.5 Fault model: table of 7 faults (kind, accidental/adversarial, stage, mechanism). Faults fire once and their identity is supplied to recovery.
- 3.6 Baselines: full restart (rollback to the initial snapshot); always-verify (LLM verifier after each report and the plan, regenerate on FAIL).
- 3.7 **[Phase 2] Selective recovery**: invalidation set = descendants of the faulty node; state restoration (snapshots/compensation); rerun with `reuse`. [TODO: final design, pseudo-code, which edge types were used]
- 3.8 **[Phase 2] Changed environment and irreversible actions**: [TODO: what cannot be rolled back, how it is detected and reported]

## 4. Experimental Setup
- Model: Qwen3.8-27B served by vLLM (temperature 0). [TODO: switch or add the course API model if used]
- Scale: 6 tasks × 7 faults × methods; [TODO: number of repetitions].
- Metrics, as defined in README "Metrics": clean success, propagation outcome, unauthorized actions, affected stages,
  wasted work, latency, tokens; for recovery: recovered correctness, recomputed/retained nodes, recovery latency,
  inference cost, tracking overhead, unrecoverable actions; for verify: detected/false alarms.
- Commands to reproduce: `python run.py --out runs/phase1 && python summarize.py runs/phase1`.

## 5. Results — Phase 1: Propagation
- Table 1: clean baseline (success rate, calls, tokens, latency per task). [TODO: from `runs/phase1/summary.md`]
- Table 2: per fault, outcome distribution (propagated/absorbed/ignored), unauthorized, affected stages, wasted tokens. **Accidental and adversarial in separate blocks.**
- Figure 2: one propagation path drawn from a real trace (e.g. R-incorrect: research:AAPL → plan → exec:1..5). [TODO]
- Key observations: [TODO: confirm with repetitions; preliminary from `runs/phase1` (Qwen3.8-27B, 1 run each)]
  - Clean baseline: 6/6 tasks succeed, about 14k tokens and 62 s per task.
  - Accidental *data* faults (R-incorrect, R-stale) propagate in 6/6 tasks: the wrong rating flows research → plan → wrong buys/stop-losses (about 3.3 affected nodes on average).
  - R-timeout is mostly ignored: the researcher just retries. This is not evidence of robust recovery.
  - E-timeout (side effect committed but reported as timed out) propagated once through shared state (T5: the retry bought more shares, 116 instead of 75).
  - Adversarial injection at the research stage (R-malicious, R-ipi) is filtered by the planner (0/6 unauthorized). Injection at the plan stage (P-malicious) is executed in 6/6 tasks and leads to an unauthorized, irreversible email. Stage matters: the executor trusts the plan.
  - Restart recovers correctness 6/6 for every fault (about 14k extra tokens, about 93 s), but cannot undo the P-malicious email (1 unrecoverable action per task).
  - Verify prevents all 6 data-fault and P-malicious failures for about 5.2k extra tokens per run (+38%) and about 1.6× latency. It does not cover executor faults (E-timeout); false alarms are rare (≤0.33 per run).

## 6. Results — Recovery (Phase 1 baselines + Phase 2)
- Table 3: restart vs. verify vs. selective under identical fault schedules, with columns for recovered correctness, unauthorized,
  recomputed/retained nodes, recovery latency, tokens, unrecoverable actions. [TODO]
- Figure 3: cost (tokens or latency) vs. recovered correctness per method. [TODO]
- Validity of reuse: are reused results identical to a clean run? [TODO]
- Precision vs. bookkeeping: coarse vs. `uses` vs. +state edges, giving recomputed nodes and tracking overhead (bytes/time). [TODO]
- Where selective recovery fails: irreversible actions, changed environment, faults that are not visible in the dependency graph. [TODO]
- Detection vs. recovery: verification as detection (detected/false alarms), kept separate from recovery quality. [TODO]

## 7. Discussion & Limitations
- Simulated tools, small task family, a single model; injection is post hoc and fires once. [TODO]
- No guarantee against arbitrary malicious agents (expected by the spec).

## 8. Experience (required by the course for the final report)
- Difficulties met / what did not work / what we spent the most time on. [TODO: each member adds 1–2 bullets]
- Tricks that worked (e.g. temperature 0 + signatures for comparing runs; logging reads and writes per tool). [TODO]

## 9. Conclusion
- [TODO: 3 sentences]

---

## Appendix A (Phase 1 report): Timeline & Milestones
| date | milestone | owner |
|---|---|---|
| Oct 10 | repo, workflow, harness, baselines running | [TODO] |
| Oct 20 | full Phase 1 run (`runs/phase1`), tables and figures | [TODO] |
| Oct 28 | **Phase 1 report + code due** | all |
| Nov 10 | selective recovery v1 (descendants + snapshot restore + reuse) | [TODO] |
| Nov 20 | shared-state / changed-environment cases, precision vs. overhead study | [TODO] |
| Dec 1 | final experiments frozen | [TODO] |
| Dec 10 | **final report + code due** | all |

## Phase 1 report (1–2 pages) = a short cut of the sections above
- Problem + setup (Sections 1, 3.1–3.6, condensed), Tables 1–2, the restart/verify rows of Table 3, Phase 2 plan (3.7) + Appendix A.
