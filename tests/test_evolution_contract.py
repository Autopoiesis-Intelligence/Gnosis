from core.evolution_contract import CoreCreationReason, CoreCreationRequest, EvolutionPatchCandidate


def test_core_creation_is_need_driven():
    request = CoreCreationRequest(
        "create-1", "core.main", "physics",
        CoreCreationReason.NEW_CAPABILITY, "need-hash", "research",
    )
    assert request.digest()


def test_evolution_patch_binds_target_state_and_analytics():
    patch = EvolutionPatchCandidate(
        "patch-1", "kernel.math.2", "core-hash", "state-hash",
        "analytics-hash", "reduce redundant work", "lower execution cost",
        "patch-hash",
    )
    assert patch.digest()


def test_need_signal_derives_candidate_for_same_core_state():
    from core.evolution_contract import EvolutionNeedSignal, candidate_from_need
    signal = EvolutionNeedSignal(
        "signal-1", "core-1", "state-1", "optimization",
        "analytics-1", "evidence-1", "local"
    )
    candidate = candidate_from_need(
        signal, "patch-1", "reduce redundant work", "lower cost", "patch-digest"
    )
    assert candidate.target_core_id == signal.core_id
    assert candidate.parent_state_hash == signal.core_state_hash
    assert candidate.analytics_digest == signal.analytics_digest


def test_need_signal_requires_evidence_identity():
    from core.evolution_contract import EvolutionNeedSignal
    with pytest.raises(ValueError, match="need signal identity"):
        EvolutionNeedSignal("signal", "core", "state", "optimization",
                            "analytics", "", "local")


def test_need_signal_creates_scoped_core_creation_proposal():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, core_creation_proposal_from_need,
    )
    signal = EvolutionNeedSignal(
        "signal-core", "core-parent", "state-parent", "specialization",
        "analytics", "evidence", "domain-x"
    )
    proposal = core_creation_proposal_from_need(
        signal, "request-1", "specialized capability",
        CoreCreationReason.SPECIALIZATION, "domain-x", "auth-digest"
    )
    assert proposal.request.parent_core_id == "core-parent"
    assert proposal.request.need_digest == signal.digest()
    assert proposal.request.capability == "specialized capability"
    assert proposal.request.scope == "domain-x"
    assert proposal.capability_scope == "specialized capability"


def test_core_creation_proposal_requires_authorization():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, core_creation_proposal_from_need,
    )
    signal = EvolutionNeedSignal(
        "signal-core", "core-parent", "state-parent", "specialization",
        "analytics", "evidence", "domain-x"
    )
    with pytest.raises(ValueError, match="authorization"):
        core_creation_proposal_from_need(
            signal, "request-1", "specialized capability",
            CoreCreationReason.SPECIALIZATION, "domain-x", ""
        )


def test_specialized_core_lifecycle_is_deterministic():
    from core.evolution_contract import CoreLifecycle, validate_core_lifecycle_transition
    chain = [
        CoreLifecycle.PROPOSED, CoreLifecycle.AUTHORIZED,
        CoreLifecycle.INSTANTIATED, CoreLifecycle.VERIFIED,
        CoreLifecycle.NETWORK_ATTACHED,
    ]
    for current, requested in zip(chain, chain[1:]):
        validate_core_lifecycle_transition(current, requested)


def test_specialized_core_cannot_attach_before_verification():
    from core.evolution_contract import CoreLifecycle, validate_core_lifecycle_transition
    for current in (
        CoreLifecycle.PROPOSED, CoreLifecycle.AUTHORIZED, CoreLifecycle.INSTANTIATED,
    ):
        with pytest.raises(ValueError, match="invalid core lifecycle transition"):
            validate_core_lifecycle_transition(
                current, CoreLifecycle.NETWORK_ATTACHED
            )


def test_network_attached_is_terminal_for_this_lifecycle():
    from core.evolution_contract import CoreLifecycle, validate_core_lifecycle_transition
    with pytest.raises(ValueError, match="invalid core lifecycle transition"):
        validate_core_lifecycle_transition(
            CoreLifecycle.NETWORK_ATTACHED, CoreLifecycle.VERIFIED
        )


