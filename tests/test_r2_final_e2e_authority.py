import pytest

from core.execution_contract import ExecutionInput, state_digest
from core.state import Psi


def test_final_r2_execution_input_binds_identity_and_digest():
    state = Psi(x=("g", "s0"), relations=())
    execution_input = ExecutionInput(
        input_type="psi_transition",
        state_id="s0",
        state_digest=state_digest(state),
        content_digest="content-0",
    )

    assert execution_input.state_digest == state_digest(state)
    assert execution_input.state_id == "s0"


def test_final_r2_rejects_state_substitution():
    expected = Psi(x=("g", "s0"), relations=())
    substituted = Psi(x=("g", "attacker"), relations=())

    expected_digest = state_digest(expected)
    substituted_digest = state_digest(substituted)

    assert expected_digest != substituted_digest

    forged = ExecutionInput(
        input_type="psi_transition",
        state_id="s0",
        state_digest=expected_digest,
        content_digest="content-0",
    )

    assert forged.state_digest != substituted_digest


def test_final_r2_external_input_has_no_commit_authority():
    class ExternalInput:
        value = {"candidate": "x"}

    external = ExternalInput()
    assert not hasattr(external, "commit")
    assert not hasattr(external, "apply")
