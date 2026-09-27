from core.legacy_engine import LegacyEngine
from core.evolution import evolutionary_transition
from core.state import State


def test_local_rule_evolution_is_independent_of_disconnected_component():
    state_a = State(values={
        "nodes": {"a": 1, "b": 2, "z": 10},
        "relations": (("a", "b"),),
        "rules": {"a": "add_neighbor"},
    })
    state_b = State(values={
        "nodes": {"a": 1, "b": 2, "z": 9999},
        "relations": (("a", "b"),),
        "rules": {"a": "add_neighbor"},
    })

    def generator(state):
        nodes = dict(state.values["nodes"])
        rules = dict(state.values["rules"])
        nodes["a"] += nodes["b"]
        rules["a"] = "add_neighbor"
        return (state.evolve(values={**state.values, "nodes": nodes, "rules": rules}),)

    def tester(state):
        return all("->" in r or isinstance(r, tuple) for r in state.values["relations"])

    transition = evolutionary_transition(generator, tester)
    result_a = LegacyEngine(transition).step(state_a)
    result_b = LegacyEngine(transition).step(state_b)

    assert result_a.values["nodes"]["a"] == result_b.values["nodes"]["a"] == 3
    assert result_a.values["rules"]["a"] == result_b.values["rules"]["a"] == "add_neighbor"


def test_local_rule_candidate_is_selected_from_local_neighborhood():
    initial = State(values={
        "nodes": {"a": 1, "b": 2, "z": 100},
        "relations": (("a", "b"),),
        "rules": {"a": "add_neighbor"},
    })
    valid = initial.evolve(values={
        "nodes": {"a": 3, "b": 2, "z": 100},
        "relations": (("a", "b"),),
        "rules": {"a": "add_neighbor"},
    })
    bad_remote = initial.evolve(values={
        "nodes": {"a": 999, "b": 2, "z": 100},
        "relations": (("a", "b"),),
        "rules": {"a": "remote_z_dependent"},
    })

    def generator(state):
        return (bad_remote, valid)

    def tester(state):
        return state.values["rules"]["a"] == "add_neighbor" and state.values["nodes"]["a"] == 3

    result = LegacyEngine(evolutionary_transition(generator, tester)).step(initial)
    assert result.values["rules"]["a"] == "add_neighbor"
    assert result.values["nodes"]["a"] == 3
