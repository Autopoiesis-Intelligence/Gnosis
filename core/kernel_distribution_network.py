"""Deterministic capacity-aware kernel distribution network."""

from __future__ import annotations

from dataclasses import dataclass

from core.distribution_contract import DistributionDecision, KernelCapacity, decide_distribution
from core.kernel_registry import KernelRegistry


@dataclass(frozen=True)
class CapacitySnapshot:
    capability: str
    capacities: tuple[KernelCapacity, ...]

    def digest(self) -> str:
        decision = decide_distribution(
            decision_id="snapshot",
            capability=self.capability,
            workload_digest="snapshot",
            capacities=self.capacities,
        )
        return decision.capacity_snapshot_digest


class KernelDistributionNetwork:
    def __init__(self, registry: KernelRegistry) -> None:
        self._registry = registry

    def snapshot(self, capability: str) -> CapacitySnapshot:
        capacities = self._registry.capacities_for(capability)
        if not capacities:
            raise ValueError("no capable kernels available")
        return CapacitySnapshot(capability, capacities)

    def route(self, *, decision_id: str, capability: str, workload_digest: str) -> DistributionDecision:
        snapshot = self.snapshot(capability)
        return decide_distribution(
            decision_id=decision_id,
            capability=capability,
            workload_digest=workload_digest,
            capacities=snapshot.capacities,
        )
