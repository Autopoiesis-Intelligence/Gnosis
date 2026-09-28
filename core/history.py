"""Append-only causal history contracts."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionRecord:
    sequence: int
    previous_hash: str
    state_hash: str
    kernel_version: str
    candidate_hash: str
    admitted: bool
    evidence_hash: str = ""
    kernel_execution_identity: str = ""
    evidence_binding_digest: str = ""
    evolution_evaluation_digest: str = ""

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self.kernel_version.strip():
            raise ValueError("kernel_version is required")
        if not self.admitted:
            raise ValueError("history may contain only accepted transitions")


@dataclass(frozen=True)
class AppendOnlyHistory:
    records: tuple[TransitionRecord, ...] = ()

    def append(self, record: TransitionRecord) -> "AppendOnlyHistory":
        if self.records:
            previous = self.records[-1]
            if record.sequence != previous.sequence + 1:
                raise ValueError("history sequence must be contiguous")
            if record.previous_hash != previous.state_hash:
                raise ValueError("history chain is broken")
        elif record.sequence != 0:
            raise ValueError("genesis record must have sequence zero")
        return AppendOnlyHistory(self.records + (record,))

    @property
    def head(self) -> TransitionRecord | None:
        return self.records[-1] if self.records else None


@dataclass(frozen=True)
class EvolutionOutcomeRecord:
    sequence: int
    previous_outcome_digest: str
    outcome_digest: str
    patch_id: str
    parent_state_hash: str
    candidate_state_hash: str
    decision: str
    evidence_digest: str

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not all((self.patch_id, self.parent_state_hash,
                    self.candidate_state_hash, self.decision,
                    self.evidence_digest, self.outcome_digest)):
            raise ValueError("evolution outcome history identity is required")
        if self.decision == "observe":
            raise ValueError("history may contain only terminal evolution outcomes")


@dataclass(frozen=True)
class EvolutionOutcomeHistory:
    records: tuple[EvolutionOutcomeRecord, ...] = ()

    def append(self, record: EvolutionOutcomeRecord) -> "EvolutionOutcomeHistory":
        if self.records:
            previous = self.records[-1]
            if record.sequence != previous.sequence + 1:
                raise ValueError("evolution outcome sequence must be contiguous")
            if record.previous_outcome_digest != previous.outcome_digest:
                raise ValueError("evolution outcome chain is broken")
        elif record.sequence != 0:
            raise ValueError("evolution outcome genesis must have sequence zero")
        return EvolutionOutcomeHistory(self.records + (record,))

    @property
    def head(self) -> EvolutionOutcomeRecord | None:
        return self.records[-1] if self.records else None
