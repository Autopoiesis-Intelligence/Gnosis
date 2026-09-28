"""Evaluation contract for safely advancing an evolution patch."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from .evolution_canary import CanaryDecision, CanaryObservation, validate_canary_transition


class EvolutionDecision(str, Enum):
    REJECT = "reject"
    CANARY = "canary"
    COMMIT = "commit"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class EvolutionEvaluation:
    patch_id: str
    parent_state_hash: str
    candidate_state_hash: str
    expected_effect_digest: str
    observed_effect_digest: str
    verification_digest: str
    decision: EvolutionDecision
    canary_digest: str = ""

    def __post_init__(self) -> None:
        if not all((
            self.patch_id,
            self.parent_state_hash,
            self.candidate_state_hash,
            self.expected_effect_digest,
            self.observed_effect_digest,
            self.verification_digest,
        )):
            raise ValueError("evolution evaluation identity is required")

    def validate(self) -> None:
        if self.decision is EvolutionDecision.COMMIT:
            if not self.canary_digest:
                raise ValueError("COMMIT evaluation requires canary evidence")
        elif self.decision is EvolutionDecision.CANARY:
            if self.canary_digest:
                raise ValueError("CANARY evaluation cannot claim terminal canary evidence")

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id,
            self.parent_state_hash,
            self.candidate_state_hash,
            self.expected_effect_digest,
            self.observed_effect_digest,
            self.verification_digest,
            self.decision.value,
            self.canary_digest,
        )).encode()
        return hashlib.sha256(payload).hexdigest()
