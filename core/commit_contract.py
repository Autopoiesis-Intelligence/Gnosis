"""Atomic/idempotent persistence-facing commit contract."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar
from .history import AppendOnlyHistory, TransitionRecord
T = TypeVar("T")


@dataclass(frozen=True)
class CommitResult(Generic[T]):
    value: T
    history: AppendOnlyHistory
    applied: bool

    @property
    def committed(self) -> bool:
        """Compatibility alias for whether this commit was newly applied."""
        return self.applied


def commit_once(history: AppendOnlyHistory, record: TransitionRecord, current: T, next_value: T) -> CommitResult[T]:
    if history.records:
        head = history.records[-1]
        if record.sequence < head.sequence:
            raise ValueError("commit sequence is stale")
        if record.sequence == head.sequence:
            if record.state_hash == head.state_hash:
                return CommitResult(current, history, False)
            raise ValueError("commit conflicts with existing head")
    elif record.sequence != 0:
        raise ValueError("genesis commit must have sequence zero")
    return CommitResult(next_value, history.append(record), True)
