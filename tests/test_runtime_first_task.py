from pathlib import Path
from tools.run_first_task import run

def test_runtime_surface_emits_durable_evidence(tmp_path: Path):
    evidence=run(tmp_path/"evidence.json", tmp_path/"runtime.sqlite")
    assert evidence["status"]=="COMMITTED"
    assert evidence["history_records"]==1
    assert evidence["provenance_records"]==1
    assert evidence["audit_records"]==1
    assert evidence["authorization"]=="ALLOWED"


def test_runtime_surface_fails_closed_on_tampered_transition(tmp_path: Path):
    import sqlite3
    from core.sqlite_persistence import SQLiteHistoryStore
    output = tmp_path / "evidence.json"
    database = tmp_path / "runtime.sqlite"
    run(output, database)
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE transition_history SET previous_hash = ? WHERE sequence = 0", ("tampered",))
        conn.commit()
    from core.state import Psi
    from core.recovery import recover_psi
    import pytest
    with pytest.raises(ValueError):
        recover_psi(Psi(x=("runtime-start",), relations=()), SQLiteHistoryStore(database), lambda _s, _r: Psi(x=("runtime-start", "runtime-done"), relations=()))
