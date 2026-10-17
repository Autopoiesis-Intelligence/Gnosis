"""Bounded E7.109 operational acceptance decision record.

Acceptance is distinct from epistemic verification. Historical decisions are
immutable records; reassessment creates a new decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcceptanceState(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class AcceptanceDecision:
    decision_id: str
    execution_id: str
    criterion_id: str
    evidence_digest: str
    epistemic_state: str
    policy_revision: str
    scope: str
    authority_reference: str
    validity_conditions: tuple[str, ...]
    decision: AcceptanceState

    def __post_init__(self) -> None:
        for name in (
            "decision_id", "execution_id", "criterion_id", "evidence_digest",
            "epistemic_state", "policy_revision", "scope",
            "authority_reference",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")

    def assert_replay_compatible(self, other: "AcceptanceDecision") -> None:
        if self.decision_id != other.decision_id:
            raise ValueError("decision identity differs.")
        immutable = (
            "execution_id", "criterion_id", "evidence_digest",
            "epistemic_state", "policy_revision", "scope",
            "authority_reference", "validity_conditions", "decision",
        )
        for field in immutable:
            if getattr(self, field) != getattr(other, field):
                raise ValueError(f"conflicting replay for {field}.")

    def reassess(self, *, new_decision_id: str, new_policy_revision: str,
                 new_epistemic_state: str, new_decision: AcceptanceState) -> "AcceptanceDecision":
        if not new_decision_id.strip() or new_decision_id == self.decision_id:
            raise ValueError("reassessment requires a new decision identity.")
        return AcceptanceDecision(
            decision_id=new_decision_id,
            execution_id=self.execution_id,
            criterion_id=self.criterion_id,
            evidence_digest=self.evidence_digest,
            epistemic_state=new_epistemic_state,
            policy_revision=new_policy_revision,
            scope=self.scope,
            authority_reference=self.authority_reference,
            validity_conditions=self.validity_conditions,
            decision=new_decision,
        )
