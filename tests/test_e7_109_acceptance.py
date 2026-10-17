import pytest

from core.e7_109_acceptance import AcceptanceDecision, AcceptanceState


def decision(state=AcceptanceState.ACCEPTED):
    return AcceptanceDecision(
        decision_id="d1",
        execution_id="e1",
        criterion_id="c1",
        evidence_digest="sha256:e",
        epistemic_state="VERIFIED",
        policy_revision="p1",
        scope="proof-batch",
        authority_reference="auth-1",
        validity_conditions=("target-unchanged",),
        decision=state,
    )


def test_identical_replay_is_compatible():
    a = decision()
    a.assert_replay_compatible(decision())


def test_conflicting_historical_replay_is_rejected():
    a = decision()
    b = AcceptanceDecision(**{**a.__dict__, "decision": AcceptanceState.REJECTED})
    with pytest.raises(ValueError):
        a.assert_replay_compatible(b)


def test_reassessment_creates_new_identity():
    a = decision()
    b = a.reassess(
        new_decision_id="d2",
        new_policy_revision="p2",
        new_epistemic_state="REVISED",
        new_decision=AcceptanceState.REJECTED,
    )
    assert b.decision_id == "d2"
    assert a.decision == AcceptanceState.ACCEPTED
    assert b.decision == AcceptanceState.REJECTED


def test_reassessment_cannot_reuse_identity():
    with pytest.raises(ValueError):
        decision().reassess(
            new_decision_id="d1",
            new_policy_revision="p2",
            new_epistemic_state="REVISED",
            new_decision=AcceptanceState.REJECTED,
        )