def test_only_verified_core_can_attach_to_network():
    from core.evolution_contract import (
        CoreLifecycle, CoreLifecycleRecord, attach_verified_core,
    )
    verified = CoreLifecycleRecord("core-1", "parent-1", CoreLifecycle.VERIFIED,
                                   "specialized", "verify-evidence")
    attachment = attach_verified_core(verified, "network-1", "attach-evidence")
    assert attachment.core_id == "core-1"
    assert attachment.network_id == "network-1"
    assert attachment.digest()


def test_unverified_core_cannot_attach_to_network():
    from core.evolution_contract import (
        CoreLifecycle, CoreLifecycleRecord, attach_verified_core,
    )
    for state in (CoreLifecycle.PROPOSED, CoreLifecycle.AUTHORIZED,
                  CoreLifecycle.INSTANTIATED):
        record = CoreLifecycleRecord("core-1", "parent-1", state,
                                     "specialized", "evidence")
        with pytest.raises(ValueError, match="VERIFIED"):
            attach_verified_core(record, "network-1", "attach-evidence")


def test_network_registry_routes_by_capability_scope():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
    )
    a = NetworkAttachment("core-1", "network-1", "physics", "attach-evidence")
    registry = NetworkRegistry().register(NetworkRegistryEntry(a, "lifecycle-evidence"))
    assert registry.require_unique_route("network-1", "physics").attachment.core_id == "core-1"


def test_network_registry_rejects_duplicate_core_registration():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
    )
    a = NetworkAttachment("core-1", "network-1", "physics", "attach-evidence")
    entry = NetworkRegistryEntry(a, "lifecycle-evidence")
    registry = NetworkRegistry().register(entry)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(entry)


def test_network_registry_rejects_ambiguous_route():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
    )
    registry = NetworkRegistry()
    for core_id in ("core-1", "core-2"):
        a = NetworkAttachment(core_id, "network-1", "physics", "evidence-"+core_id)
        registry = registry.register(NetworkRegistryEntry(a, "lifecycle-"+core_id))
    with pytest.raises(ValueError, match="exactly one core"):
        registry.require_unique_route("network-1", "physics")


def test_network_execution_binds_to_unique_core_route():
    from core.evolution_contract import (
        NetworkAttachment, NetworkExecutionRequest, NetworkRegistry,
        NetworkRegistryEntry, bind_network_execution,
    )
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(NetworkRegistryEntry(attachment, "life"))
    request = NetworkExecutionRequest("network-1", "physics", "simulate", "auth")
    binding = bind_network_execution(registry, request)
    assert binding.core_id == "core-1"
    assert binding.request.operation == "simulate"
    assert binding.attachment_digest == attachment.digest()


def test_network_execution_fails_on_ambiguous_route():
    from core.evolution_contract import (
        NetworkAttachment, NetworkExecutionRequest, NetworkRegistry,
        NetworkRegistryEntry, bind_network_execution,
    )
    registry = NetworkRegistry()
    for core_id in ("core-1", "core-2"):
        attachment = NetworkAttachment(core_id, "network-1", "physics", "attach-"+core_id)
        registry = registry.register(NetworkRegistryEntry(attachment, "life-"+core_id))
    request = NetworkExecutionRequest("network-1", "physics", "simulate", "auth")
    with pytest.raises(ValueError, match="exactly one core"):
        bind_network_execution(registry, request)


def test_network_attachment_can_be_detached_or_revoked():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentRecord, NetworkAttachmentState,
        revoke_network_attachment,
    )
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    record = NetworkAttachmentRecord(
        attachment, NetworkAttachmentState.ATTACHED, "attached-evidence"
    )
    detached = revoke_network_attachment(
        record, NetworkAttachmentState.DETACHED, "detach-evidence"
    )
    assert detached.state is NetworkAttachmentState.DETACHED
    revoked = revoke_network_attachment(
        record, NetworkAttachmentState.REVOKED, "revoke-evidence"
    )
    assert revoked.state is NetworkAttachmentState.REVOKED


def test_detached_attachment_cannot_be_revoked_again():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentRecord, NetworkAttachmentState,
        revoke_network_attachment,
    )
    record = NetworkAttachmentRecord(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        NetworkAttachmentState.DETACHED, "detach-evidence"
    )
    with pytest.raises(ValueError, match="only attached"):
        revoke_network_attachment(record, NetworkAttachmentState.REVOKED, "revoke")


