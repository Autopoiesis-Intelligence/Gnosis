"""Fail-closed provenance checks for GovernanceBinding evidence references."""
from __future__ import annotations

from dataclasses import dataclass

from .governance_execution_adapter import GovernanceBinding, verify_governance_binding


@dataclass(frozen=True)
class GovernanceEvidence:
    digest: str
    state_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.digest, str) or not self.digest.strip():
            raise ValueError("evidence digest is required.")
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("evidence state_id is required.")


def verify_governance_binding_provenance(
    binding: GovernanceBinding,
    *,
    proposal: GovernanceEvidence,
    shadow_result: GovernanceEvidence,
    governance_decision: GovernanceEvidence,
) -> None:
    """Verify binding integrity plus existence/identity of its referenced evidence.

    This does not establish semantic correctness of the evidence. It only proves
    that the referenced evidence objects exist in the supplied evidence set,
    match the declared digests, and are bound to the same state identity.
    """
    verify_governance_binding(binding)
    expected = (
        ("proposal_digest", proposal),
        ("shadow_result_digest", shadow_result),
        ("governance_decision_digest", governance_decision),
    )
    for field_name, evidence in expected:
        if getattr(binding, field_name) != evidence.digest:
            raise ValueError(f"{field_name} does not match supplied evidence.")
        if evidence.state_id != binding.state_id:
            raise ValueError(f"{field_name} is bound to a different state.")
