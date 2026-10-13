import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "evaluate_opportunity.py"


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


def run_cli(tmp_path, payload):
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(input_path)],
        cwd=SCRIPT.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_evaluates_a_single_record_as_proposal_only(tmp_path):
    result = run_cli(tmp_path, candidate())
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["decision"] == "PROPOSE"
    assert output["authority"] == "PROPOSAL_ONLY"


def test_cli_defers_unknown_capability(tmp_path):
    result = run_cli(tmp_path, candidate(capability_ref="not.catalogued"))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["decision"] == "DEFER"


def test_cli_ranks_a_batch_deterministically(tmp_path):
    result = run_cli(tmp_path, [candidate("candidate-b"), candidate("candidate-a")])
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert [item["candidate_id"] for item in output] == ["candidate-a", "candidate-b"]
    assert all(item["authority"] == "PROPOSAL_ONLY" for item in output)


def test_cli_rejects_non_object_non_list_input(tmp_path):
    result = run_cli(tmp_path, "not a record")
    assert result.returncode == 2
    assert json.loads(result.stderr)["authority"] == "PROPOSAL_ONLY"
