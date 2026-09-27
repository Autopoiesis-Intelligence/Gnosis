from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterable

from .engine import Engine
from .execution import CanonicalExecutor, Generator, Tester
from .execution_contract import execution_input_from_psi
from .relation import Relation
from .state import Psi, State
from .history import AppendOnlyHistory
from .psi_transition import PsiTransition
from .canonical_boundary import canonicalize_psi
from .legacy_engine import LegacyEngine
from .evolution import evolutionary_transition


def _unconfigured_transition(x, relations):
    raise RuntimeError("Uroboros has no transition configured; provide an Engine or use Uroboros.evolutionary().")


def _transition_content_digest(transition: PsiTransition) -> str:
    return hashlib.sha256(repr(transition.configuration).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Uroboros:
    state: State = field(default_factory=State)
    engine: Engine = field(default_factory=lambda: Engine(transition=PsiTransition(_unconfigured_transition)))
    executor: CanonicalExecutor | None = None
    generate: Generator | None = None
    test: Tester | None = None
    psi_transition: PsiTransition | None = None

    @classmethod
    def canonical(cls, *, transition: PsiTransition, state: State, kernel_version: str = "gnozis-core", history: AppendOnlyHistory | None = None) -> "Uroboros":
        if not isinstance(state, State): raise TypeError("canonical Uroboros requires a State adapter input.")
        initial = canonicalize_psi(state.to_psi()).psi
        return cls(state=State.from_psi(initial), engine=Engine(transition=transition), executor=CanonicalExecutor(history=history or AppendOnlyHistory(), kernel_version=kernel_version), psi_transition=transition)

    @classmethod
    def evolutionary(cls, *, generate: Generator, test: Tester, state: State | None = None, kernel_version: str = "gnozis-core", history: AppendOnlyHistory | None = None) -> "Uroboros":
        initial = state if state is not None else State(values={"x": (), "relations": ()})
        if not isinstance(initial, State): raise TypeError("evolutionary Uroboros requires a State adapter input.")
        initial.to_psi()
        return cls(state=initial, engine=LegacyEngine(transition=evolutionary_transition(generate, test)), executor=None, generate=generate, test=test)

    def step(self) -> "Uroboros":
        if self.psi_transition is not None and self.executor is not None:
            canonical_input = canonicalize_psi(self.state.to_psi())
            execution_input = execution_input_from_psi(canonical_input.psi, input_type="psi_transition", content_digest=_transition_content_digest(self.psi_transition))
            result = self.executor.step(canonical_input.psi, self.psi_transition, execution_input, test=self.test)
            return Uroboros(state=State.from_psi(result.psi), engine=self.engine, executor=self.executor, generate=self.generate, test=self.test, psi_transition=self.psi_transition)
        if self.executor is not None:
            if self.generate is None or self.test is None: raise RuntimeError("Canonical executor requires generate and test.")
            result = self.executor.evolve(canonicalize_psi(self.state.to_psi()).psi, self.generate, self.test)
            return Uroboros(state=State.from_psi(result.psi), engine=self.engine, executor=self.executor, generate=self.generate, test=self.test)
        try:
            next_state = self.engine.step(self.state)
        except ValueError as exc:
            if str(exc) != "No valid candidate state passed the test": raise
            next_state = self.state
        return Uroboros(state=next_state, engine=self.engine, executor=self.executor, generate=self.generate, test=self.test, psi_transition=self.psi_transition)

    def with_relations(self, relations: Iterable[Relation]) -> "Uroboros":
        new_relations = tuple(relations)
        if any(not isinstance(relation, Relation) for relation in new_relations): raise TypeError("relations must contain Relation instances.")
        values = dict(self.state.values); values["relations"] = new_relations
        return Uroboros(state=State(values=values), engine=self.engine, executor=self.executor, generate=self.generate, test=self.test, psi_transition=self.psi_transition)
