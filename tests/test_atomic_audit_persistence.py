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
