"""Causal audit chain bound to accepted transition history."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .history import TransitionRecord
from .provenance import Provenance


@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    transition_hash: str
    previous_audit_hash: str
    provenance_hash: str
    event: str = "COMMIT"

    def digest(self) -> str:
        payload = "|".join(
            (
                str(self.sequence),
                self.transition_hash,
                self.previous_audit_hash,
                self.provenance_hash,
                self.event,
            )
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AuditChain:
    records: tuple[AuditRecord, ...] = ()

    def append(self, record: AuditRecord) -> "AuditChain":
        if record.sequence != len(self.records):
            raise ValueError("audit sequence must be contiguous")
        if not self.records and record.previous_audit_hash != "genesis":
            raise ValueError("first audit record must point to genesis")
        if self.records and record.previous_audit_hash != self.records[-1].digest():
            raise ValueError("audit chain is broken")
        return AuditChain(self.records + (record,))

    def verify_against_history(
        self,
        history: tuple[TransitionRecord, ...],
        provenance: tuple[Provenance, ...],
    ) -> None:
        if len(self.records) != len(history) or len(history) != len(provenance):
            raise ValueError("audit/history/provenance lengths differ")
        previous_audit = "genesis"
        for index, (audit, transition, proof) in enumerate(
            zip(self.records, history, provenance)
        ):
            if audit.sequence != index:
                raise ValueError("audit sequence mismatch")
            if audit.previous_audit_hash != previous_audit:
                raise ValueError("audit predecessor mismatch")
            transition_hash = hashlib.sha256(
                repr(transition).encode("utf-8")
            ).hexdigest()
            provenance_hash = hashlib.sha256(
                repr(proof).encode("utf-8")
            ).hexdigest()
            if audit.transition_hash != transition_hash:
                raise ValueError("audit transition binding mismatch")
            if audit.provenance_hash != provenance_hash:
                raise ValueError("audit provenance binding mismatch")
            previous_audit = audit.digest()
