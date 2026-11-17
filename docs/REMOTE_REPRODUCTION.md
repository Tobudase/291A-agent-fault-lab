# Remote reproduction

Run orchestration, deterministic tests and model experiments on Nautilus, namespace
`ecepxie`, using a dedicated project pod/PVC. Do not run the workflows on a laptop.
The November 17 run used `python:3.11-bookworm`, 2 CPU cores / 4 GiB RAM, the existing
`cse291-phase2-qwen30b` PVC and the school Muse API (no GPU allocation needed).

1. Check out the final branch and install `pip install -r requirements-final.lock`.
2. Supply the school's existing API credentials through a Kubernetes Secret or the
   remote process environment, never a committed `.env` file. Set `LLM_MODEL=api-muse-glimmer-30b`,
   `LLM_TEMPERATURE=0`. API inference runs on the school service.
3. If the endpoint still omits its intermediate TLS certificate, use
   `export SSL_CERT_FILE=$(bash scripts/prepare_api_ca.sh /work/project-certs)`.
   This verifies the intermediate signature against certifi's root store; it does
   not disable hostname or certificate verification. A working complete server
   certificate chain needs no workaround.
4. Run `bash scripts/run_final_experiments.sh /work/phase2-final`.
   Standard matrices support matching `--resume`; completed task/fault groups
   must have matching source IDs. An interrupted drift run has no final manifest:
   preserve that partial directory separately before repeating the whole case.
5. Run `python analyze_phase2_provenance.py --run /work/phase2-final/committed --out /work/phase2-final/PROVENANCE.md`.
6. Run `python reporting/final_report.py /work/phase2-final`.
7. Copy the result directory back, verify `SHA256SUMS.json`, and retain the code
   commit, dependency lock, test/preflight logs and execution source identity.

`LIVE_RUNS_COMPLETE` means the runner reached its last experiment. Only a passing
`RELEASE_AUDIT.json` means the complete artifacts passed the independent release
checks. Neither marker implies all recovery methods succeeded.

Temporary runner pods and the run-specific API Secret can be removed after the
result copy is verified. Keep the shared project PVC and all historical results.
