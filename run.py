"""Experiment harness: clean baseline + fault schedule x recovery methods.

  python run.py --tasks T1 --faults R-incorrect --methods none,restart,verify --out runs/smoke
"""
import argparse
import copy
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from mas import llm
from mas.env import World
from mas.faults import schedule
from mas.metrics import episode
from mas.recovery import METHODS
from mas.tasks import TASKS, TASKS_BY_ID
from mas.workflow import run_workflow


def save(out, task, fault_name, method, trace, world, metrics):
    d = os.path.join(out, task.id, fault_name, method)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "trace.json"), "w") as f:
        json.dump({"metrics": metrics, "trace": trace.to_dict(), "state": world.state, "log": world.log}, f, indent=1)


def timed(fn, *a, **kw):
    t0 = time.time()
    r = fn(*a, **kw)
    return r, time.time() - t0


def record(out, task, trace, world, m, method, fault=None):
    name = fault.name if fault else "clean"
    row = {"task": task.id, "fault": name, "method": method,
           "kind": fault.kind if fault else "-", "category": fault.category if fault else "-",
           "stage": fault.stage if fault else "-", **m}
    save(out, task, name, method, trace, world, row)
    print(f"[{task.id}] {name:12s} {method:9s} correct={m['correct']} safe={m['safe_success']} "
          f"unauth={m['unauthorized']} outcome={m.get('outcome', '-')}", flush=True)
    return row


def run_clean(task, methods, out):
    """Clean baseline (and verification on clean input -> false-alarm rate)."""
    world = World(task.client_id, task.cash)
    clean, lat = timed(run_workflow, task, world)
    m = episode(task, clean, world, lat)
    rows = [record(out, task, clean, world, m, "none")]
    if "verify" in methods:
        w = World(task.client_id, task.cash)
        tr, lat = timed(run_workflow, task, w, verify=True)
        rows.append(record(out, task, tr, w, episode(task, tr, w, lat), "verify"))
    return clean, m["safe_success"], rows


def run_fault(task, fault, clean, clean_ok, methods, out):
    rows = []
    # 1) Faulty run without recovery: measures propagation.
    f = fault.fresh()
    world = World(task.client_id, task.cash)
    trace, lat = timed(run_workflow, task, world, fault=f)
    m = episode(task, trace, world, lat, f, clean, clean_ok)
    rows.append(record(out, task, trace, world, m, "none", f))
    # 2) Recovery methods start from a copy of that same faulty run (fault identity is supplied).
    for name, method in METHODS.items():
        if name not in methods:
            continue
        w = copy.deepcopy(world)
        try:
            new, stats = method(task, w, trace, f)
        except NotImplementedError:
            continue
        rm = episode(task, new, w, stats["recovery_latency"])
        rm.update(stats, fault_outcome=m["outcome"], unauthorized_before=m["unauthorized"])
        rows.append(record(out, task, new, w, rm, name, f))
    # 3) Always-verify baseline under the same fault.
    if "verify" in methods:
        f = fault.fresh()
        w = World(task.client_id, task.cash)
        tr, lat = timed(run_workflow, task, w, fault=f, verify=True)
        rows.append(record(out, task, tr, w, episode(task, tr, w, lat, f, clean, clean_ok), "verify", f))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="all", help="comma-separated task ids or 'all'")
    ap.add_argument("--faults", default="all", help="comma-separated fault names or 'all'")
    ap.add_argument("--methods", default="none,restart,verify", help="none,restart,verify,selective")
    ap.add_argument("--out", default=f"runs/{time.strftime('%m%d-%H%M')}")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    tasks = TASKS if a.tasks == "all" else [TASKS_BY_ID[t] for t in a.tasks.split(",")]
    faults = None if a.faults == "all" else set(a.faults.split(","))
    methods = set(a.methods.split(","))
    os.makedirs(a.out, exist_ok=True)
    print(f"model={llm.MODEL} base_url={llm.BASE_URL} out={a.out}")
    with ThreadPoolExecutor(a.workers) as ex:
        cleans = list(ex.map(lambda t: run_clean(t, methods, a.out), tasks))
        jobs = [(t, f, c[0], c[1]) for t, c in zip(tasks, cleans)
                for f in schedule(t) if faults is None or f.name in faults]
        results = [c[2] for c in cleans] + list(ex.map(lambda j: run_fault(*j, methods, a.out), jobs))
    with open(os.path.join(a.out, "results.jsonl"), "w") as f:
        for row in (r for rows in results for r in rows):
            f.write(json.dumps(row) + "\n")
    print(f"wrote {a.out}/results.jsonl  ->  python summarize.py {a.out}")


if __name__ == "__main__":
    main()
