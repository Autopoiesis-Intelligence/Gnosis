from pathlib import Path
import pytest
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


def test_end_to_end_crash_restart_retry_has_single_durable_commit(tmp_path: Path):
    from core.history import AppendOnlyHistory, TransitionRecord
    from core.provenance import Provenance
    from core.sqlite_persistence import SQLiteHistoryStore

    database = tmp_path / "e2e.sqlite"
    fired = {"value": False}

    def crash(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("simulated process crash after durable commit")

    rec = TransitionRecord(
        sequence=0, previous_hash="genesis", state_hash="e2e-state",
        kernel_version="e2e-v1", candidate_hash="e2e-state",
        admitted=True, evidence_hash="e2e-evidence",
    )
    provenance = Provenance("e2e-state", "e2e-evidence", "e2e-v1", ("runtime",))

    store = SQLiteHistoryStore(database, failure_injector=crash)
    with pytest.raises(RuntimeError, match="simulated process crash"):
        store.commit_once_with_audit(rec, provenance, "start", "e2e-state")

    restarted = SQLiteHistoryStore(database)
    retry = restarted.commit_once_with_audit(
        rec, provenance, "start-after-restart", "e2e-state"
    )

    assert not retry.applied
    assert len(retry.history.records) == 1
    assert len(restarted.load().records) == 1
    assert len(restarted.load_provenance()) == 1
    assert len(restarted.load_audit()) == 1


def test_end_to_end_authorized_execution_rejects_durable_head_substitution(tmp_path: Path):
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

    database = tmp_path / "head-substitution.sqlite"
    run(tmp_path / "first.json", database)

    # The durable store is authoritative for the committed head. A caller that
    # supplies a different in-memory Psi must be rejected before the transition
    # can produce a new candidate.
    supplied = Psi(x=("foreign-start",), relations=())
    task = Task.create("head-substitution-task", "must-not-run")
    info = Information(
        "head-substitution-information", "runtime", task.task_id,
        "head-substitution-execution",
        Authorization("runtime", "task-processing", "transform", "core",
                      AuthorizationStatus.ALLOWED),
        payload=task.content,
    )
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="head-substitution-task",
    )
    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="runtime-task-v1",
        durable_store=SQLiteHistoryStore(database),
    )

    with pytest.raises(ValueError, match="previous Psi does not match history head"):
        TaskProcessor(AuthorizedExecution(executor)).process(
            task, info, supplied,
            PsiTransition(lambda x, relations: (_ for _ in ()).throw(
                AssertionError("foreign transition was reached")
            )),
            execution_input_from_psi(
                supplied, input_type="task", content_digest=task.content_digest
            ),
            request,
        )

    durable = SQLiteHistoryStore(database).load()
    assert len(durable.records) == 1
