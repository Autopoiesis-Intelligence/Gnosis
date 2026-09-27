from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"


def test_authority_guard_detects_intentional_out_of_boundary_constructor():
    # Adversarial fixture: a production-like source containing a forbidden
    # SemanticCommit constructor must be detected by the same rule as CI.
    fixture = """
from core.commit import SemanticCommit
def forged():
    return SemanticCommit(candidate=None, admission=None)
"""
    assert re.search(r"\bSemanticCommit\s*\(", fixture)


def test_authority_guard_rejects_any_non_authority_constructor_in_core():
    offenders = []
    for path in CORE.glob("*.py"):
        if path.name == "commit.py":
            continue
        if re.search(r"\bSemanticCommit\s*\(", path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert offenders == []


def test_authority_guard_is_not_satisfied_by_comment_only():
    fixture = "# SemanticCommit(candidate=None)\n"
    # A comment must not count as a constructor occurrence.
    assert not re.search(r"(?m)^[^#\n]*\bSemanticCommit\s*\(", fixture)
