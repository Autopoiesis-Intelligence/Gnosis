import pytest

from core.e7_108_execution_record import ExecutionRecord, ExecutionState


def record(state=ExecutionState.PREPARED):
    return ExecutionRecord(
        execution_id="e1",
        batch_id="b1",
        target_commit_sha="abc",
        repository_ref="refs/heads/main",
        baseline_id="base",
        candidate_selection_id="sel",
        environment_identity="env",
        readiness_record_id="r1",
        state=state,
    )


def test_execution_requires_explicit_bounded_transitions():
    r = record()
    with pytest.raises(ValueError):
        r.transition(ExecutionState.COMPLETED, evidence="done")
    running = r.transition(ExecutionState.EXECUTING, evidence="started")
    completed = running.transition(ExecutionState.COMPLETED, evidence="done")
    assert completed.completed_evidence == "done"


def test_completed_requires_evidence():
    with pytest.raises(ValueError):
        ExecutionRecord(
            **{**record(ExecutionState.COMPLETED).__dict__, "completed_evidence": ""}
        )


def test_conflicting_replay_is_rejected():
    a = record()
    b = ExecutionRecord(**{**a.__dict__, "target_commit_sha": "different"})
    with pytest.raises(ValueError):
        a.assert_replay_compatible(b)


def test_same_execution_replay_is_compatible():
    a = record()
    b = record()
    a.assert_replay_compatible(b)


def test_completed_execution_cannot_transition_again():
    completed = record(ExecutionState.EXECUTING).transition(
        ExecutionState.COMPLETED, evidence="done"
    )
    with pytest.raises(ValueError):
        completed.transition(ExecutionState.EXECUTING)
