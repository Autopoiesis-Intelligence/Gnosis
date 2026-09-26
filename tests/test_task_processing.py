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
        info, operation=ExternalOperation(name="transform"), content_digest=task.content_digest, purpose="task-processing"
    )
    execution_input=execution_input_from_psi(psi,input_type="task",content_digest=task.content_digest)
    transition=PsiTransition(lambda s: Psi(x=s.x+("done",),relations=s.relations))
    result=TaskProcessor(AuthorizedExecution(CanonicalExecutor(history=__import__("core.history",fromlist=["AppendOnlyHistory"]).AppendOnlyHistory(),kernel_version="task-kernel"))).process(
        task,info,psi,transition,execution_input,request
    )
    assert result.task_id=="task-001"
    assert result.execution.psi.x==("start","done")
    assert len(result.execution.history.records)==1
