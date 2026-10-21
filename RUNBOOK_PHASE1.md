# Phase 1 runbook

Phase 1 runs the full grid (6 tasks × 7 faults × {none, restart, verify} plus clean runs = 138 episodes) for one
model, then builds `summary.md` (Tables 1–3) and figures. Two ways to run it:

- **A. School API (UCSD TritonAI):** what produced the main results (Muse Glimmer 30B).
- **B. Local model with Ollama:** what produced the Qwen3-4B comparison run (Colab T4 GPU or a laptop).

`phase1_local.py` drives both: preflight → smoke → full → report.

## 0. The runs in the report and how each was configured

| | Muse Glimmer 30B (main) | Qwen3-4B (comparison) | Qwen3.8-27B (reference) |
|---|---|---|---|
| Where | TritonAI API | Ollama, 4-bit (Colab T4) | vLLM on the lab server |
| Model id | `api-muse-glimmer-30b` | `qwen3:4b-instruct` | `qwen3.8-27b` |
| Planner prompt | original (`steps` only) | +2 fields (`selected`, `amount_per_stock`) | original |
| Reply cap (`LLM_MAX_TOKENS`) | none | 1024 | none |
| Reasoning setting | none | none (non-thinking model) | none |
| Temperature | 0 | 0 | 0 |
| Results folder | `runs/phase1-api-muse-glimmer-30b` | `phase1-qwen3-4b` (on Google Drive) | `runs/phase1-qwen27b` |
| Clean success | 6/6 | 5/6 (T3 failed) | 6/6 |

The current repo uses the **original** planner prompt, so section A reproduces the Muse and 27B setup as-is.
Reproducing the 4B run needs the two switches in section B.3.

## 1. One-time setup

```bash
conda activate cse291a            # or your own environment
pip install -r requirements.txt   # openai, matplotlib
```

Run every command from the repo folder (`291A-multi-agent/`). On Windows, Git Bash accepts the `export` lines
below as written.

## 2. A: School API run (TritonAI)

### 2.1 Credentials
```bash
export OPENAI_BASE_URL="https://tritonai-api.ucsd.edu/v1"
export OPENAI_API_KEY="<your key>"      # never commit it; .gitignore already excludes .env and *.key
```

### 2.2 Check and estimate cost (about 2 minutes, a few cents)
```bash
python phase1_local.py --backend api --model api-muse-glimmer-30b --steps preflight,smoke
```
Check that:
- **Preflight** ends with `PASS {'plain': True, 'tool_call': True, 'json_roundtrip': True}`.
- **The settings line** reads `temperature=0.0 reasoning_effort=None` with the TritonAI address.
- **Smoke** prints `clean success: 6/6` (at least `SMOKE GO`). Smoke runs the clean baseline on all 6 tasks, with
  no faults.
- **Cost:** the line `wall=... calls=... est_cost=$X` is the cost of the smoke test only. The full run costs about
  **27 × X** (measured: smoke $0.03, so about $0.80 for the full run). `reasoning` should be 0, which means no
  hidden reasoning tokens are billed.
- **Time:** the smoke step prints a cautious time estimate (about 1 h); an API run usually takes about 35–45 min.
- **Prices:** `est_cost` uses the prices typed into `mas/llm.py` (`PRICES`). Check them against TritonAI's current
  price list.

Go/no-go: if fewer than half the clean tasks are correct, do not run the full grid. Every fault on a failed task is
reported as `clean_failed`.

### 2.3 Full run and report
```bash
python phase1_local.py --backend api --model api-muse-glimmer-30b --steps full,report
```
- Runs 4 episodes at a time. If you see 429 or rate-limit errors, add `--workers 2`.
- **Resumable:** if it stops or prints `[FAILED]` lines (also in `failures.log`), run the same command again and
  finished episodes are skipped. After a resume, the printed `est_cost` covers only the resumed part.
- Do not pass `--effort` unless every compared model uses the same value; the reference runs used none.
- Other models: use the exact id from the TritonAI model list (e.g. `--model api-glm-5.3`, which costs about
  6–8× as much per token as Muse).

## 3. B: Local run with Ollama (Qwen3-4B)

### 3.1 Where to run
| Where | How |
|---|---|
| Google Colab, free T4 GPU (used for the report) | `Phase1_Colab.ipynb` (from the 291A-multi-agent-local package): `Runtime → Change runtime type → T4 GPU`, then run all cells. Results go to Google Drive and survive disconnects. |
| Laptop with Ollama | Install the Ollama app (macOS/Windows) or run `python phase1_local.py --install` (Linux), then use the commands below. |

### 3.2 Commands
```bash
python phase1_local.py --install                                  # Linux/Colab only, once per machine or session
python phase1_local.py --model qwen3-4b --steps preflight,smoke   # check
python phase1_local.py --model qwen3-4b --steps full,report       # full grid + report
```
Useful flags:
- `--tasks T1,T2,T3` runs fewer tasks (for a CPU).
- `--workers N` sets parallel episodes (default 4 on a GPU, 1 on a CPU).
- `--out-root /content/drive/MyDrive/291A-phase1-runs` saves to Drive on Colab.
- `--force` continues even if preflight or smoke fails.

`phase1_local.py` starts `ollama serve` (context 8192), downloads the model, and points `mas/llm.py` at
`http://127.0.0.1:11434/v1`. Ollama models cost nothing. Expect about 30 min for the 4B model on a T4.

