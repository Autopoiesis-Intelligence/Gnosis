"""Canary lifecycle for evolution candidates without canonical mutation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib


class CanaryDecision(str, Enum):
    OBSERVE = "observe"
    COMMIT = "commit"
    ROLLBACK = "rollback"


_ALLOWED_TRANSITIONS = {
    CanaryDecision.OBSERVE: frozenset((CanaryDecision.COMMIT, CanaryDecision.ROLLBACK)),
    CanaryDecision.COMMIT: frozenset(),
    CanaryDecision.ROLLBACK: frozenset(),
}


@dataclass(frozen=True)
class CanaryObservation:
    patch_id: str
    parent_state_hash: str
    candidate_state_hash: str
    observed_effect_digest: str
    verification_digest: str
    decision: CanaryDecision

    def __post_init__(self) -> None:
        if not all((self.patch_id, self.parent_state_hash, self.candidate_state_hash,
                    self.observed_effect_digest, self.verification_digest)):
            raise ValueError("canary observation identity is required")

    def verified(self) -> bool:
        return bool(self.observed_effect_digest and self.verification_digest)

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id, self.parent_state_hash, self.candidate_state_hash,
            self.observed_effect_digest, self.verification_digest,
            self.decision.value,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


def validate_canary_transition(current: CanaryDecision, requested: CanaryDecision) -> None:
    """Allow only terminal transitions from an observed canary."""
    if requested not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(
            f"invalid canary transition: {current.value} -> {requested.value}"
        )
