import pytest

from core.admission import Admission
from core.history import AppendOnlyHistory, TransitionRecord
from core.replay import replay
from core.sqlite_persistence import SQLiteHistoryStore
from core.state import Psi


def test_recovered_history_is_not_a_semantic_commit_authority(tmp_path):
    path = tmp_path / "history.db"
    genesis = Psi(x=("g",), relations=())
    recovered_state = Psi(x=("g", "s0"), relations=())

    # Persisted history can reconstruct a state, but recovery alone cannot
    # manufacture an Admission accepted by the semantic commit boundary.
    from core.execution_contract import state_digest

    digest = state_digest(recovered_state)
    record = TransitionRecord(
        sequence=0,
        previous_hash="genesis",
        state_hash=digest,
        kernel_version="k1",
        candidate_hash=digest,
        admitted=True,
        evidence_hash="e1",
    )
    SQLiteHistoryStore(path).commit_once(record, genesis, recovered_state)
    history = SQLiteHistoryStore(path).load()

    replayed = replay(genesis, history, lambda state, rec: recovered_state)

    assert replayed.state == recovered_state
    assert not hasattr(replayed, "admission")
    assert not hasattr(replayed, "commit")


def test_snapshot_is_observation_only_and_cannot_be_used_as_admission():
    from core.snapshot import Snapshot, SnapshotCertificate
    from core.execution_contract import state_digest

    state = Psi(x=("g", "s0"), relations=())
    snapshot = Snapshot(
        state=state,
        certificate=SnapshotCertificate(
            history_head="h1",
            state_hash=state_digest(state),
            kernel_version="k1",
        ),
    )

    assert not isinstance(snapshot, Admission)
    assert not hasattr(snapshot, "apply")
    assert not hasattr(snapshot, "commit")


def test_recovered_state_still_requires_real_admission_for_semantic_commit():
    # Structural guard: a raw recovered Psi cannot be passed where Admission is
    # required. SemanticCommit.require_admitted is the only acceptance gate.
    recovered = Psi(x=("g", "s0"), relations=())
    assert not isinstance(recovered, Admission)

    with pytest.raises(TypeError):
        from core.admission import require_admitted
        require_admitted(recovered)
