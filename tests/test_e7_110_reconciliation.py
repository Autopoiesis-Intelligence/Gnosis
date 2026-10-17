import pytest

from core.e7_110_reconciliation import ReconciliationSnapshot, ReconciliationState


def snap(reported="80", recalculated="80", status=ReconciliationState.PENDING):
    return ReconciliationSnapshot(
        reconciliation_id="r1",
        acceptance_batch_id="b1",
        input_snapshot_digest="sha256:inputs",
        metric_id="contract_progress",
        reported_value=reported,
        recalculated_value=recalculated,
        calculation_revision="calc-1",
        evidence_digests=("sha256:e1",),
        status=status,
    )


def test_matching_metric_reconciles():
    assert snap().reconcile().status == ReconciliationState.RECONCILED


def test_discrepancy_blocks_reconciliation():
    assert snap(recalculated="73").reconcile().status == ReconciliationState.DISCREPANCY


def test_reconciled_snapshot_is_immutable_terminal_record():
    reconciled = snap().reconcile()
    with pytest.raises(ValueError):
        reconciled.reconcile()


def test_conflicting_replay_is_rejected():
    a = snap()
    b = snap(recalculated="73")
    with pytest.raises(ValueError):
        a.assert_replay_compatible(b)


def test_same_identity_replay_is_compatible():
    a = snap()
    a.assert_replay_compatible(snap())


def test_snapshot_identity_is_deterministic():
    assert snap().snapshot_identity == snap().snapshot_identity
