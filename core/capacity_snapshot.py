"""Canonical capacity snapshot for deterministic expansion evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.kernel_registry import KernelRegistry


@dataclass(frozen=True)
class CapacitySnapshot:
    capability: str
    entries: tuple[tuple[str, int, bool], ...]
    digest: str

    @classmethod
    def from_registry(cls, registry: KernelRegistry, capability: str) -> "CapacitySnapshot":
        entries = tuple(
            (kernel.kernel_id, kernel.capacity.available_units, kernel.enabled)
            for kernel in registry.candidates(capability)
        )
        payload = "|".join(
            f"{kernel_id}:{available}:{enabled}"
            for kernel_id, available, enabled in entries
        ).encode()
        digest = hashlib.sha256(payload).hexdigest()
        return cls(capability, entries, digest)

    @property
    def available_units(self) -> int:
        return sum(available for _, available, enabled in self.entries if enabled)
