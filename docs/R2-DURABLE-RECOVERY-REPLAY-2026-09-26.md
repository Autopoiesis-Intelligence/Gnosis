# R2 Durable Recovery -> Replay -> Continue — 2026-09-26

## End-to-end contract

The persistence boundary is now tested through the complete recovery path:

`Commit -> injected process stop -> durable DB -> Reload -> Replay -> Verify -> Continue Commit`

A process stop after SQLite `COMMIT` is not treated as a failed semantic commit merely because the caller did not receive the return value. Recovery reads the durable history, replay reconstructs the state, and the next causal transition can continue from that recovered state.

## Adversarial condition

The same end-to-end path must fail closed when a persisted record claims a state hash that does not match the state reconstructed by its replay applier.

## Evidence

The integration tests cover:

- post-commit process-stop simulation;
- reopening the SQLite database;
- replay of the durable history;
- continuation with the next causally linked record;
- full replay after continuation;
- rejection when replay produces a state different from the persisted state hash.

## Boundary

This proves the Core persistence/replay contract at the application level. It does not prove physical power-loss durability, filesystem hardware behavior, or OS-level storage guarantees.


## Authorization replay-after-restart gate

An authorization-bearing external execution request is now bound to a stable request digest and consumed atomically in the same SQLite transaction as History + Provenance + Audit.

The adversarial test performs:

`authorized request -> durable commit -> simulated restart -> durable recovery/replay -> reuse of the same request against the recovered state -> reject`

The rejected replay leaves the durable transition count unchanged and preserves exactly one authorization-consumption record. A conflicting replay cannot become a new committed transition merely because the original authorization survived process restart.

This closes the persistence/restart authorization-replay gate at the application level. It does not claim protection against physical storage rollback, filesystem snapshots restored to an earlier point, or external authorization systems that are themselves mutable outside Core.


## Authorization provenance tamper gate

Recovery now validates durable authorization-consumption evidence before replay. The adversarial test mutates the persisted consumption event after a valid commit; recovery fails closed instead of reconstructing an executable state from tampered authorization evidence.

CI evidence: Tests, Architecture Gate and Gnozis Port CI all GREEN on the resulting implementation.
