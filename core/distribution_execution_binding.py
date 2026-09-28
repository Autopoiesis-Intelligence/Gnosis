"""Evidence contract linking a distribution decision to execution identity."""

from __future__ import annotations

from dataclasses import dataclass

from core.distribution_contract import DistributionDecision
from core.kernel_execution_contract import KernelExecutionContract
from core.execution_contract import ExecutionInput


@dataclass(frozen=True)
class DistributionExecutionBinding:
    decision_id: str
    decision_digest: str
    kernel_id: str
    execution_identity: str


def bind_distribution_to_execution(
    decision: DistributionDecision,
    contract: KernelExecutionContract,
    execution_input: ExecutionInput,
) -> DistributionExecutionBinding:
    if contract.distribution_decision_id != decision.decision_id:
        raise ValueError("distribution decision does not match execution contract")
    if contract.kernel_id != decision.selected_kernel_id:
        raise ValueError("selected kernel does not match execution contract")
    if contract.capability != decision.capability:
        raise ValueError("distribution capability does not match execution contract")
    return DistributionExecutionBinding(
        decision_id=decision.decision_id,
        decision_digest=decision.digest(),
        kernel_id=contract.kernel_id,
        execution_identity=contract.identity(execution_input, decision),
    )
