import pytest

from core.e7_107_readiness import (
    CheckState,
    E7ReadinessRecord,
    ReadinessCheck,
    ReadinessState,
)
from core.e7_108_execution import E7ExecutionRecord, ExecutionState


def readiness() -> E7ReadinessRecord:
    checks = tuple(ReadinessCheck(f"check-{i}", CheckState.PASS) for i in range(13))
    return E7ReadinessRecord(
        batch_id="batch-1",
        target_commit_sha="commit-1",
        repository_ref="refs/heads/audit/e7-integrated-proof",
        baseline_id="baseline-1",
        candidate_selection_id="candidate-1",
        evidence_policy_revision="policy-1",
        verification_matrix_revision="matrix-1",
        environment_identity="env-1",
        checks=checks,
        commands=("python tools/run_first_task.py",),
        expected_outcomes=("COMMITTED",),
        evidence_capture_mapping=("runtime-evidence/first-task.json",),
        stop_conditions=("mutation",),
        retry_rules=("same-input-only",),
    )


def test_e7_107_requires_exactly_13_checks():
    r = readiness()
    assert r.state is ReadinessState.PREPARING
    assert r.mark_ready(
        resolved_commit_sha="commit-1",
        evidence_destination="runtime-evidence",
    ).state is ReadinessState.READY


def test_e7_107_wrong_commit_blocks():
    r = readiness().mark_ready(
        resolved_commit_sha="other",
        evidence_destination="runtime-evidence",
    )
    assert r.state is ReadinessState.BLOCKED


def test_e7_107_failed_check_blocks():
    checks = tuple(
        ReadinessCheck(f"check-{i}", CheckState.FAIL if i == 4 else CheckState.PASS)
        for i in range(13)
    )
    r = readiness()
    r = E7ReadinessRecord(
        **{**r.__dict__, "checks": checks}
    ).mark_ready(
        resolved_commit_sha="commit-1",
        evidence_destination="runtime-evidence",
    )
    assert r.state is ReadinessState.BLOCKED


def test_e7_108_exact_commit_and_replay():
    r = readiness().mark_ready(
        resolved_commit_sha="commit-1",
        evidence_destination="runtime-evidence",
    )
    execution_id = E7ExecutionRecord.execution_id_for(
        "batch-1", "commit-1", "input-1"
    )
    e = E7ExecutionRecord(
        "batch-1", execution_id, "commit-1", "input-1",
        r.readiness_id, "", (), ExecutionState.PREPARING,
    ).begin(readiness_id=r.readiness_id, target_commit_sha="commit-1")
    completed = e.complete(
        runtime_evidence_digest="digest-1",
        criterion_evidence=("runtime-status:COMMITTED",),
        target_commit_sha="commit-1",
    )
    completed.assert_replay_compatible(completed)


def test_e7_108_rejects_commit_substitution():
    r = readiness().mark_ready(
        resolved_commit_sha="commit-1",
        evidence_destination="runtime-evidence",
    )
    e = E7ExecutionRecord(
        "batch-1",
        E7ExecutionRecord.execution_id_for("batch-1", "commit-1", "input-1"),
        "commit-1", "input-1", r.readiness_id, "", (),
        ExecutionState.PREPARING,
    ).begin(readiness_id=r.readiness_id, target_commit_sha="commit-1")
    with pytest.raises(ValueError):
        e.complete(
            runtime_evidence_digest="digest-1",
            criterion_evidence=("runtime-status:COMMITTED",),
            target_commit_sha="other",
        )
