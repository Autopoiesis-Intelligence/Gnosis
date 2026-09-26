"""External-information execution bridge.

Authorization is checked before the existing canonical executor is reached.
The canonical state-transition authority remains unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass

from .execution import CanonicalExecutor, ExecutionResult
from .execution_contract import ExecutionInput
from .external_execution_request import ExternalExecutionRequest
from .information_contract import Information
from .psi_transition import PsiTransition
from .state import Psi


@dataclass(frozen=True)
class AuthorizedExecution:
    executor: CanonicalExecutor

    def step(
        self,
        information: Information,
        psi: Psi,
        transition: PsiTransition,
        execution_input: ExecutionInput,
        request: ExternalExecutionRequest,
        *,
        test=None,
    ) -> ExecutionResult:
        """Authorize external information before canonical execution."""
        if not isinstance(information, Information):
            raise TypeError("information must be Information.")
        if not isinstance(request, ExternalExecutionRequest):
            raise TypeError("request must be ExternalExecutionRequest.")

        information.require_authorized()
        if request.information_id != information.information_id:
            raise ValueError("execution request does not match information")
        if request.content_digest != execution_input.content_digest:
            raise ValueError("execution request does not match execution input")
        if self.executor.durable_store is not None:
            self.executor.durable_store.assert_authorization_unused(request.authorization_digest())

        return self.executor.step(
            psi,
            transition,
            execution_input,
            test=test,
            authorization_digest=request.authorization_digest(),
            authorization_state_digest=execution_input.state_digest,
        )
