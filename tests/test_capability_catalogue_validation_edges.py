import pytest

from tools.capability_catalogue import CapabilityCatalogueError, validate_catalogue


def capability():
    sha = "a" * 40
    return {
        "capability_id": "example.read",
        "title": "Example read-only capability",
        "repository": "example/project",
        "source_revision": sha,
        "evidence_status": "CI_PROVEN",
        "operations": ["inspect"],
        "permissions": ["READ"],
        "data_classes": ["public"],
        "dependencies": ["Python standard library"],
        "limits": ["No writes"],
        "failure_modes": ["Invalid input"],
        "maintenance": ["Refresh evidence when source changes"],
        "rollback": ["Remove catalogue entry"],
        "ci_evidence": [{
            "workflow": "Tests",
            "run_id": 1,
            "conclusion": "success",
            "commit_sha": sha,
            "url": "https://example.org/actions/1",
        }],
    }


def test_non_string_evidence_status_is_rejected_as_catalogue_error():
    item = capability()
    item["evidence_status"] = []
    with pytest.raises(CapabilityCatalogueError, match="evidence_status is unknown"):
        validate_catalogue({"schema_version": "1.0", "capabilities": [item]})


def test_non_string_ci_conclusion_is_rejected_as_catalogue_error():
    item = capability()
    item["ci_evidence"][0]["conclusion"] = []
    with pytest.raises(CapabilityCatalogueError, match="conclusion is invalid"):
        validate_catalogue({"schema_version": "1.0", "capabilities": [item]})


def test_non_ci_proven_capability_may_have_no_ci_runs():
    item = capability()
    item["evidence_status"] = "IMPLEMENTED"
    item["ci_evidence"] = []
    validate_catalogue({"schema_version": "1.0", "capabilities": [item]})
