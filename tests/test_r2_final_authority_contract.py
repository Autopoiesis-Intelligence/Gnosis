from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_r2_authority_contract_documents_all_trust_boundaries():
    text = read("docs/R2-AUTHORITY-CONTRACT-2026-09-26.md")
    required = [
        "External Input",
        "ExecutionInput",
        "Proof",
        "Admission",
        "SemanticCommit",
        "SQLite",
        "Replay",
        "Snapshot",
        "Recovery",
        "Legacy",
        "MetaTransition",
    ]
    for item in required:
        assert item in text


def test_canonical_commit_authority_is_singlely_named():
    text = read("docs/R2-AUTHORITY-CONTRACT-2026-09-26.md")
    assert "SemanticCommit.apply" in text
    assert "SQLite is not semantic authority" in text
    assert "Replay is not semantic authority" in text
    assert "Snapshot is not semantic authority" in text


def test_r2_does_not_claim_unrestricted_process_security():
    text = read("docs/R2-AUTHORITY-CONTRACT-2026-09-26.md")
    assert "unrestricted hostile process" in text
    assert "not proven" in text
