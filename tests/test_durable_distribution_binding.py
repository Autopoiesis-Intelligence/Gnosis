from core.distribution_execution_binding import DistributionExecutionBinding
from core.durable_distribution_binding import DurableDistributionBinding


def test_durable_distribution_binding_round_trip():
    binding = DistributionExecutionBinding("d1", "digest-1", "kernel.math.1", "exec-1")
    durable = DurableDistributionBinding(3, binding)
    restored = DurableDistributionBinding.from_row(durable.row())
    assert restored == durable


def test_durable_distribution_binding_rejects_negative_sequence():
    binding = DistributionExecutionBinding("d1", "digest-1", "kernel.math.1", "exec-1")
    try:
        DurableDistributionBinding(-1, binding)
    except ValueError:
        return
    raise AssertionError("negative sequence must be rejected")


import sqlite3
from core.distribution_contract import DistributionDecision
from core.distribution_execution_binding import bind_distribution_to_execution
from core.execution_contract import ExecutionInput
from core.history import TransitionRecord
from core.kernel_execution_contract import KernelExecutionContract
from core.provenance import Provenance
from core.sqlite_persistence import SQLiteHistoryStore


def test_distribution_binding_survives_restart_and_tamper_is_rejected(tmp_path):
    path = tmp_path / "distribution-binding.db"
    decision = DistributionDecision("d1", "kernel.math.1", "math", "w1", "c1")
    contract = KernelExecutionContract("kernel.math.1", "math", "d1", "test", 10)
    execution_input = ExecutionInput("test", "s1", "sd1", "cd1")
    binding = bind_distribution_to_execution(decision, contract, execution_input)
    record = TransitionRecord(0, "genesis", "s0", "k1", "s0", True, "e0", kernel_execution_identity=binding.execution_identity)
    SQLiteHistoryStore(path).commit_once_with_audit(record, Provenance("s0", "e0", "k1"), None, "state", distribution_binding=binding)
    reopened = SQLiteHistoryStore(path)
    reopened.verify_cross_table_consistency()
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE distribution_execution_binding SET execution_identity='tampered' WHERE sequence=0")
        conn.commit()
    try:
        reopened.verify_cross_table_consistency()
    except ValueError as exc:
        assert "distribution execution identity" in str(exc)
        return
    raise AssertionError("tampered distribution binding must fail closed")
