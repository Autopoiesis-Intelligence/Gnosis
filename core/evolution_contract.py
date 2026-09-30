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
class NeedResolution:
    need_digest: str
    network_id: str
    capability_scope: str
    action: str
    target_core_id: str | None

    def __post_init__(self) -> None:
        if self.action not in ("reuse", "create"):
            raise ValueError("need resolution action is invalid")
        if not self.need_digest or not self.network_id or not self.capability_scope:
            raise ValueError("need resolution identity is required")
        if self.action == "reuse" and not self.target_core_id:
            raise ValueError("reuse requires an active target core")


def resolve_need_against_network(
    signal: EvolutionNeedSignal,
    network_id: str,
    capability_scope: str,
    registry: NetworkRegistry,
) -> NeedResolution:
    matches = registry.lookup(network_id, capability_scope)
    active = tuple(
        e for e in matches
        if e.attachment_state is NetworkAttachmentState.ATTACHED
    )
    if len(active) == 1:
        return NeedResolution(
            signal.digest(), network_id, capability_scope,
            "reuse", active[0].attachment.core_id,
        )
    if len(active) > 1:
        raise ValueError("need resolution is ambiguous")
    return NeedResolution(
        signal.digest(), network_id, capability_scope, "create", None
    )


def core_creation_proposal_from_resolution(
    signal: EvolutionNeedSignal,
    resolution: NeedResolution,
    request_id: str,
    reason: CoreCreationReason,
    scope: str,
    authorization_digest: str,
) -> CoreCreationProposal:
    if resolution.need_digest != signal.digest():
        raise ValueError("need resolution does not match signal")
    if resolution.action != "create":
        raise ValueError("core creation requires a create resolution")
    if resolution.network_id == "" or resolution.capability_scope == "" or scope == "":
        raise ValueError("network, capability scope, and scope are required")
    return core_creation_proposal_from_need(
        signal=signal,
        request_id=request_id,
        capability=resolution.capability_scope,
        reason=reason,
        scope=scope,
        authorization_digest=authorization_digest,
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
        capability_scope=capability,
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
class OpportunityScope:
    opportunity_id: str
    owner_id: str
    partner_id: str
    network_id: str
    interest_scope: str
    allowed_capabilities: frozenset[str]
    allowed_privacy_scopes: frozenset[str]
    allowed_core_origins: frozenset["CoreOrigin"]

    def __post_init__(self) -> None:
        if not all((self.opportunity_id, self.owner_id, self.partner_id,
                    self.network_id, self.interest_scope)):
            raise ValueError("opportunity scope identity is required")
        if not self.allowed_capabilities:
            raise ValueError("opportunity requires at least one capability")
        if not self.allowed_privacy_scopes:
            raise ValueError("opportunity requires privacy scopes")
        if not self.allowed_core_origins:
            raise ValueError("opportunity requires allowed core origins")


@dataclass(frozen=True)
class ScopedExecutionAuthorization:
    opportunity_id: str
    core_id: str
    capability_scope: str
    privacy_scope: str
    authorization_digest: str

    def __post_init__(self) -> None:
        if not all((self.opportunity_id, self.core_id, self.capability_scope,
                    self.privacy_scope, self.authorization_digest)):
            raise ValueError("scoped execution authorization requires complete identity")


def validate_core_for_opportunity(
    admission: CoreAdmission,
    scope: OpportunityScope,
) -> None:
    if admission.network_id != scope.network_id:
        raise ValueError("core network is outside opportunity scope")
    if admission.capability_scope not in scope.allowed_capabilities:
        raise ValueError("core capability is outside opportunity scope")
    if admission.privacy_scope not in scope.allowed_privacy_scopes:
        raise ValueError("core privacy scope is outside opportunity privacy scope")
    if admission.origin not in scope.allowed_core_origins:
        raise ValueError("core origin is outside opportunity scope")


def validate_scoped_execution_authorization(
    authorization: ScopedExecutionAuthorization,
    scope: OpportunityScope,
    admission: CoreAdmission,
    plan_record: OpportunityPlanRecord,
) -> None:
    if plan_record.state is not OpportunityPlanState.APPROVED:
        raise ValueError("opportunity plan is no longer approved")
    if authorization.opportunity_id != scope.opportunity_id:
        raise ValueError("authorization opportunity does not match scope")
    if authorization.core_id != admission.core_id:
        raise ValueError("authorization core does not match admission")
    if authorization.capability_scope != admission.capability_scope:
        raise ValueError("authorization capability does not match admission")
    if authorization.privacy_scope != admission.privacy_scope:
        raise ValueError("authorization privacy does not match admission")
    if admission.core_id not in plan_record.plan.candidate_core_ids:
        raise ValueError("authorized core is not selected by current plan")
    validate_core_for_opportunity(admission, scope)


def authorize_approved_opportunity(
    scope: OpportunityScope,
    plan_record: OpportunityPlanRecord,
    core: CoreAdmission,
    authorization_digest: str,
) -> ScopedExecutionAuthorization:
    if plan_record.state is not OpportunityPlanState.APPROVED:
        raise ValueError("opportunity plan must be approved")
    if core.core_id not in plan_record.plan.candidate_core_ids:
        raise ValueError("core is not selected by opportunity plan")
    validate_core_for_opportunity(core, scope)
    return ScopedExecutionAuthorization(
        scope.opportunity_id,
        core.core_id,
        core.capability_scope,
        core.privacy_scope,
        authorization_digest,
    )


class OpportunityPlanState(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


@dataclass(frozen=True)
class OpportunityPlanRecord:
    plan: "OpportunityPlan"
    state: OpportunityPlanState = OpportunityPlanState.PROPOSED

    def advance(self, target: OpportunityPlanState) -> "OpportunityPlanRecord":
        allowed = {
            OpportunityPlanState.PROPOSED: {OpportunityPlanState.APPROVED, OpportunityPlanState.REJECTED},
            OpportunityPlanState.APPROVED: {OpportunityPlanState.EXECUTED},
            OpportunityPlanState.REJECTED: set(),
            OpportunityPlanState.EXECUTED: set(),
        }
        if target not in allowed[self.state]:
            raise ValueError(f"invalid opportunity plan transition: {self.state} -> {target}")
        return OpportunityPlanRecord(self.plan, target)


@dataclass(frozen=True)
class OpportunityPlan:

    opportunity_id: str
    candidate_core_ids: tuple[str, ...]
    rationale: str
    approval_required: bool = True

    def __post_init__(self) -> None:
        if not self.opportunity_id or not self.rationale:
            raise ValueError("opportunity plan identity and rationale are required")
        if not self.candidate_core_ids:
            raise ValueError("opportunity plan requires candidates")
        if len(set(self.candidate_core_ids)) != len(self.candidate_core_ids):
            raise ValueError("opportunity plan candidates must be unique")


def build_opportunity_plan(
    scope: OpportunityScope,
    candidates: tuple[CoreAdmission, ...],
    rationale: str,
) -> OpportunityPlan:
    allowed = {item.core_id for item in discover_opportunity_candidates(scope, candidates)}
    selected = tuple(sorted(allowed))
    if not selected:
        raise ValueError("no admitted core matches opportunity scope")
    return OpportunityPlan(scope.opportunity_id, selected, rationale)


def discover_opportunity_candidates(
    scope: OpportunityScope,
    admissions: tuple[CoreAdmission, ...],
) -> tuple[CoreAdmission, ...]:
    candidates = tuple(
        admission for admission in admissions
        if admission.network_id == scope.network_id
        and admission.capability_scope in scope.allowed_capabilities
        and admission.privacy_scope in scope.allowed_privacy_scopes
        and admission.origin in scope.allowed_core_origins
    )
    return tuple(sorted(candidates, key=lambda item: item.core_id))


class CoreOrigin(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    DERIVED = "derived"


@dataclass(frozen=True)
class CoreAdmission:
    core_id: str
    origin: CoreOrigin
    network_id: str
    capability_scope: str
    privacy_scope: str
    authorization_digest: str
    verification_digest: str

    def __post_init__(self) -> None:
        if not self.core_id or not self.network_id:
            raise ValueError("core and network identity are required")
        if not self.capability_scope or not self.privacy_scope:
            raise ValueError("capability and privacy scopes are required")
        if not self.authorization_digest or not self.verification_digest:
            raise ValueError("admission requires authorization and verification")


def validate_core_admission(
    admission: CoreAdmission,
    allowed_capabilities: frozenset[str],
    allowed_privacy_scopes: frozenset[str],
) -> None:
    if admission.capability_scope not in allowed_capabilities:
        raise ValueError("core capability is outside admission scope")
    if admission.privacy_scope not in allowed_privacy_scopes:
        raise ValueError("core privacy scope is outside admission scope")


@dataclass(frozen=True)
class CoreCreationLifecycle:
    proposal: CoreCreationProposal
    record: CoreLifecycleRecord

    def __post_init__(self) -> None:
        if self.record.parent_core_id != self.proposal.request.parent_core_id:
            raise ValueError("lifecycle parent does not match creation proposal")
        if self.record.capability_scope != self.proposal.capability_scope:
            raise ValueError("lifecycle capability does not match proposal")
        if self.proposal.request.need_digest == "":
            raise ValueError("creation proposal must retain need digest")

    @property
    def need_digest(self) -> str:
        return self.proposal.request.need_digest


def advance_core_creation_lifecycle(
    current: CoreCreationLifecycle,
    requested: CoreLifecycle,
    evidence_digest: str,
) -> CoreCreationLifecycle:
    validate_core_lifecycle_transition(current.record.state, requested)
    if not evidence_digest:
        raise ValueError("lifecycle evidence is required")
    return CoreCreationLifecycle(
        current.proposal,
        CoreLifecycleRecord(
            core_id=current.record.core_id,
            parent_core_id=current.record.parent_core_id,
            state=requested,
            capability_scope=current.record.capability_scope,
            evidence_digest=evidence_digest,
        ),
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

    @staticmethod
    def from_recovered_entries(network_id: str, entries: tuple[NetworkRegistryEntry, ...]) -> "NetworkRegistrySnapshot":
        registry = NetworkRegistry(entries)
        snapshot = NetworkRegistrySnapshot.from_registry(network_id, registry)
        for entry in snapshot.entries:
            if entry.attachment.network_id != network_id:
                raise ValueError("recovered entry belongs to a different network")
        return snapshot

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
