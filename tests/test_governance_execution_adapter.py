from core.execution_contract import ExecutionInput
from core.governance_execution_adapter import (
    GovernanceBinding,
    execution_input_from_verified_governance_binding,
    governance_binding_digest,
)


def make_binding(**overrides):
    values = dict(
        proposal_id="p1",
        proposal_digest="pd1",
        state_id="s1",
        state_digest="sd1",
        shadow_result_digest="sh1",
        governance_decision_digest="gd1",
    )
    values.update(overrides)
    provisional = GovernanceBinding(**values, binding_digest="")
    values["binding_digest"] = governance_binding_digest(provisional)
    return GovernanceBinding(**values)


def test_valid_binding_projects_execution_identity():
    binding = make_binding()
    result = execution_input_from_verified_governance_binding(
        binding, input_type="external-information", content_digest="cd1"
    )
    assert isinstance(result, ExecutionInput)
    assert result.state_id == "s1"
    assert result.state_digest == "sd1"
    assert result.content_digest == "cd1"


def test_proposal_tamper_is_rejected():
    binding = make_binding()
    tampered = make_binding(proposal_id="p2", binding_digest=binding.binding_digest)
    try:
        execution_input_from_verified_governance_binding(
            tampered, input_type="external-information", content_digest="cd1"
        )
    except ValueError:
        return
    assert False, "tampered proposal must fail closed"


def test_state_digest_tamper_is_rejected():
    binding = make_binding()
    tampered = make_binding(state_digest="tampered", binding_digest=binding.binding_digest)
    try:
        execution_input_from_verified_governance_binding(
            tampered, input_type="external-information", content_digest="cd1"
        )
    except ValueError:
        return
    assert False, "tampered state digest must fail closed"


def test_binding_digest_tamper_is_rejected():
    binding = make_binding()
    tampered = make_binding(binding_digest="tampered")
    try:
        execution_input_from_verified_governance_binding(
            tampered, input_type="external-information", content_digest="cd1"
        )
    except ValueError:
        return
    assert False, "tampered binding digest must fail closed"


def test_shadow_digest_tamper_is_rejected():
    binding = make_binding()
    tampered = make_binding(
        shadow_result_digest="tampered", binding_digest=binding.binding_digest
    )
    try:
        execution_input_from_verified_governance_binding(
            tampered, input_type="external-information", content_digest="cd1"
        )
    except ValueError:
        return
    assert False, "tampered shadow digest must fail closed"


def test_governance_digest_tamper_is_rejected():
    binding = make_binding(
        governance_decision_digest="tampered"
    )
    # make_binding recomputes the digest, so this is a structurally valid
    # alternate binding; using the original digest below simulates tampering.
    original = make_binding()
    tampered = GovernanceBinding(
        proposal_id=binding.proposal_id,
        proposal_digest=binding.proposal_digest,
        state_id=binding.state_id,
        state_digest=binding.state_digest,
        shadow_result_digest=binding.shadow_result_digest,
        governance_decision_digest=binding.governance_decision_digest,
        binding_digest=original.binding_digest,
    )
    try:
        execution_input_from_verified_governance_binding(
            tampered, input_type="external-information", content_digest="cd1"
        )
    except ValueError:
        return
    assert False, "tampered governance digest must fail closed"


def test_repeated_valid_projection_is_deterministic():
    binding = make_binding()
    a = execution_input_from_verified_governance_binding(
        binding, input_type="external-information", content_digest="cd1"
    )
    b = execution_input_from_verified_governance_binding(
        binding, input_type="external-information", content_digest="cd1"
    )
    assert a == b
