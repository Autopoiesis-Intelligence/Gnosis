from __future__ import annotations

import pytest

from core.engine import Engine
from core.legacy_engine import LegacyEngine
from core.state import State


def test_legacy_state_transition_remains_explicit_compatibility_path() -> None:
    def legacy_transition(state: State) -> State:
        return state.evolve(values={"x": state.values.get("x", 0) + 1})

    result = LegacyEngine(transition=legacy_transition).step(State(values={"x": 0}))
    assert result.values["x"] == 1
    assert isinstance(result, State)


def test_canonical_engine_rejects_legacy_transition_at_execution_boundary() -> None:
    def legacy_transition(state: State) -> State:
        return state.evolve(values={"x": state.values.get("x", 0) + 1})

    with pytest.raises(AttributeError):
        Engine(transition=legacy_transition).step(State(values={"x": 0}))


def test_legacy_transition_cannot_return_non_state() -> None:
    def invalid_transition(_state: State):
        return {"x": 1}

    with pytest.raises(TypeError, match="Legacy transition must return State"):
        LegacyEngine(transition=invalid_transition).step(State(values={"x": 0}))
