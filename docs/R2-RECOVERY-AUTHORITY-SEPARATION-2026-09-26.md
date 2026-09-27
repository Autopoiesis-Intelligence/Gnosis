# R2 Recovery Authority Separation — 2026-09-26

## Contract

Recovery produces durable history and reconstructed state. It does not produce an `Admission`, `SemanticCommit`, or any other semantic execution authority.

The authority boundary remains:

`recovered history -> replay -> reconstructed Psi -> proof/admission -> SemanticCommit`

A recovered `Psi` is therefore an input to the canonical semantic pipeline, not an implicit accepted state.

Snapshots are likewise observation/cache values. They carry certification metadata but expose no semantic apply/commit operation.

## Adversarial evidence

Tests assert that:

- recovered replay results have no admission or commit capability;
- snapshots are not `Admission` values and have no mutation methods;
- a raw recovered `Psi` is rejected by `require_admitted()`.

## Result

The persistence/recovery layer is downstream of semantic authority. It can restore what was durably recorded, but it cannot manufacture authority that was not present in the canonical admission/commit boundary.

This closes the recovery-to-authority bypass contract at the object/API boundary. It does not claim universal no-bypass across every legacy/compatibility path; PM-02 remains separately tracked.
