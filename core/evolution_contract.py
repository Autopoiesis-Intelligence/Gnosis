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


@dataclass(frozen=True)
class NetworkRegistryEntry:
    attachment: NetworkAttachment
    lifecycle_evidence_digest: str
    attachment_state: NetworkAttachmentState = NetworkAttachmentState.ATTACHED

    def __post_init__(self) -> None:
        if not self.lifecycle_evidence_digest:
            raise ValueError("network registry evidence is required")


@dataclass(frozen=True)
class NetworkRegistry:
    entries: tuple[NetworkRegistryEntry, ...] = ()

    def register(self, entry: NetworkRegistryEntry) -> "NetworkRegistry":
        if any(e.attachment.core_id == entry.attachment.core_id
               and e.attachment.network_id == entry.attachment.network_id
               for e in self.entries):
            raise ValueError("core is already registered on network")
        return NetworkRegistry(self.entries + (entry,))

    def lookup(self, network_id: str, capability_scope: str) -> tuple[NetworkRegistryEntry, ...]:
        return tuple(
            e for e in self.entries
            if e.attachment.network_id == network_id
            and e.attachment.capability_scope == capability_scope
        )

    def require_unique_route(
        self, network_id: str, capability_scope: str
    ) -> NetworkRegistryEntry:
        matches = tuple(
            e for e in self.lookup(network_id, capability_scope)
            if getattr(e, "attachment_state", NetworkAttachmentState.ATTACHED)
               is NetworkAttachmentState.ATTACHED
        )
        if len(matches) != 1:
            raise ValueError("network route must resolve to exactly one core")
        return matches[0]


@dataclass(frozen=True)
class NetworkExecutionRequest:
    network_id: str
    capability_scope: str
    operation: str
    authorization_digest: str

    def __post_init__(self) -> None:
        if not all((self.network_id, self.capability_scope, self.operation,
                    self.authorization_digest)):
            raise ValueError("network execution request identity is required")


@dataclass(frozen=True)
class NetworkExecutionBinding:
    request: NetworkExecutionRequest
    core_id: str
    attachment_digest: str

    def __post_init__(self) -> None:
        if not self.attachment_digest:
            raise ValueError("execution attachment binding is required")


def bind_network_execution(
    registry: NetworkRegistry,
    request: NetworkExecutionRequest,
) -> NetworkExecutionBinding:
    entry = registry.require_unique_route(
        request.network_id, request.capability_scope
    )
    return NetworkExecutionBinding(
        request=request,
        core_id=entry.attachment.core_id,
        attachment_digest=entry.attachment.digest(),
    )


class NetworkAttachmentState(str, Enum):
    ATTACHED = "attached"
    DETACHED = "detached"
    REVOKED = "revoked"


@dataclass(frozen=True)
class NetworkAttachmentRecord:
    attachment: NetworkAttachment
    state: NetworkAttachmentState
    state_evidence_digest: str

    def __post_init__(self) -> None:
        if not self.state_evidence_digest:
            raise ValueError("attachment state evidence is required")


def revoke_network_attachment(
    record: NetworkAttachmentRecord,
    state: NetworkAttachmentState,
    evidence_digest: str,
) -> NetworkAttachmentRecord:
    if record.state is not NetworkAttachmentState.ATTACHED:
        raise ValueError("only attached network entries may be revoked or detached")
    if state not in (NetworkAttachmentState.DETACHED, NetworkAttachmentState.REVOKED):
        raise ValueError("attachment must transition to detached or revoked")
    return NetworkAttachmentRecord(record.attachment, state, evidence_digest)


def validate_network_execution_binding(
    registry: NetworkRegistry,
    binding: NetworkExecutionBinding,
) -> NetworkRegistryEntry:
    entry = registry.require_unique_route(
        binding.request.network_id, binding.request.capability_scope
    )
    if entry.attachment.core_id != binding.core_id:
        raise ValueError("execution binding core is no longer the active network route")
    if entry.attachment.digest() != binding.attachment_digest:
        raise ValueError("execution binding attachment is stale")
    return entry


@dataclass(frozen=True)
class NetworkRegistrySnapshot:
    network_id: str
    entries: tuple[NetworkRegistryEntry, ...]
    snapshot_digest: str

    @staticmethod
    def from_registry(network_id: str, registry: NetworkRegistry) -> "NetworkRegistrySnapshot":
        entries = tuple(
            e for e in registry.entries
            if e.attachment.network_id == network_id
        )
        payload = "|".join(
            f"{e.attachment.core_id}:{e.attachment.digest()}:{e.attachment_state.value}"
            for e in entries
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return NetworkRegistrySnapshot(network_id, entries, digest)

    def active_entries(self) -> tuple[NetworkRegistryEntry, ...]:
        return tuple(
            e for e in self.entries
            if e.attachment_state is NetworkAttachmentState.ATTACHED
        )


@dataclass(frozen=True)
class CapabilityTransition:
    core_id: str
    network_id: str
    previous_scope: str
    next_scope: str
    evidence_digest: str
    authorization_digest: str

    def __post_init__(self) -> None:
        if not all((self.core_id, self.network_id, self.previous_scope,
                    self.next_scope, self.evidence_digest,
                    self.authorization_digest)):
            raise ValueError("capability transition evidence is required")
        if self.previous_scope == self.next_scope:
            raise ValueError("capability transition must change scope")


def transition_core_capability(
    entry: NetworkRegistryEntry,
    next_scope: str,
    evidence_digest: str,
    authorization_digest: str,
) -> tuple[NetworkRegistryEntry, CapabilityTransition]:
    if entry.attachment_state is not NetworkAttachmentState.ATTACHED:
        raise ValueError("only attached cores may transition capability")
    transition = CapabilityTransition(
        core_id=entry.attachment.core_id,
        network_id=entry.attachment.network_id,
        previous_scope=entry.attachment.capability_scope,
        next_scope=next_scope,
        evidence_digest=evidence_digest,
        authorization_digest=authorization_digest,
    )
    attachment = NetworkAttachment(
        entry.attachment.core_id,
        entry.attachment.network_id,
        next_scope,
        entry.attachment.attachment_evidence_digest,
    )
    return (
        NetworkRegistryEntry(
            attachment,
            entry.lifecycle_evidence_digest,
            NetworkAttachmentState.ATTACHED,
        ),
        transition,
    )


@dataclass(frozen=True)
class AuthorizedCapabilityTransition:
    transition: CapabilityTransition
    execution_binding: NetworkExecutionBinding

    def __post_init__(self) -> None:
        if self.transition.core_id != self.execution_binding.core_id:
            raise ValueError("capability transition core does not match execution binding")
        if self.transition.network_id != self.execution_binding.request.network_id:
            raise ValueError("capability transition network does not match execution binding")
        if self.transition.authorization_digest != self.execution_binding.request.authorization_digest:
            raise ValueError("capability transition authorization does not match execution binding")
