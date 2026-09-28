from __future__ import annotations

import pytest

from core.execution_contract import ExecutionInput
from core.distribution_contract import DistributionDecision
from core.kernel_execution_contract import (
    KernelExecutionContract,
    verify_kernel_execution_contract,
)


def make_input() -> ExecutionInput:
    return ExecutionInput(
        input_type="test",
        state_id="state-1",
        state_digest="state-digest-1",
        content_digest="content-digest-1",
    )


def make_contract() -> KernelExecutionContract:
    return KernelExecutionContract(
        kernel_id="kernel.math.1",
        capability="math",
        distribution_decision_id="dist-1",
        scope="test",
        resource_budget=10,
    )


def test_identity_binds_kernel_to_execution_input() -> None:
    contract = make_contract()
    execution_input = make_input()
    assert contract.identity(execution_input) == contract.identity(execution_input)


def test_authorized_kernel_and_capability_are_accepted() -> None:
    verify_kernel_execution_contract(
        make_contract(),
        make_input(),
        allowed_kernel_id="kernel.math.1",
        allowed_capability="math",
    )


def test_mismatched_kernel_is_rejected() -> None:
    with pytest.raises(ValueError, match="target is not authorized"):
        verify_kernel_execution_contract(
            make_contract(), make_input(),
            allowed_kernel_id="kernel.physics.1",
            allowed_capability="math",
        )


def test_mismatched_capability_is_rejected() -> None:
    with pytest.raises(ValueError, match="capability is not authorized"):
        verify_kernel_execution_contract(
            make_contract(), make_input(),
            allowed_kernel_id="kernel.math.1",
            allowed_capability="physics",
        )


def test_identity_changes_when_content_changes() -> None:
    contract = make_contract()
    original = make_input()
    changed = ExecutionInput(
        input_type=original.input_type,
        state_id=original.state_id,
        state_digest=original.state_digest,
        content_digest="different-content",
    )
    assert contract.identity(original) != contract.identity(changed)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kernel_id", ""),
        ("capability", ""),
        ("distribution_decision_id", ""),
        ("scope", ""),
    ],
)
def test_required_fields_fail_closed(field: str, value: str) -> None:
    values = dict(
        kernel_id="kernel.math.1",
        capability="math",
        distribution_decision_id="dist-1",
        scope="test",
        resource_budget=10,
    )
    values[field] = value
    with pytest.raises(ValueError):
        KernelExecutionContract(**values)


def test_execution_rejects_kernel_mismatch_with_distribution():
    contract = make_contract()
    execution_input = make_input()
    decision = DistributionDecision(
        decision_id="dist-1",
        selected_kernel_id="other-kernel",
        capability="math",
        workload_digest="work",
        capacity_snapshot_digest="capacity",
    )
    try:
        verify_kernel_execution_contract(
            contract,
            execution_input,
            allowed_kernel_id="kernel.math.1",
            allowed_capability="math",
            distribution_decision=decision,
        )
    except ValueError as exc:
        assert "does not match distribution decision" in str(exc)
        return
    raise AssertionError("kernel mismatch must be rejected")


def test_execution_accepts_matching_distribution():
    contract = make_contract()
    execution_input = make_input()
    decision = DistributionDecision(
        decision_id="dist-1",
        selected_kernel_id="kernel.math.1",
        capability="math",
        workload_digest="work",
        capacity_snapshot_digest="capacity",
    )
    verify_kernel_execution_contract(
        contract,
        execution_input,
        allowed_kernel_id="kernel.math.1",
        allowed_capability="math",
        distribution_decision=decision,
    )


def test_identity_changes_when_distribution_decision_digest_changes():
    contract = make_contract()
    execution_input = make_input()
    decision_a = DistributionDecision(
        decision_id="dist-1", selected_kernel_id="kernel-1",
        capability="math", workload_digest="work-a",
        capacity_snapshot_digest="capacity-a",
    )
    decision_b = DistributionDecision(
        decision_id="dist-1", selected_kernel_id="kernel-1",
        capability="math", workload_digest="work-b",
        capacity_snapshot_digest="capacity-a",
    )
    assert contract.identity(execution_input, decision_a) != contract.identity(execution_input, decision_b)
