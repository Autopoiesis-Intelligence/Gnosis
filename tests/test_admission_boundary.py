"""Regression tests for the explicit semantic admission boundary."""
from __future__ import annotations

import pytest

from core.admission import Admission, admit, require_admitted
from core.evolution import evolutionary_psi_transition
from core.proof import ProofObligation
from core.state import State


def _proof(passed: bool) -> ProofObligation:
    return ProofObligation(
        passed=passed,
        invariant=passed,
        viable=passed,
        evidence={"test": True},
    )


def test_admission_accepts_only_proof_result():
    candidate = State(values={"x": "next", "relations": ()})
    result = admit(candidate, _proof(True))
    assert isinstance(result, Admission)
    assert result.accepted is True
    assert require_admitted(result) is candidate


def test_rejected_admission_cannot_be_required():
    candidate = State(values={"x": "next", "relations": ()})
    result = admit(candidate, _proof(False))
    assert result.accepted is False
    with pytest.raises(ValueError, match="not admitted"):
        require_admitted(result)


def test_admission_requires_explicit_proof_object():
    candidate = State(values={"x": "next", "relations": ()})
    with pytest.raises(TypeError, match="ProofObligation"):
        admit(candidate, True)


def test_canonical_evolution_uses_admission_before_selection():
    def generate(state):
        return (
            state.evolve(values={"x": "a", "relations": ()}),
            state.evolve(values={"x": "b", "relations": ("r",)}),
        )

    transition = evolutionary_psi_transition(
        generate=generate,
        test=lambda _candidate: True,
    )
    result = transition(State(values={"x": "current", "relations": ()}).to_psi())
    assert result.x in {"a", "b"}


def test_evidence_cannot_upgrade_rejected_admission():
    candidate = State(values={"x": "forged", "relations": ()})
    proof = ProofObligation(
        passed=False,
        invariant=False,
        viable=False,
        evidence={
            "regime": "fundamental",
            "source_ids": ("trusted-source",),
            "evidence_hash": "valid-looking",
            "attestation": True,
        },
    )
    result = admit(candidate, proof)
    assert result.accepted is False
    with pytest.raises(ValueError, match="not admitted"):
        require_admitted(result)


def test_provenance_attachment_does_not_create_admission_authority():
    from core.provenance import Provenance, attach_provenance

    record = __import__("core.history", fromlist=["TransitionRecord"]).TransitionRecord(
        0, "", "s0", "k1", "c0", True, "e0"
    )
    attached = attach_provenance(
        record, Provenance("c0", "e0", "k1", ("trusted-source",))
    )
    assert attached == record
    proof = ProofObligation(
        passed=False,
        invariant=False,
        viable=False,
        evidence={"provenance": attached, "source_ids": ("trusted-source",)},
    )
    candidate = State(values={"x": "from-provenance", "relations": ()})
    admission = admit(candidate, proof)
    assert admission.accepted is False


def test_evidence_cannot_construct_certified_meta_transition():
    candidate = State(values={"x": "evidence-only", "relations": ()})
    evidence = {
        "source_ids": ("trusted-source",),
        "attestation": True,
        "candidate_hash": "candidate-hash",
        "evidence_hash": "evidence-hash",
        "kernel_version": "k1",
    }
    rejected = admit(
        candidate,
        ProofObligation(
            passed=False,
            invariant=False,
            viable=False,
            evidence=evidence,
        ),
    )
    assert rejected.accepted is False
    with pytest.raises(ValueError, match="not admitted"):
        require_admitted(rejected)


def test_fundamental_admission_does_not_require_viability():
    candidate = State(values={"x": "fundamental", "relations": ()})
    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=False,
        evidence={"regime": "fundamental"},
    )
    result = admit(candidate, proof)
    assert result.accepted is True
    assert require_admitted(result) is candidate


def test_evolutionary_admission_requires_viability():
    candidate = State(values={"x": "evolutionary", "relations": ()})
    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=False,
        evidence={"regime": "evolutionary"},
    )
    result = admit(candidate, proof)
    assert result.accepted is False


@pytest.mark.parametrize(
    ("regime", "viable", "expected"),
    [
        ("fundamental", False, True),
        ("evolutionary", True, True),
        ("evolutionary", False, False),
    ],
)
def test_end_to_end_admission_psi_and_k0_certification(regime, viable, expected):
    from core.meta_transition import MetaTransition, RefinementProof
    from core.root_invariant import canonical_root_invariant

    candidate = State(values={"x": "certified", "relations": ()})
    proof = ProofObligation(
        passed=True,
        invariant=True,
        viable=viable,
        evidence={"regime": regime},
    )
    admission = admit(candidate, proof)
    assert admission.accepted is expected

    before_kernel = {"sealed": True, "version": 1}
    after_kernel = {"sealed": True, "version": 2}
    kernel_transition = MetaTransition(
        before_kernel,
        after_kernel,
        RefinementProof(
            canonical_root_invariant(),
            before_kernel,
            after_kernel,
            "K0 preserved independently of Psi admission",
        ),
    )

    if expected:
        assert require_admitted(admission) is candidate
        assert kernel_transition.admissible()
        assert kernel_transition.apply() == after_kernel
    else:
        assert not admission.accepted
        with pytest.raises(ValueError, match="not admitted"):
            require_admitted(admission)
        # A valid K0 certificate cannot upgrade a rejected Psi admission.
        assert kernel_transition.admissible()
