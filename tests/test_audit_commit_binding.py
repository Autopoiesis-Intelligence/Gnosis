from core.audit_chain import AuditChain, audit_for_commit
from core.history import TransitionRecord
from core.provenance import Provenance

def test_audit_for_commit_requires_matching_provenance():
    record = TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")
    bad = Provenance("other","e0","k1")
    try:
        audit_for_commit(record,bad)
    except ValueError:
        return
    raise AssertionError("mismatched provenance must fail")

def test_audit_for_commit_is_causally_bound():
    record = TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")
    proof = Provenance("s0","e0","k1")
    audit = audit_for_commit(record,proof)
    AuditChain().append(audit).verify_against_history((record,),(proof,))
