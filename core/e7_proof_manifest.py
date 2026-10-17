"""Immutable cross-layer E7 proof-run manifest.

This module links existing readiness, execution, runtime, acceptance, and
reconciliation evidence. It grants no execution authority and does not mutate
upstream records.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class ProofTerminalState(str, Enum):
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


@dataclass(frozen=True)
class E7ProofRunManifest:
    manifest_id: str
    readiness_id: str
    execution_id: str
    execution_input_identity: str
    runtime_evidence_digest: str
    acceptance_decision_id: str
    reconciliation_id: str
    target_commit_sha: str
    terminal_status: ProofTerminalState

    def __post_init__(self) -> None:
        for name in (
            "manifest_id", "readiness_id", "execution_id",
            "execution_input_identity", "runtime_evidence_digest",
            "acceptance_decision_id", "reconciliation_id",
            "target_commit_sha",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")

    @property
    def manifest_digest(self) -> str:
        payload = "|".join((
            self.manifest_id,
            self.readiness_id,
            self.execution_id,
            self.execution_input_identity,
            self.runtime_evidence_digest,
            self.acceptance_decision_id,
            self.reconciliation_id,
            self.target_commit_sha,
            self.terminal_status.value,
        )).encode()
        return sha256(payload).hexdigest()

    def assert_replay_compatible(self, other: "E7ProofRunManifest") -> None:
        if self.manifest_id != other.manifest_id:
            raise ValueError("manifest identity differs.")
        if self != other:
            raise ValueError("conflicting proof-manifest replay.")
