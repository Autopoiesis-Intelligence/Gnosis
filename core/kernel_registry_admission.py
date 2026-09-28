"""Adapter that converts only admitted provenance into a registry descriptor."""

from __future__ import annotations

from core.kernel_admission_contract import KernelAdmission
from core.distribution_contract import KernelCapacity
from core.kernel_registry import KernelDescriptor, KernelRegistry


def descriptor_from_admission(admission: KernelAdmission) -> KernelDescriptor:
    return KernelDescriptor(
        kernel_id=admission.kernel_id,
        capabilities=(admission.capability,),
        capacity=KernelCapacity(
            admission.kernel_id,
            admission.capacity_units,
            admission.capacity_units,
        ),
        enabled=True,
        product_id=admission.product_id,
        product_hash=admission.product_hash,
        parent_core_id=admission.parent_core_id,
        parent_core_hash=admission.parent_core_hash,
        kernel_identity_hash=admission.kernel_identity_hash,
    )


def admit_into_registry(
    registry: KernelRegistry,
    admission: KernelAdmission,
) -> KernelRegistry:
    descriptor = descriptor_from_admission(admission)
    if any(kernel.kernel_id == descriptor.kernel_id for kernel in registry.candidates(admission.capability)):
        raise ValueError("kernel already admitted")
    return KernelRegistry((*registry._kernels, descriptor))
