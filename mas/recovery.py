"""Recovery methods. Every method is told the identity of the faulty node (fault.target),
so recovery quality is measured independently of fault detection."""
import time

from .workflow import run_workflow


def full_restart(task, world, trace, fault):
    """Baseline: discard all work, roll the environment back to its initial state and rerun
    everything without the fault. External (irreversible) effects survive the rollback."""
    t0 = time.time()
    lost = world.restore(world.initial)
    new = run_workflow(task, world)
    return new, {"recovery_latency": time.time() - t0, "recomputed": len(new.nodes), "retained": 0,
                 "unrecoverable": len(lost), "recovery_cost": new.total_cost()}


def selective(task, world, trace, fault):
    """Phase 2 TODO: dependency-aware invalidation. Must return (new_trace, stats) with the same
    keys as `full_restart` so the harness can compare methods directly. Suggested steps:

    1. invalid = {fault.target} | trace.descendants(fault.target)
       (try both state=True / state=False, and the finer `Node.uses` edges, to study
       precision vs. bookkeeping overhead)
    2. Undo the environment effects of invalid executor nodes: e.g. take `world.snapshot()`
       before each executor node, or apply compensating actions (`sell` for `buy`, delete
       written files). Count actions in `world.state["external"]` / `irreversible` tool calls
       as unrecoverable instead of pretending they were undone.
    3. new = run_workflow(task, world, reuse={nid: n for nid, n in trace.nodes.items() if nid not in invalid})
       Note the plan may produce different steps after rerun; reused exec nodes must still match.
    4. Check that reused results really remain valid (e.g. compare against a clean run).
    """
    raise NotImplementedError


METHODS = {"restart": full_restart, "selective": selective}
