"""Immutable evidence record for kernel-network expansion decisions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.capacity_snapshot import CapacitySnapshot
from core.network_expansion_contract import ExpansionDecision, ExpansionRequest


@dataclass(frozen=True)
class ExpansionEvidence:
    request_id: str
    request_digest: str
    snapshot_digest: str
    capability: str
    workload_digest: str
    required_units: int
    available_units: int
    deficit_units: int
    expand: bool
    evidence_digest: str

    @classmethod
    def create(
        cls,
        request: ExpansionRequest,
        snapshot: CapacitySnapshot,
        decision: ExpansionDecision,
    ) -> "ExpansionEvidence":
        if request.capacity_snapshot_digest != snapshot.digest:
            raise ValueError("expansion snapshot mismatch")
        if decision.request_digest != request.digest():
            raise ValueError("expansion decision is not bound to request")
        if decision.request_id != request.request_id:
            raise ValueError("expansion decision identity mismatch")
        if snapshot.available_units != request.available_units:
            raise ValueError("snapshot capacity mismatch")
        payload = "|".join((
            request.request_id,
            request.digest(),
            snapshot.digest,
            request.capability,
            request.workload_digest,
            str(request.required_units),
            str(request.available_units),
            str(request.deficit_units),
            str(decision.expand),
        )).encode()
        return cls(
            request.request_id, request.digest(), snapshot.digest,
            request.capability, request.workload_digest, request.required_units,
            request.available_units, request.deficit_units, decision.expand,
            hashlib.sha256(payload).hexdigest(),
        )
