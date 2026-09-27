# Shadow Evaluation Contract R1

Status: audit contract / no production runtime authority

## Purpose

Define the minimum boundary for evaluating a proposal without mutating canonical state.

## Input

A shadow evaluation consumes:
- proposal_id
- proposal_digest
- state_id
- state_digest
- evaluation_input_digest

All identities are bound to the exact evaluated proposal and state.

## Output

A ShadowResult contains:
- proposal_id
- proposal_digest
- state_id
- state_digest
- outcome: PASS | FAIL
- result_digest
- provenance reference

## Invariants

1. Shadow evaluation MUST NOT mutate canonical Ψ.
2. Shadow evaluation MUST NOT consume execution authority.
3. PASS MUST NOT imply Governance approval.
4. PASS MUST NOT imply execution authorization.
5. FAIL MUST NOT mutate canonical Ψ.
6. A result for a different proposal or state MUST be rejected.
7. Tampered result/provenance MUST be rejected.
8. Replay must preserve identity binding and MUST NOT create a new authority.
9. Shadow output is evidence only until a separate Governance and execution-authority boundary is crossed.

## Required adversarial evidence

- PASS leaves canonical state unchanged.
- FAIL leaves canonical state unchanged.
- proposal/state substitution is rejected.
- result tampering is rejected.
- replay does not create authority.
