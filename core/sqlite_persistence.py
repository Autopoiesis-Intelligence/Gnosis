"""SQLite durable history + causal audit store with atomic commit boundaries."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Callable
from .audit_chain import AuditRecord, audit_for_commit
from .commit_contract import CommitResult
from .history import AppendOnlyHistory, TransitionRecord
from .provenance import Provenance
FailureInjector = Callable[[str], None]

class SQLiteHistoryStore:
    """Persist accepted transitions and their causal audit atomically."""

    def __init__(self, path: str | Path, *, failure_injector: FailureInjector | None = None):
        self.path = str(path)
        self.failure_injector = failure_injector
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS transition_history (
                sequence INTEGER PRIMARY KEY, previous_hash TEXT NOT NULL,
                state_hash TEXT NOT NULL, kernel_version TEXT NOT NULL,
                candidate_hash TEXT NOT NULL, admitted INTEGER NOT NULL CHECK (admitted = 1),
                evidence_hash TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS audit_history (
                sequence INTEGER PRIMARY KEY, transition_hash TEXT NOT NULL,
                previous_audit_hash TEXT NOT NULL, provenance_hash TEXT NOT NULL,
                event TEXT NOT NULL, audit_hash TEXT NOT NULL)""")
            conn.commit()

    def _fail(self, point: str) -> None:
        if self.failure_injector is not None:
            self.failure_injector(point)

    def load(self) -> AppendOnlyHistory:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT sequence, previous_hash, state_hash,
                kernel_version, candidate_hash, admitted, evidence_hash
                FROM transition_history ORDER BY sequence""").fetchall()
        history = AppendOnlyHistory()
        for row in rows:
            history = history.append(TransitionRecord(
                sequence=row[0], previous_hash=row[1], state_hash=row[2],
                kernel_version=row[3], candidate_hash=row[4],
                admitted=bool(row[5]), evidence_hash=row[6]))
        return history

    def load_audit(self) -> tuple[AuditRecord, ...]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT sequence, transition_hash,
                previous_audit_hash, provenance_hash, event
                FROM audit_history ORDER BY sequence""").fetchall()
        records = tuple(AuditRecord(*row) for row in rows)
        for i, record in enumerate(records):
            if record.digest() != self._audit_digest(record):
                raise ValueError("durable audit digest mismatch")
            if record.sequence != i:
                raise ValueError("durable audit sequence is not contiguous")
        return records

    @staticmethod
    def _audit_digest(record: AuditRecord) -> str:
        return record.digest()

    def commit_once_with_audit(
        self, record: TransitionRecord, provenance: Provenance,
        current, next_value,
    ) -> CommitResult:
        """Atomically commit History + canonical Audit or commit neither."""
        existing = self.load()
        if existing.records:
            head = existing.head
            if record.sequence < head.sequence:
                raise ValueError("commit sequence is stale")
            if record.sequence == head.sequence:
                if record.state_hash == head.state_hash:
                    return CommitResult(current, existing, False)
                raise ValueError("commit conflicts with existing head")
        elif record.sequence != 0:
            raise ValueError("genesis commit must have sequence zero")

        audits = self.load_audit()
        if len(audits) != len(existing.records):
            raise ValueError("durable audit/history cardinality mismatch")
        previous_audit = audits[-1] if audits else None
        audit = audit_for_commit(record, provenance, previous_audit)

        if existing.head is not None and record.previous_hash != existing.head.state_hash:
            raise ValueError("history chain is broken")

        self._fail("before_transaction")
        with sqlite3.connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._fail("before_insert")
                conn.execute("""INSERT INTO transition_history
                    (sequence, previous_hash, state_hash, kernel_version,
                     candidate_hash, admitted, evidence_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (record.sequence, record.previous_hash, record.state_hash,
                     record.kernel_version, record.candidate_hash,
                     int(record.admitted), record.evidence_hash))
                self._fail("after_history_before_audit")
                conn.execute("""INSERT INTO audit_history
                    (sequence, transition_hash, previous_audit_hash,
                     provenance_hash, event, audit_hash)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (audit.sequence, audit.transition_hash,
                     audit.previous_audit_hash, audit.provenance_hash,
                     audit.event, audit.digest()))
                self._fail("after_audit_before_commit")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        self._fail("after_commit")
        durable = self.load()
        self.load_audit()
        return CommitResult(next_value, durable, True)

    def commit_once(self, record: TransitionRecord, current, next_value) -> CommitResult:
        """Legacy history-only compatibility path; new durable commits use audit."""
        return self._commit_history_only(record, current, next_value)

    def _commit_history_only(self, record: TransitionRecord, current, next_value) -> CommitResult:
        existing = self.load()
        if existing.records:
            head = existing.head
            if record.sequence < head.sequence:
                raise ValueError("commit sequence is stale")
            if record.sequence == head.sequence:
                if record.state_hash == head.state_hash:
                    return CommitResult(current, existing, False)
                raise ValueError("commit conflicts with existing head")
        elif record.sequence != 0:
            raise ValueError("genesis commit must have sequence zero")
        if existing.head is not None and record.previous_hash != existing.head.state_hash:
            raise ValueError("history chain is broken")
        self._fail("before_transaction")
        with sqlite3.connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._fail("before_insert")
                conn.execute("""INSERT INTO transition_history
                    (sequence, previous_hash, state_hash, kernel_version,
                     candidate_hash, admitted, evidence_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (record.sequence, record.previous_hash, record.state_hash,
                     record.kernel_version, record.candidate_hash,
                     int(record.admitted), record.evidence_hash))
                self._fail("after_insert_before_commit")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        self._fail("after_commit")
        return CommitResult(next_value, self.load(), True)
