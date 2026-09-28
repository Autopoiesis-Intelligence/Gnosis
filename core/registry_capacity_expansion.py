"""Derive expansion input from current registry capacity."""

from __future__ import annotations

from core.kernel_registry import KernelRegistry
from core.capacity_snapshot import CapacitySnapshot
from core.network_expansion_contract import ExpansionRequest


def build_expansion_request(
    registry: KernelRegistry,
    *,
    request_id: str,
    capability: str,
    workload_digest: str,
    required_units: int,
    capacity_snapshot_digest: str,
) -> ExpansionRequest:
    if required_units <= 0:
        raise ValueError("required_units must be positive")
    snapshot = CapacitySnapshot.from_registry(registry, capability)
    available_units = snapshot.available_units
    return ExpansionRequest(
        request_id=request_id,
        capability=capability,
        workload_digest=workload_digest,
        required_units=required_units,
        available_units=available_units,
        capacity_snapshot_digest=snapshot.digest,
    )
