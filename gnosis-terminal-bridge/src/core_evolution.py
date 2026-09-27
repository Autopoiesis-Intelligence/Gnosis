from __future__ import annotations

from typing import Callable

from core import State
from core.legacy_engine import LegacyEngine

from .agency_context import AgencyContext

ContextualTransition = Callable[[State, AgencyContext], State]


def engine_from_agency_context(context: AgencyContext, transition: ContextualTransition) -> LegacyEngine:
    """Explicit compatibility bridge; never constructs canonical Engine authority."""
    if not context.identity.authenticated:
        raise ValueError("Agency identity is not authenticated")

    def bound_transition(state: State) -> State:
        return transition(state, context)

    return LegacyEngine(transition=bound_transition)
