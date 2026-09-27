from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping
import hashlib


Invariant = Callable[[Any], bool]


@dataclass(frozen=True)
class ProofObligation:
    """Minimal, explicit proof result for a proposed state transition.

    The proof layer does not generate candidates and does not select one.
    Callers provide the already-generated candidate pool and an invariant.
    """

    passed: bool
    invariant: bool
    viable: bool
    evidence: Mapping[str, Any]
    candidate_digest: str


def _candidate_digest(candidate: Any) -> str:
    canonical = candidate.to_psi() if hasattr(candidate, "to_psi") else candidate
    return hashlib.sha256(repr(canonical).encode("utf-8")).hexdigest()


def _strict_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must return bool exactly.")
    return value


def _invariant(invariant: Invariant, candidate: Any) -> bool:
    return _strict_bool(invariant(candidate), name="Invariant")


def _viable(
    current: Any,
    candidate: Any,
    candidates: Iterable[Any],
    invariant: Invariant,
) -> bool:
    """Depth-1 viability: fixed points are valid; changes need continuation."""
    if candidate == current:
        return True

    for continuation in candidates:
        if continuation == candidate:
            continue
        if _invariant(invariant, continuation):
            return True
    return False



def prove_fundamental_transition(
    current: Any,
    candidate: Any,
    invariant: Invariant,
) -> ProofObligation:
    """Prove a fundamental Psi transition without evolutionary viability.

    Fundamental transitions have no candidate pool. Their semantic proof is
    therefore limited to the candidate invariant; transition/result binding is
    enforced by the canonical executor.
    """
    invariant_ok = _invariant(invariant, candidate)
    return ProofObligation(
        passed=invariant_ok,
        invariant=invariant_ok,
        viable=False,
        candidate_digest=_candidate_digest(candidate),
        evidence={
            "regime": "fundamental",
            "fixed_point": candidate == current,
            "viability": "not_applicable",
        },
    )

def prove_transition(
    current: Any,
    candidate: Any,
    candidates: Iterable[Any],
    invariant: Invariant,
) -> ProofObligation:
    """Return a reproducible depth-1 proof for a proposed transition.

    An invariant-valid unchanged candidate is a fixed point. An invariant-valid
    changing candidate requires a distinct invariant-valid continuation.
    No generation, selection, or hidden state occurs here.
    """
    pool = tuple(candidates)
    invariant_ok = _invariant(invariant, candidate)
    fixed_point = candidate == current
    viable_ok = invariant_ok and _viable(current, candidate, pool, invariant)
    has_distinct_continuation = any(
        continuation != candidate and _invariant(invariant, continuation)
        for continuation in pool
    )

    evidence = {
        "candidate_count": len(pool),
        "has_distinct_continuation": has_distinct_continuation,
        "fixed_point": fixed_point,
        "depth": 1,
    }
    return ProofObligation(
        passed=invariant_ok and viable_ok,
        invariant=invariant_ok,
        viable=viable_ok,
        candidate_digest=_candidate_digest(candidate),
        evidence=evidence,
    )
