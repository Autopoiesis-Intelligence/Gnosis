"""Audit-only adversarial evidence specification for Governance Decision Contract R1.

No production governance runtime is introduced by this fixture.
"""

CASES = (
    "approve_does_not_mutate_canonical_state",
    "reject_does_not_mutate_canonical_state",
    "wrong_proposal_or_state_is_rejected",
    "stale_shadow_result_is_rejected",
    "tampered_evidence_or_decision_is_rejected",
    "replay_does_not_create_execution_authority",
    "approve_does_not_invoke_canonical_executor",
)

EXPECTED = {
    case: "no canonical mutation and no execution authority"
    for case in CASES
}
