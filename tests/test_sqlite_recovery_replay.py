import pytest

from core.execution_contract import state_digest
from core.history import TransitionRecord
from core.replay import replay
from core.sqlite_persistence import SQLiteHistoryStore
from core.provenance import Provenance
from core.state import Psi


def record(sequence, previous_hash, state):
    digest = state_digest(state)
    return TransitionRecord(
        sequence=sequence,
        previous_hash=previous_hash,
        state_hash=digest,
        kernel_version="k1",
        candidate_hash=digest,
        admitted=True,
        evidence_hash="e1",
    )


def test_crash_recover_replay_continue(tmp_path):
    path = tmp_path / "history.db"
    genesis = Psi(x=("g",), relations=())
    state0 = Psi(x=("g", "s0"), relations=())
    state1 = Psi(x=("g", "s0", "s1"), relations=())

    first = record(0, "genesis", state0)
    second = record(1, state_digest(state0), state1)

    store = SQLiteHistoryStore(path)

    def fail(point):
        if point == "after_commit":
            raise RuntimeError("simulated process stop")

    crashing_store = SQLiteHistoryStore(path, failure_injector=fail)
    with pytest.raises(RuntimeError, match="process stop"):
        crashing_store.commit_once_with_audit(
            first,
            Provenance(state_digest(state0), "e1", "k1"),
            genesis,
            state0,
        )

    recovered = SQLiteHistoryStore(path)
    durable = recovered.load()

    replayed = replay(
        genesis,
        durable,
        lambda state, rec: state0 if rec.sequence == 0 else state1,
    )
    assert replayed.state == state0
    assert replayed.applied == 1

    continued = recovered.commit_once_with_audit(
        second,
        Provenance(state_digest(state1), "e1", "k1"),
        state0,
        state1,
    )
    assert continued.applied

    final_history = SQLiteHistoryStore(path).load()
    final_replay = replay(
        genesis,
        final_history,
        lambda state, rec: state0 if rec.sequence == 0 else state1,
    )

    assert final_replay.state == state1
    assert final_replay.applied == 2


def test_recovery_rejects_durable_state_hash_mismatch(tmp_path):
    path = tmp_path / "history.db"
    genesis = Psi(x=("g",), relations=())
    valid = Psi(x=("g", "valid"), relations=())
    tampered = Psi(x=("g", "tampered"), relations=())

    store = SQLiteHistoryStore(path)
    store.commit_once_with_audit(
        record(0, "genesis", valid),
        Provenance(state_digest(valid), "e1", "k1"),
        genesis,
        valid,
    )

    with pytest.raises(ValueError, match="state_hash"):
        replay(
            genesis,
            store.load(),
            lambda state, rec: tampered,
        )
