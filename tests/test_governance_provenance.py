from core.governance_execution_adapter import GovernanceBinding, governance_binding_digest
from core.governance_provenance import GovernanceEvidence, verify_governance_binding_provenance


def make_binding(state_id="s1"):
    values = dict(
        proposal_id="p1",
        proposal_digest="pd1",
        state_id=state_id,
        state_digest="sd1",
        shadow_result_digest="sh1",
        governance_decision_digest="gd1",
    )
    provisional = GovernanceBinding(**values, binding_digest="")
    values["binding_digest"] = governance_binding_digest(provisional)
    return GovernanceBinding(**values)


def evidence(state_id="s1", *, proposal_type="proposal", shadow_type="shadow_result",
             decision_type="governance_decision"):
    return (
        GovernanceEvidence("pd1", state_id, proposal_type),
        GovernanceEvidence("sh1", state_id, shadow_type),
        GovernanceEvidence("gd1", state_id, decision_type),
    )


def verify(binding, items):
    proposal, shadow, decision = items
    verify_governance_binding_provenance(
        binding,
        proposal=proposal,
        shadow_result=shadow,
        governance_decision=decision,
    )


def test_provenance_accepts_existing_same_state_evidence():
    verify(make_binding(), evidence())


def test_missing_or_wrong_digest_is_rejected():
    binding = make_binding()
    proposal, shadow, _ = evidence()
    decision = GovernanceEvidence("other", "s1", "governance_decision")
    try:
        verify(binding, (proposal, shadow, decision))
    except ValueError:
        return
    assert False, "unresolved governance evidence must fail closed"


def test_cross_state_evidence_is_rejected():
    binding = make_binding("s1")
    proposal, shadow, _ = evidence("s1")
    decision = GovernanceEvidence("gd1", "s2", "governance_decision")
    try:
        verify(binding, (proposal, shadow, decision))
    except ValueError:
        return
    assert False, "cross-state evidence must fail closed"


def test_wrong_structural_evidence_type_is_rejected():
    binding = make_binding()
    items = evidence(proposal_type="shadow_result")
    try:
        verify(binding, items)
    except ValueError:
        return
    assert False, "wrong evidence type must fail closed"
