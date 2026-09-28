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
    assert proposal.capability_scope == "domain-x"


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
