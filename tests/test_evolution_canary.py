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
