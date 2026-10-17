# Authorization Handoff Contract R1

Status: audit contract; no new authority runtime.

## Purpose

Define the boundary between a Governance decision and the existing execution-authorization mechanism.

## Handoff input

A handoff request must bind:
- proposal_id
- proposal_digest
- state_id
- state_digest
- governance_decision_digest
- shadow_result_digest
- evidence/provenance references

## Rules

1. REJECT MUST NOT create authorization.
2. APPROVE MUST NOT itself create canonical mutation.
3. Approval is not execution authority.
4. Authorization is created only by the separate authorized authority boundary.
5. The handoff MUST NOT invoke CanonicalExecutor directly.
6. Proposal/state identity mismatch MUST reject the handoff.
7. Stale or tampered Governance/Shadow evidence MUST reject the handoff.
8. Replay MUST NOT create a second authorization.
9. An authorization, when issued, is consumed only through AuthorizedExecution.
10. External/downstream evidence is never itself an authority source.

## Separation

GovernanceDecision
  -> AuthorizationHandoff
  -> separate authority decision
  -> AuthorizedExecution
  -> CanonicalExecutor

GovernanceDecision != ExecutionAuthority
Authorization != Commit

## Required adversarial evidence

- REJECT creates no authorization;
- APPROVE creates no canonical mutation by itself;
- mismatched proposal/state is rejected;
- stale/tampered decision or shadow evidence is rejected;
- replay cannot create a second authorization;
- handoff cannot directly invoke CanonicalExecutor.
