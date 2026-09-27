"""Minimal E7.107 readiness record/state machine.

This module grants no execution or mutation authority. It only evaluates and
records fail-closed readiness for a bounded proof batch.
"""
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


@dataclass(frozen=True)
class ReadinessRecord:
    batch_id: str
    target_commit_sha: str
    repository_ref: str
    baseline_id: str
    candidate_selection_id: str
    evidence_policy_revision: str
    verification_matrix_revision: str
    environment_identity: str
    checks: tuple[str, ...]
    commands: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    evidence_capture_mapping: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    retry_rules: tuple[str, ...]
    state: ReadinessState = ReadinessState.PREPARING

    def __post_init__(self) -> None:
        required = (
            "batch_id", "target_commit_sha", "repository_ref", "baseline_id",
            "candidate_selection_id", "evidence_policy_revision",
            "verification_matrix_revision", "environment_identity",
        )
        for name in required:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")
        if len(self.checks) != 13:
            raise ValueError("E7.107 requires exactly 13 readiness checks.")

    def ready(self, *, resolved_commit_sha: str, evidence_destinations_present: bool) -> "ReadinessRecord":
        if self.state != ReadinessState.PREPARING:
            raise ValueError("only PREPARING may become READY")
        if resolved_commit_sha != self.target_commit_sha:
            return self._with(ReadinessState.BLOCKED)
        if not evidence_destinations_present:
            return self._with(ReadinessState.BLOCKED)
        return self._with(ReadinessState.READY)

    def execute(self) -> "ReadinessRecord":
        if self.state != ReadinessState.READY:
            raise ValueError("only READY may enter EXECUTING")
        return self._with(ReadinessState.EXECUTING)

    def invalidate_for_commit_change(self) -> "ReadinessRecord":
        if self.state != ReadinessState.READY:
            raise ValueError("only READY may be invalidated")
        return self._with(ReadinessState.INVALIDATED)

    def _with(self, state: ReadinessState) -> "ReadinessRecord":
        return ReadinessRecord(**{**self.__dict__, "state": state})
