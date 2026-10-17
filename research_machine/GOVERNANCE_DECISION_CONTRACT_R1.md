# Governance Decision Contract R1

Status: audit contract; no production governance runtime.

## Purpose

Define the decision boundary between proposal evidence and execution authority.

## Input

Governance evaluation consumes:
- proposal_id
- proposal_digest
- state_id
- state_digest
- shadow_result_digest
- evidence/provenance references

## Output

GovernanceDecision contains:
- proposal_id
- proposal_digest
- state_id
- state_digest
- decision: APPROVE | REJECT
- decision_digest
- evidence/provenance references

## Invariants

1. GovernanceDecision is a decision/evidence object only.
2. APPROVE MUST NOT itself create or consume execution authority.
3. REJECT MUST NOT create or consume execution authority.
4. A decision for a different proposal or state is invalid.
5. Tampered or incomplete evidence is rejected.
6. A stale ShadowResult is rejected.
7. Replay of a decision MUST NOT create new execution authority.
8. Governance MUST NOT invoke CanonicalExecutor.
9. Execution authority, when required, is a separate explicit boundary.
10. Governance MUST NOT mutate canonical Ψ.

## Separation

Proposal -> ShadowResult -> GovernanceDecision -> explicit execution authority -> AuthorizedExecution -> CanonicalExecutor.

APPROVE != ExecutionAuthority
ExecutionAuthority != Commit

## Required adversarial evidence

- approve leaves canonical state unchanged;
- reject leaves canonical state unchanged;
- wrong proposal/state is rejected;
- stale/tampered shadow evidence is rejected;
- decision tampering is rejected;
- replay does not create authority.
