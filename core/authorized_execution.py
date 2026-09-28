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
from .kernel_execution_contract import KernelExecutionContract, verify_kernel_execution_contract
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
        kernel_contract: KernelExecutionContract | None = None,
        allowed_kernel_id: str | None = None,
        allowed_capability: str | None = None,
    ) -> ExecutionResult:
        """Authorize external information before canonical execution."""
        if not isinstance(information, Information):
            raise TypeError("information must be Information.")
        if not isinstance(request, ExternalExecutionRequest):
            raise TypeError("request must be ExternalExecutionRequest.")

        information.require_authorized()
        if kernel_contract is not None:
            if allowed_kernel_id is None or allowed_capability is None:
                raise ValueError("kernel authorization policy is required.")
            verify_kernel_execution_contract(
                kernel_contract,
                execution_input,
                allowed_kernel_id=allowed_kernel_id,
                allowed_capability=allowed_capability,
            )
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
            kernel_contract=kernel_contract,
        )