def test_detached_route_is_not_selectable():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistry,
        NetworkRegistryEntry,
    )
    a = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(a, "life", NetworkAttachmentState.DETACHED)
    )
    with pytest.raises(ValueError, match="exactly one core"):
        registry.require_unique_route("network-1", "physics")


def test_existing_binding_becomes_stale_after_attachment_change():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkExecutionRequest,
        NetworkExecutionBinding, NetworkRegistry, NetworkRegistryEntry,
        validate_network_execution_binding,
    )
    a = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(NetworkRegistryEntry(a, "life"))
    request = NetworkExecutionRequest("network-1", "physics", "simulate", "auth")
    binding = NetworkExecutionBinding(request, "core-1", a.digest())
    registry = NetworkRegistry((
        NetworkRegistryEntry(a, "life", NetworkAttachmentState.REVOKED),
    ))
    with pytest.raises(ValueError, match="exactly one core"):
        validate_network_execution_binding(registry, binding)


def test_binding_cannot_cross_active_core_route():
    from core.evolution_contract import (
        NetworkAttachment, NetworkExecutionRequest, NetworkExecutionBinding,
        NetworkRegistry, NetworkRegistryEntry, validate_network_execution_binding,
    )
    a1 = NetworkAttachment("core-1", "network-1", "physics", "attach-1")
    a2 = NetworkAttachment("core-2", "network-1", "physics", "attach-2")
    request = NetworkExecutionRequest("network-1", "physics", "simulate", "auth")
    binding = NetworkExecutionBinding(request, "core-1", a1.digest())
    registry = NetworkRegistry().register(NetworkRegistryEntry(a2, "life-2"))
    with pytest.raises(ValueError, match="exactly one core"):
        validate_network_execution_binding(registry, binding)


def test_network_registry_routes_distinct_capabilities_to_distinct_cores():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
        NetworkExecutionRequest, bind_network_execution,
    )
    physics = NetworkAttachment("core-physics", "network-1", "physics", "attach-p")
    history = NetworkAttachment("core-history", "network-1", "history", "attach-h")
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(physics, "life-p")
    ).register(
        NetworkRegistryEntry(history, "life-h")
    )
    physics_binding = bind_network_execution(
        registry, NetworkExecutionRequest("network-1", "physics", "simulate", "auth-p")
    )
    history_binding = bind_network_execution(
        registry, NetworkExecutionRequest("network-1", "history", "analyze", "auth-h")
    )
    assert physics_binding.core_id == "core-physics"
    assert history_binding.core_id == "core-history"


def test_capability_route_does_not_cross_to_other_core():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
        NetworkExecutionRequest, bind_network_execution,
    )
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(
            NetworkAttachment("core-physics", "network-1", "physics", "attach"),
            "life-p",
        )
    ).register(
        NetworkRegistryEntry(
            NetworkAttachment("core-history", "network-1", "history", "attach"),
            "life-h",
        )
    )
    with pytest.raises(ValueError, match="exactly one core"):
        registry.require_unique_route("network-1", "chemistry")


def test_same_capability_on_two_active_cores_is_ambiguous():
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
        NetworkExecutionRequest, bind_network_execution,
    )
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(
            NetworkAttachment("core-1", "network-1", "physics", "a"),
            "life-1",
        )
    ).register(
        NetworkRegistryEntry(
            NetworkAttachment("core-2", "network-1", "physics", "b"),
            "life-2",
        )
    )
    with pytest.raises(ValueError, match="exactly one core"):
        bind_network_execution(
            registry,
            NetworkExecutionRequest("network-1", "physics", "simulate", "auth"),
        )


def test_attached_core_can_change_capability_with_evidence():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistryEntry,
        transition_core_capability,
    )
    entry = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life",
        NetworkAttachmentState.ATTACHED,
    )
    updated, transition = transition_core_capability(
        entry, "simulation", "transition-evidence", "auth"
    )
    assert updated.attachment.capability_scope == "simulation"
    assert transition.previous_scope == "physics"
    assert transition.next_scope == "simulation"


def test_detached_core_cannot_change_capability():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistryEntry,
        transition_core_capability,
    )
    entry = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life",
        NetworkAttachmentState.DETACHED,
    )
    with pytest.raises(ValueError, match="only attached"):
        transition_core_capability(entry, "simulation", "evidence", "auth")


