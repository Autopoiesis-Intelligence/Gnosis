"""Proof-carrying meta-transitions for protected self-evolution."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar
from .root_invariant import RootInvariant, preserve_root
T = TypeVar("T")
@dataclass(frozen=True)
class RefinementProof(Generic[T]):
    """Executable evidence that a proposed meta-transition refines its predecessor."""
    root: RootInvariant[T]
    before: T
    after: T
    statement: str
    refinement: Callable[[T, T], bool] | None = None
    @property
    def valid(self) -> bool:
        if not self.statement.strip():
            return False
        if not preserve_root(self.root, self.before, self.after):
            return False
        return self.refinement is None or bool(self.refinement(self.before, self.after))
@dataclass(frozen=True)
class MetaTransition(Generic[T]):
    """A proposed kernel/meta-state change carrying a refinement proof."""
    before: T
    after: T
    proof: RefinementProof[T]
    def admissible(self) -> bool:
        return (self.proof.before == self.before and self.proof.after == self.after and self.proof.valid)
    def apply(self) -> T:
        if not self.admissible():
            raise ValueError("meta-transition is not admitted by its refinement proof")
        return self.after
