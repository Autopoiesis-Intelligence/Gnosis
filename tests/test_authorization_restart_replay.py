import pytest

from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import execution_input_from_psi
from core.external_execution_request import ExternalExecutionRequest
from core.external_operation import ExternalOperation
from core.history import AppendOnlyHistory
from core.information_contract import Authorization, AuthorizationStatus, Information
from core.recovery import recover_psi
from core.psi_transition import PsiTransition
from core.sqlite_persistence import SQLiteHistoryStore
from core.state import Psi


def make_info() -> Information:
    return Information(
        information_id="restart-info",
        source="external",
        content_reference="restart-content",
        provenance_ref="restart-provenance",
        authorization=Authorization(
            source="external",
            purpose="restart-task",
            operation="request",
            destination="core",
            status=AuthorizationStatus.ALLOWED,
        ),
        payload="restart-content",
    )


def make_request(info: Information, psi: Psi) -> ExternalExecutionRequest:
    execution_input = execution_input_from_psi(
        psi, input_type="external-information", content_digest="restart-content-digest"
    )
    return ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="restart-task",
    )


def test_authorized_request_cannot_be_replayed_after_restart(tmp_path):
    database = tmp_path / "authorization-replay.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    first_input = execution_input_from_psi(
        genesis,
        input_type="external-information",
        content_digest="restart-content-digest",
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=first_input.content_digest,
        purpose="restart-task",
    )

    first_store = SQLiteHistoryStore(database)
    first_executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="restart-test-v1",
        durable_store=first_store,
    )
    first = AuthorizedExecution(first_executor).step(
        info,
        genesis,
        PsiTransition(lambda x, relations: (x + ("first-commit",), relations)),
        first_input,
        request,
    )
    assert first.psi == Psi(x=("genesis", "first-commit"), relations=())

    # Simulated process restart: reload all durable causal evidence and derive state.
    restarted_store = SQLiteHistoryStore(database)
    recovered = recover_psi(
        genesis,
        restarted_store,
        lambda state, record: (
            Psi(x=state.x + ("first-commit",), relations=())
            if record.sequence == 0
            else state
        ),
    )
    assert recovered.state == first.psi

    # The old authorization/request is intentionally reused against a new state.
    # It must not become a second executable permission after restart.
    retry_executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="restart-test-v1",
        durable_store=restarted_store,
    )
    retry_input = execution_input_from_psi(
        recovered.state,
        input_type="external-information",
        content_digest=request.content_digest,
    )
    with pytest.raises(ValueError, match="authorization has already been consumed"):
        AuthorizedExecution(retry_executor).step(
            info,
            recovered.state,
            PsiTransition(lambda x, relations: (x + ("replayed",), relations)),
            retry_input,
            request,
        )

    durable = SQLiteHistoryStore(database)
    assert len(durable.load().records) == 1
    assert durable.load().records[0].state_hash == first.history.records[0].state_hash
    with __import__("sqlite3").connect(database) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM authorization_consumption WHERE authorization_digest = ?",
            (request.authorization_digest(),),
        ).fetchone()
    assert row[0] == 1


def test_restart_fails_closed_when_authorization_consumption_is_tampered(tmp_path):
    database = tmp_path / "authorization-tamper.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="restart-content-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="restart-task",
    )

    store = SQLiteHistoryStore(database)
    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="restart-test-v1",
        durable_store=store,
    )
    AuthorizedExecution(executor).step(
        info,
        genesis,
        PsiTransition(lambda x, relations: (x + ("first-commit",), relations)),
        execution_input,
        request,
    )

    import sqlite3
    with sqlite3.connect(database) as conn:
        conn.execute(
            "UPDATE authorization_consumption SET consumed_event = ? WHERE authorization_digest = ?",
            ("tampered-event", request.authorization_digest()),
        )
        conn.commit()

    with pytest.raises(ValueError, match="durable authorization consumption event is invalid"):
        recover_psi(
            genesis,
            SQLiteHistoryStore(database),
            lambda state, record: (
                Psi(x=state.x + ("first-commit",), relations=())
                if record.sequence == 0 else state
            ),
        )


def test_authorization_cannot_cross_state_record(tmp_path):
    database = tmp_path / "authorization-state-binding.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    alternate = Psi(x=("alternate",), relations=())
    info = make_info()
    genesis_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="restart-content-digest"
    )
    alternate_input = execution_input_from_psi(
        alternate, input_type="external-information", content_digest="restart-content-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=genesis_input.content_digest,
        purpose="restart-task",
    )

    store = SQLiteHistoryStore(database)
    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="restart-test-v1",
        durable_store=store,
    )

    AuthorizedExecution(executor).step(
        info,
        genesis,
        PsiTransition(lambda x, relations: (x + ("first-commit",), relations)),
        genesis_input,
        request,
    )

    # The same authorization must not cross records by being reused
    # against a different state after its first durable consumption.
    with pytest.raises(ValueError, match="authorization has already been consumed"):
        AuthorizedExecution(executor).step(
            info,
            alternate,
            PsiTransition(lambda x, relations: (x + ("cross-state",), relations)),
            alternate_input,
            request,
        )

    assert request.authorization_digest()
