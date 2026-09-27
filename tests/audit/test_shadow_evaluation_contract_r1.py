"""Audit-only adversarial specification for Shadow Evaluation R1.

This fixture is intentionally non-production: it specifies the evidence cases
that a future Shadow runtime must satisfy without granting execution authority.
"""

CASES = (
    "pass_does_not_mutate_canonical_state",
    "fail_does_not_mutate_canonical_state",
    "proposal_substitution_is_rejected",
    "state_substitution_is_rejected",
    "tampered_result_or_provenance_is_rejected",
    "replay_does_not_create_authority",
)

EXPECTED_INVARIANTS = {
    case: "no canonical mutation and no execution authority consumption"
    for case in CASES
}
