# Governance Binding Identity Contract R1

Status: audit contract; no production implementation.

## Canonical identity

GovernanceBinding is an immutable identity/evidence object containing:
- proposal_id
- proposal_digest
- state_id
- state_digest
- shadow_result_digest
- governance_decision_digest

## Binding digest

binding_digest = H(
  proposal_id ||
  proposal_digest ||
  state_id ||
  state_digest ||
  shadow_result_digest ||
  governance_decision_digest
)

Fields MUST use one canonical serialization and field ordering.

## Rules

1. Any field mutation changes binding_digest.
2. Binding MUST fail closed on proposal/state mismatch.
3. Binding MUST fail closed on shadow-result mismatch or staleness.
4. Binding MUST fail closed on governance-decision mismatch or tampering.
5. GovernanceBinding is evidence/identity only; it is not execution authority.
6. GovernanceBinding MUST NOT invoke CanonicalExecutor.
7. GovernanceBinding MUST NOT mutate canonical state.
8. Replay of the same binding MUST NOT create authority.
9. External/downstream references do not become authority merely by inclusion.
10. Conversion to ExecutionInput/AuthorizationEvidence is valid only after identity verification.

## Separation

GovernanceBinding
  -> verified identity
  -> ExecutionInput
  -> AuthorizationEvidence
  -> separate Authorization
  -> AuthorizedExecution
  -> CanonicalExecutor

GovernanceBinding != ExecutionAuthority.
