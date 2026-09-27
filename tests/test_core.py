from core import Engine, Relation, State, Uroboros
from core.psi_transition import make_psi_transition


def increment_psi(x, relations):
    value = x.get("value", 0)
    return {"value": value + 1}, relations


def test_state_creation():
    state = State(values={"value": 1})
    assert state.values["value"] == 1


def test_relation_creation():
    relation = Relation(source="a", target="b")
    assert relation.source == "a"
    assert relation.target == "b"


def test_engine_creation():
    engine = Engine(transition=make_psi_transition(increment_psi))
    assert engine is not None


def test_engine_step():
    state = State(values={"value": 1})
    engine = Engine(transition=make_psi_transition(increment_psi))
    next_state = engine.step(state)
    assert next_state.values["value"] == 2


def test_engine_run():
    state = State(values={"value": 1})
    engine = Engine(transition=make_psi_transition(increment_psi))
    result = engine.run(state, steps=3)
    assert result.values["value"] == 4


def test_engine_trajectory():
    state = State(values={"value": 1})
    engine = Engine(transition=make_psi_transition(increment_psi))
    trajectory = list(engine.trajectory(state, steps=3))
    assert len(trajectory) == 4
    assert [s.values["value"] for s in trajectory] == [1, 2, 3, 4]


def test_uroboros_initialization():
    uroboros = Uroboros()
    assert uroboros.state is not None
    assert uroboros.engine is not None


def test_uroboros_step():
    uroboros = Uroboros(
        state=State(values={"value": 1}),
        engine=Engine(transition=make_psi_transition(increment_psi)),
    )
    next_uroboros = uroboros.step()
    assert next_uroboros.state.values["value"] == 2
