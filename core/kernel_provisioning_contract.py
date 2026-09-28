"""Deterministic kernel provisioning contract with product provenance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class KernelProvisionRequest:
    request_id: str
    expansion_request_digest: str
    capability: str
    required_capacity_units: int
    parent_core_id: str
    parent_core_hash: str
    product_id: str
    product_hash: str

    def __post_init__(self) -> None:
        fields = (self.request_id, self.expansion_request_digest, self.capability,
                  self.parent_core_id, self.parent_core_hash, self.product_id, self.product_hash)
        if any(not value for value in fields):
            raise ValueError("kernel provisioning identity is required")
        if self.required_capacity_units <= 0:
            raise ValueError("required_capacity_units must be positive")

    def digest(self) -> str:
        payload = "|".join((
            self.request_id, self.expansion_request_digest, self.capability,
            str(self.required_capacity_units), self.parent_core_id,
            self.parent_core_hash, self.product_id, self.product_hash,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class KernelProvisioningDecision:
    request_id: str
    provision: bool
    request_digest: str
    kernel_identity_hash: str

    def __post_init__(self) -> None:
        if not self.request_id or not self.request_digest or not self.kernel_identity_hash:
            raise ValueError("kernel provisioning decision identity is required")


def decide_provisioning(request: KernelProvisionRequest) -> KernelProvisioningDecision:
    digest = request.digest()
    kernel_identity_hash = hashlib.sha256(
        "|".join((request.product_hash, request.parent_core_hash, digest)).encode()
    ).hexdigest()
    return KernelProvisioningDecision(
        request_id=request.request_id,
        provision=True,
        request_digest=digest,
        kernel_identity_hash=kernel_identity_hash,
    )
