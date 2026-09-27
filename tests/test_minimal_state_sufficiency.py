from core.legacy_engine import LegacyEngine
from core.engine import Engine
from core.evolution import evolutionary_transition
from core.state import State


def _transition():
    def generator(state):
        # E is intentionally defined only from the exposed (X, R) projection.
        x = state.values["x"]
        relations = state.values["relations"]
        return (state.evolve(values={"x": x + len(relations), "relations": relations}),)

    def tester(state):
        return True

    return evolutionary_transition(generator, tester)


def test_same_x_and_r_have_same_transition_even_with_extra_metadata():
    base = State(values={"x": 3, "relations": (("a", "b"),)})
    enriched = State(values={
        "x": 3,
        "relations": (("a", "b"),),
        "hidden_metadata": "different",
    })

    transition = _transition()
    result_base = Engine(transition).step(base)
    result_enriched = Engine(transition).step(enriched)

    assert result_base.values["x"] == result_enriched.values["x"] == 4
    assert result_base.values["relations"] == result_enriched.values["relations"]


def test_adversarial_hidden_variable_cannot_change_transition_when_not_in_x_or_r():
    state_a = State(values={
        "x": 5,
        "relations": (("a", "b"),),
        "hidden": 0,
    })
    state_b = State(values={
        "x": 5,
        "relations": (("a", "b"),),
        "hidden": 10**9,
    })

    transition = _transition()
    result_a = Engine(transition).step(state_a)
    result_b = Engine(transition).step(state_b)

    assert result_a.values["x"] == result_b.values["x"] == 6


def test_relevant_relation_change_changes_transition():
    state_a = State(values={"x": 5, "relations": (("a", "b"),)})
    state_b = State(values={
        "x": 5,
        "relations": (("a", "b"), ("b", "c")),
    })

    transition = _transition()
    result_a = Engine(transition).step(state_a)
    result_b = Engine(transition).step(state_b)

    assert result_a.values["x"] == 6
    assert result_b.values["x"] == 7
