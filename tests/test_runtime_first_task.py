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


def test_rehydrated_executor_continues_from_recovered_durable_head(tmp_path: Path):
    from core.authorized_execution import AuthorizedExecution
    from core.execution import CanonicalExecutor
    from core.execution_contract import execution_input_from_psi
    from core.external_execution_request import ExternalExecutionRequest
    from core.external_operation import ExternalOperation
    from core.history import AppendOnlyHistory
    from core.information_contract import Authorization, AuthorizationStatus, Information
    from core.psi_transition import PsiTransition
    from core.sqlite_persistence import SQLiteHistoryStore
    from core.state import Psi
    from core.task_processing import Task, TaskProcessor

    database = tmp_path / "runtime.sqlite"
    first = run(tmp_path / "first.json", database)
    recovered = Psi(x=("runtime-start", "runtime-done"), relations=())
    task = Task.create("runtime-second-task", "continue-after-recovery")
    info = Information("runtime-second-information", "runtime", task.task_id, "runtime-execution",
        Authorization("runtime", "task-processing", "transform", "core", AuthorizationStatus.ALLOWED), payload=task.content)
    request = ExternalExecutionRequest.from_information(info, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="runtime-second-task")
    executor = CanonicalExecutor(history=AppendOnlyHistory(), kernel_version="runtime-task-v1", durable_store=SQLiteHistoryStore(database))
    result = TaskProcessor(AuthorizedExecution(executor)).process(
        task, info, recovered, PsiTransition(lambda x, relations: (x + ("runtime-second-done",), relations)),
        execution_input_from_psi(recovered, input_type="task", content_digest=task.content_digest), request)
    durable = SQLiteHistoryStore(database).load()
    assert first["result_state_digest"] != result.execution.history.head.state_hash
    assert len(durable.records) == 2
    assert result.execution.psi == Psi(x=("runtime-start", "runtime-done", "runtime-second-done"), relations=())


def test_restart_boundary_uses_durable_head_without_memory_carryover(tmp_path: Path):
    from core.authorized_execution import AuthorizedExecution
    from core.execution import CanonicalExecutor
    from core.execution_contract import execution_input_from_psi
    from core.external_execution_request import ExternalExecutionRequest
    from core.external_operation import ExternalOperation
    from core.history import AppendOnlyHistory
    from core.information_contract import Authorization, AuthorizationStatus, Information
    from core.psi_transition import PsiTransition
    from core.sqlite_persistence import SQLiteHistoryStore
    from core.state import Psi
    from core.task_processing import Task, TaskProcessor

    database = tmp_path / "restart.sqlite"
    run(tmp_path / "first.json", database)

    # Simulated process restart: no reuse of the first executor/history object.
    fresh_store = SQLiteHistoryStore(database)
    fresh_executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="runtime-task-v1",
        durable_store=fresh_store,
    )
    recovered = Psi(x=("runtime-start", "runtime-done"), relations=())
    task = Task.create("restart-task", "after-process-restart")
    info = Information("restart-information", "runtime", task.task_id, "restart-execution",
        Authorization("runtime", "task-processing", "transform", "core", AuthorizationStatus.ALLOWED),
        payload=task.content)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="restart-task")
    result = TaskProcessor(AuthorizedExecution(fresh_executor)).process(
        task, info, recovered,
        PsiTransition(lambda x, relations: (x + ("restart-done",), relations)),
        execution_input_from_psi(recovered, input_type="task", content_digest=task.content_digest),
        request)
    durable = SQLiteHistoryStore(database).load()
    assert len(durable.records) == 2
    assert result.execution.psi == Psi(
        x=("runtime-start", "runtime-done", "restart-done"), relations=())
