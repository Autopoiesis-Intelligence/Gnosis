#!/usr/bin/env python3
"""Deterministic structural validation for the public repository context manifest.

Uses only the Python standard library. It validates the local contract; it does not
verify remote links, runtime behavior, authorization, or truth of capability claims.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

MANIFEST = Path(".well-known/gnosis-context.json")
SCHEMA = Path("schemas/gnosis-context.schema.json")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / MANIFEST
    schema_path = root / SCHEMA
    if not manifest_path.is_file():
        return [f"{MANIFEST.as_posix()}: missing"]
    if not schema_path.is_file():
        return [f"{SCHEMA.as_posix()}: missing"]

    try:
        data: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{MANIFEST.as_posix()}: invalid JSON ({exc})"]
    try:
        schema: Any = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{SCHEMA.as_posix()}: invalid JSON ({exc})"]

    # Keep validation dependency-free and explicit. JSON Schema remains the published
    # interoperability contract; these checks cover the safety-critical invariants.
    if not isinstance(data, dict):
        return [f"{MANIFEST.as_posix()}: root must be an object"]
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{SCHEMA.as_posix()}: unsupported or missing JSON Schema dialect")

    required = (
        "schema_version", "identity", "purpose", "repository_revision",
        "related_repositories", "unauthenticated_profile", "authority_boundary",
        "evidence_contract", "improvement_loop", "entry_points", "status",
    )
    for key in required:
        if key not in data:
            errors.append(f"manifest: missing required field '{key}'")

    identity = data.get("identity", {})
    if not isinstance(identity, dict):
        errors.append("identity: must be an object")
        identity = {}
    if identity.get("repository") != "Autopoiesis-Intelligence/Gnosis":
        errors.append("identity.repository: must use the canonical repository identity")
    if identity.get("canonical_url") != "https://github.com/Autopoiesis-Intelligence/Gnosis":
        errors.append("identity.canonical_url: must use the canonical repository URL")

    revision = data.get("repository_revision", {})
    if not isinstance(revision, dict):
        errors.append("repository_revision: must be an object")
        revision = {}
    value = revision.get("value")
    if value is not None and (not isinstance(value, str) or not SHA40.fullmatch(value)):
        errors.append("repository_revision.value: must be null or an exact 40-character lowercase commit SHA")
    if revision.get("required_for_evidence") is not True:
        errors.append("repository_revision.required_for_evidence: must be true")

    profile = data.get("unauthenticated_profile", {})
    if not isinstance(profile, dict):
        errors.append("unauthenticated_profile: must be an object")
        profile = {}
    denied = profile.get("denied", [])
    if not isinstance(denied, list):
        errors.append("unauthenticated_profile.denied: must be an array")
    else:
        joined_denials = " ".join(item for item in denied if isinstance(item, str)).lower()
        for concept in ("authorization", "private partner data", "authoritative core state"):
            if concept not in joined_denials:
                errors.append(f"unauthenticated_profile.denied: must explicitly prohibit '{concept}'")

    boundary = data.get("authority_boundary", {})
    if not isinstance(boundary, dict):
        errors.append("authority_boundary: must be an object")
        boundary = {}
    if not isinstance(boundary.get("fail_closed_on"), list) or not boundary.get("fail_closed_on"):
        errors.append("authority_boundary.fail_closed_on: must be a non-empty array")

    loop = data.get("improvement_loop", {})
    if not isinstance(loop, dict):
        errors.append("improvement_loop: must be an object")
        loop = {}
    if loop.get("automatic_merge") is not False:
        errors.append("improvement_loop.automatic_merge: must be false")
    if loop.get("personal_tracking") is not False:
        errors.append("improvement_loop.personal_tracking: must be false")
    if loop.get("public_sources_only") is not True:
        errors.append("improvement_loop.public_sources_only: must be true")

    status = data.get("status", {})
    if not isinstance(status, dict):
        errors.append("status: must be an object")
        status = {}
    for key in ("end_to_end_autonomous_discovery", "commercial_execution_authorization"):
        if not isinstance(status.get(key), str) or not status.get(key).strip():
            errors.append(f"status.{key}: must explicitly state current evidence status")

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]).resolve() if args else Path.cwd().resolve()
    errors = validate(root)
    if errors:
        print("Repository context validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository context validation: PASS")
    print("Structural invariants passed; this does not prove remote links, authorization, or runtime capabilities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
