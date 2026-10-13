import json
from pathlib import Path

from tools.validate_repository_context import validate


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_tree(root: Path) -> dict:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
    }
    manifest = {
        "schema_version": "1.0.0",
        "identity": {
            "product": "Gnosis",
            "repository": "Autopoiesis-Intelligence/Gnosis",
            "canonical_url": "https://github.com/Autopoiesis-Intelligence/Gnosis",
            "role": "public-product-and-evidence-surface",
        },
        "purpose": "Public evidence surface.",
        "repository_revision": {
            "value": None,
            "resolution": "Resolve the exact inspected commit.",
            "required_for_evidence": True,
        },
        "related_repositories": [],
        "unauthenticated_profile": {
            "name": "A0",
            "allowed": ["Read public documentation."],
            "denied": [
                "No execution authorization.",
                "No private partner data.",
                "No authoritative Core state writes.",
            ],
            "output_label": "untrusted",
        },
        "authority_boundary": {
            "rule": "Observation does not grant authority.",
            "authorization_source": "Existing trusted gate.",
            "fail_closed_on": ["unknown permission"],
        },
        "evidence_contract": {
            "required_fields": ["source_commit_sha"],
            "evidence_classes": ["source"],
            "claim_statuses": ["unresolved"],
            "rules": ["Exact revision required."],
        },
        "improvement_loop": {
            "stages": ["discover", "verify", "review"],
            "automatic_merge": False,
            "personal_tracking": False,
            "public_sources_only": True,
            "note": "Public-only proposal loop.",
        },
        "entry_points": {"readme": "https://github.com/Autopoiesis-Intelligence/Gnosis"},
        "status": {
            "manifest": "draft",
            "end_to_end_autonomous_discovery": "unresolved",
            "commercial_execution_authorization": "not established",
        },
    }
    _write(root, ".well-known/gnosis-context.json", json.dumps(manifest))
    _write(root, "schemas/gnosis-context.schema.json", json.dumps(schema))
    return manifest


def test_context_contract_accepts_valid_manifest_and_schema(tmp_path: Path) -> None:
    _valid_tree(tmp_path)
    assert validate(tmp_path) == []


def test_context_contract_rejects_stale_or_malformed_revision(tmp_path: Path) -> None:
    manifest = _valid_tree(tmp_path)
    manifest["repository_revision"]["value"] = "main"
    _write(tmp_path, ".well-known/gnosis-context.json", json.dumps(manifest))
    assert any("exact 40-character lowercase commit SHA" in item for item in validate(tmp_path))


def test_context_contract_rejects_authority_promotion_and_automatic_merge(tmp_path: Path) -> None:
    manifest = _valid_tree(tmp_path)
    manifest["unauthenticated_profile"]["denied"] = ["No private partner data."]
    manifest["improvement_loop"]["automatic_merge"] = True
    _write(tmp_path, ".well-known/gnosis-context.json", json.dumps(manifest))
    errors = validate(tmp_path)
    assert any("authorization" in item for item in errors)
    assert any("authoritative core state" in item for item in errors)
    assert any("automatic_merge" in item for item in errors)


def test_context_contract_rejects_missing_authority_status(tmp_path: Path) -> None:
    manifest = _valid_tree(tmp_path)
    del manifest["status"]["commercial_execution_authorization"]
    _write(tmp_path, ".well-known/gnosis-context.json", json.dumps(manifest))
    assert any("commercial_execution_authorization" in item for item in validate(tmp_path))
