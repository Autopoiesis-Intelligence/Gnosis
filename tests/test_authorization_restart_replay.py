import pytest

from core.authorized_execution import AuthorizedExecution
from core.execution import CanonicalExecutor
from core.execution_contract import execution_input_from_psi, state_digest
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
    info = make_info()
    genesis_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="restart-content-digest"
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

    first = AuthorizedExecution(executor).step(
        info,
        genesis,
        PsiTransition(lambda x, relations: (x + ("first-commit",), relations)),
        genesis_input,
        request,
    )
    alternate = first.psi
    alternate_input = execution_input_from_psi(
        alternate, input_type="external-information", content_digest=request.content_digest
    )

    # The same authorization must not cross records by being reused
    # against the recovered/current successor state.
    with pytest.raises(ValueError, match="authorization has already been consumed"):
        AuthorizedExecution(executor).step(
            info,
            alternate,
            PsiTransition(lambda x, relations: (x + ("cross-state",), relations)),
            alternate_input,
            request,
        )

    assert len(SQLiteHistoryStore(database).load().records) == 1

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


def test_restart_rejects_authorization_with_tampered_state_binding(tmp_path):
    database = tmp_path / "authorization-state-binding-tamper.sqlite"
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
            "UPDATE authorization_consumption SET state_digest = ? WHERE authorization_digest = ?",
            ("forged-state-digest", request.authorization_digest()),
        )
        conn.commit()

    with pytest.raises(ValueError, match="durable authorization state binding mismatch"):
        SQLiteHistoryStore(database).verify_cross_table_consistency(initial_state_digest=state_digest(genesis))


def _assert_no_durable_commit(database, authorization_digest):
    durable = SQLiteHistoryStore(database)
    assert len(durable.load().records) == 0
    assert durable.load_authorization_consumption() == ()
    assert durable.load_audit() == ()
    assert durable.load_provenance() == ()
    durable.assert_authorization_unused(authorization_digest)


@pytest.mark.parametrize(
    "failure_point",
    [
        "before_transaction",
        "before_insert",
        "after_history_before_audit",
        "after_history_before_provenance",
        "after_provenance_before_audit",
        "after_authorization_before_audit",
        "after_audit_before_commit",
    ],
)
def test_authorized_commit_rolls_back_as_one_durable_unit(tmp_path, failure_point):
    database = tmp_path / f"authorization-atomicity-{failure_point}.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="atomicity-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="restart-task",
    )

    def fail(point):
        if point == failure_point:
            raise RuntimeError(f"injected failure: {point}")

    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="atomicity-matrix-v1",
        durable_store=SQLiteHistoryStore(database, failure_injector=fail),
    )

    with pytest.raises(RuntimeError, match="injected failure"):
        AuthorizedExecution(executor).step(
            info,
            genesis,
            PsiTransition(lambda x, relations: (x + ("must-rollback",), relations)),
            execution_input,
            request,
        )

    _assert_no_durable_commit(database, request.authorization_digest())


def test_authorized_commit_failure_rolls_back_consumption_and_transition(tmp_path):
    database = tmp_path / "authorization-atomicity.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="atomicity-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="restart-task",
    )

    def fail(point):
        if point == "after_authorization_before_audit":
            raise RuntimeError("injected atomicity failure")

    store = SQLiteHistoryStore(database, failure_injector=fail)
    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="atomicity-v1",
        durable_store=store,
    )

    with pytest.raises(RuntimeError, match="atomicity failure"):
        AuthorizedExecution(executor).step(
            info,
            genesis,
            PsiTransition(lambda x, relations: (x + ("must-rollback",), relations)),
            execution_input,
            request,
        )

    durable = SQLiteHistoryStore(database)
    assert len(durable.load().records) == 0
    assert durable.load_authorization_consumption() == ()
    assert durable.load_audit() == ()
    assert durable.load_provenance() == ()
    durable.assert_authorization_unused(request.authorization_digest())




def test_post_commit_failure_then_restart_recovers_and_rejects_replay(tmp_path):
    database = tmp_path / "authorization-post-commit-restart.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="post-commit-restart-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="post-commit-restart-task",
    )

    def fail(point):
        if point == "after_commit":
            raise RuntimeError("injected post-commit failure")

    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="post-commit-restart-v1",
        durable_store=SQLiteHistoryStore(database, failure_injector=fail),
    )
    with pytest.raises(RuntimeError, match="injected post-commit failure"):
        AuthorizedExecution(executor).step(
            info, genesis,
            PsiTransition(lambda x, relations: (x + ("committed",), relations)),
            execution_input, request,
        )

    recovered = recover_psi(
        genesis,
        SQLiteHistoryStore(database),
        lambda state, record: Psi(x=state.x + ("committed",), relations=state.relations),
    )
    assert recovered.state.x == ("genesis", "committed")

    restarted = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="post-commit-restart-v1",
        durable_store=SQLiteHistoryStore(database),
    )
    with pytest.raises(ValueError, match="already been consumed"):
        AuthorizedExecution(restarted).step(
            info, genesis,
            PsiTransition(lambda x, relations: (x + ("replay",), relations)),
            execution_input, request,
        )
def test_authorized_commit_after_commit_failure_is_durable(tmp_path):
    database = tmp_path / "authorization-after-commit.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="after-commit-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="after-commit-task",
    )

    def fail(point):
        if point == "after_commit":
            raise RuntimeError("injected post-commit failure")

    executor = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="after-commit-v1",
        durable_store=SQLiteHistoryStore(database, failure_injector=fail),
    )

    with pytest.raises(RuntimeError, match="injected post-commit failure"):
        AuthorizedExecution(executor).step(
            info,
            genesis,
            PsiTransition(lambda x, relations: (x + ("committed",), relations)),
            execution_input,
            request,
        )

    durable = SQLiteHistoryStore(database)
    assert len(durable.load().records) == 1
    assert len(durable.load_authorization_consumption()) == 1
    assert len(durable.load_audit()) == 1
    assert len(durable.load_provenance()) == 1
    durable.verify_cross_table_consistency(initial_state_digest=state_digest(genesis))
    with pytest.raises(ValueError, match="already been consumed"):
        durable.assert_authorization_unused(request.authorization_digest())


