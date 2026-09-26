"""Unified admissibility contract for self-evolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .meta_transition import MetaTransition, RefinementProof
from .root_invariant import RootInvariant, canonical_root_invariant
from .state import Psi
from .dynamics import ClosureObligation

T = TypeVar("T")


@dataclass(frozen=True)
class MetaAdmission(Generic[T]):
    transition: MetaTransition[T]
    closure: ClosureObligation
    root: RootInvariant[T]

    def admissible(self) -> bool:
        return (
            self.transition.admissible()
            and self.root is canonical_root_invariant()
            and self.root.holds(self.transition.before)
            and self.root.holds(self.transition.after)
            and self.closure.holds()
        )

    def apply(self) -> T:
        if not self.admissible():
            raise ValueError("meta-transition is not admitted by the unified contract")
        return self.transition.after
