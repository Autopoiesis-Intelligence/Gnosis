import pytest

from core.admission import Admission
from core.commit import commit
from core.history import AppendOnlyHistory
from core.proof import ProofObligation
import hashlib
from core.safety import SafetyGate
from core.state import Psi


def accepted(candidate):
    return Admission(
        True,
        candidate,
        ProofObligation(
            passed=True,
            invariant=True,
            viable=True,
            evidence={"test": True},
        ),
    )


def test_semantic_commit_respects_hard_stop_before_persistence():
    psi = Psi(x=(1,), relations=())
    candidate = Psi(x=(2,), relations=())

    with pytest.raises(PermissionError):
        commit(
            psi,
            accepted(candidate),
            "test",
            safety_gate=SafetyGate(hard_stop=True),
        ).apply(AppendOnlyHistory())


def test_semantic_commit_respects_gas_budget_before_persistence():
    psi = Psi(x=(1,), relations=())
    candidate = Psi(x=(2,), relations=())

    with pytest.raises(ValueError, match="exhausted"):
        commit(
            psi,
            accepted(candidate),
            "test",
            gas_costs=(21,),
            gas_limit=20,
        ).apply(AppendOnlyHistory())
