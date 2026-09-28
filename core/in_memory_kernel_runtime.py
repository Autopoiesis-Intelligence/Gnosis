"""Deterministic in-memory runtime adapter for kernel lifecycle testing."""

from __future__ import annotations

from core.kernel_registry import KernelDescriptor
from core.kernel_runtime_contract import KernelRuntimeHandle, KernelRuntimeStatus, bind_runtime


class InMemoryKernelRuntimeAdapter:
    def __init__(self) -> None:
        self._handles: dict[str, KernelRuntimeHandle] = {}

    def provision(self, descriptor: KernelDescriptor) -> KernelRuntimeHandle:
        descriptor.verify_provenance()
        if descriptor.kernel_id in self._handles:
            raise ValueError("kernel runtime already provisioned")
        runtime_id = f"runtime:{descriptor.kernel_id}"
        handle = KernelRuntimeHandle(
            descriptor.kernel_id,
            runtime_id,
            descriptor.product_hash,
            descriptor.kernel_identity_hash,
        )
        bind_runtime(descriptor, handle)
        self._handles[descriptor.kernel_id] = handle
        return handle

    def status(self, handle: KernelRuntimeHandle) -> KernelRuntimeStatus:
        current = self._handles.get(handle.kernel_id)
        if current != handle:
            raise ValueError("unknown runtime handle")
        return KernelRuntimeStatus(
            kernel_id=handle.kernel_id,
            runtime_id=handle.runtime_id,
            capacity_units=1,
            healthy=True,
        )

    def terminate(self, handle: KernelRuntimeHandle) -> None:
        current = self._handles.get(handle.kernel_id)
        if current != handle:
            raise ValueError("unknown runtime handle")
        del self._handles[handle.kernel_id]
