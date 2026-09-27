from core.state import Psi
import pytest

from core.admission import admit
from core.canonical_chain import admit_transition, commit_admitted_psi
from core.execution_contract import state_digest
from core.history import AppendOnlyHistory, TransitionRecord
from core.proof import prove_fundamental_transition
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

    current = Psi(x=("current",), relations=())
    candidate = Psi(x=("candidate",), relations=())
    wrong_previous = Psi(x=("wrong",), relations=())

    proof = prove_fundamental_transition(
        current,
        candidate,
        lambda _: True,
    )
    admission = admit(candidate, proof)

    head = TransitionRecord(
        sequence=0,
        previous_hash="genesis",
        state_hash=state_digest(current),
        kernel_version="test-v1",
        candidate_hash=state_digest(current),
        admitted=True,
        evidence_hash="head-evidence",
    )
    history = AppendOnlyHistory().append(head)
    history_before = history

    with pytest.raises(ValueError, match="previous Psi does not match history head"):
        commit_admitted_psi(
            history,
            wrong_previous,
            admission,
            kernel_version="test-v1",
            durable_store=store,
        )

    assert history == history_before
    assert store.load().records == ()
    assert store.load_audit() == ()
    assert store.load_provenance() == ()


def test_semantic_commit_composes_identity_admission_and_atomic_durable_commit(tmp_path):
    from core.sqlite_persistence import SQLiteHistoryStore

    database = tmp_path / "semantic-commit.sqlite"
    store = SQLiteHistoryStore(database)

    current = Psi(x=("current",), relations=())
    candidate = Psi(x=("candidate",), relations=())
    current_hash = state_digest(current)

    head = TransitionRecord(
        sequence=0,
        previous_hash="genesis",
        state_hash=current_hash,
        kernel_version="test-v1",
        candidate_hash=current_hash,
        admitted=True,
        evidence_hash="head-evidence",
    )
    head_provenance = Provenance(
        candidate_hash=current_hash,
        evidence_hash="head-evidence",
        kernel_version="test-v1",
    )
    store.commit_once_with_audit(head, head_provenance, current, current)

    history = store.load()

    proof = prove_fundamental_transition(
        current,
        candidate,
        lambda _: True,
    )
    admission = admit(candidate, proof)

    result = commit_admitted_psi(
        history,
        current,
        admission,
        kernel_version="test-v1",
        durable_store=store,
    )

    assert result.applied
    assert result.value == candidate
    assert result.history.head.state_hash == state_digest(candidate)

    durable = SQLiteHistoryStore(database)
    assert len(durable.load().records) == 2
    assert len(durable.load_audit()) == 2
    assert len(durable.load_provenance()) == 2
    durable.verify_cross_table_consistency()


def test_semantic_commit_rejects_proof_candidate_identity_substitution_before_durable_commit(tmp_path):
    from core.sqlite_persistence import SQLiteHistoryStore
    from core.proof import ProofObligation

    database = tmp_path / "proof-identity-substitution.sqlite"
    store = SQLiteHistoryStore(database)
    current = Psi(x=("current",), relations=())
    candidate = Psi(x=("candidate",), relations=())
    proof = prove_fundamental_transition(current, candidate, lambda _: True)
    tampered = ProofObligation(
        passed=proof.passed,
        invariant=proof.invariant,
        viable=proof.viable,
        evidence=proof.evidence,
        candidate_digest=state_digest(Psi(x=("substituted",), relations=())),
    )
    with pytest.raises(ValueError, match="candidate identity"):
        commit_admitted_psi(
            AppendOnlyHistory(),
            current,
            admit(candidate, tampered),
            kernel_version="test-v1",
            durable_store=store,
        )
    assert store.load().records == ()
    assert store.load_audit() == ()
    assert store.load_provenance() == ()


def test_identity_validated_candidate_is_atomic_at_durable_commit_boundary(tmp_path):
    from core.sqlite_persistence import SQLiteHistoryStore

    database = tmp_path / "identity-atomicity-composition.sqlite"

    def fail(point):
        if point == "after_provenance_before_audit":
            raise RuntimeError("injected:identity-atomicity")

    store = SQLiteHistoryStore(database, failure_injector=fail)
    current = Psi(x=("current",), relations=())
    candidate = Psi(x=("candidate",), relations=())
    proof = prove_fundamental_transition(current, candidate, lambda _: True)
    admission = admit(candidate, proof)

    with pytest.raises(RuntimeError, match="injected:identity-atomicity"):
        commit_admitted_psi(
            AppendOnlyHistory(),
            current,
            admission,
            kernel_version="test-v1",
            durable_store=store,
        )

    assert store.load().records == ()
    assert store.load_audit() == ()
    assert store.load_provenance() == ()
    assert store.load_authorization_consumption() == ()
    store.verify_cross_table_consistency()
