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
    try:
        request = ExternalExecutionRequest.from_information(info, operation=ExternalOperation.REQUEST, content_digest=execution_input.content_digest, purpose="test")
        bridge.step(info, psi, transition, execution_input, request)
    except PermissionError:
        pass
    else:
        pytest.fail("unauthorized information reached canonical executor")


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


def test_replay_request_with_same_content_but_different_information_is_rejected():
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda x, relations: (x + 1, relations))
    first = make_information(AuthorizationStatus.ALLOWED)
    second = Information(
        information_id="external-2",
        source="external",
        content_reference="content-2",
        provenance_ref="prov-2",
        authorization=Authorization(
            source="external", purpose="task", operation="execute",
            destination="core", status=AuthorizationStatus.ALLOWED,
        ),
    )
    execution_input = make_input(psi)
    stale_request = ExternalExecutionRequest.from_information(
        first, operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest, purpose="test"
    )
    with pytest.raises(ValueError, match="does not match information"):
        bridge.step(second, psi, transition, execution_input, stale_request)


def test_replay_request_with_same_identity_but_stale_execution_state_is_rejected():
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    transition = PsiTransition(lambda x, relations: (x + 1, relations))
    info = make_information(AuthorizationStatus.ALLOWED)
    stale_input = make_input(psi)
    changed = Psi(x=psi.x + 10, relations=psi.relations)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=stale_input.content_digest, purpose="test"
    )
    with pytest.raises(ValueError, match="state_id"):
        bridge.step(info, changed, transition, stale_input, request)


def test_network_binding_is_checked_at_authorized_execution_boundary():
    from core.evolution_contract import (
        NetworkAttachment, NetworkExecutionRequest, NetworkRegistry,
        NetworkRegistryEntry, bind_network_execution,
    )
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    info = make_information(AuthorizationStatus.ALLOWED)
    execution_input = make_input(psi)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest, purpose="test"
    )
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(NetworkRegistryEntry(attachment, "life"))
    network_request = NetworkExecutionRequest(
        "network-1", "physics", "simulate", request.authorization_digest()
    )
    binding = bind_network_execution(registry, network_request)
    transition = PsiTransition(lambda x, relations: (x + 1, relations))
    result = bridge.step(
        info, psi, transition, execution_input, request,
        network_binding=binding, allowed_capability="physics",
    )
    assert result.psi.x == 1


def test_network_binding_cannot_cross_authorization_boundary():
    from core.evolution_contract import NetworkExecutionRequest, NetworkExecutionBinding
    psi = make_psi()
    bridge = AuthorizedExecution(make_executor())
    info = make_information(AuthorizationStatus.ALLOWED)
    execution_input = make_input(psi)
    request = ExternalExecutionRequest.from_information(
        info, operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest, purpose="test"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "simulate", "foreign-auth"),
        "core-1", "attachment",
    )
    with pytest.raises(ValueError, match="authorization"):
        bridge.step(
            info, psi, PsiTransition(lambda x, relations: (x + 1, relations)),
            execution_input, request, network_binding=binding,
        )


def test_rehydrated_network_registry_binds_execution_after_restart(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkExecutionRequest, NetworkRegistry,
        NetworkRegistryEntry, NetworkRegistrySnapshot, bind_network_execution,
    )
    from core.sqlite_persistence import SQLiteHistoryStore
    path = tmp_path / "network-execution-restart.db"
    store = SQLiteHistoryStore(path)
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(NetworkRegistryEntry(attachment, "life"))
    store.save_network_registry_snapshot(
        NetworkRegistrySnapshot.from_registry("network-1", registry)
    )
    restored = SQLiteHistoryStore(path).rehydrate_network_registry("network-1")
    binding = bind_network_execution(
        restored,
        NetworkExecutionRequest("network-1", "physics", "simulate", "auth"),
    )
    assert binding.core_id == "core-1"


def test_rehydrated_detached_core_cannot_bind_execution(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistry,
        NetworkRegistryEntry, NetworkRegistrySnapshot, bind_network_execution,
    )
    from core.sqlite_persistence import SQLiteHistoryStore
    path = tmp_path / "network-execution-detached.db"
    store = SQLiteHistoryStore(path)
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(attachment, "life", NetworkAttachmentState.DETACHED)
    )
    store.save_network_registry_snapshot(
        NetworkRegistrySnapshot.from_registry("network-1", registry)
    )
    restored = SQLiteHistoryStore(path).rehydrate_network_registry("network-1")
    with pytest.raises(ValueError, match="exactly one core"):
        bind_network_execution(
            restored,
            NetworkExecutionRequest("network-1", "physics", "simulate", "auth"),
        )
