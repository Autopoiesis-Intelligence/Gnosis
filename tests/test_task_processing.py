import hashlib
from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import execution_input_from_psi
from core.external_execution_request import ExternalExecutionRequest
from core.external_operation import ExternalOperation
from core.information_contract import Authorization, AuthorizationStatus, Information
from core.psi_transition import PsiTransition
from core.state import Psi
from core.task_processing import Task, TaskProcessor
from core.sqlite_persistence import SQLiteHistoryStore

def test_first_independent_task_processing_path():
    psi=Psi(x=("start",), relations=())
    task=Task.create("task-001","append-result")
    info=Information(
        information_id="info-001",
        source="task",
        content_reference=task.task_id,
        provenance_ref="test",
        authorization=Authorization("task","process","transform","core",AuthorizationStatus.ALLOWED),
        payload=task.content,
    )
    request=ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST, content_digest=task.content_digest, purpose="task-processing"
    )
    execution_input=execution_input_from_psi(psi,input_type="task",content_digest=task.content_digest)
    transition=PsiTransition(lambda x, relations: (x + ("done",), relations))
    result=TaskProcessor(AuthorizedExecution(CanonicalExecutor(history=__import__("core.history",fromlist=["AppendOnlyHistory"]).AppendOnlyHistory(),kernel_version="task-kernel"))).process(
        task,info,psi,transition,execution_input,request
    )
    assert result.task_id=="task-001"
    assert result.execution.psi.x==("start","done")
    assert len(result.execution.history.records)==1


def test_task_processing_can_use_durable_audited_store(tmp_path):
    psi=Psi(x=("start",), relations=())
    task=Task.create("task-durable","append-result")
    info=Information("info-durable","task",task.task_id,"test",
        Authorization("task","process","transform","core",AuthorizationStatus.ALLOWED),
        payload=task.content)
    request=ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="task-processing")
    execution_input=execution_input_from_psi(
        psi,input_type="task",content_digest=task.content_digest)
    transition=PsiTransition(lambda x, relations: (x + ("done",), relations))
    store=SQLiteHistoryStore(tmp_path/"task.db")
    executor=CanonicalExecutor(history=__import__("core.history",fromlist=["AppendOnlyHistory"]).AppendOnlyHistory(),
        kernel_version="task-kernel", durable_store=store)
    result=TaskProcessor(AuthorizedExecution(executor)).process(
        task,info,psi,transition,execution_input,request)
    assert result.execution.psi.x==("start","done")
    assert len(store.load().records)==1
    assert len(store.load_provenance())==1
    assert len(store.load_audit())==1


def test_durable_task_result_survives_recovery(tmp_path):
    from core.recovery import recover_psi
    from core.state import Psi
    genesis=Psi(x=("start",),relations=())
    task=Task.create("task-recovery","append-result")
    info=Information("info-recovery","task",task.task_id,"test",
        Authorization("task","process","transform","core",AuthorizationStatus.ALLOWED),
        payload=task.content)
    request=ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="task-processing")
    execution_input=execution_input_from_psi(
        genesis,input_type="task",content_digest=task.content_digest)
    transition=PsiTransition(lambda x, relations: (x + ("done",), relations))
    store=SQLiteHistoryStore(tmp_path/"recovery.db")
    executor=CanonicalExecutor(
        history=__import__("core.history",fromlist=["AppendOnlyHistory"]).AppendOnlyHistory(),
        kernel_version="task-kernel", durable_store=store)
    result=TaskProcessor(AuthorizedExecution(executor)).process(
        task,info,genesis,transition,execution_input,request)
    recovered=recover_psi(
        genesis, SQLiteHistoryStore(tmp_path/"recovery.db"),
        lambda state, record: Psi(x=state.x+("done",),relations=state.relations))
    assert recovered.state == result.execution.psi
