import pytest

from core.admission import Admission
from core.commit import commit
from core.history import AppendOnlyHistory
from core.proof import ProofObligation
import hashlib
from core.state import Psi


def accepted(candidate):
    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=True,
        evidence={"test": True},
        candidate_digest=hashlib.sha256(repr(candidate).encode("utf-8")).hexdigest(),
    )
    return Admission(True, candidate, proof)


def test_commit_rejects_previous_psi_that_does_not_match_history_head():
    first = Psi(x=(1,), relations=())
    second = Psi(x=(2,), relations=())
    forged_previous = Psi(x=(999,), relations=())

    _, history = commit(first, accepted(second), "test").apply(AppendOnlyHistory())

    with pytest.raises(ValueError, match="history head"):
        commit(forged_previous, accepted(Psi(x=(3,), relations=())), "test").apply(history)
