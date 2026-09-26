import pytest

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
