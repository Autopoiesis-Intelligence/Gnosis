# Governance Binding → ExecutionInput Adapter Contract R1

Status: audit contract; no production implementation.

## Purpose

Define the smallest runtime adapter boundary capable of converting a verified GovernanceBinding into the existing ExecutionInput identity model.

## Preconditions

The adapter MUST verify:
- proposal identity;
- state_id;
- state_digest;
- shadow_result_digest;
- governance_decision_digest;
- binding_digest.

## Output

Only after successful verification may the adapter construct the existing ExecutionInput:
- input_type
- state_id
- state_digest
- content_digest

## Rules

1. The adapter MUST NOT create execution authority.
2. The adapter MUST NOT invoke CanonicalExecutor.
3. The adapter MUST NOT mutate canonical Psi.
4. Proposal/state mismatch MUST fail closed.
5. Shadow or governance evidence mismatch MUST fail closed.
6. Binding digest mismatch MUST fail closed.
7. The resulting ExecutionInput MUST retain exact state identity.
8. Conversion MUST be deterministic for identical verified inputs.
9. Replay of conversion MUST NOT create authority.
10. Authorization remains a separate explicit boundary after conversion.

## Separation

GovernanceBinding
 -> verify
 -> ExecutionInput
 -> AuthorizationEvidence
 -> separate Authorization
 -> AuthorizedExecution
 -> CanonicalExecutor

Adapter != Authority.
Adapter != Executor.
Adapter != Commit.

## Required evidence

- valid conversion preserves state identity;
- invalid proposal/state fails;
- stale/tampered shadow or governance evidence fails;
- binding digest tampering fails;
- repeated conversion has no authority side effect;
- canonical state remains unchanged.
