"""Protected root-kernel invariant for meta-evolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RootInvariant(Generic[T]):
    """Executable predicate defining the protected kernel boundary."""

    predicate: Callable[[T], bool]
    name: str = "K0"

    def holds(self, kernel: T) -> bool:
        return bool(self.predicate(kernel))

    def require(self, kernel: T) -> None:
        if not self.holds(kernel):
            raise ValueError(f"root invariant {self.name} violated")


def preserve_root(root: RootInvariant[T], before: T, after: T) -> bool:
    """K0 preservation requires the invariant to hold before and after."""
    return root.holds(before) and root.holds(after)


def canonical_root_invariant() -> RootInvariant[dict]:
    """Return the canonical K0 contract; callers cannot supply a replacement."""
    return RootInvariant(lambda kernel: kernel.get("sealed") is True, name="K0")
