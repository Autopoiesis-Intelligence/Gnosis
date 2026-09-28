"""Registry contract for discoverable execution kernels."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from core.distribution_contract import KernelCapacity


@dataclass(frozen=True)
class KernelDescriptor:
    kernel_id: str
    capabilities: tuple[str, ...]
    capacity: KernelCapacity
    enabled: bool = True
    product_id: str = ""
    product_hash: str = ""
    parent_core_id: str = ""
    parent_core_hash: str = ""
    kernel_identity_hash: str = ""
    provisioning_request_digest: str = ""

    def supports(self, capability: str) -> bool:
        return self.enabled and capability in self.capabilities

    def verify_provenance(self) -> None:
        fields = (self.product_id, self.product_hash, self.parent_core_id, self.parent_core_hash, self.kernel_identity_hash, self.provisioning_request_digest)
        if not all(fields):
            raise ValueError("incomplete kernel provenance")
        expected = hashlib.sha256("|".join((self.product_hash, self.parent_core_hash, self.provisioning_request_digest)).encode()).hexdigest()
        if self.kernel_identity_hash != expected:
            raise ValueError("kernel identity provenance mismatch")


class KernelRegistry:
    def __init__(self, kernels: tuple[KernelDescriptor, ...]) -> None:
        ids = [kernel.kernel_id for kernel in kernels]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate kernel_id")
        if any(not kernel.capacity.valid() for kernel in kernels):
            raise ValueError("invalid kernel capacity")
        for kernel in kernels:
            if kernel.product_hash or kernel.parent_core_hash or kernel.kernel_identity_hash:
                kernel.verify_provenance()
        self._kernels = tuple(sorted(kernels, key=lambda kernel: kernel.kernel_id))

    def candidates(self, capability: str) -> tuple[KernelDescriptor, ...]:
        return tuple(kernel for kernel in self._kernels if kernel.supports(capability))

    def capacities_for(self, capability: str) -> tuple[KernelCapacity, ...]:
        return tuple(kernel.capacity for kernel in self.candidates(capability))
