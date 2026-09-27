import pytest

from core.admission import admit
from core.commit import commit
from core.proof import ProofObligation
import hashlib
from core.safety import SafetyGate
from core.state import Psi


def admitted(current: Psi, candidate: Psi):
    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=True,
        evidence={"regime": "evolution", "reason": "canonical-gate-test"},
        candidate_digest=hashlib.sha256(repr(candidate).encode("utf-8")).hexdigest(),
    )
    return admit(candidate, proof)


def test_semantic_commit_uses_shared_safety_gate():
    current = Psi(x=("a",), relations=())
    candidate = Psi(x=("b",), relations=(("a", "b"),))
    admission = admitted(current, candidate)

    with pytest.raises(PermissionError):
        commit(
            current,
            admission,
            kernel_version="test-kernel",
            operation_count=2,
            gas_costs=(1, 1),
            safety_gate=SafetyGate(max_operations=1),
        ).apply(__import__("core.history", fromlist=["AppendOnlyHistory"]).AppendOnlyHistory())


def test_semantic_commit_binds_provenance_through_shared_gate():
    current = Psi(x=("a",), relations=())
    candidate = Psi(x=("b",), relations=(("a", "b"),))
    admission = admitted(current, candidate)

    value, history = commit(
        current,
        admission,
        kernel_version="test-kernel",
    ).apply(__import__("core.history", fromlist=["AppendOnlyHistory"]).AppendOnlyHistory())

    assert value == candidate
    assert history.head is not None
    assert history.head.kernel_version == "test-kernel"
    assert history.head.evidence_hash
