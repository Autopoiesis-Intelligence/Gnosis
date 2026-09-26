"""Fail-closed recovery from durable history, provenance and audit into derived state."""
from __future__ import annotations
from collections.abc import Callable
from .audit_chain import AuditChain
from .replay import ReplayResult, replay
from .sqlite_persistence import SQLiteHistoryStore
from .state import Psi

TransitionApplier = Callable[[Psi, object], Psi]

def recover_psi(
    genesis: Psi,
    store: SQLiteHistoryStore,
    apply: TransitionApplier,
) -> ReplayResult:
    """Verify the durable causal triple before deterministic replay."""
    if not isinstance(store, SQLiteHistoryStore):
        raise TypeError("recovery requires SQLiteHistoryStore.")
    history = store.load()
    provenance = store.load_provenance()
    audits = store.load_audit()
    if len(history.records) != len(provenance) or len(history.records) != len(audits):
        raise ValueError("durable history/provenance/audit cardinality mismatch")
    AuditChain(audits).verify_against_history(history.records, provenance)
    result = replay(genesis, history, apply)
    # Recovery is observational: it reconstructs state but cannot mutate or commit it.
    return result
