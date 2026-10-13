from tools.capability_catalogue import evaluate_with_catalogue, rank_with_catalogue


def candidate(candidate_id="candidate-a", capability_ref="opportunity.evaluate-curated-records"):
    return {
        "schema_version": "1.0",
        "candidate_id": candidate_id,
        "source_url": "https://example.org/issue/42",
        "source_revision": "snapshot:example-42",
        "observed_at": "2026-10-13T12:00:00Z",
        "problem": "Find a bounded improvement opportunity.",
        "capability_refs": [capability_ref],
        "evidence_refs": ["https://example.org/issue/42#evidence"],
        "evidence_status": "SUPPORTED",
        "uncertainty": "Outcome has not yet been measured in runtime.",
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


def test_catalogue_bridge_allows_matching_ci_proven_capability():
    result = evaluate_with_catalogue(candidate()).as_dict()
    assert result["decision"] == "PROPOSE"
    assert result["authority"] == "PROPOSAL_ONLY"


def test_catalogue_bridge_defers_unknown_capability():
    result = evaluate_with_catalogue(candidate(capability_ref="unknown.capability")).as_dict()
    assert result["decision"] == "DEFER"
    assert "unknown capability" in result["reasons"][0]


def test_catalogue_bridge_batch_rank_keeps_proposal_only_boundary():
    results = rank_with_catalogue([
        candidate("candidate-b"),
        candidate("candidate-a"),
    ])
    assert [item["candidate_id"] for item in results] == ["candidate-a", "candidate-b"]
    assert all(item["authority"] == "PROPOSAL_ONLY" for item in results)
