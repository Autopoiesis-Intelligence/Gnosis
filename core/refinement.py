"""Executable forward-simulation refinement for Psi transitions.

The relation is intentionally supplied by the caller: Gnosis does not assume
that every operator change has one universal notion of behavioral equivalence.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .psi_transition import PsiTransition
from .state import Psi

PsiRelation = Callable[[Psi, Psi], bool]


@dataclass(frozen=True)
class TransitionRefinement:
    """Witnessed forward-simulation obligation F_old ⊑ F_new."""

    old: PsiTransition
    new: PsiTransition
    relation: PsiRelation
    witnesses: tuple[Psi, ...]

    def holds(self) -> bool:
        for psi in self.witnesses:
            old_next = self.old(psi)
            new_next = self.new(psi)
            if not self.relation(old_next, new_next):
                return False
        return True


def refine(
    old: PsiTransition,
    new: PsiTransition,
    relation: PsiRelation,
    witnesses: Iterable[Psi],
) -> TransitionRefinement:
    return TransitionRefinement(old, new, relation, tuple(witnesses))
