"""Bounded E7.108 authoritative first-batch execution record."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class ExecutionState(str, Enum):
    PREPARED = "PREPARED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    batch_id: str
    target_commit_sha: str
    repository_ref: str
    baseline_id: str
    candidate_selection_id: str
    environment_identity: str
    readiness_record_id: str
    state: ExecutionState
    criterion_evidence: tuple[str, ...] = ()
    started_evidence: str = ""
    completed_evidence: str = ""

    def __post_init__(self) -> None:
        for name in (
            "execution_id", "batch_id", "target_commit_sha", "repository_ref",
            "baseline_id", "candidate_selection_id", "environment_identity",
            "readiness_record_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if self.state == ExecutionState.COMPLETED and not self.completed_evidence.strip():
            raise ValueError("completed execution requires completed evidence.")

    def transition(self, state: ExecutionState, *, evidence: str = "") -> "ExecutionRecord":
        if state == self.state:
            if evidence and evidence not in self.criterion_evidence:
                return replace(self, criterion_evidence=self.criterion_evidence + (evidence,))
            return self
        allowed = {
            ExecutionState.PREPARED: {ExecutionState.EXECUTING, ExecutionState.FAILED},
            ExecutionState.EXECUTING: {
                ExecutionState.COMPLETED,
                ExecutionState.FAILED,
                ExecutionState.INTERRUPTED,
            },
            ExecutionState.INTERRUPTED: {ExecutionState.EXECUTING, ExecutionState.FAILED},
            ExecutionState.COMPLETED: set(),
            ExecutionState.FAILED: set(),
        }
        if state not in allowed[self.state]:
            raise ValueError(f"invalid E7.108 transition: {self.state} -> {state}")
        kwargs = {"state": state}
        if state == ExecutionState.EXECUTING and evidence:
            kwargs["started_evidence"] = evidence
        if state == ExecutionState.COMPLETED and evidence:
            kwargs["completed_evidence"] = evidence
        return replace(self, **kwargs)

    def assert_replay_compatible(self, other: "ExecutionRecord") -> None:
        if self.execution_id != other.execution_id:
            raise ValueError("execution identity differs.")
        identity = (
            "batch_id", "target_commit_sha", "repository_ref", "baseline_id",
            "candidate_selection_id", "environment_identity", "readiness_record_id",
        )
        for field in identity:
            if getattr(self, field) != getattr(other, field):
                raise ValueError(f"conflicting replay for {field}.")
