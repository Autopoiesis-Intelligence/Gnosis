import pytest

from core.e7_107_readiness import ReadinessRecord, ReadinessState


def make_record():
    return ReadinessRecord(
        batch_id="b1",
        target_commit_sha="abc",
        repository_ref="refs/heads/main",
        baseline_id="base",
        candidate_selection_id="sel",
        evidence_policy_revision="ep1",
        verification_matrix_revision="vm1",
        environment_identity="env",
        checks=tuple(f"check-{i}" for i in range(13)),
        commands=("pytest",),
        expected_outcomes=("pass",),
        evidence_capture_mapping=("report",),
        stop_conditions=("unexpected-mutation",),
        retry_rules=("deterministic",),
    )


def test_ready_requires_exact_target_and_evidence_destination():
    record = make_record()
    assert record.ready(resolved_commit_sha="abc", evidence_destinations_present=True).state == ReadinessState.READY
    assert record.ready(resolved_commit_sha="wrong", evidence_destinations_present=True).state == ReadinessState.BLOCKED
    assert record.ready(resolved_commit_sha="abc", evidence_destinations_present=False).state == ReadinessState.BLOCKED


def test_only_ready_can_execute():
    record = make_record()
    with pytest.raises(ValueError):
        record.execute()
    ready = record.ready(resolved_commit_sha="abc", evidence_destinations_present=True)
    assert ready.execute().state == ReadinessState.EXECUTING


def test_target_change_invalidates_ready_batch():
    ready = make_record().ready(resolved_commit_sha="abc", evidence_destinations_present=True)
    assert ready.invalidate_for_commit_change().state == ReadinessState.INVALIDATED


def test_exactly_thirteen_checks_required():
    with pytest.raises(ValueError):
        ReadinessRecord(**{**make_record().__dict__, "checks": ("only-one",)})
