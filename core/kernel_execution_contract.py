"""Runtime contract for binding canonical execution to a bounded kernel."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .execution_contract import ExecutionInput
from .distribution_contract import DistributionDecision


@dataclass(frozen=True)
class KernelExecutionContract:
    """Identity and scope of one admissible kernel execution."""

    kernel_id: str
    capability: str
    distribution_decision_id: str
    scope: str
    resource_budget: int

    def __post_init__(self) -> None:
        for name in (
            "kernel_id",
            "capability",
            "distribution_decision_id",
            "scope",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if self.resource_budget < 0:
            raise ValueError("resource_budget must be non-negative.")

    def identity(self, execution_input: ExecutionInput, distribution_decision: DistributionDecision | None = None) -> str:
        """Bind kernel identity to exact input and optional distribution decision."""
        decision_digest = ""
        if distribution_decision is not None:
            if distribution_decision.decision_id != self.distribution_decision_id:
                raise ValueError("execution distribution decision does not match contract.")
            decision_digest = distribution_decision.digest()
        payload = "\x1f".join(
            (
                self.kernel_id,
                self.capability,
                self.distribution_decision_id,
                decision_digest,
                self.scope,
                str(self.resource_budget),
                execution_input.input_type,
                execution_input.state_id,
                execution_input.state_digest,
                execution_input.content_digest,
            )
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def verify_kernel_execution_contract(
    contract: KernelExecutionContract,
    execution_input: ExecutionInput,
    *,
    allowed_kernel_id: str,
    allowed_capability: str,
    distribution_decision: DistributionDecision | None = None,
) -> None:
    """Fail closed unless the selected kernel/capability matches policy."""
    if not isinstance(contract, KernelExecutionContract):
        raise TypeError("contract must be KernelExecutionContract.")
    if not isinstance(execution_input, ExecutionInput):
        raise TypeError("execution_input must be ExecutionInput.")

    if contract.kernel_id != allowed_kernel_id:
        raise ValueError("kernel execution target is not authorized.")
    if contract.capability != allowed_capability:
        raise ValueError("kernel capability is not authorized.")
    if distribution_decision is not None:
        if contract.distribution_decision_id != distribution_decision.decision_id:
            raise ValueError("execution distribution decision does not match contract.")
        if contract.kernel_id != distribution_decision.selected_kernel_id:
            raise ValueError("execution kernel does not match distribution decision.")
        if contract.capability != distribution_decision.capability:
            raise ValueError("execution capability does not match distribution decision.")
