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


def test_adapter_is_observational_only(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("adapter must not invoke mutation/executor path")

    monkeypatch.setattr("core.canonical_chain.commit_admitted_psi", forbidden, raising=False)

    binding = make_binding()
    result = execution_input_from_verified_governance_binding(
        binding,
        input_type="external-information",
        content_digest="cd1",
    )

    assert result.state_id == binding.state_id
    assert result.state_digest == binding.state_digest
    assert calls == []


def test_rejected_binding_is_observational_only():
    binding = make_binding()
    tampered = GovernanceBinding(
        proposal_id=binding.proposal_id,
        proposal_digest=binding.proposal_digest,
        state_id=binding.state_id,
        state_digest=binding.state_digest,
        shadow_result_digest=binding.shadow_result_digest,
        governance_decision_digest=binding.governance_decision_digest,
        binding_digest="tampered",
    )

    try:
        execution_input_from_verified_governance_binding(
            tampered,
            input_type="external-information",
            content_digest="cd1",
        )
    except ValueError:
        pass
    else:
        assert False, "tampered binding must fail closed"
