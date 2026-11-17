#!/usr/bin/env bash
# Run inside the dedicated Nautilus runner after unpacking the evaluation source.
set -euo pipefail
cd "$(dirname "$0")/.."
root=${1:?supply a new or matching remote results directory}
mkdir -p "$root"
python -m pip install --disable-pip-version-check -r requirements-final.lock > "$root/dependency-install.log" 2>&1
python -m pip freeze > "$root/dependencies.txt"
sha256sum evaluation/holdout.{json,py} evaluation/tracking.py > "$root/protocol.sha256"
python -m evaluation.tracking /work/final-1117/release/committed "$root/tracking.json"
for rep in 1 2 3; do
  python -m evaluation.holdout "$root/repeat-$rep" --resume
done
date -u > "$root/RUNNER_FINISHED"
