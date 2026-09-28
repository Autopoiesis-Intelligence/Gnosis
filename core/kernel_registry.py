"""Registry contract for discoverable execution kernels."""

from __future__ import annotations

from dataclasses import dataclass

from core.distribution_contract import KernelCapacity


@dataclass(frozen=True)
class KernelDescriptor:
    kernel_id: str
    capabilities: tuple[str, ...]
    capacity: KernelCapacity
    enabled: bool = True

    def supports(self, capability: str) -> bool:
        return self.enabled and capability in self.capabilities


class KernelRegistry:
    def __init__(self, kernels: tuple[KernelDescriptor, ...]) -> None:
        ids = [kernel.kernel_id for kernel in kernels]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate kernel_id")
        if any(not kernel.capacity.valid() for kernel in kernels):
            raise ValueError("invalid kernel capacity")
        self._kernels = tuple(sorted(kernels, key=lambda kernel: kernel.kernel_id))

    def candidates(self, capability: str) -> tuple[KernelDescriptor, ...]:
        return tuple(kernel for kernel in self._kernels if kernel.supports(capability))

    def capacities_for(self, capability: str) -> tuple[KernelCapacity, ...]:
        return tuple(kernel.capacity for kernel in self.candidates(capability))
