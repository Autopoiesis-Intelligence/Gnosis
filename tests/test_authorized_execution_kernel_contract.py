from __future__ import annotations

import pytest

from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import ExecutionInput
from core.external_execution_request import ExternalExecutionRequest
from core.history import AppendOnlyHistory
from core.information_contract import Information
from core.kernel_execution_contract import KernelExecutionContract
from core.psi_transition import PsiTransition
from core.state import Psi


def test_kernel_contract_rejects_mismatched_target() -> None:
    bridge = AuthorizedExecution(CanonicalExecutor(history=AppendOnlyHistory(), kernel_version="test"))
    execution_input = ExecutionInput("test", "state", "state-digest", "content-digest")
    request = ExternalExecutionRequest(
        operation="execute",
        information_id="info",
        purpose="test",
    )
    info = Information(
        information_id="info",
        content_digest="content-digest",
        authorization_status="authorized",
    )
    contract = KernelExecutionContract(
        kernel_id="kernel.math.1",
        capability="math",
        distribution_decision_id="dist-1",
        scope="test",
        resource_budget=1,
    )

    with pytest.raises(ValueError, match="target is not authorized"):
        bridge.step(
            info, Psi((), ()), PsiTransition(lambda x, r: (x, r)),
            execution_input, request,
            kernel_contract=contract,
            allowed_kernel_id="kernel.physics.1",
            allowed_capability="math",
        )
