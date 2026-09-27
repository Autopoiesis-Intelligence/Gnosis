import pytest
import sqlite3

from core.history import TransitionRecord
from core.sqlite_persistence import SQLiteHistoryStore
from core.provenance import Provenance


def rec(seq, prev, state):
    return TransitionRecord(
        sequence=seq,
        previous_hash=prev,
        state_hash=state,
        kernel_version="k1",
        candidate_hash=state,
        admitted=True,
        evidence_hash="e1",
    )


def test_sqlite_commit_survives_reopen(tmp_path):
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)

    result = store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    assert result.applied
    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == (rec(0, "genesis", "s0"),)


def test_failure_before_insert_rolls_back(tmp_path):
    path = tmp_path / "history.db"

    def fail(point):
        if point == "before_insert":
            raise RuntimeError("injected crash")

    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="injected crash"):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    assert SQLiteHistoryStore(path).load().records == ()


def test_failure_after_insert_before_commit_rolls_back(tmp_path):
    path = tmp_path / "history.db"

    def fail(point):
        if point == "after_insert_before_commit":
            raise RuntimeError("injected crash")

    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="injected crash"):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    assert SQLiteHistoryStore(path).load().records == ()


def test_failure_after_commit_leaves_durable_record_for_recovery(tmp_path):
    path = tmp_path / "history.db"

    def fail(point):
        if point == "after_commit":
            raise RuntimeError("process stopped after durable commit")

    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="durable commit"):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    recovered = SQLiteHistoryStore(path).load()
    assert recovered.records == (rec(0, "genesis", "s0"),)


def test_retry_after_post_commit_failure_is_idempotent(tmp_path):
    path = tmp_path / "history.db"

    fired = {"value": False}

    def fail(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("post-commit failure")

    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    retry = SQLiteHistoryStore(path).commit_once(
        rec(0, "genesis", "s0"),
        "current-after-recovery",
        "next-after-recovery",
    )

    assert not retry.applied
    assert retry.value == "current-after-recovery"
    assert len(retry.history.records) == 1


def test_sqlite_rejects_conflicting_existing_head(tmp_path):
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)
    store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    with pytest.raises(ValueError, match="conflicts"):
        store.commit_once(rec(0, "genesis", "different"), "current", "other")


