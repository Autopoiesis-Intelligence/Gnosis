import pytest
import sqlite3

from core.history import TransitionRecord
from core.sqlite_persistence import SQLiteHistoryStore
from core.provenance import Provenance


def rec(seq, prev, state):
    return TransitionRecord(
        sequence=seq,
        previous_hash=prev,
        state_hash=state,
        kernel_version="k1",
        candidate_hash=state,
        admitted=True,
        evidence_hash="e1",
    )


def test_legacy_history_only_commit_is_fail_closed(tmp_path):
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)

    with pytest.raises(ValueError, match="history-only durable commit path is disabled"):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    assert store.load().records == ()


def test_failure_injection_cannot_reach_disabled_legacy_path(tmp_path):
    path = tmp_path / "history.db"

    def fail(point):
        if point == "before_insert":
            raise RuntimeError("injected crash")

    store = SQLiteHistoryStore(path, failure_injector=fail)
    with pytest.raises(ValueError, match="history-only durable commit path is disabled"):
        store.commit_once(rec(0, "genesis", "s0"), "current", "next")

    assert SQLiteHistoryStore(path).load().records == ()


def test_atomic_audit_commit_rolls_back_on_interrupted_transaction(tmp_path):
    path = tmp_path / "atomic.db"

    def fail(point):
        if point == "after_audit_before_commit":
            raise RuntimeError("crash before durable commit")

    store = SQLiteHistoryStore(path, failure_injector=fail)
    provenance = Provenance("s0", "e1", "k1", ("source",))
    with pytest.raises(RuntimeError, match="crash before durable commit"):
        store.commit_once_with_audit(
            rec(0, "genesis", "s0"), provenance, "current", "next"
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == ()
    assert reopened.load_audit() == ()
    assert reopened.load_provenance() == ()


@pytest.mark.parametrize(
    "failure_point",
    [
        "after_history_before_audit",
        "after_history_before_provenance",
        "after_provenance_before_audit",
        "after_authorization_before_audit",
        "after_audit_before_commit",
    ],
)
def test_atomic_commit_rolls_back_all_evidence_for_every_precommit_failure(
    tmp_path, failure_point
):
    path = tmp_path / f"atomic-{failure_point}.db"

    def fail(point):
        if point == failure_point:
            raise RuntimeError(f"injected failure at {point}")

    store = SQLiteHistoryStore(path, failure_injector=fail)
    provenance = Provenance("s0", "e1", "k1", ("source",))

    with pytest.raises(RuntimeError, match=failure_point):
        store.commit_once_with_audit(
            rec(0, "genesis", "s0"),
            provenance,
            "current",
            "next",
            authorization_digest="auth-0" if failure_point == "after_authorization_before_audit" else None,
            authorization_state_digest="genesis" if failure_point == "after_authorization_before_audit" else None,
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records == ()
    assert reopened.load_audit() == ()
    assert reopened.load_provenance() == ()
    assert reopened.load_authorization_consumption() == ()
    reopened.verify_cross_table_consistency()



def test_atomic_audit_post_commit_failure_is_recoverable_and_idempotent(tmp_path):
    path = tmp_path / "post-commit-recovery.db"
    fired = {"value": False}

    def fail(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("process stopped after durable commit")

    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="durable commit"):
        store.commit_once_with_audit(record, provenance, "current", "next")

    recovered = SQLiteHistoryStore(path)
    assert recovered.load().records == (record,)
    assert len(recovered.load_audit()) == 1
    assert recovered.load_provenance() == (provenance,)
    recovered.verify_cross_table_consistency()

    retry = recovered.commit_once_with_audit(
        record,
        provenance,
        "current-after-recovery",
        "next-after-recovery",
    )
    assert not retry.applied
    assert retry.value == "current-after-recovery"
    assert retry.history.records == (record,)
    assert len(SQLiteHistoryStore(path).load_audit()) == 1
    assert SQLiteHistoryStore(path).load_provenance() == (provenance,)


def test_atomic_audit_post_commit_failure_with_authorization_is_idempotent(tmp_path):
    path = tmp_path / "authorized-post-commit-recovery.db"
    fired = {"value": False}

    def fail(point):
        if point == "after_commit" and not fired["value"]:
            fired["value"] = True
            raise RuntimeError("process stopped after durable commit")

    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store = SQLiteHistoryStore(path, failure_injector=fail)

    with pytest.raises(RuntimeError, match="durable commit"):
        store.commit_once_with_audit(
            record,
            provenance,
            "current",
            "next",
            authorization_digest="auth-0",
            authorization_state_digest="genesis",
        )

    recovered = SQLiteHistoryStore(path)
    assert len(recovered.load().records) == 1
    assert len(recovered.load_audit()) == 1
    assert recovered.load_provenance() == (provenance,)
    assert len(recovered.load_authorization_consumption()) == 1
    recovered.verify_cross_table_consistency(initial_state_digest="genesis")

    retry = recovered.commit_once_with_audit(
        record,
        provenance,
        "current-after-recovery",
        "next-after-recovery",
        authorization_digest="auth-0",
        authorization_state_digest="genesis",
    )
    assert not retry.applied
    assert retry.value == "current-after-recovery"
    assert len(SQLiteHistoryStore(path).load().records) == 1
    assert len(SQLiteHistoryStore(path).load_audit()) == 1
    assert len(SQLiteHistoryStore(path).load_provenance()) == 1
    assert len(SQLiteHistoryStore(path).load_authorization_consumption()) == 1


def _seed_consistent_audit_store(path):
    store = SQLiteHistoryStore(path)
    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store.commit_once_with_audit(record, provenance, "current", "next")
    return record, provenance


def test_commit_fails_closed_when_history_is_tampered(tmp_path):
    path = tmp_path / "tampered-history.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE transition_history SET state_hash = ? WHERE sequence = 0",
            ("tampered-state",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable transition binding mismatch"):
        store.commit_once_with_audit(
            rec(1, "tampered-state", "s1"),
            provenance,
            "current",
            "next",
        )

    reopened = SQLiteHistoryStore(path)
    assert reopened.load().records[0].state_hash == "tampered-state"


def test_commit_fails_closed_when_provenance_is_tampered(tmp_path):
    path = tmp_path / "tampered-provenance.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 0",
            ("tampered-candidate",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable candidate binding mismatch"):
        store.commit_once_with_audit(
            rec(1, record.state_hash, "s1"),
            provenance,
            "current",
            "next",
        )


def test_commit_fails_closed_when_audit_is_tampered(tmp_path):
    path = tmp_path / "tampered-audit.db"
    record, provenance = _seed_consistent_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            ("tampered-transition",),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable audit digest mismatch"):
        store.commit_once_with_audit(
            rec(1, record.state_hash, "s1"),
            provenance,
            "current",
            "next",
        )


def _seed_two_transition_audit_store(path):
    store = SQLiteHistoryStore(path)
    first = rec(0, "genesis", "s0")
    second = rec(1, "s0", "s1")
    p0 = Provenance("s0", "e1", "k1", ("source-0",))
    p1 = Provenance("s1", "e1", "k1", ("source-1",))
    store.commit_once_with_audit(first, p0, "current", "s0")
    store.commit_once_with_audit(second, p1, "s0", "s1")
    return first, second, p0, p1


def test_commit_fails_closed_when_provenance_rows_are_cross_bound(tmp_path):
    path = tmp_path / "cross-bound-provenance.db"
    first, second, p0, p1 = _seed_two_transition_audit_store(path)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 0",
            (p1.candidate_hash,),
        )
        conn.execute(
            "UPDATE provenance_history SET candidate_hash = ? WHERE sequence = 1",
            (p0.candidate_hash,),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable candidate binding mismatch"):
        store.commit_once_with_audit(
            rec(2, "s1", "s2"),
            Provenance("s2", "e1", "k1", ("source-2",)),
            "s1",
            "s2",
        )


def test_commit_fails_closed_when_audit_rows_are_cross_bound(tmp_path):
    path = tmp_path / "cross-bound-audit.db"
    first, second, p0, p1 = _seed_two_transition_audit_store(path)

    audits = SQLiteHistoryStore(path).load_audit()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 0",
            (audits[1].transition_hash,),
        )
        conn.execute(
            "UPDATE audit_history SET transition_hash = ? WHERE sequence = 1",
            (audits[0].transition_hash,),
        )
        conn.commit()

    store = SQLiteHistoryStore(path)
    with pytest.raises(ValueError, match="durable audit digest mismatch"):
        store.commit_once_with_audit(
            rec(2, "s1", "s2"),
            Provenance("s2", "e1", "k1", ("source-2",)),
            "s1",
            "s2",
        )


def test_commit_fails_closed_when_authorization_rows_are_cross_bound(tmp_path):
    path = tmp_path / "cross-bound-authorization.db"
    store = SQLiteHistoryStore(path)

    first = rec(0, "genesis", "s0")
    second = rec(1, "s0", "s1")
    p0 = Provenance("s0", "e1", "k1", ("source-0",))
    p1 = Provenance("s1", "e1", "k1", ("source-1",))

    store.commit_once_with_audit(
        first, p0, "current", "s0",
        authorization_digest="auth-0",
        authorization_state_digest="genesis",
    )
    store.commit_once_with_audit(
        second, p1, "s0", "s1",
        authorization_digest="auth-1",
        authorization_state_digest="s0",
    )

    with sqlite3.connect(path) as conn:
        conn.execute(
            """UPDATE authorization_consumption
               SET state_digest = CASE sequence
                   WHEN 0 THEN 's0'
                   WHEN 1 THEN 'genesis'
               END,
               candidate_hash = CASE sequence
                   WHEN 0 THEN 's1'
                   WHEN 1 THEN 's0'
               END"""
        )
        conn.commit()

    with pytest.raises(ValueError, match="durable authorization candidate binding mismatch"):
        SQLiteHistoryStore(path).commit_once_with_audit(
            rec(2, "s1", "s2"),
            Provenance("s2", "e1", "k1", ("source-2",)),
            "s1",
            "s2",
        )


def test_authorization_consumption_cannot_be_replayed_across_transitions(tmp_path):
    path = tmp_path / "authorization-replay.db"
    store = SQLiteHistoryStore(path)

    first = rec(0, "genesis", "s0")
    second = rec(1, "s0", "s1")
    p0 = Provenance("s0", "e1", "k1", ("source-0",))
    p1 = Provenance("s1", "e1", "k1", ("source-1",))

    store.commit_once_with_audit(
        first, p0, "current", "s0",
        authorization_digest="auth-replay",
        authorization_state_digest="genesis",
    )

    with pytest.raises(ValueError, match="authorization has already been consumed"):
        store.commit_once_with_audit(
            second, p1, "s0", "s1",
            authorization_digest="auth-replay",
            authorization_state_digest="s0",
        )


def test_commit_fails_closed_when_genesis_authorization_state_is_tampered(tmp_path):
    path = tmp_path / "tampered-genesis-authorization.db"
    store = SQLiteHistoryStore(path)
    first = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source-0",))
    store.commit_once_with_audit(
        first, provenance, "current", "s0",
        authorization_digest="auth-genesis",
        authorization_state_digest="genesis",
    )

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE authorization_consumption SET state_digest = ? WHERE sequence = 0",
            ("tampered-genesis",),
        )
        conn.commit()

    with pytest.raises(ValueError, match="durable authorization state binding mismatch"):
        SQLiteHistoryStore(path).commit_once_with_audit(
            rec(1, "s0", "s1"),
            Provenance("s1", "e1", "k1", ("source-1",)),
            "s0",
            "s1",
        )


def test_kernel_execution_provenance_survives_restart(tmp_path):
    path = tmp_path / "kernel-provenance.db"
    record = TransitionRecord(
        sequence=0,
        previous_hash="genesis",
        state_hash="s0",
        kernel_version="k1",
        candidate_hash="s0",
        admitted=True,
        evidence_hash="e1",
        kernel_execution_identity="exec-id-1",
        evidence_binding_digest="binding-1",
    )
    provenance = Provenance("s0", "e1", "k1", ("source",))
    SQLiteHistoryStore(path).commit_once_with_audit(record, provenance, "current", "next")

    reopened = SQLiteHistoryStore(path)
    recovered = reopened.load().records
    assert recovered == (record,)
    assert recovered[0].kernel_execution_identity == "exec-id-1"
    assert recovered[0].evidence_binding_digest == "binding-1"
    reopened.verify_cross_table_consistency()


def test_tampering_kernel_execution_identity_breaks_durable_audit(tmp_path):
    path = tmp_path / "tamper-kernel-identity.db"
    record = TransitionRecord(
        sequence=0,
        previous_hash="genesis",
        state_hash="s0",
        kernel_version="k1",
        candidate_hash="s0",
        admitted=True,
        evidence_hash="e1",
        kernel_execution_identity="exec-id-1",
        evidence_binding_digest="binding-1",
    )
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(record, provenance, "current", "next")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE transition_history SET kernel_execution_identity = ? WHERE sequence = 0",
            ("tampered",),
        )
        conn.commit()
    with pytest.raises(ValueError, match="durable transition binding mismatch"):
        SQLiteHistoryStore(path).verify_cross_table_consistency()


def test_evolution_commit_rolls_back_outcome_when_transaction_fails(tmp_path):
    path = tmp_path / "evolution-atomic-failure.db"
    store = SQLiteHistoryStore(path)
    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    from core.history import EvolutionOutcomeRecord
    outcome = EvolutionOutcomeRecord(
        0, "", "outcome-0", "patch-0", "genesis", "s0",
        "commit", "evidence-0",
    )
    store.failure_injector = lambda point: (_ for _ in ()).throw(RuntimeError("injected failure")) if point == "after_audit_before_commit" else None
    with pytest.raises(RuntimeError, match="injected failure"):
        store.commit_evolution_with_audit(
            record, provenance, outcome, "current", "s0"
        )
    assert store.load().records == ()
    assert store.load_evolution_outcomes().records == ()


def test_evolution_commit_persists_outcome_and_state_together(tmp_path):
    path = tmp_path / "evolution-atomic-success.db"
    store = SQLiteHistoryStore(path)
    record = rec(0, "genesis", "s0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    from core.history import EvolutionOutcomeRecord
    outcome = EvolutionOutcomeRecord(
        0, "", "outcome-0", "patch-0", "genesis", "s0",
        "commit", "evidence-0",
    )
    result = store.commit_evolution_with_audit(
        record, provenance, outcome, "current", "s0"
    )
    assert result.committed
    assert len(store.load().records) == 1
    assert store.load_evolution_outcomes().head == outcome


def test_evolution_replay_integrity_after_restart(tmp_path):
    path = tmp_path / "evolution-replay.db"
    store = SQLiteHistoryStore(path)
    from core.history import EvolutionOutcomeRecord
    outcome = EvolutionOutcomeRecord(0, "", "outcome-0", "patch-0", "genesis", "s0", "commit", "evidence-0")
    record = TransitionRecord(0, "genesis", "s0", "k1", "s0", True, "e1", evolution_evaluation_digest="outcome-0")
    provenance = Provenance("s0", "e1", "k1", ("source",))
    store.commit_evolution_with_audit(record, provenance, outcome, "current", "s0")
    reopened = SQLiteHistoryStore(path)
    reopened.verify_evolution_outcomes()
    reopened.verify_evolution_cross_table_consistency()
    assert reopened.load_evolution_outcomes().head == outcome


def test_network_registry_snapshot_persists_and_excludes_no_entries_from_other_networks(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistry,
        NetworkRegistryEntry, NetworkRegistrySnapshot,
    )
    path = tmp_path / "network-registry.db"
    store = SQLiteHistoryStore(path)
    a1 = NetworkAttachment("core-1", "network-1", "physics", "attach-1")
    a2 = NetworkAttachment("core-2", "network-2", "physics", "attach-2")
    registry = NetworkRegistry().register(NetworkRegistryEntry(a1, "life-1"))
    registry = registry.register(NetworkRegistryEntry(a2, "life-2", NetworkAttachmentState.REVOKED))
    snapshot = NetworkRegistrySnapshot.from_registry("network-1", registry)
    store.save_network_registry_snapshot(snapshot)
    reopened = SQLiteHistoryStore(path)
    row = reopened.load_network_registry_snapshot("network-1")
    assert row is not None
    assert row[0] == snapshot.snapshot_digest


def test_network_registry_rehydrates_after_restart(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistry,
        NetworkRegistryEntry, NetworkRegistrySnapshot,
    )
    path = tmp_path / "network-rehydrate.db"
    store = SQLiteHistoryStore(path)
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(
        NetworkRegistryEntry(attachment, "life", NetworkAttachmentState.ATTACHED)
    )
    snapshot = NetworkRegistrySnapshot.from_registry("network-1", registry)
    store.save_network_registry_snapshot(snapshot)
    reopened = SQLiteHistoryStore(path)
    restored = reopened.rehydrate_network_registry("network-1")
    assert restored.require_unique_route("network-1", "physics").attachment.core_id == "core-1"


def test_network_registry_rehydrate_fails_on_digest_tampering(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkRegistry, NetworkRegistryEntry,
        NetworkRegistrySnapshot,
    )
    path = tmp_path / "network-rehydrate-tamper.db"
    store = SQLiteHistoryStore(path)
    attachment = NetworkAttachment("core-1", "network-1", "physics", "attach")
    registry = NetworkRegistry().register(NetworkRegistryEntry(attachment, "life"))
    snapshot = NetworkRegistrySnapshot.from_registry("network-1", registry)
    store.save_network_registry_snapshot(snapshot)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE network_registry_snapshots SET payload = ? WHERE network_id = ?",
            (repr((("core-tampered", "network-1", "physics", "attach", "attached", "life"),)), "network-1")
        )
        conn.commit()
    with pytest.raises(ValueError, match="digest mismatch"):
        SQLiteHistoryStore(path).rehydrate_network_registry("network-1")


def test_capability_transition_history_survives_restart(tmp_path):
    from core.evolution_contract import (
        AuthorizedCapabilityTransition, CapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    path = tmp_path / "capability-history.db"
    transition = CapabilityTransition(
        "core-1", "network-1", "physics", "simulation",
        "evidence-1", "auth-1",
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth-1"),
        "core-1", "attachment-1",
    )
    authorized = AuthorizedCapabilityTransition(transition, binding)
    SQLiteHistoryStore(path).persist_capability_transition(authorized)
    history = SQLiteHistoryStore(path).load_capability_transitions(
        "core-1", "network-1"
    )
    assert history == [(
        "core-1", "network-1", "physics", "simulation",
        "evidence-1", "auth-1", "attachment-1",
    )]


def test_capability_transition_and_registry_state_commit_together(tmp_path):
    from core.evolution_contract import (
        AuthorizedCapabilityTransition, CapabilityTransition,
        NetworkAttachment, NetworkAttachmentState, NetworkExecutionBinding,
        NetworkExecutionRequest, NetworkRegistryEntry,
        transition_core_capability,
    )
    path = tmp_path / "capability-atomic.db"
    previous = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    next_entry, transition = transition_core_capability(
        previous, "simulation", "evidence", "auth"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth"),
        "core-1", previous.attachment.digest(),
    )
    authorized = AuthorizedCapabilityTransition(transition, binding)
    SQLiteHistoryStore(path).commit_capability_transition_atomically(
        authorized, previous, next_entry
    )
    store = SQLiteHistoryStore(path)
    history = store.load_capability_transitions("core-1", "network-1")
    assert history[0][2:4] == ("physics", "simulation")
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT capability_scope, attachment_state FROM network_registry_state "
            "WHERE network_id = ? AND core_id = ?", ("network-1", "core-1")
        ).fetchone()
    assert row == ("simulation", "attached")


def test_recover_network_capability_uses_latest_transition(tmp_path):
    from core.evolution_contract import (
        NetworkAttachmentState, NetworkAttachment, NetworkRegistryEntry,
        CapabilityTransition, AuthorizedCapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    path = tmp_path / "capability-recovery.db"
    store = SQLiteHistoryStore(path)
    previous = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    from core.evolution_contract import transition_core_capability
    next_entry, transition = transition_core_capability(
        previous, "simulation", "evidence", "auth"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth"),
        "core-1", previous.attachment.digest(),
    )
    store.commit_capability_transition_atomically(
        AuthorizedCapabilityTransition(transition, binding), previous, next_entry
    )
    restored = SQLiteHistoryStore(path).recover_network_capability_state(
        "core-1", "network-1"
    )
    assert restored.attachment.capability_scope == "simulation"


def test_recover_network_capability_fails_closed_on_history_divergence(tmp_path):
    from core.evolution_contract import (
        NetworkAttachmentState, NetworkAttachment, NetworkRegistryEntry,
        CapabilityTransition, AuthorizedCapabilityTransition,
        NetworkExecutionBinding, NetworkExecutionRequest,
    )
    path = tmp_path / "capability-recovery-tamper.db"
    store = SQLiteHistoryStore(path)
    previous = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    from core.evolution_contract import transition_core_capability
    next_entry, transition = transition_core_capability(
        previous, "simulation", "evidence", "auth"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth"),
        "core-1", previous.attachment.digest(),
    )
    store.commit_capability_transition_atomically(
        AuthorizedCapabilityTransition(transition, binding), previous, next_entry
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE network_registry_state SET capability_scope = ? "
            "WHERE network_id = ? AND core_id = ?",
            ("tampered", "network-1", "core-1"),
        )
        conn.commit()
    with pytest.raises(ValueError, match="diverges"):
        SQLiteHistoryStore(path).recover_network_capability_state(
            "core-1", "network-1"
        )


def test_rehydrate_network_registry_from_durable_state_rebuilds_active_routes(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistryEntry,
        AuthorizedCapabilityTransition, NetworkExecutionBinding,
        NetworkExecutionRequest, transition_core_capability,
    )
    path = tmp_path / "network-state-rebuild.db"
    previous = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "physics", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    next_entry, transition = transition_core_capability(
        previous, "simulation", "evidence", "auth"
    )
    binding = NetworkExecutionBinding(
        NetworkExecutionRequest("network-1", "physics", "evolve", "auth"),
        "core-1", previous.attachment.digest(),
    )
    SQLiteHistoryStore(path).commit_capability_transition_atomically(
        AuthorizedCapabilityTransition(transition, binding), previous, next_entry
    )
    snapshot, active = SQLiteHistoryStore(path).rehydrate_network_registry_from_state(
        "network-1"
    )
    assert snapshot.network_id == "network-1"
    assert len(active) == 1
    assert active[0].attachment.capability_scope == "simulation"


def test_rehydrate_network_registry_excludes_detached_state(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState,
        NetworkRegistryEntry, NetworkRegistrySnapshot,
    )
    path = tmp_path / "network-state-detached.db"
    store = SQLiteHistoryStore(path)
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE network_registry_state (
            network_id TEXT NOT NULL, core_id TEXT NOT NULL,
            capability_scope TEXT NOT NULL, attachment_state TEXT NOT NULL,
            attachment_evidence_digest TEXT NOT NULL,
            lifecycle_evidence_digest TEXT NOT NULL,
            PRIMARY KEY (network_id, core_id))""")
        conn.execute(
            "INSERT INTO network_registry_state VALUES (?, ?, ?, ?, ?, ?)",
            ("network-1", "core-1", "physics", "detached", "attach", "life"),
        )
        conn.commit()
    snapshot, active = store.rehydrate_network_registry_from_state("network-1")
    assert len(snapshot.entries) == 1
    assert active == ()


def test_rehydrated_active_route_can_bind_execution_directly(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistryEntry,
        AuthorizedCapabilityTransition, NetworkExecutionBinding,
        NetworkExecutionRequest, transition_core_capability,
    )
    path = tmp_path / "rehydrated-dispatch.db"
    previous = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "simulation", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    from core.evolution_contract import NetworkRegistrySnapshot
    store = SQLiteHistoryStore(path)
    snapshot = NetworkRegistrySnapshot.from_registry(
        "network-1",
        __import__("core.evolution_contract", fromlist=["NetworkRegistry"]).NetworkRegistry((previous,))
    )
    store.save_network_registry_snapshot(snapshot)
    binding = store.bind_rehydrated_network_execution(
        "network-1", "simulation", "simulate", "auth"
    )
    assert binding.core_id == "core-1"


def test_rehydrated_dispatch_rejects_missing_capability(tmp_path):
    from core.evolution_contract import (
        NetworkAttachment, NetworkAttachmentState, NetworkRegistry,
        NetworkRegistryEntry, NetworkRegistrySnapshot,
    )
    path = tmp_path / "rehydrated-dispatch-missing.db"
    entry = NetworkRegistryEntry(
        NetworkAttachment("core-1", "network-1", "simulation", "attach"),
        "life", NetworkAttachmentState.ATTACHED,
    )
    store = SQLiteHistoryStore(path)
    store.save_network_registry_snapshot(
        NetworkRegistrySnapshot.from_registry(
            "network-1", NetworkRegistry((entry,))
        )
    )
    with pytest.raises(ValueError, match="exactly one core"):
        store.bind_rehydrated_network_execution(
            "network-1", "chemistry", "simulate", "auth"
        )


def test_core_creation_lifecycle_survives_restart(tmp_path):
    from core.evolution_contract import (
        CoreCreationLifecycle, CoreCreationReason, CoreLifecycle,
        CoreLifecycleRecord, EvolutionNeedSignal, NetworkRegistry,
        core_creation_proposal_from_resolution, resolve_need_against_network,
        advance_core_creation_lifecycle,
    )
    path = tmp_path / "core-lifecycle.db"
    signal = EvolutionNeedSignal(
        "need-durable", "parent", "state", "chemistry",
        "analytics", "evidence", "research",
    )
    resolution = resolve_need_against_network(
        signal, "network-1", "chemistry", NetworkRegistry()
    )
    proposal = core_creation_proposal_from_resolution(
        signal, resolution, "request-durable",
        CoreCreationReason.MISSING_CAPABILITY, "network-1", "auth"
    )
    lifecycle = CoreCreationLifecycle(
        proposal,
        CoreLifecycleRecord(
            "core-new", "parent", CoreLifecycle.PROPOSED,
            "network-1", "proposal-evidence"
        ),
    )
    authorized = advance_core_creation_lifecycle(
        lifecycle, CoreLifecycle.AUTHORIZED, "authorization-evidence"
    )
    store = SQLiteHistoryStore(path)
    store.persist_core_lifecycle(authorized)
    restored = SQLiteHistoryStore(path).load_core_lifecycle("core-new")
    assert restored.need_digest == signal.digest()
    assert restored.record.state is CoreLifecycle.AUTHORIZED
    assert restored.proposal.authorization_digest == "auth"


def test_core_admission_survives_restart_with_scope(tmp_path):
    from core.evolution_contract import CoreAdmission, CoreOrigin
    path = tmp_path / "admission.db"
    admission = CoreAdmission(
        "external-1", CoreOrigin.EXTERNAL, "network-1",
        "physics", "owner-scoped", "auth-1", "verify-1",
    )
    store = SQLiteHistoryStore(path)
    store.persist_core_admission(admission)
    restored = SQLiteHistoryStore(path).load_core_admission("external-1")
    assert restored[0] == admission
    assert restored[1] == "active"


def test_revoked_core_admission_stays_revoked_after_restart(tmp_path):
    from core.evolution_contract import CoreAdmission, CoreOrigin
    path = tmp_path / "revoked-admission.db"
    admission = CoreAdmission(
        "external-2", CoreOrigin.EXTERNAL, "network-1",
        "physics", "owner-scoped", "auth-2", "verify-2",
    )
    store = SQLiteHistoryStore(path)
    store.persist_core_admission(admission)
    store.revoke_core_admission("external-2")
    restored = SQLiteHistoryStore(path).load_core_admission("external-2")
    assert restored[1] == "revoked"


def test_revoked_external_core_cannot_receive_network_binding(tmp_path):
    from core.evolution_contract import CoreAdmission, CoreOrigin
    path = tmp_path / "admission-routing.db"
    store = SQLiteHistoryStore(path)
    store.persist_core_admission(CoreAdmission(
        "external-route", CoreOrigin.EXTERNAL, "network-1",
        "physics", "owner-scoped", "auth", "verify",
    ))
    store.revoke_core_admission("external-route")
    with pytest.raises(ValueError, match="exactly one active admitted core"):
        store.bind_admitted_network_execution(
            "network-1", "physics", "simulate", "auth"
        )


def test_active_admitted_core_can_receive_network_binding(tmp_path):
    from core.evolution_contract import (
        CoreAdmission, CoreOrigin, NetworkAttachment,
        NetworkAttachmentState, NetworkRegistry, NetworkRegistryEntry,
        NetworkRegistrySnapshot,
    )
    path = tmp_path / "admission-routing-active.db"
    store = SQLiteHistoryStore(path)
    store.persist_core_admission(CoreAdmission(
        "external-route-active", CoreOrigin.EXTERNAL, "network-1",
        "physics", "owner-scoped", "auth", "verify",
    ))
    store.save_network_registry_snapshot(NetworkRegistrySnapshot.from_registry(
        "network-1",
        NetworkRegistry().register(NetworkRegistryEntry(
            NetworkAttachment(
                "external-route-active", "network-1", "physics", "attach"
            ),
            "life", NetworkAttachmentState.ATTACHED,
        ))
    ))
    binding = store.bind_admitted_network_execution(
        "network-1", "physics", "simulate", "auth"
    )
    assert binding.core_id == "external-route-active"


def test_opportunity_scope_survives_restart(tmp_path):
    from core.evolution_contract import CoreOrigin, OpportunityScope
    path = tmp_path / "opportunity.db"
    scope = OpportunityScope(
        "opp-durable", "client-1", "partner-1", "network-1", "materials",
        frozenset({"physics", "chemistry"}),
        frozenset({"owner-scoped"}),
        frozenset({CoreOrigin.EXTERNAL, CoreOrigin.DERIVED}),
    )
    store = SQLiteHistoryStore(path)
    store.persist_opportunity_scope(scope)
    restored = SQLiteHistoryStore(path).load_opportunity_scope("opp-durable")
    assert restored == scope
