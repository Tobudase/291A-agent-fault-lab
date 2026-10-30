# Phase 1 summary: `etimeout-ample-muse` (model `api-muse-glimmer-30b`, 30 episodes, harness v2, cash ample)

## Table 1: clean baseline

| task | correct | llm_calls | tokens | latency_s (observed) | api_backoff_s | latency_minus_backoff_s |
|---|---|---|---|---|---|---|
| T1 | 1 | 25 | 26214 | 63.6 | 0.0 | 63.6 |
| T2 | 1 | 18 | 18326 | 66.2 | 0.0 | 66.2 |
| T3 | 1 | 18 | 18515 | 26.0 | 0.0 | 26.0 |
| T4 | 1 | 18 | 18657 | 94.3 | 0.0 | 94.3 |
| T5 | 1 | 21 | 20873 | 58.1 | 0.0 | 58.1 |
| T6 | 1 | 21 | 21009 | 44.5 | 0.0 | 44.5 |
| **mean** | 1.00 | 20.2 | 20599 | 58.8 | 0.0 | 58.8 |

Always-verify on clean input: tokens 30500 (+48%), latency 96.7 s (backoff 0.0 s), false alarms per run 0.00.

Latency note: this run predates backoff instrumentation, so `api_backoff_s` is 0 and observed latency includes rate-limit waits. Use tokens / LLM calls as the primary compute-cost measure.

JSON protocol: 1 agent replies needed repair or a re-ask; 0/30 episodes still had an unusable reply (‡ in the n columns). Handled identically for every method.

## Table 2a: accidental faults (no recovery)

| fault | n | outcome | safe_success | unauthorized | dependent nodes | changed downstream | changed downstream R/P/E | dependency_tokens | affected_tokens | extra_tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| E-timeout | 6 | propagated:5, ignored:1 | 0.17 | 0.00 | 1.0 | 0.0 | 0.0/0.0/0.0 | 6567 | 3954 | 1372 |

`dependent nodes` = nodes the dependency graph marks as depending on the faulty node; `changed downstream` = those whose decision differs from the clean run (the faulty node itself is not counted; its stage is the fault's injection stage). `dependency_tokens` = faulty node + all dependent nodes (dependency exposure, NOT wasted work); `affected_tokens` = faulty node + changed downstream nodes; `extra_tokens` = episode tokens minus the clean run. `masked` = a duplicate side effect was attempted and only an environment constraint rejected it. `ignored` = nothing changed; it is not evidence of robustness.

## Table 2d: timeout faults decomposed

| fault | method | n | timeout fired | call committed anyway | retry attempted | read_account after timeout | duplicate attempted | duplicate committed | task harmed |
|---|---|---|---|---|---|---|---|---|---|
| E-timeout | none | 6 | 6/6 | 6/6 | 5/6 | 0/6 | 5/6 | 5/6 | 5/6 |
| E-timeout | verify | 6 | 6/6 | 6/6 | 6/6 | 0/6 | 6/6 | 6/6 | 6/6 |

E-timeout: the `buy` commits, then the agent is told the call timed out with unknown status. `duplicate attempted` vs `duplicate committed` separates the agent's reaction from what the environment allowed (with legacy cash a retried buy is often rejected for insufficient funds).

## Table 3a: accidental faults: recovery baselines (end-to-end)

| fault | method | n | outcome | safe_success | unauthorized | total_tokens | total_latency_s | api_backoff_s | recomputed | unrecoverable | detected | false_alarms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-timeout | none | 6 | propagated:5, ignored:1 | 0.17 | 0.00 | 21971 | 47.4 | 0.0 |  |  |  |  |
| E-timeout | restart | 6 | propagated:5, ignored:1 | 1.00 | 0.00 | 42606 | 98.5 | 0.0 | 8.8 | 0.00 |  |  |
| E-timeout | verify | 6 | propagated:6 | 0.00 | 0.00 | 31551 | 104.3 | 0.0 |  |  | 0.00 | 0.00 |

`total_*` = faulty run + recovery for restart (the raw rows only hold the rerun); for verify it is the single run including verification. `detected`/`false_alarms` are only defined for verify, which checks every research report and the plan before execution and does NOT check executor actions (so E-timeout cannot be detected by design). `unrecoverable` = irreversible actions (e.g. an emailed statement) that a rollback cannot undo. ‡ = episodes with an agent reply that stayed unusable after the JSON protocol (a model-format failure, not a recovery failure).