def test_atomic_audit_commit_rolls_back_on_interrupted_transaction(tmp_path):
    path = tmp_path / "atomic.db"

    def fail(point):
        if point == "after_audit_before_commit":
            raise RuntimeError("crash before durable commit")

    store = SQLiteHistoryStore(path, failure_injector=fail)
    provenance = Provenance("s0", "e1", "k1", ("source",))
    with pytest.raises(RuntimeError, match="crash before durable commit"):
        store.commit_once_with_audit(
            rec(0, "genesis", "s0"), provenance, "current", "next"
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == ()
    assert reopened.load_audit() == ()
    assert reopened.load_provenance() == ()


@pytest.mark.parametrize(
    "failure_point",
    [
        "after_history_before_audit",
        "after_history_before_provenance",
        "after_provenance_before_audit",
        "after_authorization_before_audit",
        "after_audit_before_commit",
    ],
)
def test_atomic_commit_rolls_back_all_evidence_for_every_precommit_failure(
    tmp_path, failure_point
):
    path = tmp_path / f"atomic-{failure_point}.db"

    def fail(point):
        if point == failure_point:
            raise RuntimeError(f"injected failure at {point}")

    store = SQLiteHistoryStore(path, failure_injector=fail)
    provenance = Provenance("s0", "e1", "k1", ("source",))

    with pytest.raises(RuntimeError, match=failure_point):
        store.commit_once_with_audit(
            rec(0, "genesis", "s0"),
            provenance,
            "current",
            "next",
            authorization_digest="auth-0" if failure_point == "after_authorization_before_audit" else None,
            authorization_state_digest="genesis" if failure_point == "after_authorization_before_audit" else None,
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == ()
    assert reopened.load_audit() == ()
    assert reopened.load_provenance() == ()
    assert reopened.load_authorization_consumption() == ()
    reopened.verify_cross_table_consistency()



def test_atomic_audit_post_commit_failure_is_recoverable_and_idempotent(tmp_path):
    path = tmp_path / "post-commit-recovery.db"
    fired = {"value": False}

    def fail(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("process stopped after durable commit")

    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="durable commit"):
        store.commit_once_with_audit(record, provenance, "current", "next")

    recovered = SQLiteHistoryStore(path)
    assert recovered.load().records == (record,)
    assert len(recovered.load_audit()) == 1
    assert recovered.load_provenance() == (provenance,)
    recovered.verify_cross_table_consistency()

    retry = recovered.commit_once_with_audit(
        record,
        provenance,
        "current-after-recovery",
        "next-after-recovery",
    )
    assert not retry.applied
    assert retry.value == "current-after-recovery"
    assert retry.history.records == (record,)
    assert len(SQLiteHistoryStore(path).load_audit()) == 1
    assert SQLiteHistoryStore(path).load_provenance() == (provenance,)


def test_atomic_audit_post_commit_failure_with_authorization_is_idempotent(tmp_path):
    path = tmp_path / "authorized-post-commit-recovery.db"
    fired = {"value": False}

    def fail(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("process stopped after durable commit")

    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="durable commit"):
        store.commit_once_with_audit(
            record,
            provenance,
            "current",
            "next",
            authorization_digest="auth-0",
            authorization_state_digest="genesis",
        )

    recovered = SQLiteHistoryStore(path)
    assert len(recovered.load().records) == 1
    assert len(recovered.load_audit()) == 1
    assert recovered.load_provenance() == (provenance,)
    assert len(recovered.load_authorization_consumption()) == 1
    recovered.verify_cross_table_consistency(initial_state_digest="genesis")

    retry = recovered.commit_once_with_audit(
        record,
        provenance,
        "current-after-recovery",
        "next-after-recovery",
        authorization_digest="auth-0",
        authorization_state_digest="genesis",
    )
    assert not retry.applied
    assert retry.value == "current-after-recovery"
    assert len(SQLiteHistoryStore(path).load().records) == 1
    assert len(SQLiteHistoryStore(path).load_audit()) == 1
    assert len(SQLiteHistoryStore(path).load_provenance()) == 1
    assert len(SQLiteHistoryStore(path).load_authorization_consumption()) == 1


def _seed_consistent_audit_store(path):
    store = SQLiteHistoryStore(path)
    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store.commit_once_with_audit(record, provenance, "current", "next")
    return record, provenance


def test_commit_fails_closed_when_history_is_tampered(tmp_path):
    path = tmp_path / "tampered-history.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE transition_history SET state_hash = ? WHERE sequence = 0",
            ("tampered-state",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable transition binding mismatch"):
        store.commit_once_with_audit(
            rec(1, "tampered-state", "s1"),
            provenance,
            "current",
            "next",
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records[0].state_hash == "tampered-state"


def test_commit_fails_closed_when_provenance_is_tampered(tmp_path):
    path = tmp_path / "tampered-provenance.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 0",
            ("tampered-candidate",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable candidate binding mismatch"):
        store.commit_once_with_audit(
            rec(1, record.state_hash, "s1"),
            provenance,
            "current",
            "next",
        )


def test_commit_fails_closed_when_audit_is_tampered(tmp_path):
    path = tmp_path / "tampered-audit.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            ("tampered-transition",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable audit digest mismatch"):
        store.commit_once_with_audit(
            rec(1, record.state_hash, "s1"),
            provenance,
            "current",
            "next",
        )


def _seed_two_transition_audit_store(path):
    store = SQLiteHistoryStore(path)
    first = rec(0, "genesis", "s0")
    second = rec(1, "s0", "s1")
    p0 = Provenance("s0", "e1", "k1", ("source-0",))
    p1 = Provenance("s1", "e1", "k1", ("source-1",))
    store.commit_once_with_audit(first, p0, "current", "s0")
    store.commit_once_with_audit(second, p1, "s0", "s1")
    return first, second, p0, p1


def test_commit_fails_closed_when_provenance_rows_are_cross_bound(tmp_path):
    path = tmp_path / "cross-bound-provenance.db"
    first, second, p0, p1 = _seed_two_transition_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 0",
            (p1.candidate_hash,),
        )
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 1",
            (p0.candidate_hash,),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable candidate binding mismatch"):
        store.commit_once_with_audit(
            rec(2, "s1", "s2"),
            Provenance("s2", "e1", "k1", ("source-2",)),
            "s1",
            "s2",
        )


def test_commit_fails_closed_when_audit_rows_are_cross_bound(tmp_path):
    path = tmp_path / "cross-bound-audit.db"
    first, second, p0, p1 = _seed_two_transition_audit_store(path)

    audits = SQLiteHistoryStore(path).load_audit()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            (audits[1].transition_hash,),
        )
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 1",
            (audits[0].transition_hash,),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable transition binding mismatch"):
        store.commit_once_with_audit(
            rec(2, "s1", "s2"),
            Provenance("s2", "e1", "k1", ("source-2",)),
            "s1",
            "s2",
        )
