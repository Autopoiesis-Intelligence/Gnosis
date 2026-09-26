from pathlib import Path
from tools.run_first_task import run

def test_runtime_surface_emits_durable_evidence(tmp_path: Path):
    evidence=run(tmp_path/"evidence.json", tmp_path/"runtime.sqlite")
    assert evidence["status"]=="COMMITTED"
    assert evidence["history_records"]==1
    assert evidence["provenance_records"]==1
    assert evidence["audit_records"]==1
    assert evidence["authorization"]=="ALLOWED"
