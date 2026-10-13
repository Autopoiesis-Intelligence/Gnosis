"""Deterministic ranking for Gnosis opportunity candidates.

This module is deliberately pure: it does not fetch sources, mutate repositories,
execute proposals, issue authorization, or infer missing evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0"
EVALUATOR_VERSION = "gnosis-opportunity-score/1"
EVIDENCE_STATUSES = {
    "OBSERVED", "SUPPORTED", "ACCEPTED", "HYPOTHESIZED",
    "UNRESOLVED", "REJECTED", "SUPERSEDED",
}
SCORE_KEYS = {
    "user_value", "evidence_strength", "capability_fit", "effort", "cost",
    "security_risk", "privacy_risk", "maintenance_burden", "reversibility",
}
# Weights are intentionally explicit and versioned. All inputs use a 0..5 scale.
WEIGHTS = {
    "user_value": 0.25,
    "evidence_strength": 0.25,
    "capability_fit": 0.20,
    "reversibility": 0.10,
    "effort": -0.05,
    "cost": -0.05,
    "security_risk": -0.05,
    "privacy_risk": -0.03,
    "maintenance_burden": -0.02,
}
NON_PROMOTABLE = {"HYPOTHESIZED", "UNRESOLVED", "REJECTED", "SUPERSEDED"}


class OpportunityRecordError(ValueError):
    """Raised when a candidate cannot be scored safely."""


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    score: float | None
    decision: str
    reasons: tuple[str, ...]
    evaluator_version: str = EVALUATOR_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "score": self.score,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "evaluator_version": self.evaluator_version,
            "authority": "PROPOSAL_ONLY",
        }


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate safety-critical fields without third-party dependencies."""
    if not isinstance(record, Mapping):
        raise OpportunityRecordError("record must be an object")
    required = {
        "schema_version", "candidate_id", "source_url", "source_revision",
        "observed_at", "problem", "capability_refs", "evidence_refs",
        "evidence_status", "uncertainty", "scores", "evaluator_version",
    }
    missing = sorted(required - set(record))
    if missing:
        raise OpportunityRecordError("missing required fields: " + ", ".join(missing))
    if record["schema_version"] != SCHEMA_VERSION:
        raise OpportunityRecordError("unsupported schema_version")
    for field in ("candidate_id", "source_url", "source_revision", "observed_at",
                  "problem", "uncertainty", "evaluator_version"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise OpportunityRecordError(f"{field} must be a non-empty string")
    if not record["source_url"].startswith(("https://", "http://")):
        raise OpportunityRecordError("source_url must be an HTTP(S) URL")
    if not isinstance(record["capability_refs"], list) or not all(
        isinstance(v, str) and v.strip() for v in record["capability_refs"]
    ):
        raise OpportunityRecordError("capability_refs must be a list of non-empty strings")
    if len(set(record["capability_refs"])) != len(record["capability_refs"]):
        raise OpportunityRecordError("capability_refs must be unique")
    if not isinstance(record["evidence_refs"], list) or not all(
        isinstance(v, str) and v.strip() for v in record["evidence_refs"]
    ):
        raise OpportunityRecordError("evidence_refs must be a list of non-empty strings")
    if len(set(record["evidence_refs"])) != len(record["evidence_refs"]):
        raise OpportunityRecordError("evidence_refs must be unique")
    if record["evidence_status"] not in EVIDENCE_STATUSES:
        raise OpportunityRecordError("unknown evidence_status")
    scores = record["scores"]
    if not isinstance(scores, Mapping) or set(scores) != SCORE_KEYS:
        raise OpportunityRecordError("scores must contain exactly the versioned score fields")
    for key, value in scores.items():
        # bool is a subclass of int; explicitly disallow it.
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise OpportunityRecordError(f"scores.{key} must be an integer from 0 to 5")


def evaluate(record: Mapping[str, Any], known_capabilities: set[str] | None = None) -> Evaluation:
    """Return a stable proposal/defer/reject result; never grant execution authority."""
    validate_record(record)
    candidate_id = record["candidate_id"]
    status = record["evidence_status"]
    reasons: list[str] = []

    if status in NON_PROMOTABLE:
        reasons.append(f"evidence status {status} is not sufficient for ranking as a proposal")
        return Evaluation(candidate_id, None, "DEFER", tuple(reasons))

    if not record["evidence_refs"]:
        reasons.append("no evidence references supplied")
        return Evaluation(candidate_id, None, "DEFER", tuple(reasons))

    refs = set(record["capability_refs"])
    if known_capabilities is not None:
        unknown = sorted(refs - known_capabilities)
        if unknown:
            reasons.append("unknown capability references: " + ", ".join(unknown))
            return Evaluation(candidate_id, None, "DEFER", tuple(reasons))

    scores = record["scores"]
    raw = sum(scores[key] * weight for key, weight in WEIGHTS.items())
    # Transform weighted score to a readable 0..100 band without hiding penalties.
    score = round(max(0.0, min(100.0, raw / 3.75 * 100.0)), 2)
    if scores["security_risk"] >= 4 or scores["privacy_risk"] >= 4:
        reasons.append("high security/privacy risk requires redesign or explicit review")
        return Evaluation(candidate_id, score, "DEFER", tuple(reasons))
    if scores["evidence_strength"] <= 1:
        reasons.append("weak evidence; gather stronger evidence before implementation")
        return Evaluation(candidate_id, score, "DEFER", tuple(reasons))
    reasons.append("scored using explicit value, evidence, fit, effort, cost, risk, maintenance and reversibility")
    reasons.append("result is a proposal only; execution authority is not represented")
    return Evaluation(candidate_id, score, "PROPOSE", tuple(reasons))


def rank_opportunities(
    records: Iterable[Mapping[str, Any]],
    known_capabilities: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Rank deterministically by score descending, then candidate_id ascending."""
    results = [evaluate(record, known_capabilities).as_dict() for record in records]
    ids = [result["candidate_id"] for result in results]
    if len(ids) != len(set(ids)):
        raise OpportunityRecordError("candidate_id values must be unique in one evaluation batch")
    return sorted(
        results,
        key=lambda item: (
            item["score"] is None,
            -(item["score"] if item["score"] is not None else 0.0),
            item["candidate_id"],
        ),
    )
