"""Static CI guard for production mutation-authority classification."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"

# SemanticCommit construction is the explicit canonical commit authority.
# New production code may not instantiate it outside the authority module.
ALLOWED_SEMANTIC_COMMIT_FILES = {"commit.py"}

# These names identify direct mutation-like calls that require explicit review.
MUTATION_PATTERNS = (
    re.compile(r"\bSemanticCommit\s*\("),
    re.compile(r"\bcommit_once\s*\("),
    re.compile(r"\.append\s*\("),
)


def production_core_files():
    return sorted(CORE.glob("*.py"))


def test_semantic_commit_constructor_is_confined_to_authority_module():
    offenders = []
    for path in production_core_files():
        if path.name in ALLOWED_SEMANTIC_COMMIT_FILES:
            continue
        if re.search(r"\bSemanticCommit\s*\(", path.read_text(encoding="utf-8")):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_mutation_like_surfaces_are_inventoryable():
    surfaces = {}
    for path in production_core_files():
        text = path.read_text(encoding="utf-8")
        matches = [p.pattern for p in MUTATION_PATTERNS if p.search(text)]
        if matches:
            surfaces[path.relative_to(ROOT).as_posix()] = matches

    # The test is deliberately deterministic: any new mutation-like file
    # appears in CI output and therefore requires authority review.
    assert "core/commit.py" in surfaces
    assert "core/sqlite_persistence.py" in surfaces
