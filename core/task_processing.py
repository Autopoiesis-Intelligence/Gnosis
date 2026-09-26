"""Minimal product task-processing boundary over the canonical execution path."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from .authorized_execution import AuthorizedExecution
from .execution import ExecutionResult
from .execution_contract import ExecutionInput
from .external_execution_request import ExternalExecutionRequest
from .information_contract import Information
from .psi_transition import PsiTransition
from .state import Psi

@dataclass(frozen=True)
class Task:
    task_id: str
    content: str
    content_digest: str

    @classmethod
    def create(cls, task_id: str, content: str) -> "Task":
        if not task_id.strip() or not content.strip():
            raise ValueError("task_id and content are required")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(task_id, content, digest)

@dataclass(frozen=True)
class TaskResult:
    task_id: str
    content_digest: str
    execution: ExecutionResult

class TaskProcessor:
    """Process one authorized task without bypassing canonical execution."""

    def __init__(self, execution: AuthorizedExecution):
        self.execution = execution

    def process(
        self,
        task: Task,
        information: Information,
        psi: Psi,
        transition: PsiTransition,
        execution_input: ExecutionInput,
        request: ExternalExecutionRequest,
        *,
        test=None,
    ) -> TaskResult:
        if request.information_id != information.information_id:
            raise ValueError("task request information mismatch")
        if request.content_digest != task.content_digest:
            raise ValueError("task content digest mismatch")
        if execution_input.content_digest != task.content_digest:
            raise ValueError("execution input content digest mismatch")
        result = self.execution.step(
            information, psi, transition, execution_input, request, test=test
        )
        return TaskResult(task.task_id, task.content_digest, result)
