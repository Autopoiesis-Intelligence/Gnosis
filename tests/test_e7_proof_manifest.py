import pytest
from core.e7_proof_manifest import E7ProofRunManifest, ProofTerminalState

def make_manifest(**kw):
    data={"manifest_id":"m1","readiness_id":"r1","execution_id":"e1","execution_input_identity":"i1","runtime_evidence_digest":"d1","acceptance_decision_id":"a1","reconciliation_id":"q1","target_commit_sha":"c1","terminal_status":ProofTerminalState.COMMITTED}
    data.update(kw)
    return E7ProofRunManifest(**data)

def test_digest_deterministic():
    assert make_manifest().manifest_digest == make_manifest().manifest_digest

def test_identical_replay():
    m=make_manifest()
    m.assert_replay_compatible(make_manifest())

def test_conflicting_replay_rejected():
    m=make_manifest()
    with pytest.raises(ValueError):
        m.assert_replay_compatible(make_manifest(execution_id="e2"))

def test_terminal_status_is_identity():
    m=make_manifest()
    with pytest.raises(ValueError):
        m.assert_replay_compatible(make_manifest(terminal_status=ProofTerminalState.FAILED))

def test_required_identity_fail_closed():
    with pytest.raises(ValueError):
        make_manifest(execution_id="")