@pytest.mark.parametrize(
    "tamper_sql, expected",
    [
        (
            "UPDATE authorization_consumption SET candidate_hash = ? WHERE authorization_digest = ?",
            "durable authorization candidate binding mismatch",
        ),
        (
            "UPDATE authorization_consumption SET state_digest = ? WHERE authorization_digest = ?",
            "durable authorization state binding mismatch",
        ),
    ],
)
def test_restart_fails_closed_on_tampered_authorization_binding(tmp_path, tamper_sql, expected):
    database = tmp_path / "authorization-binding-tamper.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="tamper-binding-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="tamper-binding",
    )
    store = SQLiteHistoryStore(database)
    AuthorizedExecution(
        CanonicalExecutor(
            history=AppendOnlyHistory(),
            kernel_version="tamper-binding-v1",
            durable_store=store,
        )
    ).step(
        info, genesis,
        PsiTransition(lambda x, relations: (x + ("committed",), relations)),
        execution_input, request,
    )

    import sqlite3
    with sqlite3.connect(database) as conn:
        conn.execute(tamper_sql, ("forged-binding", request.authorization_digest()))
        conn.commit()

    with pytest.raises(ValueError, match=expected):
        recover_psi(
            genesis,
            SQLiteHistoryStore(database),
            lambda state, record: Psi(
                x=state.x + ("committed",), relations=state.relations
            ),
        )


@pytest.mark.parametrize(
    "tamper_sql",
    [
        "UPDATE transition_history SET candidate_hash = ? WHERE sequence = 0",
        "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 0",
        "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
    ],
)
def test_restart_fails_closed_on_tampered_durable_evidence(tmp_path, tamper_sql):
    database = tmp_path / "durable-evidence-tamper.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="tamper-evidence-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="tamper-evidence",
    )
    AuthorizedExecution(
        CanonicalExecutor(
            history=AppendOnlyHistory(),
            kernel_version="tamper-evidence-v1",
            durable_store=SQLiteHistoryStore(database),
        )
    ).step(
        info, genesis,
        PsiTransition(lambda x, relations: (x + ("committed",), relations)),
        execution_input, request,
    )
    import sqlite3
    with sqlite3.connect(database) as conn:
        conn.execute(tamper_sql, ("forged-evidence",))
        conn.commit()

    with pytest.raises(ValueError):
        recover_psi(
            genesis,
            SQLiteHistoryStore(database),
            lambda state, record: Psi(
                x=state.x + ("committed",), relations=state.relations
            ),
        )


def test_recovery_is_observational_and_does_not_create_or_consume_authority(tmp_path):
    database = tmp_path / "recovery-observational.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    store = SQLiteHistoryStore(database)
    before = (
        store.load().records,
        store.load_provenance(),
        store.load_audit(),
        store.load_authorization_consumption(),
    )

    result = recover_psi(
        genesis,
        store,
        lambda state, record: Psi(x=state.x, relations=state.relations),
    )

    assert result.state == genesis
    after = (
        store.load().records,
        store.load_provenance(),
        store.load_audit(),
        store.load_authorization_consumption(),
    )
    assert after == before


def test_end_to_end_restart_tamper_replay_fails_closed(tmp_path):
    database = tmp_path / "restart-tamper-replay.sqlite"
    genesis = Psi(x=("genesis",), relations=())
    info = make_info()
    execution_input = execution_input_from_psi(
        genesis, input_type="external-information", content_digest="e2e-replay-digest"
    )
    request = ExternalExecutionRequest.from_information(
        info,
        operation=ExternalOperation.REQUEST,
        content_digest=execution_input.content_digest,
        purpose="e2e-replay",
    )
    AuthorizedExecution(
        CanonicalExecutor(
            history=AppendOnlyHistory(),
            kernel_version="e2e-v1",
            durable_store=SQLiteHistoryStore(database),
        )
    ).step(
        info, genesis,
        PsiTransition(lambda x, relations: (x + ("committed",), relations)),
        execution_input, request,
    )

    import sqlite3
    with sqlite3.connect(database) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            ("forged-transition",),
        )
        conn.commit()

    with pytest.raises(ValueError):
        recover_psi(
            genesis,
            SQLiteHistoryStore(database),
            lambda state, record: Psi(
                x=state.x + ("committed",), relations=state.relations
            ),
        )

    # Repair the evidence, restart, then the original authorization must still be rejected.
    with sqlite3.connect(database) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            (transition_digest(SQLiteHistoryStore(database).load().records[0]),),
        )
        conn.commit()

    recovered = recover_psi(
        genesis,
        SQLiteHistoryStore(database),
        lambda state, record: Psi(
            x=state.x + ("committed",), relations=state.relations
        ),
    )
    assert recovered.state.x == ("genesis", "committed")

    restarted = CanonicalExecutor(
        history=AppendOnlyHistory(),
        kernel_version="e2e-v1",
        durable_store=SQLiteHistoryStore(database),
    )
    with pytest.raises(ValueError, match="already been consumed"):
        AuthorizedExecution(restarted).step(
            info, genesis,
            PsiTransition(lambda x, relations: (x + ("replay",), relations)),
            execution_input, request,
        )
