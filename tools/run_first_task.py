"""Execute one deterministic task through the product runtime boundary."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import execution_input_from_psi, state_digest
from core.external_execution_request import ExternalExecutionRequest
from core.external_operation import ExternalOperation
from core.history import AppendOnlyHistory
from core.information_contract import Authorization, AuthorizationStatus, Information
from core.psi_transition import PsiTransition
from core.sqlite_persistence import SQLiteHistoryStore
from core.state import Psi
from core.task_processing import Task, TaskProcessor

def run(output: Path, database: Path) -> dict:
    psi = Psi(x=("runtime-start",), relations=())
    task = Task.create("runtime-first-task", "append-runtime-result")
    information = Information("runtime-information", "runtime", task.task_id, "runtime-execution",
        Authorization("runtime", "task-processing", "transform", "core", AuthorizationStatus.ALLOWED),
        payload=task.content)
    request = ExternalExecutionRequest.from_information(
        information, operation=ExternalOperation.REQUEST,
        content_digest=task.content_digest, purpose="runtime-first-task")
    execution_input = execution_input_from_psi(
        psi, input_type="task", content_digest=task.content_digest)
    transition = PsiTransition(lambda x, relations: (x + ("runtime-done",), relations))
    store = SQLiteHistoryStore(database)
    executor = CanonicalExecutor(history=AppendOnlyHistory(),
        kernel_version="runtime-task-v1", durable_store=store)
    result = TaskProcessor(AuthorizedExecution(executor)).process(
        task, information, psi, transition, execution_input, request)
    history, provenance, audit = store.load(), store.load_provenance(), store.load_audit()
    if (len(history.records), len(provenance), len(audit)) != (1, 1, 1):
        raise RuntimeError("runtime evidence cardinality invariant failed")
    if result.execution.psi != Psi(x=("runtime-start", "runtime-done"), relations=()):
        raise RuntimeError("runtime result invariant failed")
    evidence = {"schema":"gnozis-runtime-evidence-v1","task_id":result.task_id,
        "content_digest":result.content_digest,"initial_state_digest":state_digest(psi),
        "result_state_digest":state_digest(result.execution.psi),"history_records":1,
        "provenance_records":1,"audit_records":1,
        "authorization":information.authorization.status.value,
        "kernel_version":history.records[0].kernel_version,"status":"COMMITTED"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return evidence

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="runtime-evidence/first-task.json")
    parser.add_argument("--database", default="runtime-evidence/first-task.sqlite")
    args=parser.parse_args()
    print(json.dumps(run(Path(args.output), Path(args.database)), sort_keys=True))

if __name__ == "__main__":
    main()
