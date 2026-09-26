import pytest

from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import ExecutionInput
from core.external_execution_request import ExternalExecutionRequest
from core.external_operation import ExternalOperation
from core.information_contract import Authorization, AuthorizationStatus, Information
from core.psi_transition import PsiTransition
from core.state import Psi


def make_information(status):
    return Information(
        information_id="external-1",
        source="external",
        content_reference="content-1",
        provenance_ref="prov-1",
        authorization=Authorization(
            source="external",
            purpose="task",
            operation="execute",
            destination="core",
            status=status,
        ),
    )


def make_executor():
    return CanonicalExecutor(history=__import__("core.history", fromlist=["AppendOnlyHistory"]).AppendOnlyHistory(), kernel_version="test")


def make_psi():
    return Psi(x=0, relations=())


def make_input(psi):
    digest = __import__("hashlib").sha256(repr((psi.x, psi.relations)).encode()).hexdigest()
    state_id = __import__("hashlib").sha256(("gnozis-state-id-v1:" + digest).encode()).hexdigest()
    return ExecutionInput(
        input_type="external-information",
        state_id=state_id,
        state_digest=digest,
        content_digest="content-digest",
    )


def test_allowed_information_reaches_canonical_executor():
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda x, relations: (x + 1, relations))
    info = make_information(AuthorizationStatus.ALLOWED)
    execution_input = make_input(psi)
    request = ExternalExecutionRequest.from_information(info, operation=ExternalOperation.REQUEST, content_digest=execution_input.content_digest, purpose="test")
    result = bridge.step(info, psi, transition, execution_input, request)
    assert result.psi.x == 1


@pytest.mark.parametrize("status", [
    AuthorizationStatus.UNKNOWN,
    AuthorizationStatus.DENIED,
    AuthorizationStatus.EXPIRED,
    AuthorizationStatus.REVOKED,
])
def test_unauthorized_information_cannot_reach_canonical_executor(status):
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda p: (_ for _ in ()).throw(AssertionError("executor was reached")))
    info = make_information(status)
    execution_input = make_input(psi)
    request = ExternalExecutionRequest.from_information(info, operation=ExternalOperation.REQUEST, content_digest=execution_input.content_digest, purpose="test")
    with pytest.raises(PermissionError):
        bridge.step(info, psi, transition, execution_input, request)


def test_state_substitution_is_rejected_before_transition():
    psi = make_psi()
    foreign = Psi(x=99, relations=())
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda x, relations: (_ for _ in ()).throw(
        AssertionError("transition was reached")
    ))
    info = make_information(AuthorizationStatus.ALLOWED)
    execution_input = make_input(foreign)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest, purpose="test"
    )
    with pytest.raises(ValueError, match="state_id"):
        bridge.step(info, psi, transition, execution_input, request)


def test_content_substitution_is_rejected_at_authorized_boundary():
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda x, relations: (x + 1, relations))
    info = make_information(AuthorizationStatus.ALLOWED)
    execution_input = make_input(psi)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest="foreign-content", purpose="test"
    )
    with pytest.raises(ValueError, match="does not match execution input"):
        bridge.step(info, psi, transition, execution_input, request)