Presets: `qwen3-4b` (recommended), `qwen3-8b` and `qwen3-1.7b` (both run in no-think mode), `qwen2.5-7b`,
`llama3.2-3b`, `llama3.2-1b`. Any other `--model` value is used as a raw Ollama tag.

### 3.3 To reproduce the reported Qwen3-4B numbers
The 4B run used two settings the current repo does not use by default:

1. **Reply cap:** set it before running.
   ```bash
   export LLM_MAX_TOKENS=1024
   ```
2. **Planner prompt with two extra fields.** Without them, Qwen3-4B divided the budget by the number of candidates
   (T1: $2,500 instead of $5,000 per stock). In `mas/agents.py`, replace these two lines of `PLANNER`:
   ```
   Reply with ONLY a JSON object: {"steps": [{"instruction": str, "uses": [str]}]}
   - Apply every selection criterion in the task exactly, checking each criterion against the reports.
   ```
   with:
   ```
   Reply with ONLY a JSON object: {"selected": [str], "amount_per_stock": number, "steps": [{"instruction": str, "uses": [str]}]}
   - "selected": the candidate tickers that meet EVERY selection criterion in the task, checked against the reports.
   - "amount_per_stock": the budget divided by the number of SELECTED stocks (not the number of candidates).
   ```
   **Undo this change before any API or 27B run.** Those runs use the original prompt.

The 4B run also used a version of `mas/faults.py` that keeps the two extra fields when P-malicious rewrites the plan.
The executor receives the same steps either way; only the plan text the verifier reads differs.

## 4. Re-running the 27B reference (vLLM), if needed
`mas/llm.py` defaults to the 27B setup, so with the vLLM server running:
```bash
LLM_BASE_URL=http://localhost:8001/v1 LLM_MODEL=qwen3.8-27b python run.py --resume --out runs/phase1-qwen27b-rerun
python summarize.py runs/phase1-qwen27b-rerun
```
Set `LLM_BASE_URL` explicitly. Otherwise an `OPENAI_BASE_URL` left in your shell (e.g. on DataHub) sends the calls
to TritonAI instead. Write to a new folder so the original run is kept. Expect small differences: the hosted and
batched servers are not bit-identical even at temperature 0.

## 5. Outputs
For each run, `runs/phase1-<model>/` contains:
- `results.jsonl`: one row per episode.
- `summary.md`: Table 1 (clean baseline), Tables 2a/2b (propagation), Tables 3a/3b (recovery).
- `figs/fig1..fig6` as `.png` and `.pdf`: architecture, propagation path, outcomes, cost vs. correctness, dependency
  precision, outcome heatmap.
- `<task>/<fault>/<method>/trace.json`: messages, tool actions and dependency edges.
- `phase1-<model>_results.zip`: everything above, for download.

The report step also writes the cross-model figure `figs-compare/fig7_models` from every `phase1-*` folder under
`runs/`, plus the 27B reference. It looks for the reference at `runs/phase1-qwen`. If yours is named
`runs/phase1-qwen27b`, rename it or change line 215 of `phase1_local.py`
(`os.path.join(HERE, "runs", "phase1-qwen27b")`).

Report-ready condensed tables (Markdown + LaTeX) and renamed figures for the milestone are in `phase1_report.zip`,
built from these three runs.

## 6. Known issues
- **Malformed planner JSON.** The planner sometimes leaves off the closing `}`, so no steps are parsed and nothing
  executes: Muse 6/138 episodes, 27B 1/138, 4B 3/138. To find them, open the plan node in `trace.json`, which shows
  0 steps and a reply ending in `]`. They are footnoted (‡) in the report tables.
- **Latency on the API** includes rate-limit retry waits (often about 60 s per wait; 94/138 Muse episodes had one).
  Use tokens and LLM calls as the cost measure, and treat latency as approximate.
- **`retries=` > 0** in the run summary is normal (rate limits or brief server errors that succeeded on retry).
- **OneDrive folders** sync about 140 trace files during a run. If you get "permission denied", pause syncing.
- **`--model mock` and `--backend hf`** still appear in `phase1_local.py` but no longer work (their code was
  removed). Use `--backend api` or the default Ollama backend.
- **Smoke NO-GO on a small model:** see the printed diagnosis or `smoke-<model>/<task>/clean/none/trace.json`
  (check the plan steps and `checks`), then try a bigger preset.

## 7. Milestone report checklist (due Oct 28)
- [ ] Setup (OUTLINE §4): Muse Glimmer 30B via TritonAI, temperature 0, 138 episodes, 1 run per cell; 27B and 4B as
      comparison runs (state the 4B differences from section 0).
- [ ] Table 1 clean baseline, Table 2 propagation (accidental and adversarial separate), Table 3 restart vs. verify.
- [ ] Figure 1 architecture, Figure 2 real propagation path, Figure 3 cost vs. correctness; optionally the outcome
      bars, heatmap, dependency precision (bridge to Phase 2) and the cross-model figure.
- [ ] State: faults fire once, and fault identity is given to recovery (detection is measured separately by verify's
      detected / false alarms).
- [ ] Report unrecoverable actions (the P-malicious email) instead of counting a rerun as full recovery.
- [ ] Caveats: malformed planner JSON (‡), latency includes API waits, one run per cell.
- [ ] Phase 2 plan (OUTLINE §3.7) and the timeline appendix (OUTLINE Appendix A, with owners).