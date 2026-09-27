"""Bounded E7.107 readiness record and fail-closed state machine."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReadinessState(str, Enum):
    PREPARING = "PREPARING"
    READY = "READY"
    BLOCKED = "BLOCKED"
    INVALIDATED = "INVALIDATED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CheckState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    status: CheckState

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("check_id is required.")


@dataclass(frozen=True)
class E7ReadinessRecord:
    batch_id: str
    target_commit_sha: str
    repository_ref: str
    baseline_id: str
    candidate_selection_id: str
    evidence_policy_revision: str
    verification_matrix_revision: str
    environment_identity: str
    checks: tuple[ReadinessCheck, ...]
    commands: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    evidence_capture_mapping: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    retry_rules: tuple[str, ...]
    state: ReadinessState = ReadinessState.PREPARING

    def __post_init__(self) -> None:
        for name in (
            "batch_id", "target_commit_sha", "repository_ref", "baseline_id",
            "candidate_selection_id", "evidence_policy_revision",
            "verification_matrix_revision", "environment_identity",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if len(self.checks) != 13:
            raise ValueError("E7.107 requires exactly 13 readiness checks.")
        for value_name in (
            "commands", "expected_outcomes", "evidence_capture_mapping",
            "stop_conditions", "retry_rules",
        ):
            if not getattr(self, value_name):
                raise ValueError(f"{value_name} is required.")

    @property
    def readiness_id(self) -> str:
        import hashlib
        payload = "|".join((
            self.batch_id, self.target_commit_sha, self.repository_ref,
            self.baseline_id, self.candidate_selection_id,
            self.evidence_policy_revision, self.verification_matrix_revision,
            self.environment_identity,
        )).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def mark_ready(self, *, resolved_commit_sha: str, evidence_destination: str) -> "E7ReadinessRecord":
        if self.state != ReadinessState.PREPARING:
            raise ValueError("only PREPARING readiness may become READY")
        if resolved_commit_sha != self.target_commit_sha:
            return self._with_state(ReadinessState.BLOCKED)
        if not evidence_destination.strip():
            return self._with_state(ReadinessState.BLOCKED)
        if any(check.status != CheckState.PASS for check in self.checks):
            return self._with_state(ReadinessState.BLOCKED)
        return self._with_state(ReadinessState.READY)

    def begin(self) -> "E7ReadinessRecord":
        if self.state != ReadinessState.READY:
            raise ValueError("only READY readiness may begin execution")
        return self._with_state(ReadinessState.EXECUTING)

    def invalidate(self) -> "E7ReadinessRecord":
        if self.state in {ReadinessState.COMPLETED, ReadinessState.FAILED}:
            raise ValueError("terminal readiness cannot be invalidated")
        return self._with_state(ReadinessState.INVALIDATED)

    def _with_state(self, state: ReadinessState) -> "E7ReadinessRecord":
        return E7ReadinessRecord(
            self.batch_id, self.target_commit_sha, self.repository_ref,
            self.baseline_id, self.candidate_selection_id,
            self.evidence_policy_revision, self.verification_matrix_revision,
            self.environment_identity, self.checks, self.commands,
            self.expected_outcomes, self.evidence_capture_mapping,
            self.stop_conditions, self.retry_rules, state,
        )
