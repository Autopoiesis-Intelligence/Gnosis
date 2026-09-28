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
