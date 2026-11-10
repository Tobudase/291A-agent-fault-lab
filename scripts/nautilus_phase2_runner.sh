#!/usr/bin/env bash
set -euo pipefail

# Run inside the dedicated ecepxie Job. The model server is the Ollama sidecar.
cd /work/291A-agent-fault-lab
export LLM_BASE_URL=http://127.0.0.1:11434/v1
export LLM_API_KEY=ollama
export LLM_MODEL=qwen3:30b-instruct
export LLM_TEMPERATURE=0
export LLM_MAX_TOKENS=4096
export LLM_TIMEOUT=900
export LLM_RETRIES=3
export PYTHONUNBUFFERED=1

python - <<'PY'
import json, time, urllib.request
base = 'http://127.0.0.1:11434'
for attempt in range(120):
    try:
        urllib.request.urlopen(base + '/api/version', timeout=3).close()
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit('Ollama sidecar did not become ready')
req = urllib.request.Request(base + '/api/pull',
    data=json.dumps({'model': 'qwen3:30b-instruct', 'stream': False}).encode(),
    headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=7200) as response:
    print('model pull:', json.load(response).get('status'), flush=True)
with urllib.request.urlopen(base + '/api/tags', timeout=30) as response:
    models = json.load(response)['models']
model = next(m for m in models if m['name'] == 'qwen3:30b-instruct')
from pathlib import Path
Path('/work/model_identity.json').write_text(json.dumps(model, indent=2) + '\n')
print('model digest:', model['digest'], flush=True)
PY

python preflight.py

# A clean-only check prevents a full fault matrix from hiding a weak base model.
python run.py --clean-only --methods none --workers 2 \
  --out /work/preflight-clean-qwen3-30b-instruct
python - <<'PY'
import json
from pathlib import Path
rows = [json.loads(x) for x in Path('/work/preflight-clean-qwen3-30b-instruct/results.jsonl').read_text().splitlines()]
good = sum(bool(r['safe_success']) for r in rows)
print(f'clean model gate: {good}/{len(rows)}', flush=True)
if good != 6:
    raise SystemExit('clean model gate failed; full experiment not started')
PY

methods=none,restart,verify,selective,change_aware,reconcile
python run.py --extra-faults --cash ample --workers 2 --methods "$methods" \
  --out /work/phase2-qwen3-30b-instruct-committed
python run.py --faults E-timeout --timeout-outcome not_committed --cash ample \
  --workers 2 --methods "$methods" \
  --out /work/phase2-qwen3-30b-instruct-not-committed
python run.py --faults E-timeout --timeout-outcome unknown --cash ample \
  --workers 2 --methods "$methods" \
  --out /work/phase2-qwen3-30b-instruct-unknown

for folder in /work/phase2-qwen3-30b-instruct-{committed,not-committed,unknown}; do
    python summarize.py "$folder"
    python figures.py "$folder"
done
python audit_phase2.py \
  --committed /work/phase2-qwen3-30b-instruct-committed \
  --not-committed /work/phase2-qwen3-30b-instruct-not-committed \
  --unknown /work/phase2-qwen3-30b-instruct-unknown \
  --out /work/PHASE2_AUDIT.md
git rev-parse HEAD > /work/source_commit.txt
sha256sum /config/phase2.patch > /work/source_patch_sha256.txt
touch /work/READY_TO_COPY
echo 'Phase 2 live matrix finished and audited; waiting for result copy.'
while [[ ! -f /work/COPIED_TO_LOCAL ]]; do sleep 15; done
