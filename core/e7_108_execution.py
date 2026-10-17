"""Bounded E7.108 authoritative first-proof execution record."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class ExecutionState(str, Enum):
    PREPARING = "PREPARING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True)
class E7ExecutionRecord:
    batch_id: str
    execution_id: str
    target_commit_sha: str
    execution_input_identity: str
    readiness_id: str
    runtime_evidence_digest: str
    criterion_evidence: tuple[str, ...]
    state: ExecutionState

    @staticmethod
    def execution_id_for(
        batch_id: str,
        target_commit_sha: str,
        execution_input_identity: str,
    ) -> str:
        payload = "|".join((
            "gnozis-e7-execution-v1",
            batch_id,
            target_commit_sha,
            execution_input_identity,
        )).encode("utf-8")
        return sha256(payload).hexdigest()

    def __post_init__(self) -> None:
        for name in (
            "batch_id", "execution_id", "target_commit_sha",
            "execution_input_identity", "readiness_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if self.state == ExecutionState.COMPLETED and not self.runtime_evidence_digest:
            raise ValueError("completed execution requires runtime evidence digest")

    def begin(self, *, readiness_id: str, target_commit_sha: str) -> "E7ExecutionRecord":
        if self.state != ExecutionState.PREPARING:
            raise ValueError("execution may begin only from PREPARING")
        if readiness_id != self.readiness_id:
            raise ValueError("readiness identity mismatch")
        if target_commit_sha != self.target_commit_sha:
            raise ValueError("target commit mismatch")
        return self._replace(state=ExecutionState.EXECUTING)

    def complete(
        self,
        *,
        runtime_evidence_digest: str,
        criterion_evidence: tuple[str, ...],
        target_commit_sha: str,
    ) -> "E7ExecutionRecord":
        if self.state != ExecutionState.EXECUTING:
            raise ValueError("only EXECUTING execution may complete")
        if target_commit_sha != self.target_commit_sha:
            raise ValueError("target commit changed during execution")
        if not runtime_evidence_digest.strip():
            raise ValueError("runtime evidence digest is required")
        if not criterion_evidence:
            raise ValueError("criterion evidence is required")
        return self._replace(
            runtime_evidence_digest=runtime_evidence_digest,
            criterion_evidence=criterion_evidence,
            state=ExecutionState.COMPLETED,
        )

    def interrupt(self) -> "E7ExecutionRecord":
        if self.state != ExecutionState.EXECUTING:
            raise ValueError("only EXECUTING execution may interrupt")
        return self._replace(state=ExecutionState.INTERRUPTED)

    def fail(self) -> "E7ExecutionRecord":
        if self.state not in {ExecutionState.PREPARING, ExecutionState.EXECUTING}:
            raise ValueError("only active execution may fail")
        return self._replace(state=ExecutionState.FAILED)

    def assert_replay_compatible(self, other: "E7ExecutionRecord") -> None:
        if self.execution_id != other.execution_id:
            raise ValueError("execution identity differs")
        for field in (
            "batch_id", "target_commit_sha", "execution_input_identity",
            "readiness_id", "runtime_evidence_digest",
            "criterion_evidence", "state",
        ):
            if getattr(self, field) != getattr(other, field):
                raise ValueError(f"conflicting execution replay for {field}")

    def _replace(self, **changes: object) -> "E7ExecutionRecord":
        values = {
            "batch_id": self.batch_id,
            "execution_id": self.execution_id,
            "target_commit_sha": self.target_commit_sha,
            "execution_input_identity": self.execution_input_identity,
            "readiness_id": self.readiness_id,
            "runtime_evidence_digest": self.runtime_evidence_digest,
            "criterion_evidence": self.criterion_evidence,
            "state": self.state,
        }
        values.update(changes)
        return E7ExecutionRecord(**values)
