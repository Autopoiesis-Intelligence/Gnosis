"""Separate contracts for need-driven core creation and evolution patches."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


class CoreCreationReason(str, Enum):
    NEW_CAPABILITY = "new_capability"
    NEW_OPERATION = "new_operation"
    SPECIALIZATION = "specialization"
    ISOLATION = "isolation"
    RELIABILITY = "reliability"
    DOMAIN_EXPANSION = "domain_expansion"
    PRODUCT_REQUIREMENT = "product_requirement"


@dataclass(frozen=True)
class CoreCreationRequest:
    request_id: str
    parent_core_id: str
    capability: str
    reason: CoreCreationReason
    need_digest: str
    scope: str

    def digest(self) -> str:
        payload = "|".join((
            self.request_id, self.parent_core_id, self.capability,
            self.reason.value, self.need_digest, self.scope,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvolutionPatchCandidate:
    patch_id: str
    target_core_id: str
    target_core_hash: str
    parent_state_hash: str
    analytics_digest: str
    hypothesis: str
    expected_effect: str
    patch_digest: str

    def __post_init__(self) -> None:
        if not all((
            self.patch_id, self.target_core_id, self.target_core_hash,
            self.parent_state_hash, self.analytics_digest,
            self.hypothesis, self.expected_effect, self.patch_digest,
        )):
            raise ValueError("evolution patch identity is required")

    def digest(self) -> str:
        payload = "|".join((
            self.patch_id, self.target_core_id, self.target_core_hash,
            self.parent_state_hash, self.analytics_digest,
            self.hypothesis, self.expected_effect, self.patch_digest,
        )).encode()
        return hashlib.sha256(payload).hexdigest()
