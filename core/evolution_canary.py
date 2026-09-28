"""Canary lifecycle for evolution candidates without canonical mutation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib


class CanaryDecision(str, Enum):
    OBSERVE = "observe"
    COMMIT = "commit"
    ROLLBACK = "rollback"


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

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id, self.parent_state_hash, self.candidate_state_hash,
            self.observed_effect_digest, self.verification_digest,
            self.decision.value,
        )).encode()
        return hashlib.sha256(payload).hexdigest()
