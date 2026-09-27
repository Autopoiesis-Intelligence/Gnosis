"""Bounded E7.110 deterministic reconciliation record.

Reconciliation recalculates supplied metrics from immutable inputs, blocks
discrepancies, and never mutates the upstream acceptance records.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class ReconciliationState(str, Enum):
    PENDING = "PENDING"
    RECALCULATED = "RECALCULATED"
    RECONCILED = "RECONCILED"
    DISCREPANCY = "DISCREPANCY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ReconciliationSnapshot:
    reconciliation_id: str
    acceptance_batch_id: str
    input_snapshot_digest: str
    metric_id: str
    reported_value: str
    recalculated_value: str
    calculation_revision: str
    evidence_digests: tuple[str, ...]
    status: ReconciliationState

    @property
    def snapshot_identity(self) -> str:
        raw = "|".join((
            self.reconciliation_id,
            self.input_snapshot_digest,
            self.calculation_revision,
        ))
        return sha256(raw.encode()).hexdigest()

    def __post_init__(self) -> None:
        for name in (
            "reconciliation_id", "acceptance_batch_id",
            "input_snapshot_digest", "metric_id", "reported_value",
            "recalculated_value", "calculation_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")

    def reconcile(self) -> "ReconciliationSnapshot":
        if self.status not in {
            ReconciliationState.PENDING,
            ReconciliationState.RECALCULATED,
        }:
            raise ValueError("only pending/recalculated snapshots may reconcile")
        status = (
            ReconciliationState.RECONCILED
            if self.reported_value == self.recalculated_value
            else ReconciliationState.DISCREPANCY
        )
        return ReconciliationSnapshot(
            reconciliation_id=self.reconciliation_id,
            acceptance_batch_id=self.acceptance_batch_id,
            input_snapshot_digest=self.input_snapshot_digest,
            metric_id=self.metric_id,
            reported_value=self.reported_value,
            recalculated_value=self.recalculated_value,
            calculation_revision=self.calculation_revision,
            evidence_digests=self.evidence_digests,
            status=status,
        )

    def assert_replay_compatible(self, other: "ReconciliationSnapshot") -> None:
        if self.reconciliation_id != other.reconciliation_id:
            raise ValueError("reconciliation identity differs.")
        fields = (
            "acceptance_batch_id", "input_snapshot_digest", "metric_id",
            "reported_value", "recalculated_value", "calculation_revision",
            "evidence_digests", "status",
        )
        for field in fields:
            if getattr(self, field) != getattr(other, field):
                raise ValueError(f"conflicting replay for {field}.")
