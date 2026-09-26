"""Canonical admission chain tying safety, gas, provenance and semantic commit."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .admission import Admission, require_admitted
from .canonical_boundary import canonicalize_psi
from .commit_contract import CommitResult, commit_once
from .gas import GasBudget
from .history import AppendOnlyHistory, TransitionRecord
from .mutation_guard import guard_transition
from .provenance import Provenance
from .safety import SafetyGate
from .state import Psi


@dataclass(frozen=True)
class CanonicalAdmission:
    history: AppendOnlyHistory
    record: TransitionRecord
    provenance: Provenance
    gas: GasBudget


def _state_hash(psi: Psi) -> str:
    from .execution_contract import state_digest

    return state_digest(psi)


def _evidence_hash(admission: Admission) -> str:
    payload = repr(sorted(admission.proof.evidence.items())).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def admit_transition(
    history: AppendOnlyHistory,
    record: TransitionRecord,
    provenance: Provenance,
    current_state,
    next_state,
    operation_count: int,
    gas_costs: tuple[int, ...],
    gate: SafetyGate | None = None,
    gas_limit: int = 20,
) -> CommitResult:
    """Universal pre-commit gate for an already constructed causal record."""
    guard_transition(
        record,
        provenance,
        operation_count=operation_count,
        gas_costs=gas_costs,
        gate=gate,
        gas_limit=gas_limit,
    )
    return commit_once(history, record, current_state, next_state)


def commit_admitted_psi(
    history: AppendOnlyHistory,
    previous: Psi,
    admission: Admission,
    *,
    kernel_version: str,
    operation_count: int = 1,
    gas_costs: tuple[int, ...] = (1,),
    gate: SafetyGate | None = None,
    gas_limit: int = 20,
) -> CommitResult[Psi]:
    """Compose Ψ semantic invariants with the universal canonical gate.

    This is the sole composition point between Ψ-specific admission and the
    generic safety/gas/provenance/commit boundary.
    """
    candidate = require_admitted(admission)
    canonical = canonicalize_psi(candidate)
    head = history.head

    if head is not None and _state_hash(previous) != head.state_hash:
        raise ValueError("previous Psi does not match history head.")

    sequence = 0 if head is None else head.sequence + 1
    previous_hash = "genesis" if head is None else head.state_hash
    next_hash = _state_hash(canonical.psi)
    evidence_hash = _evidence_hash(admission)

    record = TransitionRecord(
        sequence=sequence,
        previous_hash=previous_hash,
        state_hash=next_hash,
        kernel_version=kernel_version,
        candidate_hash=next_hash,
        admitted=True,
        evidence_hash=evidence_hash,
    )
    provenance = Provenance(
        candidate_hash=next_hash,
        evidence_hash=evidence_hash,
        kernel_version=kernel_version,
    )
    return admit_transition(
        history,
        record,
        provenance,
        previous,
        canonical.psi,
        operation_count,
        gas_costs,
        gate,
        gas_limit,
    )
