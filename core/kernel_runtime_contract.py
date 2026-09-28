"""Port contract for provisioning and observing a real kernel runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.kernel_registry import KernelDescriptor


@dataclass(frozen=True)
class KernelRuntimeHandle:
    kernel_id: str
    runtime_id: str
    product_hash: str
    kernel_identity_hash: str


@dataclass(frozen=True)
class KernelRuntimeStatus:
    kernel_id: str
    runtime_id: str
    capacity_units: int
    healthy: bool


class KernelRuntimeAdapter(Protocol):
    def provision(self, descriptor: KernelDescriptor) -> KernelRuntimeHandle: ...

    def status(self, handle: KernelRuntimeHandle) -> KernelRuntimeStatus: ...

    def terminate(self, handle: KernelRuntimeHandle) -> None: ...


def bind_runtime(descriptor: KernelDescriptor, handle: KernelRuntimeHandle) -> None:
    if handle.kernel_id != descriptor.kernel_id:
        raise ValueError("runtime kernel identity mismatch")
    if handle.product_hash != descriptor.product_hash:
        raise ValueError("runtime product provenance mismatch")
    if handle.kernel_identity_hash != descriptor.kernel_identity_hash:
        raise ValueError("runtime kernel provenance mismatch")
    if not handle.runtime_id:
        raise ValueError("runtime identity is required")
