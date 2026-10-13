"""Command-line entry point for catalogue-backed opportunity evaluation.

Input is local JSON supplied by the caller. This command performs no network
access, repository writes, integration installation, or execution of proposals.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.capability_catalogue import (
    CapabilityCatalogueError,
    evaluate_with_catalogue,
    rank_with_catalogue,
)
from tools.opportunity_evaluator import OpportunityRecordError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate caller-supplied opportunity JSON against the evidence-bound capability catalogue."
    )
    parser.add_argument("--input", required=True, help="Path to a JSON opportunity object or list of objects")
    parser.add_argument("--catalogue", help="Optional path to a versioned capability catalogue JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload: Any = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            result = evaluate_with_catalogue(payload, args.catalogue) if args.catalogue else evaluate_with_catalogue(payload)
            output: Any = result.as_dict()
        elif isinstance(payload, list):
            output = rank_with_catalogue(payload, args.catalogue) if args.catalogue else rank_with_catalogue(payload)
        else:
            raise ValueError("input JSON must be an object or a list of objects")
    except (OSError, json.JSONDecodeError, CapabilityCatalogueError, OpportunityRecordError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "authority": "PROPOSAL_ONLY"}, sort_keys=True), file=sys.stderr)
        return 2

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
