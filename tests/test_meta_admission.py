import pytest
from core.dynamics import closure
from core.meta_admission import MetaAdmission
from core.meta_transition import MetaTransition, RefinementProof
from core.psi_transition import make_psi_transition
from core.root_invariant import RootInvariant
from core.state import Psi


def test_unified_meta_admission_requires_k0_refinement_and_closure():
    root = RootInvariant(lambda k: k["sealed"])
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
    root = RootInvariant(lambda k: k["sealed"])
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
    root = RootInvariant(lambda k: k["sealed"])
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
