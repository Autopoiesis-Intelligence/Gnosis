"""Ψ semantic commit facade composed with the universal canonical gate."""

from __future__ import annotations

from dataclasses import dataclass

from .admission import Admission
from .canonical_chain import commit_admitted_psi
from .history import AppendOnlyHistory
from .safety import SafetyGate
from .state import Psi


@dataclass(frozen=True)
class SemanticCommit:
    previous: Psi
    admission: Admission
    kernel_version: str
    operation_count: int = 1
    gas_costs: tuple[int, ...] = (1,)
    safety_gate: SafetyGate | None = None
    gas_limit: int = 20

    def apply(self, history: AppendOnlyHistory) -> tuple[Psi, AppendOnlyHistory]:
        result = commit_admitted_psi(
            history,
            self.previous,
            self.admission,
            kernel_version=self.kernel_version,
            operation_count=self.operation_count,
            gas_costs=self.gas_costs,
            gate=self.safety_gate,
            gas_limit=self.gas_limit,
        )
        return result.value, result.history


def commit(
    previous: Psi,
    admission: Admission,
    kernel_version: str,
    *,
    operation_count: int = 1,
    gas_costs: tuple[int, ...] = (1,),
    safety_gate: SafetyGate | None = None,
    gas_limit: int = 20,
) -> SemanticCommit:
    if not isinstance(previous, Psi):
        raise TypeError("previous must be Psi.")
    if not kernel_version.strip():
        raise ValueError("kernel_version is required.")
    return SemanticCommit(
        previous=previous,
        admission=admission,
        kernel_version=kernel_version,
        operation_count=operation_count,
        gas_costs=gas_costs,
        safety_gate=safety_gate,
        gas_limit=gas_limit,
    )
