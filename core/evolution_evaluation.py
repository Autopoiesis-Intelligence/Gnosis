"""Evaluation contract for safely advancing an evolution patch."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


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

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id,
            self.parent_state_hash,
            self.candidate_state_hash,
            self.expected_effect_digest,
            self.observed_effect_digest,
            self.verification_digest,
            self.decision.value,
        )).encode()
        return hashlib.sha256(payload).hexdigest()
