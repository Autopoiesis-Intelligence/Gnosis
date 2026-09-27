# R2 Authority Contract — 2026-09-26

## Canonical trust path

`External Input -> ExecutionInput -> Proof -> Admission -> SemanticCommit.apply -> TransitionRecord -> SQLite`

The canonical semantic mutation authority is `SemanticCommit.apply`, after the required proof/admission gates.

## Non-authoritative surfaces

- SQLite is not semantic authority.
- Replay is not semantic authority.
- Snapshot is not semantic authority.
- Merge/resolution candidates are not authority without matching admission.
- External adapters are not trusted state writers.
- Research-Memory is evidence/context, never Core authority.
- Legacy State->State APIs are compatibility surfaces, not canonical Ψ authority.

## Recovery path

`SQLite -> Recovery -> Replay -> Verify -> Continue`

Recovery reconstructs durable state but cannot manufacture an Admission or semantic commit authority.

## Meta path

`MetaTransition -> RefinementProof -> MetaAdmission -> apply`

Meta self-change has a separate explicit proof/admission boundary.

## CI enforcement

Static/AST inventory detects direct and indirect mutation-like surfaces. Runtime adversarial tests verify that dynamic callable/type lookup does not manufacture admission authority.

## Evidence status

The R2 implementation and adversarial evidence cover the inspected production surfaces and the end-to-end durable recovery path.

The contract deliberately does **not** claim unrestricted process security. A hostile process with arbitrary memory/native/OS capabilities is outside the application-level semantic authority model and requires process isolation.

The contract also does **not** claim that future code can never introduce a new mutation surface. CI inventory is the change-detection mechanism requiring re-audit.

## Closure criterion

R2 authority is considered operationally closed for the audited surface only when:
1. every mutation-like production surface is classified;
2. canonical semantic mutation enters the required proof/admission gate;
3. persistence/recovery cannot manufacture authority;
4. adversarial bypass tests remain green;
5. CI detects introduction of new mutation-like surfaces.

This is an evidence-backed operational closure, not a universal proof of arbitrary Python execution safety.
