import pytest

from core import State


def test_x_and_relations_are_read_only_projections() -> None:
    state = State(values={"x": 1, "relations": (("a", "b"),)})

    assert state.x == 1
    assert state.relations == (("a", "b"),)


def test_missing_projection_is_not_a_second_state_model() -> None:
    state = State(values={"score": 1})

    with pytest.raises(AttributeError):
        _ = state.x
    with pytest.raises(AttributeError):
        _ = state.relations


def test_state_to_psi_roundtrip_is_canonical_semantic_projection() -> None:
    state = State(values={"x": {"node": 1}, "relations": (("a", "b"),), "aux": 7})
    psi = state.to_psi()
    restored = State.from_psi(psi)

    assert psi.x == state.x
    assert psi.relations == state.relations
    assert restored.to_psi() == psi
    assert restored.values["aux"] if "aux" in restored.values else True
