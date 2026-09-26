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
            conn.execute("""CREATE TABLE IF NOT EXISTS authorization_consumption (
                authorization_digest TEXT PRIMARY KEY, sequence INTEGER NOT NULL,
                consumed_event TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS provenance_history (
                sequence INTEGER PRIMARY KEY, candidate_hash TEXT NOT NULL,
                evidence_hash TEXT NOT NULL, kernel_version TEXT NOT NULL,
                source_ids TEXT NOT NULL)""")
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

    def load_authorization_consumption(self) -> tuple[tuple[str, int, str], ...]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """SELECT authorization_digest, sequence, consumed_event
                FROM authorization_consumption ORDER BY sequence, authorization_digest"""
            ).fetchall()
        return tuple(rows)

    def verify_authorization_consumption(self) -> None:
        """Fail closed if durable authorization-consumption evidence is malformed."""
        history = self.load()
        consumptions = self.load_authorization_consumption()
        seen: set[str] = set()
        for digest, sequence, event in consumptions:
            if not digest or not digest.strip():
                raise ValueError("durable authorization digest is empty")
            if digest in seen:
                raise ValueError("duplicate durable authorization consumption")
            seen.add(digest)
            if event != "execution-authorized-commit":
                raise ValueError("durable authorization consumption event is invalid")
            if sequence < 0 or sequence >= len(history.records):
                raise ValueError("durable authorization consumption sequence is invalid")
        if len(consumptions) > len(history.records):
            raise ValueError("durable authorization consumption cardinality mismatch")

    def load_audit(self) -> tuple[AuditRecord, ...]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT sequence, transition_hash,
                previous_audit_hash, provenance_hash, event, audit_hash
                FROM audit_history ORDER BY sequence""").fetchall()
        records = tuple(AuditRecord(*row[:5]) for row in rows)
        for i, (row, record) in enumerate(zip(rows, records)):
            if record.digest() != row[5]:
                raise ValueError("durable audit digest mismatch")
            if record.sequence != i:
                raise ValueError("durable audit sequence is not contiguous")
        return records

    def load_provenance(self) -> tuple[Provenance, ...]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT candidate_hash, evidence_hash,
                kernel_version, source_ids FROM provenance_history
                ORDER BY sequence""").fetchall()
        return tuple(
            Provenance(a, b, c, tuple(d.split("\x1f")) if d else ())
            for a, b, c, d in rows
        )

    def commit_once_with_audit(
        self, record: TransitionRecord, provenance: Provenance,
        current, next_value, authorization_digest: str | None = None,
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
        provenances = self.load_provenance()
        if len(audits) != len(existing.records) or len(provenances) != len(existing.records):
            raise ValueError("durable history/audit/provenance cardinality mismatch")
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
                self._fail("after_history_before_provenance")
                conn.execute("""INSERT INTO provenance_history
                    (sequence, candidate_hash, evidence_hash, kernel_version, source_ids)
                    VALUES (?, ?, ?, ?, ?)""",
                    (record.sequence, provenance.candidate_hash,
                     provenance.evidence_hash, provenance.kernel_version,
                     "\x1f".join(provenance.source_ids)))
                self._fail("after_provenance_before_audit")
                if authorization_digest is not None:
                    if not authorization_digest.strip():
                        raise ValueError("authorization_digest is required when supplied")
                    try:
                        conn.execute("""INSERT INTO authorization_consumption
                            (authorization_digest, sequence, consumed_event)
                            VALUES (?, ?, ?)""",
                            (authorization_digest, record.sequence, "execution-authorized-commit"))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError("authorization has already been consumed") from exc
                self._fail("after_authorization_before_audit")
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
        durable_audit = self.load_audit()
        durable_provenance = self.load_provenance()
        if len(durable.records) != len(durable_audit) or len(durable.records) != len(durable_provenance):
            raise ValueError("durable triple cardinality mismatch")
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
