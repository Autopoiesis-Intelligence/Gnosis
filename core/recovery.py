"""Fail-closed recovery from durable history into derived semantic state.

Durable persistence is a substrate, not semantic authority. Recovery first
loads and validates the append-only history, then derives Psi by deterministic
replay. A persisted record never becomes trusted merely because it exists.
"""
from __future__ import annotations

from collections.abc import Callable

from .history import AppendOnlyHistory
from .replay import ReplayResult, replay
from .sqlite_persistence import SQLiteHistoryStore
from .state import Psi

TransitionApplier = Callable[[Psi, object], Psi]


def recover_psi(
    genesis: Psi,
    store: SQLiteHistoryStore,
    apply: TransitionApplier,
) -> ReplayResult:
    """Recover semantic state from validated durable history."""
    if not isinstance(store, SQLiteHistoryStore):
        raise TypeError("recovery requires SQLiteHistoryStore.")
    history: AppendOnlyHistory = store.load()
    return replay(genesis, history, apply)
