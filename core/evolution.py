from __future__ import annotations

import warnings
from typing import Callable, Iterable

from .proof import prove_transition
from .admission import admit
from .psi_transition import PsiTransition
from .state import Psi, State

Generator = Callable[[State], Iterable[State]]
Tester = Callable[[State], bool]


def _test_candidate(test: Tester, candidate: State) -> bool:
    result = test(candidate)
    if type(result) is not bool:
        raise TypeError("Test(candidate) must return bool exactly.")
    return result


def _generic_score(state: State) -> tuple[str]:
    return (repr(state),)


def _psi_score(state: State) -> tuple[int, str]:
    psi = state.to_psi()
    return (len(psi.relations), repr(psi))


def select_next_state(state: State, generate: Generator, test: Tester) -> State:
    """Legacy compatibility selector; not a canonical execution authority."""
    warnings.warn(
        "select_next_state() is legacy compatibility API; use Uroboros.evolutionary().step().",
        DeprecationWarning,
        stacklevel=2,
    )
    candidates = list(generate(state))
    if not candidates:
        raise ValueError("Generator must produce at least one candidate state")
    valid = [candidate for candidate in candidates if _test_candidate(test, candidate)]
    if not valid:
        raise ValueError("No valid candidate state passed the test")
    return min(valid, key=_generic_score)


def evolutionary_transition(generate: Generator, test: Tester) -> Callable[[State], State]:
    """Legacy State transition compatibility API; never a canonical authority."""
    warnings.warn(
        "evolutionary_transition() is legacy compatibility API; use Uroboros.evolutionary().step().",
        DeprecationWarning,
        stacklevel=2,
    )
    return lambda state: select_next_state(state, generate, test)


def evolutionary_psi_transition(generate: Generator, test: Tester) -> PsiTransition:
    """Pure compatibility F: Psi -> Psi transition; never performs SemanticCommit.

    Canonical persistence/execution belongs to CanonicalExecutor.
    """
    def transition(x: object, relations: object) -> tuple[object, object]:
        current = State.from_psi(Psi(x, relations))
        candidates = list(generate(current))
        if not candidates:
            raise ValueError("Generator must produce at least one candidate state")
        proofs = [
            prove_transition(current, candidate, candidates, test)
            for candidate in candidates
        ]
        admissions = [
            admit(candidate, proof)
            for candidate, proof in zip(candidates, proofs)
        ]
        valid = [a for a in admissions if a.accepted]
        if not valid:
            raise ValueError("No candidate state passed ProofObligation")
        selected = min(valid, key=lambda a: _psi_score(a.candidate))
        next_psi = selected.candidate.to_psi()
        return next_psi.x, next_psi.relations

    return PsiTransition(function=transition)
