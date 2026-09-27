from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_adaptation_is_not_a_core_state_writer():
    rules = source("docs/CORE-TRUST-RULES.md")
    assert "External connectors are adapters, never trusted state writers." in rules


def test_meta_transition_apply_is_fail_closed():
    meta = source("core/meta_transition.py")
    admission = source("core/meta_admission.py")
    assert "admissible" in meta
    assert "if not self.admissible()" in admission
    assert "raise ValueError" in admission


def test_meta_apply_requires_refinement_proof():
    meta = source("core/meta_transition.py")
    assert "RefinementProof" in meta
    assert "refinement" in meta


def test_research_memory_is_not_core_authority():
    rules = source("docs/CORE-TRUST-RULES.md")
    assert "Research-Memory is evidence/context material, never Core authority." in rules
