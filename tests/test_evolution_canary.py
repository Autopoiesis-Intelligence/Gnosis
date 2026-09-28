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
