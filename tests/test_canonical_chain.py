import pytest

from core.canonical_chain import admit_transition
from core.history import AppendOnlyHistory, TransitionRecord
from core.provenance import Provenance
from core.safety import SafetyGate


def rec():
    return TransitionRecord(0, "", "s0", "k1", "c0", True, "e0")


def prov():
    return Provenance("c0", "e0", "k1")


def test_canonical_chain_requires_safety_gas_provenance_and_commit():
    result = admit_transition(
        AppendOnlyHistory(), rec(), prov(), "before", "after", 2, (1, 2)
    )
    assert result.applied
    assert result.value == "after"
    assert result.history.head.state_hash == "s0"


def test_canonical_chain_fails_before_commit_on_bad_provenance():
    with pytest.raises(ValueError, match="evidence"):
        admit_transition(
            AppendOnlyHistory(), rec(), Provenance("c0", "wrong", "k1"),
            "before", "after", 1, (1,)
        )


def test_canonical_chain_respects_hard_stop():
    with pytest.raises(PermissionError):
        admit_transition(
            AppendOnlyHistory(), rec(), prov(), "before", "after", 1, (1,),
            SafetyGate(hard_stop=True)
        )


def test_canonical_chain_respects_gas_limit():
    with pytest.raises(ValueError, match="exhausted"):
        admit_transition(
            AppendOnlyHistory(), rec(), prov(), "before", "after", 2, (15, 6),
            gas_limit=20
        )


def test_commit_rejects_substituted_candidate_after_admission():
    history = AppendOnlyHistory()
    admitted = rec()
    provenance = prov()

    # The provenance binds candidate c0. Supplying a different candidate hash
    # at the canonical commit boundary must fail before durable mutation.
    substituted = TransitionRecord(
        admitted.sequence, admitted.previous_hash, admitted.state_hash,
        admitted.kernel_version, "substituted-candidate", admitted.admitted,
        admitted.evidence_hash,
    )
    with pytest.raises(ValueError, match="candidate"):
        admit_transition(
            history, substituted, provenance, "before", "after", 1, (1,)
        )
    assert history.head is None


def test_state_identity_failure_leaves_durable_history_unchanged(tmp_path):
    from core.sqlite_persistence import SQLiteHistoryStore
    database = tmp_path / "state-identity-atomicity.sqlite"
    store = SQLiteHistoryStore(database)
    history = AppendOnlyHistory()
    previous = Psi(x=("wrong",), relations=())
    admission = rec()
    with pytest.raises(ValueError, match="previous Psi does not match history head"):
        commit_admitted_psi(
            history,
            previous,
            admission,
            kernel_version="test-v1",
            durable_store=store,
        )
    assert store.load().records == ()
    assert store.load_audit() == ()
    assert store.load_provenance() == ()
