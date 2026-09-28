"""Append-only causal history contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TransitionRecord:
    sequence: int
    previous_hash: str
    state_hash: str
    kernel_version: str
    candidate_hash: str
    admitted: bool
    evidence_hash: str = ""
    kernel_execution_identity: str = ""
    evidence_binding_digest: str = ""

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self.kernel_version.strip():
            raise ValueError("kernel_version is required")
        if not self.admitted:
            raise ValueError("history may contain only accepted transitions")


@dataclass(frozen=True)
class AppendOnlyHistory:
    records: tuple[TransitionRecord, ...] = ()

    def append(self, record: TransitionRecord) -> "AppendOnlyHistory":
        if self.records:
            previous = self.records[-1]
            if record.sequence != previous.sequence + 1:
                raise ValueError("history sequence must be contiguous")
            if record.previous_hash != previous.state_hash:
                raise ValueError("history chain is broken")
        elif record.sequence != 0:
            raise ValueError("genesis record must have sequence zero")
        return AppendOnlyHistory(self.records + (record,))

    @property
    def head(self) -> TransitionRecord | None:
        return self.records[-1] if self.records else None
