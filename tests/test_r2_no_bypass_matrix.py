from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_legacy_engine_has_no_canonical_commit_authority():
    source = read("core/legacy_engine.py")
    assert "SemanticCommit" not in source
    assert "commit(" not in source


def test_merge_only_constructs_candidates_or_conflicts():
    source = read("core/merge.py")
    assert "commit(" not in source
    assert "SemanticCommit" not in source


def test_resolution_requires_admission_candidate_identity():
    source = read("core/resolution.py")
    assert "admission.candidate != resolution.candidate" in source
    assert "admit_resolution" in source
    assert "commit_resolution" in source


def test_replay_and_snapshot_are_not_mutation_authorities():
    replay = read("core/replay.py")
    snapshot = read("core/snapshot.py")
    assert "SemanticCommit" not in replay
    assert "commit(" not in replay
    assert "SemanticCommit" not in snapshot
    assert "commit(" not in snapshot


def test_external_generic_canonical_chain_is_not_claimed_as_executor_identity():
    execution = read("core/execution.py")
    chain = read("core/canonical_chain.py")
    assert "commit(" in execution
    assert "admit_transition" in chain
