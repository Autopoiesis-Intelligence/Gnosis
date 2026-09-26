"""Deterministic replay with fail-closed state/hash binding."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .execution_contract import state_digest
from .history import AppendOnlyHistory, TransitionRecord
from .state import Psi

TransitionApplier = Callable[[Psi, TransitionRecord], Psi]


@dataclass(frozen=True)
class ReplayResult:
    state: Psi
    applied: int


def replay(
    genesis: Psi,
    history: AppendOnlyHistory,
    apply: TransitionApplier,
) -> ReplayResult:
    """Reconstruct state while binding every applied record to causal hashes."""
    if not isinstance(genesis, Psi):
        raise TypeError("replay requires a canonical Psi genesis state.")
    if apply is None or not callable(apply):
        raise TypeError("replay requires an explicit transition applier.")

    state = genesis

    for index, record in enumerate(history.records):
        if record.sequence != index:
            raise ValueError("replay sequence is not contiguous.")

        if index == 0:
            if record.previous_hash != "genesis":
                raise ValueError("replay genesis record has invalid previous_hash.")
        else:
            actual_previous = state_digest(state)
            if actual_previous != record.previous_hash:
                raise ValueError("replay state does not match record.previous_hash.")

        next_state = apply(state, record)
        if not isinstance(next_state, Psi):
            raise TypeError("replay applier must return Psi.")

        actual_next = state_digest(next_state)
        if actual_next != record.state_hash:
            raise ValueError("replay result does not match record.state_hash.")

        if record.candidate_hash != record.state_hash:
            raise ValueError("replay candidate_hash is not bound to state_hash.")

        state = next_state

    return ReplayResult(state=state, applied=len(history.records))
