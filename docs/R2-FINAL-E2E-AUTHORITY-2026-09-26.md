# R2 Final E2E Authority Evidence — 2026-09-26

## Final contract

The audited authority chain is:

`External Input -> ExecutionInput(identity + digest) -> Proof -> Admission -> SemanticCommit -> TransitionRecord -> SQLite -> Crash -> Recovery -> Replay -> Verify -> Continue`

The final execution-input check binds both `state_id` and `state_digest`. A substituted state therefore cannot satisfy the original execution identity merely by preserving an external label.

External input itself carries no commit/apply authority.

## Evidence boundary

This document closes the application-level R2 authority contract for the inspected surfaces. It does not claim unrestricted process security or physical storage guarantees.

Future mutation surfaces remain subject to the CI inventory invariant and must receive an explicit authority classification.
