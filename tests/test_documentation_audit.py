from pathlib import Path

from tools.audit_documentation import audit_repository


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_tree(root: Path) -> None:
    _write(
        root,
        "README.md",
        "# Gnosis\n\n## Getting started\n\n## Current capabilities and limitations\n\n## Feedback and communication\n\n[Bug report](.github/ISSUE_TEMPLATE/bug_report.md)\n",
    )
    _write(root, ".github/ISSUE_TEMPLATE/bug_report.md", "# Report a bug\n")
    _write(root, ".github/ISSUE_TEMPLATE/feature_request.md", "# Request a feature\n")
    _write(root, "CONTRIBUTING.md", "# Contributing\n")
    _write(root, "SUPPORT.md", "# Support\n")


def test_audit_passes_for_complete_canonical_user_docs(tmp_path: Path) -> None:
    _valid_tree(tmp_path)
    assert audit_repository(tmp_path) == []


def test_audit_flags_missing_readme_sections_and_user_routes(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "# Gnosis\n")
    findings = audit_repository(tmp_path)
    assert any("missing heading 'Getting started'" in item for item in findings)
    assert any("missing user-facing document" in item for item in findings)


def test_audit_flags_stale_branding_and_broken_local_links(tmp_path: Path) -> None:
    _valid_tree(tmp_path)
    _write(
        tmp_path,
        "README.md",
        "# Gnosis\n\n## Getting started\n\n## Current capabilities and limitations\n\n## Feedback and communication\n\nGnozis is the old spelling. [Broken](missing.md)\n",
    )
    findings = audit_repository(tmp_path)
    assert any("stale brand spelling" in item for item in findings)
    assert any("broken local link" in item for item in findings)
