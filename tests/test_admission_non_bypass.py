"""Adversarial regression for the canonical evolutionary admission gate."""
import pytest

from core import evolution
from core.state import State


def test_canonical_evolution_cannot_select_when_all_proofs_fail(monkeypatch):
    def reject_all(*_args, **_kwargs):
        from core.proof import ProofObligation
import hashlib
        return ProofObligation(
            passed=False,
            invariant=False,
            viable=False,
            evidence={"adversarial": True},
        )

    monkeypatch.setattr(evolution, "prove_transition", reject_all)

    transition = evolution.evolutionary_psi_transition(
        generate=lambda state: (
            state.evolve(values={"x": 1, "relations": ()}),
        ),
        test=lambda _candidate: True,
    )

    with pytest.raises(ValueError, match="No candidate state passed ProofObligation"):
        transition(State(values={"x": 0, "relations": ()}).to_psi())


def test_rejected_admission_is_never_a_selection_input():
    from core.admission import admit, require_admitted
    from core.proof import ProofObligation

    rejected = admit(
        object(),
        ProofObligation(
            passed=False,
            invariant=False,
            viable=False,
            evidence={"adversarial": True},
        ),
    )

    with pytest.raises(ValueError, match="not admitted"):
        require_admitted(rejected)
