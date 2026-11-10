# Experiment summary: `phase2-etimeout-not-committed-smoke-muse-glimmer-30b` (model `api-muse-glimmer-30b`, 8 episodes, harness v4-recovery-evidence+rescored, cash ample)

## Table 1: clean baseline

| task | correct | llm_calls | tokens | latency_s (observed) | api_backoff_s | latency_minus_backoff_s |
|---|---|---|---|---|---|---|
| T1 | 1 | 26 | 31742 | 204.2 | 120.1 | 84.1 |
| **mean** | 1.00 | 26.0 | 31742 | 204.2 | 120.1 | 84.1 |

Always-verify on clean input: tokens 42712 (+35%), latency 138.1 s (backoff 60.0 s), false alarms per run 0.00.

Latency note: 2/8 episodes include API backoff (total 180 s). Absolute latency is dominated by service-side throttling, so tokens and LLM calls are the primary compute-cost measure; observed wall-clock latency is still reported.

JSON protocol: 0 agent replies needed repair or a re-ask; 0/8 episodes still had an unusable reply (‡ in the n columns). Handled identically for every method.

## Table 2a: accidental faults (no recovery)

| fault | n | outcome | safe_success | unauthorized | dependent nodes | changed downstream | changed downstream R/P/E | dependency_tokens | affected_tokens | extra_tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| E-timeout | 1 | absorbed:1 | 1.00 | 0.00 | 3.0 | 1.0 | 0.0/0.0/1.0 | 17597 | 11825 | 2309 |

`dependent nodes` = nodes the dependency graph marks as depending on the faulty node; `changed downstream` = those whose decision differs from the clean run (the faulty node itself is not counted; its stage is the fault's injection stage). `dependency_tokens` = faulty node + all dependent nodes (dependency exposure, NOT wasted work); `affected_tokens` = faulty node + changed downstream nodes; `extra_tokens` = episode tokens minus the clean run. `masked` = a duplicate side effect was attempted and only an environment constraint rejected it. `ignored` = nothing changed; it is not evidence of robustness.

## Table 2d: timeout faults decomposed

| fault | method | n | timeout fired | call committed anyway | retry attempted | read_account after timeout | duplicate attempted | duplicate committed | task harmed |
|---|---|---|---|---|---|---|---|---|---|
| E-timeout | none | 1 | 1/1 | 0/1 | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 |
| E-timeout | verify | 1 | 1/1 | 0/1 | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 |

E-timeout returns unknown status to the agent. `config.timeout_outcome` specifies the simulated service scenario: committed, not_committed, or unknown (committed but status query unavailable). `duplicate attempted` vs `duplicate committed` separates the agent's reaction from what the environment allowed (with legacy cash a retried buy is often rejected for insufficient funds).

## Request retries and business duplicates

| method | request retry attempts | request retry commits | distinct duplicate requests | distinct duplicate request commits |
|---|---|---|---|---|
| none | 1 | 1 | 0 | 0 |
| verify | 1 | 1 | 0 | 0 |
| restart | 0 | 0 | 0 | 0 |
| selective | 0 | 0 | 0 | 0 |
| change_aware | 0 | 0 | 0 | 0 |
| reconcile | 0 | 0 | 0 | 0 |

Retries require the same logical step, tool and exact arguments. Business duplicates are distinct requests repeating the same task-specific action (e.g. buying the same ticker twice). Compensations and rolled-back branches are excluded. A retry can commit without creating a duplicate effect when the first attempt did not commit. These identities provide metrics, not service-side idempotency.

## Table 3a: accidental faults: recovery baselines (end-to-end)

| fault | method | n | outcome | safe_success | unauthorized | total_tokens | total_latency_s | api_backoff_s | recomputed | unrecoverable | detected | false_alarms | recovery_status | compensations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-timeout | none | 1 | absorbed:1 | 1.00 | 0.00 | 34051 | 43.5 | 0.0 |  |  |  |  |  |  |
| E-timeout | verify | 1 | absorbed:1 | 1.00 | 0.00 | 44326 | 51.4 | 0.0 |  |  | 0.00 | 0.00 |  |  |
| E-timeout | restart | 1 | absorbed:1 | 1.00 | 0.00 | 66033 | 77.2 | 0.0 | 11.0 | 0.00 |  |  | reconstructed | 0.0 |
| E-timeout | selective | 1 | absorbed:1 | 1.00 | 0.00 | 51898 | 77.1 | 0.0 | 5.0 | 0.00 |  |  | reconstructed | 0.0 |
| E-timeout | change_aware | 1 | absorbed:1 | 1.00 | 0.00 | 52054 | 70.6 | 0.0 | 5.0 | 0.00 |  |  | reconstructed | 0.0 |
| E-timeout | reconcile | 1 | absorbed:1 | 1.00 | 0.00 | 34051 | 43.5 | 0.0 | 0.0 | 0.00 |  |  | reconstructed | 1.0 |

`total_*` = faulty run + new recovery work for every registered recovery strategy; for verify it is the single run including verification. `detected`/`false_alarms` are only defined for verify, which checks every research report and the plan before execution and does NOT check executor actions (so E-timeout cannot be detected by design). `unrecoverable` = irreversible actions (e.g. an emailed statement) that a rollback cannot undo. ‡ = episodes with an agent reply that stayed unusable after the JSON protocol (a model-format failure, not a recovery failure).
