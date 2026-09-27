import pytest

from core.commit import commit
from core.admission import admit
from core.proof import ProofObligation
import hashlib
from core.state import Psi


def proof(candidate, passed):
    return ProofObligation(
        passed=passed,
        invariant=passed,
        viable=passed,
        evidence={"test": True},
        candidate_digest=hashlib.sha256(repr(candidate).encode("utf-8")).hexdigest(),
    )


def test_only_admitted_psi_can_cross_semantic_commit():
    current = Psi(x=("a",), relations=())
    candidate = Psi(x=("b",), relations=())

    result = commit(current, admit(candidate, proof(candidate, True)), kernel_version="test-kernel")
    assert result.apply(__import__('core.history', fromlist=['AppendOnlyHistory']).AppendOnlyHistory())[0] == candidate


def test_rejected_candidate_cannot_cross_semantic_commit():
    current = Psi(x=("a",), relations=())
    candidate = Psi(x=("b",), relations=())

    result = commit(current, admit(candidate, proof(candidate, False)), kernel_version="test-kernel")
    with pytest.raises(ValueError, match="not admitted"):
        result.apply(__import__('core.history', fromlist=['AppendOnlyHistory']).AppendOnlyHistory())


def test_non_psi_candidate_cannot_be_semantic_commit():
    current = Psi(x=("a",), relations=())
    candidate = object()
    result = commit(current, admit(candidate, proof(candidate, True)), kernel_version="test-kernel")
    with pytest.raises(TypeError):
        result.apply()
