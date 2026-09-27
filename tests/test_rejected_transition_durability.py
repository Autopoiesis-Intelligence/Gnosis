"""Adversarial evidence for rejected-transition durable non-existence.

R2.3.5: an admission rejected before semantic commit must not create
history/provenance/audit evidence and must remain absent after recovery.
"""

import pytest

from core.admission import admit, require_admitted
from core.canonical_chain import commit_admitted_psi
from core.history import AppendOnlyHistory
from core.proof import prove_fundamental_transition
from core.recovery import recover_psi
from core.sqlite_persistence import SQLiteHistoryStore
from core.state import Psi


def test_rejected_admission_cannot_cross_commit_boundary_or_survive_recovery(tmp_path):
    database = tmp_path / "rejected-transition.sqlite"
    store = SQLiteHistoryStore(database)

    genesis = Psi(x=("genesis",), relations=())
    candidate = Psi(x=("rejected",), relations=())

    proof = prove_fundamental_transition(
        genesis,
        candidate,
        lambda _: False,
    )
    admission = admit(candidate, proof)

    assert admission.accepted is False

    with pytest.raises(ValueError, match="Candidate was not admitted"):
        require_admitted(admission)

    with pytest.raises(ValueError, match="Candidate was not admitted"):
        commit_admitted_psi(
            AppendOnlyHistory(),
            genesis,
            admission,
            kernel_version="r2-3-5-test",
            durable_store=store,
        )

    assert store.load().records == ()
    assert store.load_audit() == ()
    assert store.load_provenance() == ()
    assert store.load_authorization_consumption() == ()

    restarted = SQLiteHistoryStore(database)
    recovered = recover_psi(
        genesis,
        restarted,
        lambda state, _record: state,
    )
    assert recovered == genesis
    assert restarted.load().records == ()
    assert restarted.load_audit() == ()
    assert restarted.load_provenance() == ()
    assert restarted.load_authorization_consumption() == ()
