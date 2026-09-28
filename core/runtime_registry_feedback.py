"""Runtime health/capacity feedback contract for registry state."""

from __future__ import annotations

from dataclasses import dataclass

from core.kernel_registry import KernelDescriptor, KernelRegistry
from core.kernel_runtime_contract import KernelRuntimeStatus


@dataclass(frozen=True)
class RuntimeCapacityObservation:
    kernel_id: str
    runtime_id: str
    capacity_units: int
    healthy: bool

    @classmethod
    def from_status(cls, status: KernelRuntimeStatus) -> "RuntimeCapacityObservation":
        if status.capacity_units < 0:
            raise ValueError("capacity_units must be non-negative")
        if not status.runtime_id:
            raise ValueError("runtime identity is required")
        return cls(status.kernel_id, status.runtime_id, status.capacity_units, status.healthy)


def apply_runtime_observation(
    registry: KernelRegistry,
    observation: RuntimeCapacityObservation,
) -> KernelRegistry:
    matches = [k for k in registry.candidates_for_kernel(observation.kernel_id)]
    if len(matches) != 1:
        raise ValueError("runtime kernel is not uniquely registered")
    current = matches[0]
    if not current.enabled:
        raise ValueError("kernel is disabled")
    if observation.healthy is False:
        updated = KernelDescriptor(
            current.kernel_id, current.capabilities, current.capacity, False,
            current.product_id, current.product_hash, current.parent_core_id,
            current.parent_core_hash, current.kernel_identity_hash,
            current.provisioning_request_digest,
        )
        return KernelRegistry(tuple(k if k.kernel_id != current.kernel_id else updated for k in registry._kernels))
    if observation.capacity_units <= 0:
        raise ValueError("healthy runtime must report positive capacity")
    updated_capacity = type(current.capacity)(
        current.capacity.kernel_id,
        observation.capacity_units,
        observation.capacity_units,
    )
    updated = KernelDescriptor(
        current.kernel_id, current.capabilities, updated_capacity, True,
        current.product_id, current.product_hash, current.parent_core_id,
        current.parent_core_hash, current.kernel_identity_hash,
        current.provisioning_request_digest,
    )
    return KernelRegistry(tuple(k if k.kernel_id != current.kernel_id else updated for k in registry._kernels))
