"""Durable serialization contract for distribution/execution evidence."""

from __future__ import annotations

from dataclasses import dataclass

from core.distribution_execution_binding import DistributionExecutionBinding


@dataclass(frozen=True)
class DurableDistributionBinding:
    sequence: int
    binding: DistributionExecutionBinding

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")

    def row(self) -> tuple[int, str, str, str, str]:
        return (
            self.sequence,
            self.binding.decision_id,
            self.binding.decision_digest,
            self.binding.kernel_id,
            self.binding.execution_identity,
        )

    @classmethod
    def from_row(cls, row: tuple[int, str, str, str, str]) -> "DurableDistributionBinding":
        sequence, decision_id, decision_digest, kernel_id, execution_identity = row
        return cls(
            sequence=sequence,
            binding=DistributionExecutionBinding(
                decision_id=decision_id,
                decision_digest=decision_digest,
                kernel_id=kernel_id,
                execution_identity=execution_identity,
            ),
        )
