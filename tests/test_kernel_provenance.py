from __future__ import annotations

from core.execution_contract import ExecutionInput
from core.kernel_execution_contract import KernelExecutionContract
from core.kernel_provenance import KernelExecutionIdentity


def make_input(content_digest: str = "content-1") -> ExecutionInput:
    return ExecutionInput(
        input_type="test",
        state_id="state-1",
        state_digest="state-1-digest",
        content_digest=content_digest,
    )


def make_contract(
    kernel_id: str = "kernel.math.1",
    capability: str = "math",
) -> KernelExecutionContract:
    return KernelExecutionContract(
        kernel_id=kernel_id,
        capability=capability,
        distribution_decision_id="dist-1",
        scope="test",
        resource_budget=10,
    )


def test_same_contract_and_input_produce_same_identity() -> None:
    contract = make_contract()
    execution_input = make_input()
    left = KernelExecutionIdentity.from_contract(contract, execution_input)
    right = KernelExecutionIdentity.from_contract(contract, execution_input)
    assert left == right
    assert left.complete()


def test_content_change_changes_execution_identity() -> None:
    contract = make_contract()
    left = KernelExecutionIdentity.from_contract(contract, make_input("content-1"))
    right = KernelExecutionIdentity.from_contract(contract, make_input("content-2"))
    assert left != right
    assert left.execution_input_digest != right.execution_input_digest


def test_kernel_change_changes_execution_identity() -> None:
    execution_input = make_input()
    left = KernelExecutionIdentity.from_contract(
        make_contract(kernel_id="kernel.math.1"), execution_input
    )
    right = KernelExecutionIdentity.from_contract(
        make_contract(kernel_id="kernel.physics.1"), execution_input
    )
    assert left != right


def test_capability_change_changes_execution_identity() -> None:
    execution_input = make_input()
    left = KernelExecutionIdentity.from_contract(
        make_contract(capability="math"), execution_input
    )
    right = KernelExecutionIdentity.from_contract(
        make_contract(capability="physics"), execution_input
    )
    assert left != right
