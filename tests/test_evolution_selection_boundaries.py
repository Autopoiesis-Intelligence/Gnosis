import pytest

from core import State
from core.evolution import evolutionary_psi_transition, select_next_state


def test_generic_selection_does_not_require_psi_fields():
    initial = State(values={"score": 0})

    def generate(_state):
        return [State(values={"score": 2}), State(values={"score": 1})]

    def test(_state):
        return True

    result = select_next_state(initial, generate, test)
    assert result.values["score"] == 1


def test_canonical_psi_selection_requires_x_and_relations():
    def generate(_state):
        return [
            State(values={"x": 1, "relations": ("r",)}),
            State(values={"x": 2, "relations": ("r",)}),
        ]

    def test(_state):
        return True

    transition = evolutionary_psi_transition(generate, test)
    result = transition(State(values={"x": 0, "relations": ()}).to_psi())

    assert result.x == 1
    assert result.relations == ("r",)


def test_evolution_candidate_cannot_commit_without_admission():
    initial = State(values={"x": 0, "relations": ()})
    forbidden = State(values={"x": 999, "relations": ("forbidden",)})

    def generate(_state):
        return [forbidden]

    def reject(_state):
        return False

    transition = evolutionary_psi_transition(generate, reject)
    with pytest.raises(ValueError, match="ProofObligation"):
        transition(initial.to_psi())

    assert initial.values == {"x": 0, "relations": ()}


def test_evolution_selector_cannot_use_external_candidate_authority():
    initial = State(values={"x": 0, "relations": ()})
    candidate = State(values={"x": 1, "relations": ("accepted",)})

    def generate(_state):
        return [candidate]

    def accept(_state):
        return True

    def generate_with_continuation(_state):
        return [candidate, State(values={"x": 2, "relations": ("accepted",)})]

    transition = evolutionary_psi_transition(generate_with_continuation, accept)
    result = transition(initial.to_psi())

    assert result.x == 1
    assert result.relations == ("accepted",)
