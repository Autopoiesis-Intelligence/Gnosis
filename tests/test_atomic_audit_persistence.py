import sqlite3
import pytest
from core.history import TransitionRecord
from core.provenance import Provenance
from core.sqlite_persistence import SQLiteHistoryStore

def rec():
    return TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")
def prov():
    return Provenance("s0","e0","k1")

def test_history_and_audit_are_atomic(tmp_path):
    path=tmp_path/"atomic.db"
    def fail(point):
        if point=="after_history_before_audit":
            raise RuntimeError("injected")
    store=SQLiteHistoryStore(path,failure_injector=fail)
    with pytest.raises(RuntimeError):
        store.commit_once_with_audit(rec(),prov(),None,"state")
    assert store.load().records == ()
    assert store.load_audit() == ()

def test_durable_audit_tamper_fails_closed(tmp_path):
    path=tmp_path/"audit.db"
    store=SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(),prov(),None,"state")
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE audit_history SET audit_hash='tampered' WHERE sequence=0")
        conn.commit()
    with pytest.raises(ValueError, match="digest"):
        store.load_audit()


def test_authorization_history_provenance_audit_are_atomic(tmp_path):
    path = tmp_path / "full-evidence.db"
    def fail(point):
        if point == "after_authorization_before_audit":
            raise RuntimeError("injected")
    store = SQLiteHistoryStore(path, failure_injector=fail)
    provenance = prov()
    with pytest.raises(RuntimeError, match="injected"):
        store.commit_once_with_audit(
            rec(), provenance, None, "state",
            authorization_digest="auth-1",
            authorization_state_digest="state-0",
        )
    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == ()
    assert reopened.load_audit() == ()
    assert reopened.load_provenance() == ()
    assert reopened.load_authorization_consumption() == ()


def test_authorization_tamper_fails_closed_with_candidate_binding(tmp_path):
    path = tmp_path / "authorization-tamper.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(
        rec(), prov(), None, "state",
        authorization_digest="auth-1",
        authorization_state_digest="state-0",
    )
    import sqlite3
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE authorization_consumption SET candidate_hash='tampered' WHERE authorization_digest='auth-1'"
        )
        conn.commit()
    with pytest.raises(ValueError, match="candidate binding"):
        store.verify_authorization_consumption()


@pytest.mark.parametrize(
    ("table", "column", "value", "message"),
    [
        ("transition_history", "candidate_hash", "tampered-candidate", "candidate binding"),
        ("transition_history", "evidence_hash", "tampered-evidence", "evidence binding"),
        ("provenance_history", "candidate_hash", "tampered-proof", "candidate binding"),
        ("audit_history", "provenance_hash", "tampered-proof", "provenance binding"),
        ("audit_history", "transition_hash", "tampered-transition", "transition binding"),
    ],
)
def test_cross_table_tamper_fails_closed(tmp_path, table, column, value, message):
    path = tmp_path / "cross-table.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), prov(), None, "state")
    with sqlite3.connect(path) as conn:
        conn.execute(f"UPDATE {table} SET {column}=? WHERE sequence=0", (value,))
        conn.commit()
    with pytest.raises(ValueError):
        SQLiteHistoryStore(path).verify_cross_table_consistency()


@pytest.mark.parametrize("mutation", ["delete_first", "delete_middle", "duplicate_sequence", "rewrite_previous_hash"])
def test_chain_continuity_mutation_fails_closed(tmp_path, mutation):
    path = tmp_path / "chain-mutation.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), prov(), None, "state")
    second = TransitionRecord(1, "s0", "s1", "k1", "s1", True, "e1")
    store.commit_once_with_audit(
        second,
        Provenance("s1", "e1", "k1"),
        "state",
        "state-1",
    )
    third = TransitionRecord(2, "s1", "s2", "k1", "s2", True, "e2")
    store.commit_once_with_audit(
        third,
        Provenance("s2", "e2", "k1"),
        "state-1",
        "state-2",
    )

    with sqlite3.connect(path) as conn:
        if mutation == "delete_first":
            conn.execute("DELETE FROM transition_history WHERE sequence=0")
            conn.execute("DELETE FROM provenance_history WHERE sequence=0")
            conn.execute("DELETE FROM audit_history WHERE sequence=0")
        elif mutation == "delete_middle":
            conn.execute("DELETE FROM transition_history WHERE sequence=1")
            conn.execute("DELETE FROM provenance_history WHERE sequence=1")
            conn.execute("DELETE FROM audit_history WHERE sequence=1")
        elif mutation == "duplicate_sequence":
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO transition_history VALUES (2, 's1', 's2', 'k1', 's2', 1, 'e2')"
                )
            return
        elif mutation == "rewrite_previous_hash":
            conn.execute(
                "UPDATE transition_history SET previous_hash='forged' WHERE sequence=1"
            )
        conn.commit()

    with pytest.raises(ValueError):
        store.verify_cross_table_consistency()


def test_audit_chain_reorder_and_previous_audit_tamper_fail_closed(tmp_path):
    path = tmp_path / "audit-chain.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), prov(), None, "state")
    second = TransitionRecord(1, "s0", "s1", "k1", "s1", True, "e1")
    store.commit_once_with_audit(second, Provenance("s1", "e1", "k1"), "state", "state-1")

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE audit_history SET previous_audit_hash='reordered' WHERE sequence=1"
        )
        conn.commit()
    with pytest.raises(ValueError):
        SQLiteHistoryStore(path).load_audit()


def test_audit_sequence_gap_fails_closed_after_restart(tmp_path):
    path = tmp_path / "audit-gap.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), prov(), None, "state")
    second = TransitionRecord(1, "s0", "s1", "k1", "s1", True, "e1")
    store.commit_once_with_audit(second, Provenance("s1", "e1", "k1"), "state", "state-1")

    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM audit_history WHERE sequence=0")
        conn.commit()
    reopened = SQLiteHistoryStore(path)
    with pytest.raises(ValueError):
        reopened.verify_cross_table_consistency()




def test_persisted_evidence_does_not_create_admission_after_restart(tmp_path):
    path = tmp_path / "evidence-authority.db"
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(
        rec(), prov(), None, "state",
        authorization_digest="auth-1",
        authorization_state_digest="state-0",
    )

    reopened = SQLiteHistoryStore(path)
    reopened.verify_cross_table_consistency()
    persisted = reopened.load_provenance()[0]

    from core.admission import admit
    from core.proof import ProofObligation
    from core.state import State

    proof = ProofObligation(
        passed=False,
        invariant=False,
        viable=False,
        evidence={"persisted_provenance": persisted},
    )
    admission = admit(
        State(values={"x": "replay", "relations": ()}),
        proof,
    )
    assert admission.accepted is False
