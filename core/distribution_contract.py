"""Deterministic contract for distributing bounded work across kernels."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.kernel_registry import KernelRegistry


@dataclass(frozen=True)
class KernelCapacity:
    kernel_id: str
    available_units: int
    max_units: int

    def valid(self) -> bool:
        return bool(self.kernel_id) and 0 <= self.available_units <= self.max_units and self.max_units > 0


@dataclass(frozen=True)
class DistributionDecision:
    decision_id: str
    selected_kernel_id: str
    capability: str
    workload_digest: str
    capacity_snapshot_digest: str

    def digest(self) -> str:
        payload = "|".join((self.decision_id, self.selected_kernel_id, self.capability, self.workload_digest, self.capacity_snapshot_digest)).encode()
        return hashlib.sha256(payload).hexdigest()


def decide_distribution(*, decision_id: str, capability: str, workload_digest: str, capacities: tuple[KernelCapacity, ...]) -> DistributionDecision:
    if not decision_id or not capability or not workload_digest:
        raise ValueError("distribution inputs are required")
    if registry is not None:
        capacities = registry.capacities_for(capability)
    if capacities is None or not capacities or any(not item.valid() for item in capacities):
        raise ValueError("invalid kernel capacity")
    ordered = tuple(sorted(capacities, key=lambda item: (-item.available_units, item.kernel_id)))
    selected = ordered[0]
    snapshot = "|".join(f"{item.kernel_id}:{item.available_units}/{item.max_units}" for item in ordered)
    return DistributionDecision(
        decision_id=decision_id,
        selected_kernel_id=selected.kernel_id,
        capability=capability,
        workload_digest=workload_digest,
        capacity_snapshot_digest=hashlib.sha256(snapshot.encode()).hexdigest(),
    )
