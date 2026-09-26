import pytest
from core.dynamics import closure
from core.meta_admission import MetaAdmission
from core.meta_transition import MetaTransition, RefinementProof
from core.psi_transition import make_psi_transition
from core.root_invariant import RootInvariant, canonical_root_invariant
from core.state import Psi


def test_unified_meta_admission_requires_k0_refinement_and_closure():
    root = canonical_root_invariant()
    before = {"sealed": True, "v": 1}
    after = {"sealed": True, "v": 2}

    transition = MetaTransition(
        before,
        after,
        RefinementProof(
            root,
            before,
            after,
            "preserves K0 and refines",
            refinement=lambda a, b: b["v"] >= a["v"],
        ),
    )

    f = make_psi_transition(lambda x, r: (x, r))
    from core.state import Psi
    psi = Psi(x=("a",), relations=())
    obligation = closure(f, lambda p: "a" in p.x, [psi])

    admission = MetaAdmission(transition, obligation, root)
    assert admission.admissible()
    assert admission.apply() == after


def test_meta_admission_cannot_bypass_root_invariant():
    root = canonical_root_invariant()
    before = {"sealed": True, "v": 1}
    after = {"sealed": False, "v": 999}
    transition = MetaTransition(
        before, after,
        RefinementProof(root, before, after, "forged", refinement=lambda _a, _b: True),
    )
    f = make_psi_transition(lambda x, r: (x, r))
    psi = Psi(x=("a",), relations=())
    obligation = closure(f, lambda p: "a" in p.x, [psi])
    admission = MetaAdmission(transition, obligation, root)
    assert not admission.admissible()
    with pytest.raises(ValueError, match="not admitted"):
        admission.apply()


def test_meta_admission_cannot_bypass_closure_obligation():
    root = canonical_root_invariant()
    before = {"sealed": True, "v": 1}
    after = {"sealed": True, "v": 999}
    transition = MetaTransition(
        before, after,
        RefinementProof(root, before, after, "forged", refinement=lambda _a, _b: True),
    )
    f = make_psi_transition(lambda x, r: (x, r))
    psi = Psi(x=("a",), relations=())
    obligation = closure(f, lambda _p: False, [psi])
    admission = MetaAdmission(transition, obligation, root)
    assert not admission.admissible()


def test_meta_admission_cannot_replace_canonical_k0():
    canonical = canonical_root_invariant()
    forged = RootInvariant(lambda _kernel: True, name="K0")
    before = {"sealed": True, "v": 1}
    after = {"sealed": False, "v": 2}
    proof = RefinementProof(forged, before, after, "forged", refinement=lambda _a, _b: True)
    transition = MetaTransition(before, after, proof)
    f = make_psi_transition(lambda x, r: (x, r))
    psi = Psi(x=("a",), relations=())
    obligation = closure(f, lambda p: "a" in p.x, [psi])
    admission = MetaAdmission(transition, obligation, forged)
    assert not admission.admissible()
    with pytest.raises(ValueError, match="not admitted"):
        admission.apply()
    assert canonical.holds(before)
