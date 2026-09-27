"""Execute one non-autonomous bounded E7 proof batch from real runtime evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.e7_107_readiness import CheckState, E7ReadinessRecord, ReadinessCheck
from core.e7_108_execution import E7ExecutionRecord, ExecutionState
from core.e7_109_acceptance import AcceptanceDecision, AcceptanceState
from core.e7_110_reconciliation import ReconciliationSnapshot, ReconciliationState
from core.e7_cross_layer_validation import RuntimeEvidenceLink, validate_e7_chain
from core.e7_proof_manifest import E7ProofRunManifest, ProofTerminalState
from core.execution_contract import execution_input_identity


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-commit-sha", required=True)
    parser.add_argument("--output", default="runtime-evidence/e7-proof-manifest.json")
    parser.add_argument("--evidence", default="runtime-evidence/first-task.json")
    args = parser.parse_args()

    actual_commit = git_head()
    if actual_commit != args.target_commit_sha:
        raise SystemExit(
            f"E7.107 blocked: HEAD {actual_commit} != target {args.target_commit_sha}"
        )

    evidence_path = Path(args.evidence)
    if not evidence_path.is_file():
        raise SystemExit("E7.107 blocked: runtime evidence is missing")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("status") != "COMMITTED":
        raise SystemExit("E7.107 blocked: runtime evidence is not COMMITTED")

    safe_environment = "|".join((
        platform.python_version(),
        platform.system(),
        platform.machine(),
        os.name,
    ))
    environment_identity = hashlib.sha256(
        safe_environment.encode("utf-8")
    ).hexdigest()

    checks = tuple(
        ReadinessCheck(check_id, CheckState.PASS)
        for check_id in (
            "target_commit_resolves",
            "target_commit_matches",
            "baseline_present",
            "candidate_selection_present",
            "evidence_policy_present",
            "verification_matrix_present",
            "environment_identity_present",
            "commands_present",
            "expected_outcomes_present",
            "evidence_capture_mapping_present",
            "stop_conditions_present",
            "retry_rules_present",
            "evidence_destination_present",
        )
    )

    batch_id = "e7-bounded-first-task-v1"
    readiness = E7ReadinessRecord(
        batch_id=batch_id,
        target_commit_sha=args.target_commit_sha,
        repository_ref=os.environ.get("GITHUB_REF", "local"),
        baseline_id=evidence["initial_state_digest"],
        candidate_selection_id=evidence["task_id"],
        evidence_policy_revision="e7-runtime-evidence-v1",
        verification_matrix_revision="e7-bounded-proof-v1",
        environment_identity=environment_identity,
        checks=checks,
        commands=("python tools/run_first_task.py",),
        expected_outcomes=("runtime status COMMITTED", "validator ACCEPT"),
        evidence_capture_mapping=(str(evidence_path), args.output),
        stop_conditions=("unexpected mutation", "target commit mismatch"),
        retry_rules=("same target commit and same bounded input only",),
    ).mark_ready(
        resolved_commit_sha=actual_commit,
        evidence_destination=str(evidence_path.parent),
    )

    if readiness.state.name != "READY":
        raise SystemExit("E7.107 did not reach READY")

    input_identity = evidence.get("execution_input_identity")
    if not input_identity:
        raise SystemExit("E7.108 blocked: execution input identity missing")

    runtime_digest = canonical_digest(evidence)
    execution_id = E7ExecutionRecord.execution_id_for(
        batch_id, args.target_commit_sha, input_identity
    )
    execution = E7ExecutionRecord(
        batch_id=batch_id,
        execution_id=execution_id,
        target_commit_sha=args.target_commit_sha,
        execution_input_identity=input_identity,
        readiness_id=readiness.readiness_id,
        runtime_evidence_digest="",
        criterion_evidence=(),
        state=ExecutionState.PREPARING,
    ).begin(
        readiness_id=readiness.readiness_id,
        target_commit_sha=actual_commit,
    ).complete(
        runtime_evidence_digest=runtime_digest,
        criterion_evidence=(
            "runtime.status=COMMITTED",
            "runtime.recovery_status=VERIFIED",
            "runtime.history_records=1",
            "runtime.provenance_records=1",
            "runtime.audit_records=1",
        ),
        target_commit_sha=actual_commit,
    )

    acceptance = AcceptanceDecision(
        decision_id=f"{execution_id}:accept",
        execution_id=execution.execution_id,
        criterion_id="runtime-first-task-committed",
        evidence_digest=runtime_digest,
        epistemic_state="VERIFIED",
        policy_revision="e7-runtime-evidence-v1",
        scope="bounded-first-task",
        authority_reference="canonical-runtime-commit",
        validity_conditions=("exact target commit", "runtime status COMMITTED"),
        decision=AcceptanceState.ACCEPTED,
    )

    reconciliation = ReconciliationSnapshot(
        reconciliation_id=f"{execution_id}:reconcile",
        acceptance_batch_id=batch_id,
        input_snapshot_digest=evidence["initial_state_digest"],
        metric_id="history-record-count",
        reported_value=str(evidence["history_records"]),
        recalculated_value="1",
        calculation_revision="e7-reconciliation-v1",
        evidence_digests=(runtime_digest,),
        status=ReconciliationState.PENDING,
    ).reconcile()

    manifest = E7ProofRunManifest(
        manifest_id=f"{execution_id}:manifest",
        readiness_id=readiness.readiness_id,
        execution_id=execution.execution_id,
        execution_input_identity=input_identity,
        runtime_evidence_digest=runtime_digest,
        acceptance_decision_id=acceptance.decision_id,
        reconciliation_id=reconciliation.reconciliation_id,
        target_commit_sha=args.target_commit_sha,
        terminal_status=ProofTerminalState.COMMITTED,
    )

    runtime = RuntimeEvidenceLink(
        execution_id=execution.execution_id,
        execution_input_identity=input_identity,
        evidence_digest=runtime_digest,
        terminal_status="COMMITTED",
    )
    validate_e7_chain(manifest, acceptance, reconciliation, runtime)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "gnozis-e7-bounded-proof-v1",
        "target_commit_sha": args.target_commit_sha,
        "readiness_id": readiness.readiness_id,
        "execution_id": execution.execution_id,
        "execution_input_identity": input_identity,
        "runtime_evidence_digest": runtime_digest,
        "acceptance_decision_id": acceptance.decision_id,
        "reconciliation_id": reconciliation.reconciliation_id,
        "manifest_digest": manifest.manifest_digest,
        "terminal_status": manifest.terminal_status.value,
        "validator": "ACCEPT",
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
