import copy
import json
from pathlib import Path

from analysis import load
from mas import tasks as tasks_mod
from mas.faults import schedule
from mas.recovery import METHODS
from mas.tasks import TASKS
from rescore import rescore
from run import run_clean, run_fault, load_row


def test_saved_results_resume_and_rescore(tmp_path, monkeypatch):
    monkeypatch.setattr(tasks_mod, 'CASH_MODE', 'ample')
    methods = set(METHODS) | {'none', 'verify'}
    task = TASKS[0]
    clean, ok, rows = run_clean(task, methods, str(tmp_path))
    fault = next(f for f in schedule(task) if f.name == 'R-incorrect')
    rows += run_fault(task, fault, clean, ok, methods, str(tmp_path))
    result_file = tmp_path / 'results.jsonl'
    result_file.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    derived = load(str(tmp_path))
    base = next(r for r in rows if r['fault'] == 'R-incorrect' and r['method'] == 'none')
    for row in derived:
        if row['method'] in METHODS:
            assert row['total_tokens'] == base['tokens'] + row['recovery_tokens']
            assert load_row(str(tmp_path), task, 'R-incorrect', row['method']) is not None
    resumed = run_fault(task, fault, clean, ok, methods, str(tmp_path), resume=True)
    assert len(resumed) == len(METHODS) + 2
    rescore(str(tmp_path))
    rescored = load(str(tmp_path))
    for before, after in zip(derived, rescored):
        assert before['total_tokens'] == after['total_tokens']
        assert before['safe_success'] == after['safe_success']
        if before['method'] in METHODS:
            assert before['recovery_status'] == after['recovery_status']
    snapshot = result_file.read_text()
    rescore(str(tmp_path))
    assert result_file.read_text() == snapshot


def test_resume_rejects_config_change(tmp_path, monkeypatch):
    task = TASKS[0]
    run_clean(task, {'none'}, str(tmp_path))
    p = tmp_path / 'T1/clean/none/trace.json'
    data = json.loads(p.read_text())
    data['metrics']['config']['signature'] = 'different'
    p.write_text(json.dumps(data))
    assert load_row(str(tmp_path), task, 'clean', 'none') is None
