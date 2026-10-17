"""Minimal GovernanceBinding -> ExecutionInput adapter and fail-closed verifier."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .execution_contract import ExecutionInput


@dataclass(frozen=True)
class GovernanceBinding:
    proposal_id: str
    proposal_digest: str
    state_id: str
    state_digest: str
    shadow_result_digest: str
    governance_decision_digest: str
    binding_digest: str


def governance_binding_digest(binding: GovernanceBinding) -> str:
    canonical = "\x1f".join(
        (
            binding.proposal_id,
            binding.proposal_digest,
            binding.state_id,
            binding.state_digest,
            binding.shadow_result_digest,
            binding.governance_decision_digest,
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_governance_binding(binding: GovernanceBinding) -> None:
    if not isinstance(binding, GovernanceBinding):
        raise TypeError("binding must be GovernanceBinding.")
    fields = (
        "proposal_id",
        "proposal_digest",
        "state_id",
        "state_digest",
        "shadow_result_digest",
        "governance_decision_digest",
    )
    if any(
        not isinstance(getattr(binding, name), str) or not getattr(binding, name).strip()
        for name in fields
    ):
        raise ValueError("governance binding fields are required.")
    if binding.binding_digest != governance_binding_digest(binding):
        raise ValueError("governance binding digest mismatch.")


def execution_input_from_verified_governance_binding(
    binding: GovernanceBinding,
    *,
    content_digest: str,
    input_type: str,
) -> ExecutionInput:
    verify_governance_binding(binding)
    if not isinstance(content_digest, str) or not content_digest.strip():
        raise ValueError("content_digest is required.")
    if not isinstance(input_type, str) or not input_type.strip():
        raise ValueError("input_type is required.")
    return ExecutionInput(
        input_type=input_type,
        state_id=binding.state_id,
        state_digest=binding.state_digest,
        content_digest=content_digest,
    )
