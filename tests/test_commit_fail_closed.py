import pytest

from core.commit import commit
from core.admission import Admission
from core.proof import ProofObligation
import hashlib
from core.state import Psi, State
from core.history import AppendOnlyHistory


def test_canonical_commit_rejects_unadmitted_candidate():
    previous = Psi(x=(), relations=())
    rejected = Psi(x=(1,), relations=())

    proof = ProofObligation(
        passed=False,
        invariant=False,
        viable=False,
        evidence={"adversarial": True},
        candidate_digest=hashlib.sha256(repr(rejected).encode("utf-8")).hexdigest(),
    )
    admission = Admission(
        accepted=False,
        candidate=rejected,
        proof=proof,
    )

    with pytest.raises(ValueError, match="not admitted"):
        commit(previous, admission, kernel_version="test-kernel").apply(AppendOnlyHistory())


def test_canonical_commit_accepts_admitted_psi():
    previous = Psi(x=(), relations=())
    candidate = Psi(x=(1,), relations=())

    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=True,
        evidence={"test": True},
        candidate_digest=hashlib.sha256(repr(candidate).encode("utf-8")).hexdigest(),
    )
    admission = Admission(
        accepted=True,
        candidate=candidate,
        proof=proof,
    )

    assert commit(previous, admission, kernel_version="test-kernel").apply(AppendOnlyHistory())[0] == candidate


def test_canonical_commit_rejects_legacy_state_even_if_admitted():
    previous = Psi(x=(), relations=())
    legacy_candidate = State.from_psi(Psi(x=(2,), relations=()))

    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=True,
        evidence={"legacy-adversarial": True},
        candidate_digest=hashlib.sha256(repr(legacy_candidate.to_psi()).encode("utf-8")).hexdigest(),
    )
    admission = Admission(
        accepted=True,
        candidate=legacy_candidate,
        proof=proof,
    )

    with pytest.raises(TypeError, match="canonical"):
        commit(previous, admission, kernel_version="test-kernel").apply(AppendOnlyHistory())
