"""Causal audit chain bound to accepted transition history and provenance."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from .history import TransitionRecord
from .provenance import Provenance

def transition_digest(record: TransitionRecord) -> str:
    return hashlib.sha256(repr(record).encode("utf-8")).hexdigest()

def provenance_digest(provenance: Provenance) -> str:
    return hashlib.sha256(repr(provenance).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    transition_hash: str
    previous_audit_hash: str
    provenance_hash: str
    event: str = "COMMIT"
    def digest(self) -> str:
        payload = "|".join((str(self.sequence), self.transition_hash, self.previous_audit_hash, self.provenance_hash, self.event)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

def audit_for_commit(record: TransitionRecord, provenance: Provenance, previous: AuditRecord | None = None) -> AuditRecord:
    if not provenance.complete():
        raise ValueError("incomplete provenance")
    if record.candidate_hash != provenance.candidate_hash or record.evidence_hash != provenance.evidence_hash or record.kernel_version != provenance.kernel_version:
        raise ValueError("provenance does not bind transition")
    sequence = record.sequence
    previous_hash = "genesis" if previous is None else previous.digest()
    if previous is not None and previous.sequence + 1 != sequence:
        raise ValueError("audit sequence is not contiguous")
    return AuditRecord(sequence, transition_digest(record), previous_hash, provenance_digest(provenance))

@dataclass(frozen=True)
class AuditChain:
    records: tuple[AuditRecord, ...] = ()
    def append(self, record: AuditRecord) -> "AuditChain":
        expected = len(self.records)
        if record.sequence != expected:
            raise ValueError("audit sequence must be contiguous")
        expected_prev = "genesis" if not self.records else self.records[-1].digest()
        if record.previous_audit_hash != expected_prev:
            raise ValueError("audit chain is broken")
        return AuditChain(self.records + (record,))
    def verify_against_history(self, history: tuple[TransitionRecord, ...], provenance: tuple[Provenance, ...]) -> None:
        if len(self.records) != len(history) or len(history) != len(provenance):
            raise ValueError("audit/history/provenance lengths differ")
        chain = AuditChain()
        for audit, transition, proof in zip(self.records, history, provenance):
            expected = audit_for_commit(transition, proof, chain.records[-1] if chain.records else None)
            if audit != expected:
                raise ValueError("audit binding mismatch")
            chain = chain.append(audit)
