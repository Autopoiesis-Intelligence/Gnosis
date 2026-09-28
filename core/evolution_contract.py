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


@dataclass(frozen=True)
class EvolutionNeedSignal:
    signal_id: str
    core_id: str
    core_state_hash: str
    need_type: str
    analytics_digest: str
    evidence_digest: str
    scope: str

    def __post_init__(self) -> None:
        if not all((self.signal_id, self.core_id, self.core_state_hash,
                    self.need_type, self.analytics_digest,
                    self.evidence_digest, self.scope)):
            raise ValueError("evolution need signal identity is required")

    def digest(self) -> str:
        payload = "|".join((
            self.signal_id, self.core_id, self.core_state_hash,
            self.need_type, self.analytics_digest,
            self.evidence_digest, self.scope,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


def candidate_from_need(
    signal: EvolutionNeedSignal,
    patch_id: str,
    hypothesis: str,
    expected_effect: str,
    patch_digest: str,
) -> EvolutionPatchCandidate:
    if signal.need_type.strip() == "":
        raise ValueError("need type is required")
    return EvolutionPatchCandidate(
        patch_id=patch_id,
        target_core_id=signal.core_id,
        target_core_hash=signal.core_state_hash,
        parent_state_hash=signal.core_state_hash,
        analytics_digest=signal.analytics_digest,
        hypothesis=hypothesis,
        expected_effect=expected_effect,
        patch_digest=patch_digest,
    )


@dataclass(frozen=True)
class CoreCreationProposal:
    request: CoreCreationRequest
    authorization_digest: str
    capability_scope: str

    def __post_init__(self) -> None:
        if not self.authorization_digest:
            raise ValueError("core creation authorization is required")
        if not self.capability_scope:
            raise ValueError("core creation capability scope is required")


def core_creation_proposal_from_need(
    signal: EvolutionNeedSignal,
    request_id: str,
    capability: str,
    reason: CoreCreationReason,
    scope: str,
    authorization_digest: str,
) -> CoreCreationProposal:
    if signal.core_state_hash != signal.core_state_hash:
        raise ValueError("unreachable state binding")
    request = CoreCreationRequest(
        request_id=request_id,
        parent_core_id=signal.core_id,
        capability=capability,
        reason=reason,
        need_digest=signal.digest(),
        scope=scope,
    )
    return CoreCreationProposal(
        request=request,
        authorization_digest=authorization_digest,
        capability_scope=scope,
    )


class CoreLifecycle(str, Enum):
    PROPOSED = "proposed"
    AUTHORIZED = "authorized"
    INSTANTIATED = "instantiated"
    VERIFIED = "verified"
    NETWORK_ATTACHED = "network_attached"


_ALLOWED_CORE_LIFECYCLE = {
    CoreLifecycle.PROPOSED: frozenset((CoreLifecycle.AUTHORIZED,)),
    CoreLifecycle.AUTHORIZED: frozenset((CoreLifecycle.INSTANTIATED,)),
    CoreLifecycle.INSTANTIATED: frozenset((CoreLifecycle.VERIFIED,)),
    CoreLifecycle.VERIFIED: frozenset((CoreLifecycle.NETWORK_ATTACHED,)),
    CoreLifecycle.NETWORK_ATTACHED: frozenset(),
}


def validate_core_lifecycle_transition(
    current: CoreLifecycle, requested: CoreLifecycle
) -> None:
    if requested not in _ALLOWED_CORE_LIFECYCLE[current]:
        raise ValueError(
            f"invalid core lifecycle transition: "
            f"{current.value} -> {requested.value}"
        )


@dataclass(frozen=True)
class CoreLifecycleRecord:
    core_id: str
    parent_core_id: str
    state: CoreLifecycle
    capability_scope: str
    evidence_digest: str

    def __post_init__(self) -> None:
        if not all((self.core_id, self.parent_core_id,
                    self.capability_scope, self.evidence_digest)):
            raise ValueError("core lifecycle identity is required")


@dataclass(frozen=True)
class NetworkAttachment:
    core_id: str
    network_id: str
    capability_scope: str
    attachment_evidence_digest: str

    def __post_init__(self) -> None:
        if not all((self.core_id, self.network_id, self.capability_scope,
                    self.attachment_evidence_digest)):
            raise ValueError("network attachment identity is required")

    def digest(self) -> str:
        return hashlib.sha256("|".join((
            self.core_id, self.network_id, self.capability_scope,
            self.attachment_evidence_digest,
        )).encode()).hexdigest()


def attach_verified_core(
    lifecycle: CoreLifecycleRecord,
    network_id: str,
    attachment_evidence_digest: str,
) -> NetworkAttachment:
    if lifecycle.state is not CoreLifecycle.VERIFIED:
        raise ValueError("only VERIFIED cores may attach to network")
    return NetworkAttachment(
        core_id=lifecycle.core_id,
        network_id=network_id,
        capability_scope=lifecycle.capability_scope,
        attachment_evidence_digest=attachment_evidence_digest,
    )
