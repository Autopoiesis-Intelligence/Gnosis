from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .psi_transition import PsiTransition
from .state import State


def _validate_steps(steps: int) -> None:
    """Require a real integer step count; bool is intentionally rejected."""
    if type(steps) is not int:
        raise TypeError("steps must be an int, not bool or another numeric type.")
    if steps < 0:
        raise ValueError("steps must be non-negative.")


@dataclass
class Engine:
    """Canonical Ψ transition engine.

    Legacy State-callable transitions are intentionally excluded from this API.
    Use core.legacy_engine.LegacyEngine only for explicit compatibility use.
    """

    transition: PsiTransition

    def step(self, state: State) -> State:
        next_state = self.transition.on_state(state)
        if not isinstance(next_state, State):
            raise TypeError("PsiTransition must return a State instance.")
        return next_state

    def run(self, state: State, steps: int) -> State:
        _validate_steps(steps)
        current = state
        for _ in range(steps):
            current = self.step(current)
        return current

    def trajectory(self, state: State, steps: int) -> Iterable[State]:
        _validate_steps(steps)
        current = state
        yield current
        for _ in range(steps):
            current = self.step(current)
            yield current
