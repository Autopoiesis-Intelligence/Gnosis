import pytest

from core.e7_109_acceptance import AcceptanceDecision, AcceptanceState
from core.e7_110_reconciliation import ReconciliationSnapshot, ReconciliationState
from core.e7_proof_manifest import E7ProofRunManifest, ProofTerminalState
from core.e7_cross_layer_validation import RuntimeEvidenceLink, validate_e7_chain

def make():
    acceptance=AcceptanceDecision("a1","e1","c1","d","VERIFIED","p1","scope","auth",(),AcceptanceState.ACCEPTED)
    reconciliation=ReconciliationSnapshot("r1","b1","inputs","metric","80","80","calc",("d",),ReconciliationState.RECONCILED)
    runtime=RuntimeEvidenceLink("e1","i1","runtime","COMMITTED")
    manifest=E7ProofRunManifest("m1","ready","e1","i1","runtime","a1","r1","commit",ProofTerminalState.COMMITTED)
    return manifest,acceptance,reconciliation,runtime

def test_matching_chain_validates():
    validate_e7_chain(*make())

def test_wrong_execution_is_rejected():
    m,a,r,rt=make()
    with pytest.raises(ValueError):
        validate_e7_chain(m,a,r,RuntimeEvidenceLink("other","i1","runtime","COMMITTED"))

def test_wrong_input_identity_is_rejected():
    m,a,r,rt=make()
    with pytest.raises(ValueError):
        validate_e7_chain(m,a,r,RuntimeEvidenceLink("e1","other","runtime","COMMITTED"))

def test_wrong_runtime_digest_is_rejected():
    m,a,r,rt=make()
    with pytest.raises(ValueError):
        validate_e7_chain(m,a,r,RuntimeEvidenceLink("e1","i1","other","COMMITTED"))

def test_wrong_acceptance_is_rejected():
    m,a,r,rt=make()
    with pytest.raises(ValueError):
        validate_e7_chain(m,AcceptanceDecision("a2","e1","c1","d","VERIFIED","p1","scope","auth",(),AcceptanceState.ACCEPTED),r,rt)

def test_wrong_reconciliation_is_rejected():
    m,a,r,rt=make()
    bad=ReconciliationSnapshot("other","b1","inputs","metric","80","80","calc",("d",),ReconciliationState.RECONCILED)
    with pytest.raises(ValueError):
        validate_e7_chain(m,a,bad,rt)
