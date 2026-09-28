import pytest
from core.evolution_canary import CanaryDecision, CanaryObservation


def test_canary_observation_is_deterministically_identified():
    o = CanaryObservation("p1", "parent", "candidate", "effect", "verify",
                          CanaryDecision.OBSERVE)
    assert o.digest() == o.digest()


def test_canary_observation_requires_identity():
    with pytest.raises(ValueError, match="identity"):
        CanaryObservation("", "parent", "candidate", "effect", "verify",
                          CanaryDecision.OBSERVE)


def test_canary_allows_observe_to_commit_or_rollback():
    from core.evolution_canary import validate_canary_transition
    validate_canary_transition(CanaryDecision.OBSERVE, CanaryDecision.COMMIT)
    validate_canary_transition(CanaryDecision.OBSERVE, CanaryDecision.ROLLBACK)


def test_canary_rejects_terminal_state_reentry():
    from core.evolution_canary import validate_canary_transition
    for current in (CanaryDecision.COMMIT, CanaryDecision.ROLLBACK):
        for requested in CanaryDecision:
            with pytest.raises(ValueError, match="invalid canary transition"):
                validate_canary_transition(current, requested)


def test_canary_rejects_direct_observe_to_observe():
    from core.evolution_canary import validate_canary_transition
    with pytest.raises(ValueError, match="invalid canary transition"):
        validate_canary_transition(CanaryDecision.OBSERVE, CanaryDecision.OBSERVE)


def test_commit_evaluation_is_derived_from_matching_canary():
    from core.evolution_evaluation import EvolutionEvaluation
    o = CanaryObservation("p1", "parent", "candidate", "observed", "verified",
                          CanaryDecision.COMMIT)
    e = EvolutionEvaluation.from_canary_commit(
        "p1", "parent", "candidate", "expected", o
    )
    assert e.decision.value == "commit"
    assert e.canary_digest == o.digest()


def test_commit_evaluation_rejects_mismatched_canary():
    from core.evolution_evaluation import EvolutionEvaluation
    o = CanaryObservation("other", "parent", "candidate", "observed", "verified",
                          CanaryDecision.COMMIT)
    with pytest.raises(ValueError, match="patch identity"):
        EvolutionEvaluation.from_canary_commit(
            "p1", "parent", "candidate", "expected", o
        )


def test_commit_evaluation_rejects_non_commit_canary():
    from core.evolution_evaluation import EvolutionEvaluation
    o = CanaryObservation("p1", "parent", "candidate", "observed", "verified",
                          CanaryDecision.ROLLBACK)
    with pytest.raises(ValueError, match="terminal COMMIT"):
        EvolutionEvaluation.from_canary_commit(
            "p1", "parent", "candidate", "expected", o
        )


def test_rollback_requires_reason_and_evidence():
    from core.evolution_canary import CanaryRollback
    r = CanaryRollback("p1", "parent", "candidate", "reason", "evidence")
    assert r.digest()


def test_rollback_cannot_be_empty_evidence():
    from core.evolution_canary import CanaryRollback
    with pytest.raises(ValueError, match="rollback evidence identity"):
        CanaryRollback("p1", "parent", "candidate", "reason", "")


def test_evolution_outcome_is_terminal():
    from core.evolution_canary import EvolutionOutcome
    o = CanaryObservation("p1", "parent", "candidate", "effect", "verified",
                          CanaryDecision.COMMIT)
    outcome = EvolutionOutcome.from_commit(o)
    assert outcome.decision is CanaryDecision.COMMIT
    assert outcome.outcome_digest


def test_evolution_outcome_cannot_be_observe():
    from core.evolution_canary import EvolutionOutcome
    with pytest.raises(ValueError, match="terminal"):
        EvolutionOutcome("p1", "parent", "candidate", CanaryDecision.OBSERVE,
                         "evidence", "digest")


def test_rollback_produces_terminal_evolution_outcome():
    from core.evolution_canary import CanaryRollback, EvolutionOutcome
    rollback = CanaryRollback("p1", "parent", "candidate", "reason", "evidence")
    outcome = EvolutionOutcome.from_rollback(rollback)
    assert outcome.decision is CanaryDecision.ROLLBACK
