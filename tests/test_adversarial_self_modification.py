from core.legacy_engine import LegacyEngine
from core.evolution import evolutionary_transition
from core.state import State


def test_invalid_rule_candidate_is_rejected_before_next_generation():
    initial = State(values={"x": 0, "relations": ("a->b",), "rule": "stable"})
    invalid = initial.evolve(values={"x": 99, "relations": ("a->b", "b->c"), "rule": "corrupt"})
    valid = initial.evolve(values={"x": 1, "relations": ("a->b", "b->c"), "rule": "extend"})

    def generator(state):
        return (invalid, valid)

    def tester(state):
        return state.values["rule"] in {"stable", "extend"}

    result = LegacyEngine(evolutionary_transition(generator, tester)).step(initial)

    assert result.values["rule"] == "extend"
    assert result.values["x"] == 1


def test_no_valid_rule_cannot_enter_recursive_cycle():
    initial = State(values={"x": 0, "relations": (), "rule": "stable"})
    invalid = initial.evolve(values={"x": 99, "relations": ("broken",), "rule": "corrupt"})

    def generator(state):
        return (invalid,)

    def tester(state):
        return state.values["rule"] in {"stable", "extend"}

    transition = evolutionary_transition(generator, tester)

    try:
        LegacyEngine(transition).step(initial)
    except (ValueError, RuntimeError):
        return

    raise AssertionError("invalid self-modifying rule escaped Test/Select")
