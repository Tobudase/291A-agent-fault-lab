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
- Model: Muse Glimmer 30B via UCSD TritonAI (`api-muse-glimmer-30b`), temperature 0.
- Scale: 6 tasks × 8 faults (7 + R-distractor control) × {none, restart, verify} + clean = 156 episodes, 1 run per cell;
  plus 30 episodes of E-timeout with `--cash ample`.
- Metrics (README "Metrics"): clean success; outcome propagated / masked / absorbed / ignored (decisions compared with the
  clean run, not wording); unauthorized actions; changed downstream nodes per stage; dependency vs. affected tokens
  (not "wasted tokens"); latency with API backoff recorded separately; for recovery: correctness, recomputed nodes,
  latency, tokens, unrecoverable actions; for verify: detected / false alarms.
- Reproduce: README "Quick start" / RUNBOOK_PHASE1.md. Data: `runs/phase1-v2-muse-glimmer-30b`, `runs/etimeout-ample-muse`.

## 5. Results — Phase 1: Propagation (final, `runs/phase1-v2-muse-glimmer-30b`)
- Clean baseline: 6/6 safe success, 20.2 LLM calls, 20.7k tokens, 34.7 s per task; always-verify on clean input +45% tokens,
  0 false alarms. No API retries in the run; 7 replies needed JSON repair/re-ask, 0 unusable.
- R-incorrect / R-stale propagate 6/6: plan changes, 2.7 executor nodes change (wrong buys/stop-losses), via message and
  shared-state edges (Figure 2: R-incorrect, T5).
- P-malicious propagates 6/6: unauthorized, irreversible email; the executor trusts the plan.
- Relevance control: R-distractor ignored 6/6 although the graph marks 5.3 dependent nodes.
- R-timeout ignored 6/6: the researcher retried the lookup (retry, not robust recovery).
- R-malicious reached the planner 6/6 and its decisions matched the clean run (0 unauthorized); R-ipi never left the
  researcher (0/6 reports repeated it), so it does not test the planner.
- E-timeout: buy commits, agent told "timed out": 6/6 retried, 2/6 duplicates committed, 4/6 masked (rejected only for
  insufficient cash). With ample cash: 5/6 duplicates committed and harmed (6/6 under verify; restart recovers 6/6).
- Dependency exposure vs. affected work: R-timeout 15.8k vs 3.1k tokens; R-distractor 15.0k vs 2.3k; R-incorrect 13.4k vs 10.9k.
- Restart: correct for every fault except P-malicious (email unrecoverable), 2x tokens (42.0k vs 21.3k) and latency (111 vs 56 s),
  recomputes all 8.8 nodes. Verify: 0.96 safe success, +48% tokens, detects 30/30 faulty reports/plans, 0 false alarms,
  0/6 on E-timeout (executor actions are not verified), also repairs harmless R-distractor faults.
- Phase 2 bridge: message edges invalidate 4.7 nodes for R-incorrect (3.7 change) and 5.3 for R-distractor (0 change);
  declared `uses` invalidate 2.5 for R-incorrect, i.e. they under-invalidate when the plan itself changes.

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
| Oct 10 | repo, workflow, harness, baselines running (done) | [TODO] |
| Oct 20 | first full Phase 1 grid, tables and figures (done) | [TODO] |
| Oct 28 | **Phase 1 report + code due**; final Muse runs (done) | all |
| Nov 10 | selective recovery v1: invalid set, per-node snapshots, rerun with reuse | [TODO] |
| Nov 17 | reuse validity check vs. clean runs; compensating actions | [TODO] |
| Nov 24 | changed-environment cases (irreversible effects, drift); precision vs. tracking overhead | [TODO] |
| Dec 1 | final experiments frozen: selective vs. restart vs. verify, same fault schedules | [TODO] |
| Dec 10 | **final report + code due** | all |

## Phase 1 report (1–2 pages) = a short cut of the sections above
- Problem + setup (Sections 1, 3.1–3.6, condensed), Tables 1–2, the restart/verify rows of Table 3, Phase 2 plan (3.7) + Appendix A.
