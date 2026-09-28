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


@dataclass(frozen=True)
class CanaryRollback:
    patch_id: str
    parent_state_hash: str
    candidate_state_hash: str
    reason_digest: str
    evidence_digest: str

    def __post_init__(self) -> None:
        if not all((self.patch_id, self.parent_state_hash, self.candidate_state_hash,
                    self.reason_digest, self.evidence_digest)):
            raise ValueError("rollback evidence identity is required")

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id, self.parent_state_hash, self.candidate_state_hash,
            self.reason_digest, self.evidence_digest,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvolutionOutcome:
    patch_id: str
    parent_state_hash: str
    candidate_state_hash: str
    decision: CanaryDecision
    evidence_digest: str
    outcome_digest: str

    def __post_init__(self) -> None:
        if not all((self.patch_id, self.parent_state_hash, self.candidate_state_hash,
                    self.evidence_digest, self.outcome_digest)):
            raise ValueError("evolution outcome identity is required")
        if self.decision is CanaryDecision.OBSERVE:
            raise ValueError("evolution outcome must be terminal")

    @classmethod
    def from_commit(cls, observation: CanaryObservation) -> "EvolutionOutcome":
        if observation.decision is not CanaryDecision.COMMIT or not observation.verified():
            raise ValueError("commit outcome requires verified canary")
        return cls(observation.patch_id, observation.parent_state_hash,
                   observation.candidate_state_hash, observation.decision,
                   observation.verification_digest, observation.digest())

    @classmethod
    def from_rollback(cls, rollback: CanaryRollback) -> "EvolutionOutcome":
        return cls(rollback.patch_id, rollback.parent_state_hash,
                   rollback.candidate_state_hash, CanaryDecision.ROLLBACK,
                   rollback.evidence_digest, rollback.digest())
