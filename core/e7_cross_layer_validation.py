"""Cross-layer structural validation for the bounded E7 proof chain."""
from __future__ import annotations

from dataclasses import dataclass

from .e7_109_acceptance import AcceptanceDecision
from .e7_110_reconciliation import ReconciliationSnapshot
from .e7_proof_manifest import E7ProofRunManifest, ProofTerminalState


@dataclass(frozen=True)
class RuntimeEvidenceLink:
    execution_id: str
    execution_input_identity: str
    evidence_digest: str
    terminal_status: str


def validate_e7_chain(
    manifest: E7ProofRunManifest,
    acceptance: AcceptanceDecision,
    reconciliation: ReconciliationSnapshot,
    runtime: RuntimeEvidenceLink,
) -> None:
    if manifest.execution_id != runtime.execution_id:
        raise ValueError("manifest/runtime execution mismatch")
    if manifest.execution_input_identity != runtime.execution_input_identity:
        raise ValueError("manifest/runtime input identity mismatch")
    if manifest.runtime_evidence_digest != runtime.evidence_digest:
        raise ValueError("manifest/runtime evidence mismatch")
    if manifest.acceptance_decision_id != acceptance.decision_id:
        raise ValueError("manifest/acceptance mismatch")
    if acceptance.execution_id != manifest.execution_id:
        raise ValueError("acceptance execution mismatch")
    if manifest.reconciliation_id != reconciliation.reconciliation_id:
        raise ValueError("manifest/reconciliation mismatch")
    if reconciliation.status.value not in {"RECONCILED", "DISCREPANCY"}:
        raise ValueError("reconciliation is not terminal")
    expected_terminal = ProofTerminalState.COMMITTED.value
    if manifest.terminal_status.value == expected_terminal and runtime.terminal_status != expected_terminal:
        raise ValueError("runtime is not committed while manifest is committed")
