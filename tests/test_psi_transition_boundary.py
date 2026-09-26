from core.psi_transition import make_psi_transition
from core.state import State
from core.root_invariant import canonical_root_invariant, preserve_root


def test_transition_cannot_observe_auxiliary_state_metadata():
    transition = make_psi_transition(
        lambda x, relations: (x + len(relations), relations)
    )

    a = State(values={"x": 3, "relations": (("a", "b"),), "hidden": 0})
    b = State(values={"x": 3, "relations": (("a", "b"),), "hidden": 10**9})

    assert transition.on_state(a).values == transition.on_state(b).values
    assert transition.on_state(a).values == {"x": 4, "relations": (("a", "b"),)}


def test_transition_boundary_preserves_only_fundamental_projection():
    transition = make_psi_transition(lambda x, relations: (x, relations))
    state = State(values={"x": 7, "relations": (("a", "b"),), "memory": "aux"})

    result = transition.on_state(state)
    assert result.values == {"x": 7, "relations": (("a", "b"),)}


def test_transition_is_defined_only_on_canonical_psi_projection():
    transition = make_psi_transition(lambda x, relations: (x + 1, relations))
    state = State(values={"x": 7, "relations": (("a", "b"),), "hidden": "must-not-enter"})
    projected = state.to_psi()
    result = transition(projected)
    assert result.x == 8
    assert result.relations == projected.relations


def test_psi_transition_cannot_change_k0_authority():
    transition = make_psi_transition(
        lambda x, relations: (x + 1, relations + (("new", "relation"),))
    )
    state = State(values={"x": 7, "relations": (("a", "b"),), "hidden": "aux"})
    before_kernel = {"sealed": True, "version": 1}
    after_kernel = {"sealed": True, "version": 2}

    result = transition.on_state(state)

    assert result.values["x"] == 8
    assert len(result.values["relations"]) == 2
    assert canonical_root_invariant().holds(before_kernel)
    assert canonical_root_invariant().holds(after_kernel)
    assert preserve_root(canonical_root_invariant(), before_kernel, after_kernel)


def test_psi_transition_cannot_self_authorize_kernel_change():
    transition = make_psi_transition(lambda x, relations: (x, relations))
    state = State(values={"x": 1, "relations": ()})
    forged_after_kernel = {"sealed": False, "version": 99}

    result = transition.on_state(state)

    assert result.values == state.values
    assert not canonical_root_invariant().holds(forged_after_kernel)
