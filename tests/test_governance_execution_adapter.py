from core.execution_contract import ExecutionInput
from core.governance_execution_adapter import (
    VerifiedGovernanceBinding,
    execution_input_from_verified_governance_binding,
)


def make_binding():
    return VerifiedGovernanceBinding(
        proposal_id="p1",
        proposal_digest="pd1",
        state_id="s1",
        state_digest="sd1",
        shadow_result_digest="sh1",
        governance_decision_digest="gd1",
        binding_digest="bd1",
    )


def test_verified_binding_projects_only_execution_identity():
    binding = make_binding()
    result = execution_input_from_verified_governance_binding(
        binding,
        input_type="external-information",
        content_digest="cd1",
    )
    assert isinstance(result, ExecutionInput)
    assert result.state_id == "s1"
    assert result.state_digest == "sd1"
    assert result.content_digest == "cd1"


def test_adapter_has_no_authority_side_effect():
    binding = make_binding()
    a = execution_input_from_verified_governance_binding(
        binding, input_type="external-information", content_digest="cd1"
    )
    b = execution_input_from_verified_governance_binding(
        binding, input_type="external-information", content_digest="cd1"
    )
    assert a == b
