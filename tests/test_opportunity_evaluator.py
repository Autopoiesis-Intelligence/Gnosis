from copy import deepcopy

import pytest

from tools.opportunity_evaluator import (
    OpportunityRecordError,
    evaluate,
    rank_opportunities,
)


def candidate(candidate_id="candidate-a", **overrides):
    record = {
        "schema_version": "1.0",
        "candidate_id": candidate_id,
        "source_url": "https://example.org/issue/42",
        "source_revision": "commit:abc123",
        "observed_at": "2026-10-13T12:00:00Z",
        "problem": "Reduce repeated manual repository context reconstruction.",
        "capability_refs": ["docs.context-contract"],
        "evidence_refs": ["https://example.org/issue/42#comment-7"],
        "evidence_status": "SUPPORTED",
        "uncertainty": "Impact has not yet been measured in runtime.",
        "scores": {
            "user_value": 5,
            "evidence_strength": 4,
            "capability_fit": 5,
            "effort": 2,
            "cost": 1,
            "security_risk": 1,
            "privacy_risk": 1,
            "maintenance_burden": 2,
            "reversibility": 5,
        },
        "evaluator_version": "gnosis-opportunity-score/1",
    }
    record.update(overrides)
    return record


def test_supported_candidate_is_proposal_only():
    result = evaluate(candidate(), {"docs.context-contract"}).as_dict()
    assert result["decision"] == "PROPOSE"
    assert result["score"] is not None
    assert result["authority"] == "PROPOSAL_ONLY"


def test_unresolved_candidate_is_deferred_not_promoted():
    result = evaluate(candidate(evidence_status="UNRESOLVED")).as_dict()
    assert result["decision"] == "DEFER"
    assert result["score"] is None


def test_unknown_capability_is_deferred():
    result = evaluate(candidate(), {"other.capability"}).as_dict()
    assert result["decision"] == "DEFER"
    assert "unknown capability" in result["reasons"][0]


def test_high_privacy_or_security_risk_is_deferred():
    record = candidate()
    record["scores"]["privacy_risk"] = 4
    assert evaluate(record).decision == "DEFER"


def test_missing_source_revision_is_rejected():
    record = candidate(source_revision="")
    with pytest.raises(OpportunityRecordError, match="source_revision"):
        evaluate(record)


def test_boolean_is_not_accepted_as_a_score():
    record = candidate()
    record["scores"]["user_value"] = True
    with pytest.raises(OpportunityRecordError, match="integer from 0 to 5"):
        evaluate(record)


def test_duplicate_candidate_ids_in_batch_are_rejected():
    with pytest.raises(OpportunityRecordError, match="candidate_id values must be unique"):
        rank_opportunities([candidate("same"), candidate("same")])


def test_rank_order_and_tie_breaking_are_deterministic():
    a = candidate("candidate-a")
    b = candidate("candidate-b")
    assert rank_opportunities([b, a]) == rank_opportunities([a, b])
    assert [r["candidate_id"] for r in rank_opportunities([b, a])] == [
        "candidate-a", "candidate-b"
    ]


def test_input_records_are_not_mutated():
    record = candidate()
    before = deepcopy(record)
    evaluate(record)
    assert record == before


def test_rejected_evidence_cannot_be_scored_as_proposal():
    assert evaluate(candidate(evidence_status="REJECTED")).decision == "DEFER"
