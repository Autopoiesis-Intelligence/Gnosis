"""Deterministic contract for requesting expansion of the kernel network."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpansionRequest:
    request_id: str
    capability: str
    workload_digest: str
    required_units: int
    available_units: int
    capacity_snapshot_digest: str

    def __post_init__(self) -> None:
        if not self.request_id or not self.capability or not self.workload_digest:
            raise ValueError("expansion request identity is required")
        if self.required_units <= 0:
            raise ValueError("required_units must be positive")
        if self.available_units < 0:
            raise ValueError("available_units must be non-negative")
        if not self.capacity_snapshot_digest:
            raise ValueError("capacity snapshot digest is required")

    @property
    def deficit_units(self) -> int:
        return max(0, self.required_units - self.available_units)

    def digest(self) -> str:
        payload = "|".join((
            self.request_id,
            self.capability,
            self.workload_digest,
            str(self.required_units),
            str(self.available_units),
            self.capacity_snapshot_digest,
        )).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ExpansionDecision:
    request_id: str
    expand: bool
    deficit_units: int
    request_digest: str

    def __post_init__(self) -> None:
        if not self.request_id or not self.request_digest:
            raise ValueError("expansion decision identity is required")
        if self.deficit_units < 0:
            raise ValueError("deficit_units must be non-negative")


def decide_expansion(request: ExpansionRequest) -> ExpansionDecision:
    return ExpansionDecision(
        request_id=request.request_id,
        expand=request.deficit_units > 0,
        deficit_units=request.deficit_units,
        request_digest=request.digest(),
    )
