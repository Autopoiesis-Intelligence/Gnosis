from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_semantic_commit_constructor_remains_confined():
    offenders = []
    for path in (ROOT / "core").glob("*.py"):
        if path.name == "commit.py":
            continue
        if "SemanticCommit(" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []


def test_direct_commit_callers_are_explicitly_inventoried():
    evolution = source("core/evolution.py")
    resolution = source("core/resolution.py")
    assert "commit(" not in evolution
    assert "commit(" in resolution
    assert "commit_resolution" in resolution


def test_legacy_transition_is_deprecated_and_not_canonical():
    source_text = source("core/evolution.py")
    assert "DeprecationWarning" in source_text
    legacy = source("core/legacy_engine.py")
    assert "SemanticCommit" not in legacy


def test_bridge_is_not_canonical_commit_authority():
    bridge = source("gnosis-terminal-bridge/src/core_evolution.py")
    assert "SemanticCommit" not in bridge
    assert "Engine(transition=bound_transition)" in bridge


def test_uroboros_keeps_canonical_executor_wired():
    uroboros = source("core/uroboros.py")
    assert "executor=CanonicalExecutor(" in uroboros
    assert "psi_transition=transition" in uroboros