def test_capability_transition_requires_actual_change():
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistryEntry,
        transition_core_capability,
    )
    entry = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life",
        NetworkAttachmentState.ATTACHED,
    )
    with pytest.raises(ValueError, match="must change"):
        transition_core_capability(entry, "physics", "evidence", "auth")


def test_capability_transition_requires_matching_execution_authorization():
    from core.evolution_contract import (
        AuthorizedCapabilityTransition, CapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    transition = CapabilityTransition(
        "core-1", "network-1", "physics", "simulation", "evidence", "auth-1"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth-1"),
        "core-1", "attachment",
    )
    authorized = AuthorizedCapabilityTransition(transition, binding)
    assert authorized.transition.next_scope == "simulation"


def test_capability_transition_rejects_foreign_authorization():
    from core.evolution_contract import (
        AuthorizedCapabilityTransition, CapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    transition = CapabilityTransition(
        "core-1", "network-1", "physics", "simulation", "evidence", "auth-1"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth-2"),
        "core-1", "attachment",
    )
    with pytest.raises(ValueError, match="authorization"):
        AuthorizedCapabilityTransition(transition, binding)


def test_capability_transition_rejects_foreign_core():
    from core.evolution_contract import (
        AuthorizedCapabilityTransition, CapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    transition = CapabilityTransition(
        "core-1", "network-1", "physics", "simulation", "evidence", "auth"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth"),
        "core-2", "attachment",
    )
    with pytest.raises(ValueError, match="core"):
        AuthorizedCapabilityTransition(transition, binding)


def test_need_resolution_reuses_existing_specialized_core():
    from core.evolution_contract import (
        EvolutionNeedSignal, NetworkAttachment, NetworkAttachmentState,
        NetworkRegistry, NetworkRegistryEntry, resolve_need_against_network,
    )
    signal = EvolutionNeedSignal(
        "need-1", "core-parent", "state", "physics",
        "analytics", "evidence", "research",
    )
    registry = NetworkRegistry().register(NetworkRegistryEntry(
        NetworkAttachment("core-physics", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    ))
    result = resolve_need_against_network(
        signal, "network-1", "physics", registry
    )
    assert (result.action, result.target_core_id) == ("reuse", "core-physics")


def test_need_resolution_requests_new_core_when_capability_is_absent():
    from core.evolution_contract import (
        EvolutionNeedSignal, NetworkRegistry, resolve_need_against_network,
    )
    signal = EvolutionNeedSignal(
        "need-2", "core-parent", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    result = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    assert (result.action, result.target_core_id) == ("create", None)


def test_need_resolution_rejects_ambiguous_existing_capability():
    from core.evolution_contract import (
        EvolutionNeedSignal, NetworkAttachment, NetworkAttachmentState,
        NetworkRegistry, NetworkRegistryEntry, resolve_need_against_network,
    )
    signal = EvolutionNeedSignal(
        "need-3", "core-parent", "state", "physics",
        "analytics", "evidence", "research",
    )
    registry = NetworkRegistry().register(NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "a"),
        "life-1", NetworkAttachmentState.ATTACHED,
    )).register(NetworkRegistryEntry(
        NetworkAttachment("core-2", "network-1", "physics", "b"),
        "life-2", NetworkAttachmentState.ATTACHED,
    ))
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_need_against_network(
            signal, "network-1", "physics", registry
        )


def test_core_creation_proposal_preserves_capability_when_scope_differs():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, NetworkRegistry,
        core_creation_proposal_from_resolution, resolve_need_against_network,
    )
    signal = EvolutionNeedSignal(
        "need-separation", "parent", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    resolution = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    proposal = core_creation_proposal_from_resolution(
        signal, resolution, "request-separation",
        CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth",
    )
    assert proposal.request.capability == "chemistry"
    assert proposal.request.scope == "network-1"
    assert proposal.capability_scope == "chemistry"


def test_core_creation_proposal_requires_create_resolution():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, NetworkRegistry,
        resolve_need_against_network, core_creation_proposal_from_resolution,
    )
    signal = EvolutionNeedSignal(
        "need-create", "parent", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    resolution = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    proposal = core_creation_proposal_from_resolution(
        signal, resolution, "request-1",
        CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth-1"
    )
    assert proposal.request.need_digest == signal.digest()
    assert proposal.request.capability == "chemistry"


def test_core_creation_proposal_rejects_reuse_resolution():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, NetworkAttachment,
        NetworkAttachmentState, NetworkRegistry, NetworkRegistryEntry,
        resolve_need_against_network, core_creation_proposal_from_resolution,
    )
    signal = EvolutionNeedSignal(
        "need-reuse", "parent", "state", "physics",
        "analytics", "evidence", "research",
    )
    registry = NetworkRegistry().register(NetworkRegistryEntry(
        NetworkAttachment("core-physics", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    ))
    resolution = resolve_need_against_network(
        signal, "network-1", "physics", registry
    )
    with pytest.raises(ValueError, match="create resolution"):
        core_creation_proposal_from_resolution(
            signal, resolution, "request-2",
            CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth-2"
        )


def test_core_creation_proposal_rejects_foreign_resolution():
    from core.evolution_contract import (
        CoreCreationReason, EvolutionNeedSignal, NetworkRegistry,
        NeedResolution, core_creation_proposal_from_resolution,
    )
    signal = EvolutionNeedSignal(
        "need-a", "parent", "state", "physics",
        "analytics", "evidence", "research",
    )
    foreign = NeedResolution(
        "foreign-digest", "network-1", "physics", "create", None
    )
    with pytest.raises(ValueError, match="does not match signal"):
        core_creation_proposal_from_resolution(
            signal, foreign, "request-3",
            CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth-3"
        )


def test_core_creation_lifecycle_preserves_originating_need():
    from core.evolution_contract import (
        CoreCreationLifecycle, CoreCreationReason, CoreLifecycle,
        CoreLifecycleRecord, EvolutionNeedSignal, NetworkRegistry,
        core_creation_proposal_from_resolution, resolve_need_against_network,
        advance_core_creation_lifecycle,
    )
    signal = EvolutionNeedSignal(
        "need-lifecycle", "parent", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    resolution = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    proposal = core_creation_proposal_from_resolution(
        signal, resolution, "request-life",
        CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth"
    )
    lifecycle = CoreCreationLifecycle(
        proposal,
        CoreLifecycleRecord(
            "core-new", "parent", CoreLifecycle.PROPOSED, "network-1", "proposal-evidence"
        ),
    )
    authorized = advance_core_creation_lifecycle(
        lifecycle, CoreLifecycle.AUTHORIZED, "authorization-evidence"
    )
    assert authorized.need_digest == signal.digest()
    assert authorized.record.state is CoreLifecycle.AUTHORIZED


def test_core_creation_lifecycle_rejects_wrong_parent():
    from core.evolution_contract import (
        CoreCreationLifecycle, CoreCreationReason, CoreLifecycle,
        CoreLifecycleRecord, EvolutionNeedSignal, NetworkRegistry,
        core_creation_proposal_from_resolution, resolve_need_against_network,
    )
    signal = EvolutionNeedSignal(
        "need-parent", "parent-a", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    resolution = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    proposal = core_creation_proposal_from_resolution(
        signal, resolution, "request-parent",
        CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth"
    )
    with pytest.raises(ValueError, match="parent"):
        CoreCreationLifecycle(
            proposal,
            CoreLifecycleRecord(
                "core-new", "parent-b", CoreLifecycle.PROPOSED,
                "network-1", "proposal-evidence"
            ),
        )


def test_core_admission_supports_internal_external_and_derived_origins():
    from core.evolution_contract import CoreAdmission, CoreOrigin, validate_core_admission
    allowed_capabilities = frozenset({"physics", "chemistry"})
    allowed_privacy = frozenset({"public", "owner-scoped"})
    for origin in CoreOrigin:
        admission = CoreAdmission(
            f"core-{origin.value}", origin, "network-1", "physics",
            "owner-scoped", "auth", "verified",
        )
        validate_core_admission(admission, allowed_capabilities, allowed_privacy)


def test_core_admission_rejects_out_of_scope_capability():
    from core.evolution_contract import CoreAdmission, CoreOrigin, validate_core_admission
    admission = CoreAdmission(
        "core-external", CoreOrigin.EXTERNAL, "network-1", "finance",
        "owner-scoped", "auth", "verified",
    )
    with pytest.raises(ValueError, match="capability"):
        validate_core_admission(
            admission, frozenset({"physics"}), frozenset({"owner-scoped"})
        )


def test_core_admission_rejects_out_of_scope_privacy():
    from core.evolution_contract import CoreAdmission, CoreOrigin, validate_core_admission
    admission = CoreAdmission(
        "core-external", CoreOrigin.EXTERNAL, "network-1", "physics",
        "private-all-users", "auth", "verified",
    )
    with pytest.raises(ValueError, match="privacy"):
        validate_core_admission(
            admission, frozenset({"physics"}), frozenset({"owner-scoped"})
        )


def test_opportunity_candidate_discovery_is_scoped_and_deterministic():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityScope,
        discover_opportunity_candidates,
    )
    scope = OpportunityScope(
        "opp-discover", "client", "partner", "network-1", "materials",
        frozenset({"physics", "chemistry"}),
        frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL, CoreOrigin.DERIVED}),
    )
    admissions = (
        CoreAdmission("z-core", CoreOrigin.EXTERNAL, "network-1", "physics", "owner-scoped", "a", "v"),
        CoreAdmission("a-core", CoreOrigin.DERIVED, "network-1", "chemistry", "owner-scoped", "a", "v"),
        CoreAdmission("foreign-network", CoreOrigin.EXTERNAL, "network-2", "physics", "owner-scoped", "a", "v"),
        CoreAdmission("wrong-privacy", CoreOrigin.EXTERNAL, "network-1", "physics", "public", "a", "v"),
        CoreAdmission("wrong-capability", CoreOrigin.EXTERNAL, "network-1", "finance", "owner-scoped", "a", "v"),
    )
    result = discover_opportunity_candidates(scope, admissions)
    assert tuple(a.core_id for a in result) == ("a-core", "z-core")


def test_opportunity_candidate_discovery_returns_empty_without_match():
    from core.evolution_contract import CoreAdmission, CoreOrigin, OpportunityScope, discover_opportunity_candidates
    scope = OpportunityScope(
        "opp-empty", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    admissions = (
        CoreAdmission("chem", CoreOrigin.EXTERNAL, "network-1", "chemistry", "owner-scoped", "a", "v"),
    )
    assert discover_opportunity_candidates(scope, admissions) == ()


def test_opportunity_plan_contains_only_scoped_candidates():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityScope, build_opportunity_plan,
    )
    scope = OpportunityScope(
        "opp-plan", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    candidates = (
        CoreAdmission("z", CoreOrigin.EXTERNAL, "network-1", "physics", "owner-scoped", "a", "v"),
        CoreAdmission("bad", CoreOrigin.EXTERNAL, "network-1", "finance", "owner-scoped", "a", "v"),
    )
    plan = build_opportunity_plan(scope, candidates, "client materials objective")
    assert plan.candidate_core_ids == ("z",)
    assert plan.approval_required is True


def test_opportunity_plan_rejects_duplicate_candidates():
    from core.evolution_contract import OpportunityPlan
    with pytest.raises(ValueError, match="unique"):
        OpportunityPlan("opp", ("core-a", "core-a"), "reason")


def test_opportunity_plan_lifecycle_requires_approval_before_execution():
    from core.evolution_contract import OpportunityPlan, OpportunityPlanRecord, OpportunityPlanState
    record = OpportunityPlanRecord(OpportunityPlan("opp-life", ("core-a",), "reason"))
    approved = record.advance(OpportunityPlanState.APPROVED)
    executed = approved.advance(OpportunityPlanState.EXECUTED)
    assert record.state is OpportunityPlanState.PROPOSED
    assert approved.state is OpportunityPlanState.APPROVED
    assert executed.state is OpportunityPlanState.EXECUTED
    with pytest.raises(ValueError, match="invalid"):
        record.advance(OpportunityPlanState.EXECUTED)


def test_opportunity_plan_rejection_is_terminal():
    from core.evolution_contract import OpportunityPlan, OpportunityPlanRecord, OpportunityPlanState
    rejected = OpportunityPlanRecord(
        OpportunityPlan("opp-reject", ("core-a",), "reason")
    ).advance(OpportunityPlanState.REJECTED)
    with pytest.raises(ValueError, match="invalid"):
        rejected.advance(OpportunityPlanState.APPROVED)


def test_approved_opportunity_creates_scoped_execution_authorization():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityPlan, OpportunityPlanRecord,
        OpportunityPlanState, OpportunityScope, authorize_approved_opportunity,
    )
    scope = OpportunityScope(
        "opp-auth", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    core = CoreAdmission(
        "core-auth", CoreOrigin.EXTERNAL, "network-1", "physics",
        "owner-scoped", "core-auth", "verify",
    )
    plan = OpportunityPlanRecord(
        OpportunityPlan("opp-auth", ("core-auth",), "client objective")
    ).advance(OpportunityPlanState.APPROVED)
    auth = authorize_approved_opportunity(scope, plan, core, "exec-auth")
    assert auth.opportunity_id == "opp-auth"
    assert auth.core_id == "core-auth"
    assert auth.capability_scope == "physics"


def test_unapproved_opportunity_cannot_authorize_execution():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityPlan, OpportunityPlanRecord,
        OpportunityScope, authorize_approved_opportunity,
    )
    scope = OpportunityScope(
        "opp-no", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    core = CoreAdmission("core-no", CoreOrigin.EXTERNAL, "network-1", "physics", "owner-scoped", "a", "v")
    plan = OpportunityPlanRecord(OpportunityPlan("opp-no", ("core-no",), "objective"))
    with pytest.raises(ValueError, match="approved"):
        authorize_approved_opportunity(scope, plan, core, "exec")


def test_scoped_authorization_requires_current_approved_plan_and_matching_scopes():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityPlan, OpportunityPlanRecord,
        OpportunityPlanState, OpportunityScope, ScopedExecutionAuthorization,
        validate_scoped_execution_authorization,
    )
    scope = OpportunityScope(
        "opp-valid", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    core = CoreAdmission(
        "core-valid", CoreOrigin.EXTERNAL, "network-1", "physics",
        "owner-scoped", "auth", "verify",
    )
    plan = OpportunityPlanRecord(
        OpportunityPlan("opp-valid", ("core-valid",), "objective")
    ).advance(OpportunityPlanState.APPROVED)
    auth = ScopedExecutionAuthorization(
        "opp-valid", "core-valid", "physics", "owner-scoped", "exec"
    )
    validate_scoped_execution_authorization(auth, scope, core, plan)


def test_scoped_authorization_rejects_revoked_or_unapproved_plan():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityPlan, OpportunityPlanRecord,
        OpportunityPlanState, OpportunityScope, ScopedExecutionAuthorization,
        validate_scoped_execution_authorization,
    )
    scope = OpportunityScope(
        "opp-invalid", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    core = CoreAdmission(
        "core-invalid", CoreOrigin.EXTERNAL, "network-1", "physics",
        "owner-scoped", "auth", "verify",
    )
    auth = ScopedExecutionAuthorization(
        "opp-invalid", "core-invalid", "physics", "owner-scoped", "exec"
    )
    plan = OpportunityPlanRecord(
        OpportunityPlan("opp-invalid", ("core-invalid",), "objective")
    )
    with pytest.raises(ValueError, match="no longer approved"):
        validate_scoped_execution_authorization(auth, scope, core, plan)


def test_scoped_authorization_rejects_changed_privacy_scope():
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, OpportunityPlan, OpportunityPlanRecord,
        OpportunityPlanState, OpportunityScope, ScopedExecutionAuthorization,
        validate_scoped_execution_authorization,
    )
    scope = OpportunityScope(
        "opp-scope-change", "client", "partner", "network-1", "materials",
        frozenset({"physics"}), frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL}),
    )
    core = CoreAdmission(
        "core-scope-change", CoreOrigin.EXTERNAL, "network-1", "physics",
        "owner-scoped", "auth", "verify",
    )
    plan = OpportunityPlanRecord(
        OpportunityPlan("opp-scope-change", ("core-scope-change",), "objective")
    ).advance(OpportunityPlanState.APPROVED)
    stale_auth = ScopedExecutionAuthorization(
        "opp-scope-change", "core-scope-change", "physics", "public", "exec"
    )
    with pytest.raises(ValueError, match="privacy"):
        validate_scoped_execution_authorization(
            stale_auth, scope, core, plan
        )
