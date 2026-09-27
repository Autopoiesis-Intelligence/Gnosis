# Pure Shadow Evaluator Contract R1

Status: audit contract; no production implementation.

## Function

evaluate(proposal, state_snapshot) -> ShadowResult

## Preconditions

- proposal identity and digest are present
- state identity and digest are present
- evaluation input is bound to the exact proposal and state

## Postconditions

- returns PASS, FAIL, or ERROR
- does not mutate canonical state
- does not consume or create execution authority
- does not create a canonical transition
- does not invoke CanonicalExecutor
- result is bound to proposal_id/proposal_digest and state_id/state_digest

## Formal invariants

For every evaluation result r:

Delta(Psi_canonical) = 0
Delta(ExecutionAuthority) = 0
Delta(CanonicalHistory) = 0

A result for another proposal or state is invalid.
Tampered result/provenance is invalid.
Replay cannot create authority.

## Separation

ShadowResult is evidence only.

Shadow PASS != Governance approval
Governance approval != Execution authorization
Execution authorization != Commit

## Required adversarial evidence

1. PASS leaves canonical state unchanged.
2. FAIL leaves canonical state unchanged.
3. ERROR leaves canonical state unchanged.
4. proposal substitution is rejected.
5. state substitution is rejected.
6. result/provenance tampering is rejected.
7. replay cannot create authority.
