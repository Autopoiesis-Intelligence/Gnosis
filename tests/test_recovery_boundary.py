import pytest

from core.history import AppendOnlyHistory, TransitionRecord
from core.recovery import recover_psi
from core.replay import replay
from core.execution_contract import state_digest
from core.provenance import Provenance
from core.sqlite_persistence import SQLiteHistoryStore
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
        evidence_hash="evidence-0",
    )


def test_replay_rejects_non_genesis_previous_hash():
    genesis = Psi(x=("g",), relations=())
    state = Psi(x=("g", "s0"), relations=())
    history = AppendOnlyHistory().append(record(0, "tampered", state))

    with pytest.raises(ValueError, match="genesis"):
        replay(genesis, history, lambda _state, _record: state)


def test_recovery_loads_durable_history_then_derives_state(tmp_path):
    genesis = Psi(x=("g",), relations=())
    state = Psi(x=("g", "s0"), relations=())
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)
    rec = record(0, "genesis", state)
    proof = Provenance(candidate_hash=rec.candidate_hash, evidence_hash=rec.evidence_hash, kernel_version=rec.kernel_version)
    store.commit_once_with_audit(rec, proof, genesis, state)

    result = recover_psi(
        genesis,
        SQLiteHistoryStore(path),
        lambda _state, _record: state,
    )

    assert result.state == state
    assert result.applied == 1


def test_recovery_fails_closed_on_tampered_durable_chain(tmp_path):
    genesis = Psi(x=("g",), relations=())
    state = Psi(x=("g", "s0"), relations=())
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)
    rec = record(0, "genesis", state)
    proof = Provenance(candidate_hash=rec.candidate_hash, evidence_hash=rec.evidence_hash, kernel_version=rec.kernel_version)
    store.commit_once_with_audit(rec, proof, genesis, state)

    import sqlite3
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE transition_history SET previous_hash = ? WHERE sequence = 0",
            ("tampered",),
        )
        conn.commit()

    with pytest.raises(ValueError, match="transition binding mismatch"):
        recover_psi(
            genesis,
            SQLiteHistoryStore(path),
            lambda _state, _record: state,
        )


def test_recovered_state_cannot_bypass_canonical_commit_boundary(tmp_path):
    genesis = Psi(x=("g",), relations=())
    state = Psi(x=("g", "s0"), relations=())
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)
    rec = record(0, "genesis", state)
    proof = Provenance(candidate_hash=rec.candidate_hash, evidence_hash=rec.evidence_hash, kernel_version=rec.kernel_version)
    store.commit_once_with_audit(rec, proof, genesis, state)

    recovered = recover_psi(genesis, SQLiteHistoryStore(path), lambda _s, _r: state)
    assert recovered.state == state

    # Recovery returns a derived value only; the durable store remains unchanged.
    before = SQLiteHistoryStore(path).load()
    assert len(before.records) == 1
    assert before.head.state_hash == state_digest(state)


def test_adversarial_tamper_recovery_rejects_and_does_not_commit(tmp_path):
    genesis = Psi(x=("g",), relations=())
    state = Psi(x=("g", "s0"), relations=())
    path = tmp_path / "history.db"
    store = SQLiteHistoryStore(path)
    rec = record(0, "genesis", state)
    proof = Provenance(candidate_hash=rec.candidate_hash, evidence_hash=rec.evidence_hash, kernel_version=rec.kernel_version)
    store.commit_once_with_audit(rec, proof, genesis, state)

    import sqlite3
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE transition_history SET state_hash = ? WHERE sequence = 0",
            ("tampered-state",),
        )
        conn.commit()

    with pytest.raises(ValueError):
        recover_psi(genesis, SQLiteHistoryStore(path), lambda _s, _r: state)

    durable = SQLiteHistoryStore(path).load()
    assert len(durable.records) == 1
    assert durable.head.state_hash == state_digest(state)
