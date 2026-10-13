from copy import deepcopy
import json
from pathlib import Path

import pytest

from tools.capability_catalogue import (
    CapabilityCatalogueError,
    load_catalogue,
    validate_catalogue,
    verified_capability_ids,
)

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "capability-catalogue.json"


def valid_capability():
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


def test_checked_in_catalogue_loads_and_exposes_only_ci_proven_ids():
    catalogue = load_catalogue(CATALOGUE_PATH)
    assert verified_capability_ids(catalogue) == {"opportunity.evaluate-curated-records"}


def test_stale_or_mismatched_ci_sha_is_rejected():
    payload = {"schema_version": "1.0", "capabilities": [valid_capability()]}
    payload["capabilities"][0]["ci_evidence"][0]["commit_sha"] = "b" * 40
    with pytest.raises(CapabilityCatalogueError, match="does not match source_revision"):
        validate_catalogue(payload)


def test_ci_proven_entry_cannot_contain_failed_run():
    payload = {"schema_version": "1.0", "capabilities": [valid_capability()]}
    payload["capabilities"][0]["ci_evidence"][0]["conclusion"] = "failure"
    with pytest.raises(CapabilityCatalogueError, match="all-success"):
        validate_catalogue(payload)


def test_unverified_capability_is_not_exposed_for_matching():
    item = valid_capability()
    item["evidence_status"] = "TESTED"
    payload = {"schema_version": "1.0", "capabilities": [item]}
    assert verified_capability_ids(payload) == set()


def test_duplicate_capability_ids_are_rejected():
    payload = {"schema_version": "1.0", "capabilities": [valid_capability(), valid_capability()]}
    with pytest.raises(CapabilityCatalogueError, match="duplicate capability_id"):
        validate_catalogue(payload)


def test_boolean_run_id_is_not_accepted_as_integer():
    payload = {"schema_version": "1.0", "capabilities": [valid_capability()]}
    payload["capabilities"][0]["ci_evidence"][0]["run_id"] = True
    with pytest.raises(CapabilityCatalogueError, match="positive integer"):
        validate_catalogue(payload)


def test_validation_does_not_mutate_input():
    payload = {"schema_version": "1.0", "capabilities": [valid_capability()]}
    before = deepcopy(payload)
    validate_catalogue(payload)
    assert payload == before
