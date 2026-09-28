"""Deterministic provenance binding for bounded kernel executions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .execution_contract import ExecutionInput
from .kernel_execution_contract import KernelExecutionContract


@dataclass(frozen=True)
class KernelExecutionIdentity:
    """Stable identity of one kernel execution against one exact input."""

    execution_identity: str
    kernel_id: str
    capability: str
    distribution_decision_id: str
    execution_input_digest: str

    @classmethod
    def from_contract(
        cls,
        contract: KernelExecutionContract,
        execution_input: ExecutionInput,
    ) -> "KernelExecutionIdentity":
        execution_identity = contract.identity(execution_input)
        payload = "|".join(
            (
                execution_input.input_type,
                execution_input.state_id,
                execution_input.state_digest,
                execution_input.content_digest,
            )
        ).encode("utf-8")
        input_digest = hashlib.sha256(payload).hexdigest()
        return cls(
            execution_identity=execution_identity,
            kernel_id=contract.kernel_id,
            capability=contract.capability,
            distribution_decision_id=contract.distribution_decision_id,
            execution_input_digest=input_digest,
        )

    def evidence_binding_digest(self, evidence_hash: str) -> str:
        if not evidence_hash.strip():
            raise ValueError("evidence_hash is required")
        payload = "|".join(
            (
                self.execution_identity,
                self.kernel_id,
                self.capability,
                self.distribution_decision_id,
                self.execution_input_digest,
                evidence_hash,
            )
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def complete(self) -> bool:
        return all(
            (
                self.execution_identity,
                self.kernel_id,
                self.capability,
                self.distribution_decision_id,
                self.execution_input_digest,
            )
        )
