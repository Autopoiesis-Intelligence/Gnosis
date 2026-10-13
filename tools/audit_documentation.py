#!/usr/bin/env python3
"""Read-only audit for public documentation freshness.

This tool reports documentation drift; it never edits files or publishes changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_README_HEADINGS = (
    "Getting started",
    "Current capabilities and limitations",
    "Feedback and communication",
)
USER_FACING_FILES = (
    Path("README.md"),
    Path(".github/ISSUE_TEMPLATE/bug_report.md"),
    Path(".github/ISSUE_TEMPLATE/feature_request.md"),
    Path("CONTRIBUTING.md"),
    Path("SUPPORT.md"),
)
STALE_BRAND = re.compile(r"\b(?:gnozis|genezis)\b", re.IGNORECASE)
MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def audit_repository(root: Path) -> list[str]:
    """Return deterministic findings for the repository at *root*."""
    findings: list[str] = []
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return ["README.md: missing required root README"]

    readme = readme_path.read_text(encoding="utf-8")
    normalized_headings = {
        re.sub(r"[^a-z0-9]+", " ", line.lstrip("#").strip().lower()).strip()
        for line in readme.splitlines()
        if line.lstrip().startswith("#")
    }
    for heading in REQUIRED_README_HEADINGS:
        normalized = re.sub(r"[^a-z0-9]+", " ", heading.lower()).strip()
        if normalized not in normalized_headings:
            findings.append(f"README.md: missing heading '{heading}'")

    for relative in USER_FACING_FILES:
        path = root / relative
        if not path.is_file():
            if relative == Path("README.md"):
                continue
            # Templates and support documents are required user communication routes.
            findings.append(f"{relative.as_posix()}: missing user-facing document")
            continue

        content = path.read_text(encoding="utf-8")
        if STALE_BRAND.search(content):
            findings.append(
                f"{relative.as_posix()}: stale brand spelling; use Gnosis / Genesis"
            )

        for match in MARKDOWN_LINK.finditer(content):
            destination = match.group(1).strip().split()[0].strip("<>")
            if not destination or destination.startswith(("#", "https://", "http://", "mailto:")):
                continue
            target = destination.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                resolved = root / target.lstrip("/")
            else:
                resolved = (path.parent / target).resolve()
            if not resolved.exists():
                findings.append(
                    f"{relative.as_posix()}: broken local link '{destination}'"
                )

    return sorted(set(findings))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]).resolve() if args else Path.cwd().resolve()
    findings = audit_repository(root)
    if findings:
        print("Documentation audit: FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Documentation audit: PASS")
    print("Checked README sections, user-facing files, canonical brand spelling, and local Markdown links.")
    print("This audit detects drift; it does not prove documented capabilities are implemented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
