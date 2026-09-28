"""Kernel admission contract: only provenance-bound provisioned kernels enter the network."""

from __future__ import annotations

from dataclasses import dataclass

from core.kernel_provisioning_contract import KernelProvisioningDecision, KernelProvisionRequest


@dataclass(frozen=True)
class KernelAdmission:
    kernel_id: str
    product_id: str
    product_hash: str
    parent_core_id: str
    parent_core_hash: str
    kernel_identity_hash: str
    capability: str
    capacity_units: int
    provisioning_request_digest: str


def admit_kernel(
    request: KernelProvisionRequest,
    decision: KernelProvisioningDecision,
    *,
    kernel_id: str,
) -> KernelAdmission:
    if not decision.provision:
        raise ValueError("kernel provisioning was not approved")
    if decision.request_id != request.request_id:
        raise ValueError("provisioning decision does not match request")
    if decision.request_digest != request.digest():
        raise ValueError("provisioning request digest mismatch")
    expected_identity = __import__("hashlib").sha256(
        "|".join((request.product_hash, request.parent_core_hash, decision.request_digest)).encode()
    ).hexdigest()
    if decision.kernel_identity_hash != expected_identity:
        raise ValueError("kernel identity provenance mismatch")
    if not kernel_id:
        raise ValueError("kernel_id is required")
    return KernelAdmission(
        kernel_id=kernel_id,
        product_id=request.product_id,
        product_hash=request.product_hash,
        parent_core_id=request.parent_core_id,
        parent_core_hash=request.parent_core_hash,
        kernel_identity_hash=decision.kernel_identity_hash,
        capability=request.capability,
        capacity_units=request.required_capacity_units,
        provisioning_request_digest=decision.request_digest,
    )
