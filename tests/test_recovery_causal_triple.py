import sqlite3
import pytest
from core.recovery import recover_psi
from core.sqlite_persistence import SQLiteHistoryStore
from core.history import TransitionRecord
from core.provenance import Provenance

def rec():
    return TransitionRecord(0,"genesis","s0","k1","s0",True,"e0")

def test_recovery_rejects_missing_provenance(tmp_path):
    path=tmp_path/"missing.db"
    store=SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), Provenance("s0","e0","k1"), None, "state")
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM provenance_history WHERE sequence=0")
        conn.commit()
    with pytest.raises(ValueError, match="cardinality"):
        recover_psi(__import__("core.state",fromlist=["Psi"]).Psi(x=("g",),relations=()), SQLiteHistoryStore(path), lambda s,r: s)

def test_recovery_verifies_audit_binding(tmp_path):
    path=tmp_path/"tampered.db"
    store=SQLiteHistoryStore(path)
    store.commit_once_with_audit(rec(), Provenance("s0","e0","k1"), None, "state")
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE audit_history SET provenance_hash='tampered' WHERE sequence=0")
        conn.commit()
    with pytest.raises(ValueError):
        recover_psi(__import__("core.state",fromlist=["Psi"]).Psi(x=("g",),relations=()), SQLiteHistoryStore(path), lambda s,r: s)
