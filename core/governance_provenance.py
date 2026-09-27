"""Fail-closed structural provenance checks for GovernanceBinding evidence."""
from __future__ import annotations

from dataclasses import dataclass

from .governance_execution_adapter import GovernanceBinding, verify_governance_binding


@dataclass(frozen=True)
class GovernanceEvidence:
    digest: str
    state_id: str
    evidence_type: str

    def __post_init__(self) -> None:
        for name in ("digest", "state_id", "evidence_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")


def verify_governance_binding_provenance(
    binding: GovernanceBinding,
    *,
    proposal: GovernanceEvidence,
    shadow_result: GovernanceEvidence,
    governance_decision: GovernanceEvidence,
) -> None:
    """Verify binding integrity, evidence identity, type, and state binding.

    This establishes structural provenance only; it does not establish
    semantic correctness or causal validity of the supplied evidence.
    """
    verify_governance_binding(binding)
    expected = (
        ("proposal_digest", proposal, "proposal"),
        ("shadow_result_digest", shadow_result, "shadow_result"),
        ("governance_decision_digest", governance_decision, "governance_decision"),
    )
    for field_name, evidence, expected_type in expected:
        if getattr(binding, field_name) != evidence.digest:
            raise ValueError(f"{field_name} does not match supplied evidence.")
        if evidence.evidence_type != expected_type:
            raise ValueError(f"{field_name} has invalid evidence type.")
        if evidence.state_id != binding.state_id:
            raise ValueError(f"{field_name} is bound to a different state.")
