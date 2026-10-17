# Governance → Authorization Binding Contract R1

Status: audit contract; no production implementation.

## Purpose

Bind a Governance decision to a later authorization request without making the Governance decision itself an authority source.

## Binding tuple

The binding MUST cover:
- proposal_id
- proposal_digest
- state_id
- state_digest
- shadow_result_digest
- governance_decision_digest

An authorization request MUST additionally bind the resulting AuthorizationEvidence.

## Separation

GovernanceDecision = decision/evidence.
AuthorizationEvidence = execution-identity evidence.
ExecutionAuthority = separate capability.
CanonicalExecutor = mutation boundary.

No object in this contract may implicitly convert decision/evidence into execution authority.

## Rules

1. REJECT produces no authorization request.
2. APPROVE alone produces no execution authority.
3. Proposal/state identity mismatch rejects the binding.
4. Shadow result mismatch or staleness rejects the binding.
5. Governance decision tampering rejects the binding.
6. AuthorizationEvidence mismatch rejects the binding.
7. Replay of the same binding cannot create a second authority.
8. Binding evaluation cannot invoke CanonicalExecutor.
9. External/downstream evidence cannot become authority merely by being referenced.
10. Canonical state remains unchanged throughout binding evaluation.

## Required evidence

- deterministic binding digest;
- identity mismatch rejection;
- stale/tampered evidence rejection;
- replay rejection;
- proof that binding evaluation does not invoke canonical mutation;
- proof that authority is created only by the separate authorization boundary.
