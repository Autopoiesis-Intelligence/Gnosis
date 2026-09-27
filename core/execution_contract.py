"""Canonical execution-boundary contracts for plan safety and state identity."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .gas import GasBudget
from .safety import SafetyGate
from .state import Psi


@dataclass(frozen=True)
class ExecutionPlan:
    operation_count: int
    gas_costs: tuple[int, ...]

    def validate(self, gate: SafetyGate, gas_limit: int) -> GasBudget:
        if len(self.gas_costs) != self.operation_count:
            raise ValueError("operation/cost cardinality mismatch")
        gate.require(self.operation_count)
        budget = GasBudget(gas_limit)
        for cost in self.gas_costs:
            budget = budget.charge(cost)
        return budget


def validate_execution_plan(
    operation_count: int,
    gas_costs: tuple[int, ...],
    gate: SafetyGate | None = None,
    gas_limit: int = 20,
) -> GasBudget:
    plan = ExecutionPlan(operation_count, gas_costs)
    return plan.validate(gate or SafetyGate(max_operations=gas_limit), gas_limit)


def state_digest(psi: Psi) -> str:
    """Return the canonical runtime digest used by commit history."""
    if not isinstance(psi, Psi):
        raise TypeError("state_digest requires Psi.")
    payload = repr((psi.x, psi.relations)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def state_id(psi: Psi) -> str:
    """Return deterministic identity for one canonical Psi state."""
    digest = state_digest(psi)
    payload = f"gnozis-state-id-v1:{digest}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ExecutionInput:
    """Explicit execution identity supplied at the runtime boundary."""

    input_type: str
    state_id: str
    state_digest: str
    content_digest: str

    def __post_init__(self) -> None:
        for field_name in (
            "input_type",
            "state_id",
            "state_digest",
            "content_digest",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required.")


def execution_input_from_psi(
    psi: Psi,
    *,
    input_type: str,
    content_digest: str,
) -> ExecutionInput:
    """Construct an ExecutionInput bound to one exact Psi state."""
    digest = state_digest(psi)
    return ExecutionInput(
        input_type=input_type,
        state_id=state_id(psi),
        state_digest=digest,
        content_digest=content_digest,
    )


def verify_execution_input(execution_input: ExecutionInput, psi: Psi) -> None:
    """Fail closed unless declared state identity and digest match Psi."""
    if not isinstance(execution_input, ExecutionInput):
        raise TypeError("execution_input must be ExecutionInput.")
    actual_digest = state_digest(psi)
    actual_state_id = state_id(psi)
    if execution_input.state_id != actual_state_id:
        raise ValueError("ExecutionInput state_id does not match execution state.")
    if execution_input.state_digest != actual_digest:
        raise ValueError("ExecutionInput state_digest does not match execution state.")


def execution_input_identity(execution_input: ExecutionInput) -> str:
    """Return H(input_type || state_id || state_digest || content_digest)."""
    payload = "\x1f".join(
        (
            execution_input.input_type,
            execution_input.state_id,
            execution_input.state_digest,
            execution_input.content_digest,
        )
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AuthorizationEvidence:
    """Runtime projection of authorization identity without granting authority."""
    authorization_digest: str
    state_digest: str
    content_digest: str

    def __post_init__(self) -> None:
        for field_name in (
            "authorization_digest",
            "state_digest",
            "content_digest",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required.")


def authorization_evidence_from_input(
    authorization_digest: str,
    execution_input: ExecutionInput,
) -> AuthorizationEvidence:
    """Bind evidence to the same state/content identity as the execution input."""
    if not isinstance(authorization_digest, str) or not authorization_digest.strip():
        raise ValueError("authorization_digest is required.")
    return AuthorizationEvidence(
        authorization_digest=authorization_digest,
        state_digest=execution_input.state_digest,
        content_digest=execution_input.content_digest,
    )
