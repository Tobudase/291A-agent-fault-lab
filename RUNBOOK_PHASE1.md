# Phase 1 runbook

Reproduces the two result folders the Phase 1 report is built from:

| folder | episodes | what |
|---|---|---|
| `runs/phase1-v2-muse-glimmer-30b` | 156 | 6 tasks × 8 faults (7 + R-distractor control) × {none, restart, verify} + clean runs |
| `runs/etimeout-ample-muse` | 30 | E-timeout with `--cash ample` (+ its clean runs) |

Setup used: Muse Glimmer 30B (`api-muse-glimmer-30b`) on UCSD TritonAI, temperature 0, one run per cell.
These are the code defaults, so only the API key has to be set.

## 1. Setup (once)

```bash
pip install -r requirements.txt        # openai, matplotlib
```
Run every command from the repo folder. Set the key in the shell you run from (never commit it; `.gitignore`
excludes `.env` and `*.key`):

```bash
export OPENAI_API_KEY="<your key>"      # Windows cmd: set OPENAI_API_KEY=<your key>
```

## 2. Smoke test (about 2 minutes)

```bash
python run.py --tasks T1 --faults R-incorrect --out runs/scratch/smoke
```
The first line must read `model=api-muse-glimmer-30b base_url=https://tritonai-api.ucsd.edu/v1 temperature=0.0`.
Expect `correct=True` for the clean run and `outcome=propagated` for the faulty run.

## 3. Main run (about 45 min with 4 workers)

```bash
python run.py --extra-faults --workers 4 --out runs/phase1-v2-muse-glimmer-30b
python summarize.py runs/phase1-v2-muse-glimmer-30b
python figures.py runs/phase1-v2-muse-glimmer-30b
```
`--extra-faults` adds the R-distractor control. With `--workers 1` the run takes about 2 h; rate-limit waits are
recorded separately as `backoff_s`, so parallel workers do not distort the latency columns.

## 4. Controlled E-timeout (about 10 min)

```bash
python run.py --faults E-timeout --cash ample --workers 4 --out runs/etimeout-ample-muse
python summarize.py runs/etimeout-ample-muse
```
Different starting cash, so always a separate folder (the summary warns if cash modes are mixed).

## 5. Outputs

- `results.jsonl`: one row per episode (metrics defined in README "Metrics").
- `summary.md`: Table 1 clean baseline, 2a/2b propagation (accidental / adversarial), 2c relevance control,
  2d timeout decomposition, 3a/3b recovery baselines.
- `figs/`: architecture, propagation path, outcomes, cost vs. correctness, dependency precision, heatmap (PNG + PDF).
- `<task>/<fault>/<method>/trace.json`: messages, artifacts (with pre-fault versions), tool actions, dependency edges.

## 6. Notes and known issues

- **Interrupted run / `[FAILED]` lines:** rerun the same command with `--resume`; finished episodes are skipped
  (only episodes saved by the same code version are reused). Failures are listed in `failures.log`.
- **Not bit-identical:** the hosted model can give different replies at temperature 0, so a rerun can differ in
  individual episodes. `python rescore.py <folder>` recomputes the metrics from saved traces exactly (no LLM calls).
- **Malformed JSON** from an agent is repaired (unclosed brackets) or re-asked once, for every method alike; the
  summary reports how often (`JSON protocol` line). The verifier is fail-closed.
- **OneDrive folders** sync the trace files during a run. If you get "permission denied", pause syncing.
- **Other models:** set `LLM_MODEL` (and `LLM_BASE_URL`); `phase1_local.py` runs the grid on a local Ollama model.
  Results from another model belong in their own folder.
