import pytest

from core.engine import Engine
from core.psi_transition import make_psi_transition
from core.state import State


def test_canonical_engine_requires_psi_transition() -> None:
    with pytest.raises(AttributeError):
        Engine(transition=lambda state: state).step(State(values={"x": 0, "relations": ()}))


def test_canonical_engine_executes_psi_transition() -> None:
    transition = make_psi_transition(
        lambda x, relations: (x + 1, relations)
    )
    result = Engine(transition=transition).step(State(values={"x": 0, "relations": ()}))
    assert result.values["x"] == 1
