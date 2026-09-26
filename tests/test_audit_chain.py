from dataclasses import replace
import hashlib
import pytest

from core.audit_chain import AuditChain, AuditRecord
from core.history import AppendOnlyHistory, TransitionRecord
from core.provenance import Provenance


def _transition(seq=0):
    return TransitionRecord(
        sequence=seq,
        previous_hash="genesis",
        state_hash="state-0",
        kernel_version="k1",
        candidate_hash="state-0",
        admitted=True,
        evidence_hash="evidence-0",
    )


def _proof():
    return Provenance(
        candidate_hash="state-0",
        evidence_hash="evidence-0",
        kernel_version="k1",
    )


def _audit(t, p):
    return AuditRecord(
        sequence=0,
        transition_hash=hashlib.sha256(repr(t).encode()).hexdigest(),
        previous_audit_hash="genesis",
        provenance_hash=hashlib.sha256(repr(p).encode()).hexdigest(),
    )


def test_audit_chain_verifies_against_history_and_provenance():
    t = _transition()
    p = _proof()
    AuditChain().append(_audit(t, p)).verify_against_history((t,), (p,))


def test_audit_chain_rejects_transition_tampering():
    t = _transition()
    p = _proof()
    a = _audit(t, p)
    tampered = replace(t, state_hash="tampered")
    with pytest.raises(ValueError, match="transition binding"):
        AuditChain().append(a).verify_against_history((tampered,), (p,))


def test_audit_chain_rejects_provenance_tampering():
    t = _transition()
    p = _proof()
    a = _audit(t, p)
    tampered = replace(p, kernel_version="tampered")
    with pytest.raises(ValueError, match="provenance binding"):
        AuditChain().append(a).verify_against_history((t,), (tampered,))


def test_audit_chain_rejects_missing_audit_event():
    t = _transition()
    p = _proof()
    with pytest.raises(ValueError, match="lengths differ"):
        AuditChain().verify_against_history((t,), (p,))
