"""Public strategy registry and compatibility adapters for the experiment harness."""
import copy

from .recover.contracts import RecoveryContext
from .recover.engine import recover
from .recover.selective import Restart, Selective
from .recover.change_aware import ChangeAware
from .recover.reconcile import Reconcile

STRATEGIES = {}
METHODS = {}


def register(strategy):
    if strategy.name in METHODS:
        raise ValueError('duplicate recovery strategy: ' + strategy.name)
    STRATEGIES[strategy.name] = strategy

    def run(task, world, trace, fault):
        old = copy.deepcopy(trace)
        # The diagnostic identifies the failed node, not its corrected answer.
        for node in old.nodes.values():
            node.original = None
            for a in node.actions:
                a.pop('raw_result', None)
                a.pop('state_changed', None)
        # Preserve receipt equality without exposing injection-only oracle fields.
        source = copy.deepcopy(world)
        for a in source.log:
            a.pop('raw_result', None)
            a.pop('state_changed', None)
        result = recover(RecoveryContext(task, old, fault.target), source, strategy)
        if result.stats['recovery_status'] != 'stopped':
            world.state, world.log = source.state, source.log
        return result.trace, result.stats

    METHODS[strategy.name] = run
    return run


full_restart = register(Restart())
selective = register(Selective())
change_aware = register(ChangeAware())
reconcile = register(Reconcile())
