"""Adversarial contract tests for the canonical Ψ semantic boundary.

These tests are intentionally structural: they verify that the canonical
surface is the PsiEngine/PsiTransition path and that the legacy State->State
surface is explicitly classified as compatibility, not Ψ authority.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_canonical_path_is_psi_typed():
    source = _read("core/psi_engine.py")
    assert "PsiTransition" in source
    assert "Psi" in source


def test_legacy_engine_is_not_declared_canonical():
    audit = _read("docs/PM-05_APPLY_PATH_AUDIT.md")
    assert "LEGACY/GENERIC COMPATIBILITY" in audit
    assert "CANONICAL Ψ" in audit


def test_admission_gate_is_present_on_canonical_evolution():
    source = _read("core/evolution.py")
    admission = _read("core/admission.py")
    assert "admit(" in source
    assert "require_admitted" in admission
    assert "PsiTransition" in source


def test_global_bypass_is_not_claimed_without_adversarial_evidence():
    context = _read("AI_CONTEXT.md")
    assert "Do not claim global non-bypass" in context


def test_uroboros_canonical_wires_transition_to_executor():
    source = _read("core/uroboros.py")
    assert "engine=Engine(transition=transition)" in source
    assert "executor=CanonicalExecutor(" in source
    assert "psi_transition=transition" in source


def test_canonical_step_uses_transition_executor_path():
    source = _read("core/uroboros.py")
    assert "self.executor.step(" in source
    assert "self.psi_transition" in source
    assert "canonicalize_psi(self.state.to_psi())" in source


def test_legacy_uroboros_does_not_construct_canonical_executor():
    source = _read("core/uroboros.py")
    start = source.index("    def evolutionary(")
    end = source.index("    def step(", start)
    block = source[start:end]
    assert "LegacyEngine" in block
    assert "executor=None" in block
    assert "CanonicalExecutor(" not in block


def test_replay_is_reconstruction_only():
    source = _read("core/replay.py")
    assert "commit_once_with_audit" not in source
    assert "SemanticCommit" not in source


def test_snapshot_is_observation_only():
    source = _read("core/snapshot.py")
    assert "commit_once_with_audit" not in source
    assert "SemanticCommit" not in source


def test_merge_produces_candidates_or_conflicts_only():
    source = _read("core/merge.py")
    assert "commit_once_with_audit" not in source
    assert "SemanticCommit" not in source
    assert "candidate=None" in source
