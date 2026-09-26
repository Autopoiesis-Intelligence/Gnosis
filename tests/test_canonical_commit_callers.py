from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_canonical_commit_authority_is_executor():
    source = _read("core/execution.py")
    assert "commit_admitted_psi(" in source
    assert "CanonicalExecutor" in source


def test_evolution_transition_does_not_construct_semantic_commit():
    source = _read("core/evolution.py")
    assert "SemanticCommit(" not in source
    assert "commit(" not in source


def test_resolution_checks_candidate_identity_before_commit():
    source = _read("core/resolution.py")
    assert "admission.candidate != resolution.candidate" in source
    assert "commit(previous, admission" in source


def test_no_direct_semantic_commit_constructor_outside_commit_module():
    core = ROOT / "core"
    offenders = []
    for path in core.glob("*.py"):
        if path.name == "commit.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "SemanticCommit(" in text:
            offenders.append(str(path))
    assert offenders == []
