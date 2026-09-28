from __future__ import annotations

import pytest

from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import ExecutionInput, execution_input_from_psi
from core.external_execution_request import ExternalExecutionRequest
from core.external_operation import ExternalOperation
from core.history import AppendOnlyHistory
from core.information_contract import Authorization, AuthorizationStatus, Information
from core.kernel_execution_contract import KernelExecutionContract
from core.psi_transition import PsiTransition
from core.state import Psi


def test_kernel_contract_rejects_mismatched_target() -> None:
    bridge = AuthorizedExecution(CanonicalExecutor(history=AppendOnlyHistory(), kernel_version="test"))
    execution_input = ExecutionInput("test", "state", "state-digest", "content-digest")
    request = ExternalExecutionRequest(
        operation=ExternalOperation.REQUEST,
        information_id="info",
        content_digest="content-digest",
        purpose="test",
    )
    info = Information(
        information_id="info",
        source="test-source",
        content_reference="content-digest",
        provenance_ref="test-provenance",
        authorization=Authorization(
            source="test-source",
            purpose="test",
            operation=ExternalOperation.REQUEST,
            destination="core",
            status=AuthorizationStatus.ALLOWED,
        ),
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


def test_kernel_contract_identity_is_bound_to_transition_record() -> None:
    psi = Psi((), ())
    execution_input = execution_input_from_psi(psi, input_type="test", content_digest="content-digest")
    bridge = AuthorizedExecution(
        CanonicalExecutor(history=AppendOnlyHistory(), kernel_version="test")
    )
    request = ExternalExecutionRequest(
        operation=ExternalOperation.REQUEST,
        information_id="info",
        content_digest="content-digest",
        purpose="test",
    )
    info = Information(
        information_id="info",
        source="test-source",
        content_reference="content-digest",
        provenance_ref="test-provenance",
        authorization=Authorization(
            source="test-source",
            purpose="test",
            operation=ExternalOperation.REQUEST,
            destination="core",
            status=AuthorizationStatus.ALLOWED,
        ),
    )
    contract = KernelExecutionContract(
        kernel_id="kernel.math.1",
        capability="math",
        distribution_decision_id="dist-1",
        scope="test",
        resource_budget=1,
    )

    result = bridge.step(
        info, psi, PsiTransition(lambda x, r: (x, r)),
        execution_input, request,
        kernel_contract=contract,
        allowed_kernel_id="kernel.math.1",
        allowed_capability="math",
    )

    record = result.history.head
    assert record is not None
    assert record.kernel_execution_identity == contract.identity(execution_input)
    assert record.evidence_binding_digest
