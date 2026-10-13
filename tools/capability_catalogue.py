"""Strict reader and safe adapter for the evidence-bound capability catalogue.

Catalogue membership is descriptive only. It never grants permissions or
execution authority. Matching uses only entries whose exact source SHA is
bound to successful recorded CI evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
_ALLOWED_STATUSES = {
    "DOCUMENTED", "IMPLEMENTED", "TESTED", "CI_PROVEN",
    "RUNTIME_PROVEN", "UNRESOLVED",
}
DEFAULT_CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "capability-catalogue.json"


class CapabilityCatalogueError(ValueError):
    """Raised when the catalogue is malformed or its provenance conflicts."""


def validate_catalogue(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise CapabilityCatalogueError("catalogue must be an object")
    if set(payload) != {"schema_version", "capabilities"}:
        raise CapabilityCatalogueError("catalogue must contain exactly schema_version and capabilities")
    if payload["schema_version"] != "1.0":
        raise CapabilityCatalogueError("unsupported schema_version")
    capabilities = payload["capabilities"]
    if not isinstance(capabilities, list):
        raise CapabilityCatalogueError("capabilities must be a list")

    seen: set[str] = set()
    required = {
        "capability_id", "title", "repository", "source_revision", "evidence_status",
        "operations", "permissions", "data_classes", "dependencies", "limits",
        "failure_modes", "maintenance", "rollback", "ci_evidence",
    }
    for index, capability in enumerate(capabilities):
        prefix = f"capabilities[{index}]"
        if not isinstance(capability, Mapping) or set(capability) != required:
            raise CapabilityCatalogueError(f"{prefix} has missing or unexpected fields")
        capability_id = capability["capability_id"]
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise CapabilityCatalogueError(f"{prefix}.capability_id must be non-empty")
        if capability_id in seen:
            raise CapabilityCatalogueError(f"duplicate capability_id: {capability_id}")
        seen.add(capability_id)
        if not isinstance(capability["source_revision"], str) or not _SHA_RE.fullmatch(capability["source_revision"]):
            raise CapabilityCatalogueError(f"{prefix}.source_revision must be a full lowercase SHA")
        if capability["evidence_status"] not in _ALLOWED_STATUSES:
            raise CapabilityCatalogueError(f"{prefix}.evidence_status is unknown")
        for field in ("operations", "permissions", "data_classes", "dependencies",
                      "limits", "failure_modes", "maintenance", "rollback"):
            values = capability[field]
            if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
                raise CapabilityCatalogueError(f"{prefix}.{field} must be a list of non-empty strings")
        evidence = capability["ci_evidence"]
        if not isinstance(evidence, list):
            raise CapabilityCatalogueError(f"{prefix}.ci_evidence must be a list")
        for evidence_index, item in enumerate(evidence):
            item_prefix = f"{prefix}.ci_evidence[{evidence_index}]"
            if not isinstance(item, Mapping) or set(item) != {"workflow", "run_id", "conclusion", "commit_sha", "url"}:
                raise CapabilityCatalogueError(f"{item_prefix} has missing or unexpected fields")
            if not isinstance(item["workflow"], str) or not item["workflow"].strip():
                raise CapabilityCatalogueError(f"{item_prefix}.workflow must be non-empty")
            if isinstance(item["run_id"], bool) or not isinstance(item["run_id"], int) or item["run_id"] < 1:
                raise CapabilityCatalogueError(f"{item_prefix}.run_id must be a positive integer")
            if item["conclusion"] not in {"success", "failure", "cancelled", "skipped", "unknown"}:
                raise CapabilityCatalogueError(f"{item_prefix}.conclusion is invalid")
            if not isinstance(item["commit_sha"], str) or not _SHA_RE.fullmatch(item["commit_sha"]):
                raise CapabilityCatalogueError(f"{item_prefix}.commit_sha must be a full lowercase SHA")
            if item["commit_sha"] != capability["source_revision"]:
                raise CapabilityCatalogueError(f"{item_prefix} commit_sha does not match source_revision")
            if not isinstance(item["url"], str) or not item["url"].startswith("https://"):
                raise CapabilityCatalogueError(f"{item_prefix}.url must be HTTPS")

        if capability["evidence_status"] == "CI_PROVEN":
            if not evidence or any(item["conclusion"] != "success" for item in evidence):
                raise CapabilityCatalogueError(f"{prefix} CI_PROVEN requires non-empty all-success evidence")


def load_catalogue(path: str | Path = DEFAULT_CATALOGUE_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityCatalogueError(f"cannot read catalogue: {exc}") from exc
    validate_catalogue(payload)
    return payload


def verified_capability_ids(payload: Mapping[str, Any]) -> set[str]:
    """Return only IDs whose source SHA matches successful recorded CI evidence."""
    validate_catalogue(payload)
    return {
        item["capability_id"]
        for item in payload["capabilities"]
        if item["evidence_status"] == "CI_PROVEN"
        and item["ci_evidence"]
        and all(
            proof["commit_sha"] == item["source_revision"]
            and proof["conclusion"] == "success"
            for proof in item["ci_evidence"]
        )
    }


def evaluate_with_catalogue(record: Mapping[str, Any], catalogue_path: str | Path = DEFAULT_CATALOGUE_PATH):
    """Evaluate one record using only capability IDs backed by matching CI evidence."""
    from tools.opportunity_evaluator import evaluate

    catalogue = load_catalogue(catalogue_path)
    return evaluate(record, verified_capability_ids(catalogue))


def rank_with_catalogue(records, catalogue_path: str | Path = DEFAULT_CATALOGUE_PATH):
    """Rank records against the verified catalogue; output remains proposal-only."""
    from tools.opportunity_evaluator import rank_opportunities

    catalogue = load_catalogue(catalogue_path)
    return rank_opportunities(records, verified_capability_ids(catalogue))
