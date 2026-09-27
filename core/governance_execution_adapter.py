"""Minimal GovernanceBinding -> ExecutionInput adapter.

Audit-stage implementation only. This module intentionally contains no
authority creation, authorization consumption, executor invocation, or commit.
"""
from __future__ import annotations

from dataclasses import dataclass

from .execution_contract import ExecutionInput


@dataclass(frozen=True)
class VerifiedGovernanceBinding:
    proposal_id: str
    proposal_digest: str
    state_id: str
    state_digest: str
    shadow_result_digest: str
    governance_decision_digest: str
    binding_digest: str


def execution_input_from_verified_governance_binding(
    binding: VerifiedGovernanceBinding,
    *,
    content_digest: str,
    input_type: str,
) -> ExecutionInput:
    """Project a verified governance identity into the existing execution identity.

    Verification of the binding itself is intentionally a precondition of this
    adapter. The adapter performs no authorization or execution.
    """
    if not isinstance(binding, VerifiedGovernanceBinding):
        raise TypeError("binding must be VerifiedGovernanceBinding.")
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
