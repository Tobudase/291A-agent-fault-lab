"""Researcher -> Planner -> Executor workflow with fault injection, verification and node reuse."""
from . import agents
from .faults import mutate, tool_hook
from .trace import Trace, add_cost


def run_workflow(task, world, fault=None, verify=False, reuse=None):
    """Run the whole workflow on `world` and return its Trace.

    fault  : Fault to inject (or None for a clean run)
    verify : "always verify" baseline - check every research report and the plan, regenerate once on FAIL
    reuse  : {node_id: Node} results to keep instead of recomputing (hook for Phase 2 selective recovery;
             the caller is responsible for `world` already reflecting the effects of reused executor nodes)
    """
    reuse = reuse or {}
    trace = Trace(task.id)
    world.tool_hook = tool_hook(fault) if fault else None

    def produce(nid, make):
        if nid in reuse:
            trace.add(reuse[nid])
            return reuse[nid]
        node = make()
        if fault and fault.target == nid:
            mutate(fault, node, task.client_id)
            node.fault = fault.name if fault.fired else None
            fault.done = True  # later regenerations of this node are clean
        if verify and node.agent in ("researcher", "planner"):
            verdict, vcost = agents.verify(task, node, world, trace)
            if verdict["verdict"] == "FAIL":
                old, node = node, make()
                node.cost, node.attempt = add_cost(old.cost, node.cost), 1
                node.fault = old.fault  # keep provenance: this id was faulty at first
            node.verdict, node.verify_cost = verdict, vcost
        trace.add(node)
        return node

    research = [produce(f"research:{t}", lambda t=t: agents.research(task, t, world)) for t in task.tickers]
    p = produce("plan", lambda: agents.plan(task, research))
    for i, step in enumerate(p.data or []):
        produce(f"exec:{i}", lambda i=i, step=step: agents.execute(task, i, step, world))
    world.tool_hook = None
    return trace
