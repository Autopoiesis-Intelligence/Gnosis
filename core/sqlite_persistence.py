"""SQLite durable history + causal audit store with atomic commit boundaries."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Callable
from .audit_chain import AuditRecord, audit_for_commit, transition_digest, provenance_digest
from .commit_contract import CommitResult
from .history import AppendOnlyHistory, TransitionRecord, EvolutionOutcomeHistory, EvolutionOutcomeRecord
from .provenance import Provenance
from .distribution_execution_binding import DistributionExecutionBinding
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
                evidence_hash TEXT NOT NULL,
                kernel_execution_identity TEXT NOT NULL DEFAULT '',
                evidence_binding_digest TEXT NOT NULL DEFAULT '',
                evolution_evaluation_digest TEXT NOT NULL DEFAULT '')""")
            columns = {row[1] for row in conn.execute("PRAGMA table_info(transition_history)").fetchall()}
            if "kernel_execution_identity" not in columns:
                conn.execute("ALTER TABLE transition_history ADD COLUMN kernel_execution_identity TEXT NOT NULL DEFAULT ''")
            if "evidence_binding_digest" not in columns:
                conn.execute("ALTER TABLE transition_history ADD COLUMN evidence_binding_digest TEXT NOT NULL DEFAULT ''")
            if "evolution_evaluation_digest" not in columns:
                conn.execute("ALTER TABLE transition_history ADD COLUMN evolution_evaluation_digest TEXT NOT NULL DEFAULT ''")
            conn.execute("""CREATE TABLE IF NOT EXISTS evolution_outcome_history (
                sequence INTEGER PRIMARY KEY, previous_outcome_digest TEXT NOT NULL,
                outcome_digest TEXT NOT NULL, patch_id TEXT NOT NULL,
                parent_state_hash TEXT NOT NULL, candidate_state_hash TEXT NOT NULL,
                decision TEXT NOT NULL, evidence_digest TEXT NOT NULL)
            conn.execute("""CREATE TABLE IF NOT EXISTS audit_history (
                sequence INTEGER PRIMARY KEY, transition_hash TEXT NOT NULL,
                previous_audit_hash TEXT NOT NULL, provenance_hash TEXT NOT NULL,
                event TEXT NOT NULL, audit_hash TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS authorization_consumption (
                authorization_digest TEXT PRIMARY KEY, sequence INTEGER NOT NULL,
                state_digest TEXT NOT NULL, candidate_hash TEXT NOT NULL,
                consumed_event TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS durable_metadata (
                key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS provenance_history (
                sequence INTEGER PRIMARY KEY, candidate_hash TEXT NOT NULL,
                evidence_hash TEXT NOT NULL, kernel_version TEXT NOT NULL,
                source_ids TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS distribution_execution_binding (sequence INTEGER PRIMARY KEY, decision_id TEXT NOT NULL, decision_digest TEXT NOT NULL, kernel_id TEXT NOT NULL, execution_identity TEXT NOT NULL)""")
            conn.commit()

    def _fail(self, point: str) -> None:
        if self.failure_injector is not None:
            self.failure_injector(point)

    def load_evolution_outcomes(self) -> EvolutionOutcomeHistory:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT sequence, previous_outcome_digest,
                outcome_digest, patch_id, parent_state_hash, candidate_state_hash,
                decision, evidence_digest FROM evolution_outcome_history
                ORDER BY sequence""").fetchall()
        history = EvolutionOutcomeHistory()
        for row in rows:
            history = history.append(EvolutionOutcomeRecord(*row))
        return history

    def append_evolution_outcome(self, record: EvolutionOutcomeRecord) -> EvolutionOutcomeHistory:
        existing = self.load_evolution_outcomes()
        if existing.records:
            if record.sequence != existing.head.sequence + 1:
                raise ValueError("evolution outcome sequence is not contiguous")
            if record.previous_outcome_digest != existing.head.outcome_digest:
                raise ValueError("evolution outcome predecessor mismatch")
        elif record.sequence != 0:
            raise ValueError("evolution outcome genesis must have sequence zero")
        with sqlite3.connect(self.path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("""INSERT INTO evolution_outcome_history
                    (sequence, previous_outcome_digest, outcome_digest, patch_id,
                     parent_state_hash, candidate_state_hash, decision, evidence_digest)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record.sequence, record.previous_outcome_digest, record.outcome_digest,
                     record.patch_id, record.parent_state_hash, record.candidate_state_hash,
                     record.decision, record.evidence_digest))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return self.load_evolution_outcomes()

    def verify_evolution_cross_table_consistency(self) -> None:
        """Verify committed evolution outcomes are bound to canonical transitions."""
        outcomes = self.load_evolution_outcomes()
        transitions = self.load()
        for outcome in outcomes.records:
            if outcome.decision != "commit":
                continue
            matches = [r for r in transitions.records
                       if r.evolution_evaluation_digest == outcome.outcome_digest
                       and r.state_hash == outcome.candidate_state_hash
                       and r.previous_hash == outcome.parent_state_hash]
            if len(matches) != 1:
                raise ValueError("evolution outcome has no unique canonical binding")

    def verify_evolution_outcomes(self) -> None:
        history = self.load_evolution_outcomes()
        for i, record in enumerate(history.records):
            if record.sequence != i:
                raise ValueError("evolution outcome sequence is not contiguous")
            if i == 0:
                if record.previous_outcome_digest:
                    raise ValueError("evolution outcome genesis predecessor must be empty")
            elif record.previous_outcome_digest != history.records[i - 1].outcome_digest:
                raise ValueError("evolution outcome chain mismatch")

    def load(self) -> AppendOnlyHistory:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute("""SELECT sequence, previous_hash, state_hash,
                kernel_version, candidate_hash, admitted, evidence_hash,
                kernel_execution_identity, evidence_binding_digest, evolution_evaluation_digest
                FROM transition_history ORDER BY sequence""").fetchall()
        history = AppendOnlyHistory()
        for row in rows:
            history = history.append(TransitionRecord(
                sequence=row[0], previous_hash=row[1], state_hash=row[2],
                kernel_version=row[3], candidate_hash=row[4],
                admitted=bool(row[5]), evidence_hash=row[6],
                kernel_execution_identity=row[7], evidence_binding_digest=row[8], evolution_evaluation_digest=row[9]))
        return history

    def verify_cross_table_consistency(self, *, initial_state_digest: str | None = None) -> None:
        """Verify that all durable evidence tables describe the same accepted transitions."""
        history = self.load()
        audits = self.load_audit()
        provenances = self.load_provenance()
        consumptions = self.load_authorization_consumption()
        bindings = self.load_distribution_execution_bindings()
        if not (len(history.records) == len(audits) == len(provenances)):
            raise ValueError("durable evidence cardinality mismatch")
        for i, (record, audit, proof) in enumerate(zip(history.records, audits, provenances)):
            if record.sequence != i or audit.sequence != i:
                raise ValueError("durable sequence binding mismatch")
            if i == 0 and record.previous_hash != "genesis":
                raise ValueError("durable transition binding mismatch: genesis predecessor")
            if i > 0 and record.previous_hash != history.records[i - 1].state_hash:
                raise ValueError("durable transition binding mismatch: predecessor chain")
            if i > 0 and audit.previous_audit_hash != audits[i - 1].digest():
                raise ValueError("durable audit predecessor chain mismatch")
            if record.candidate_hash != proof.candidate_hash:
                raise ValueError("durable candidate binding mismatch")
            if record.evidence_hash != proof.evidence_hash:
                raise ValueError("durable evidence binding mismatch")
            if record.kernel_version != proof.kernel_version:
                raise ValueError("durable kernel binding mismatch")
            if audit.transition_hash != transition_digest(record):
                raise ValueError("durable transition binding mismatch")
            if audit.provenance_hash != provenance_digest(proof):
                raise ValueError("durable provenance binding mismatch")
        for sequence, decision_id, decision_digest, kernel_id, execution_identity in bindings:
            if sequence < 0 or sequence >= len(history.records):
                raise ValueError("durable distribution binding sequence mismatch")
            if history.records[sequence].kernel_execution_identity != execution_identity:
                raise ValueError("durable distribution execution identity mismatch")
            if not decision_id or not decision_digest or not kernel_id:
                raise ValueError("durable distribution binding is incomplete")
        self.verify_authorization_consumption(initial_state_digest=initial_state_digest)
        for digest, sequence, state_digest, candidate_hash, event in consumptions:
            if sequence < 0 or sequence >= len(history.records):
                raise ValueError("durable authorization sequence binding mismatch")
            if candidate_hash != history.records[sequence].candidate_hash:
                raise ValueError("durable authorization candidate binding mismatch")

    def load_distribution_execution_bindings(self) -> tuple[tuple, ...]:
        with sqlite3.connect(self.path) as conn:
            return tuple(conn.execute("SELECT sequence, decision_id, decision_digest, kernel_id, execution_identity FROM distribution_execution_binding ORDER BY sequence").fetchall())

    def load_authorization_consumption(self) -> tuple[tuple[str, int, str], ...]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """SELECT authorization_digest, sequence, state_digest, candidate_hash, consumed_event
                FROM authorization_consumption ORDER BY sequence, authorization_digest"""
            ).fetchall()
        return tuple(rows)

    def assert_authorization_unused(self, authorization_digest: str) -> None:
        if not authorization_digest.strip():
            raise ValueError("authorization_digest is required")
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT 1 FROM authorization_consumption WHERE authorization_digest = ?",
                (authorization_digest,),
            ).fetchone()
        if row is not None:
            raise ValueError("authorization has already been consumed")

    def _load_initial_state_digest(self) -> str | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT value FROM durable_metadata WHERE key = 'initial_state_digest'").fetchone()
        return row[0] if row is not None else None

    def verify_authorization_consumption(self, *, initial_state_digest: str | None = None) -> None:
        """Fail closed if durable authorization-consumption evidence is malformed."""
        history = self.load()
        consumptions = self.load_authorization_consumption()
        if initial_state_digest is None:
            initial_state_digest = self._load_initial_state_digest()
        seen: set[str] = set()
        for digest, sequence, state_digest, candidate_hash, event in consumptions:
            if not digest or not digest.strip():
                raise ValueError("durable authorization digest is empty")
            if digest in seen:
                raise ValueError("duplicate durable authorization consumption")
            seen.add(digest)
            if not state_digest or not candidate_hash:
                raise ValueError("durable authorization binding evidence is incomplete")
            if event != "execution-authorized-commit":
                raise ValueError("durable authorization consumption event is invalid")
            if sequence < 0 or sequence >= len(history.records):
                raise ValueError("durable authorization consumption sequence is invalid")
            if candidate_hash != history.records[sequence].candidate_hash:
                raise ValueError("durable authorization candidate binding mismatch")
            expected_state_digest = (history.records[sequence - 1].state_hash if sequence > 0 else initial_state_digest)
            if expected_state_digest is not None and state_digest != expected_state_digest:
                raise ValueError("durable authorization state binding mismatch")
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
        authorization_state_digest: str | None = None,
        distribution_binding: DistributionExecutionBinding | None = None,
        evolution_outcome: EvolutionOutcomeRecord | None = None,
    ) -> CommitResult:
        """Atomically commit History + Audit and optional evolution outcome."""
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

        # A new commit may extend durable evidence only from a verified base.
        # Cardinality equality alone is insufficient: hashes/bindings may be corrupted
        # while all tables still contain the same number of rows.
        self.verify_cross_table_consistency()
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
                if record.sequence == 0 and authorization_digest is not None:
                    conn.execute("INSERT OR IGNORE INTO durable_metadata(key, value) VALUES (?, ?)", ("initial_state_digest", authorization_state_digest or record.previous_hash))
                if record.sequence == 0 and authorization_digest is not None:
                    conn.execute("INSERT OR IGNORE INTO durable_metadata(key, value) VALUES (?, ?)", ("initial_state_digest", authorization_state_digest or record.previous_hash))
                if distribution_binding is not None:
                    if distribution_binding.execution_identity != record.kernel_execution_identity:
                        raise ValueError("distribution binding execution identity mismatch")
                    conn.execute("INSERT INTO distribution_execution_binding (sequence, decision_id, decision_digest, kernel_id, execution_identity) VALUES (?, ?, ?, ?, ?)", (record.sequence, distribution_binding.decision_id, distribution_binding.decision_digest, distribution_binding.kernel_id, distribution_binding.execution_identity))
                conn.execute("""INSERT INTO transition_history
                    (sequence, previous_hash, state_hash, kernel_version,
                     candidate_hash, admitted, evidence_hash,
                     kernel_execution_identity, evidence_binding_digest, evolution_evaluation_digest)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record.sequence, record.previous_hash, record.state_hash,
                     record.kernel_version, record.candidate_hash,
                     int(record.admitted), record.evidence_hash,
                     record.kernel_execution_identity, record.evidence_binding_digest, record.evolution_evaluation_digest))
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
                            (authorization_digest, sequence, state_digest, candidate_hash, consumed_event)
                            VALUES (?, ?, ?, ?, ?)""",
                            (authorization_digest, record.sequence, authorization_state_digest or record.previous_hash,
             record.candidate_hash, "execution-authorized-commit"))
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
                if evolution_outcome is not None:
                    if evolution_outcome.decision != "commit":
                        raise ValueError("canonical evolution commit requires COMMIT outcome")
                    if evolution_outcome.candidate_state_hash != record.state_hash:
                        raise ValueError("evolution outcome candidate does not match committed state")
                    if evolution_outcome.parent_state_hash != record.previous_hash:
                        raise ValueError("evolution outcome parent does not match committed predecessor")
                    conn.execute("""INSERT INTO evolution_outcome_history
                        (sequence, previous_outcome_digest, outcome_digest, patch_id,
                         parent_state_hash, candidate_state_hash, decision, evidence_digest)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (evolution_outcome.sequence, evolution_outcome.previous_outcome_digest,
                         evolution_outcome.outcome_digest, evolution_outcome.patch_id,
                         evolution_outcome.parent_state_hash, evolution_outcome.candidate_state_hash,
                         evolution_outcome.decision, evolution_outcome.evidence_digest))
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

    def commit_evolution_with_audit(
        self, record: TransitionRecord, provenance: Provenance,
        evolution_outcome: EvolutionOutcomeRecord, current, next_value,
        authorization_digest: str | None = None,
        authorization_state_digest: str | None = None,
        distribution_binding: DistributionExecutionBinding | None = None,
    ) -> CommitResult:
        """Atomically persist a terminal COMMIT outcome with the canonical transition."""
        if evolution_outcome.decision != "commit":
            raise ValueError("canonical evolution commit requires COMMIT outcome")
        if evolution_outcome.candidate_state_hash != record.state_hash:
            raise ValueError("evolution outcome candidate does not match committed state")
        if evolution_outcome.parent_state_hash != record.previous_hash:
            raise ValueError("evolution outcome parent does not match committed predecessor")
        return self.commit_once_with_audit(
            record, provenance, current, next_value,
            authorization_digest=authorization_digest,
            authorization_state_digest=authorization_state_digest,
            distribution_binding=distribution_binding,
            evolution_outcome=evolution_outcome,
        )

    def commit_once(self, record: TransitionRecord, current, next_value) -> CommitResult:
        """Fail closed: history-only durable writes are not a canonical commit path."""
        raise ValueError(
            "history-only durable commit path is disabled; use commit_once_with_audit()"
        )

