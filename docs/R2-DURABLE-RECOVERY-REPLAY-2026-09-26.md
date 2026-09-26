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


## Cross-record authorization binding gate

Durable authorization consumption is now bound to the committed sequence, execution-state digest, and candidate hash. The authorization identity remains immutable and one-time; execution-state metadata is evidence of what the authorization actually consumed.

The external execution boundary also checks the durable consumption index before entering canonical execution. Therefore a previously consumed authorization cannot be transferred to a later/successor state or another transition record, even when the new request reaches a structurally valid execution boundary.

The atomic UNIQUE authorization key remains the final commit-time race/conflict barrier. Recovery additionally verifies that persisted candidate binding is consistent with the referenced transition record.

CI evidence: Tests, Architecture Gate and Gnozis Port CI are GREEN at HEAD 32d6fc39025766e747100f8e0c804bace9a60c76.


## Persistence integrity gate — full evidence transaction

The durable commit boundary now has adversarial evidence for the complete History + Provenance + Authorization-consumption + Audit unit. A failure injected after authorization consumption but before audit insertion rolls back all four records; no partial durable evidence remains.

A second test mutates persisted authorization candidate binding after a successful commit. Verification fails closed and refuses to treat the tampered authorization evidence as valid.

CI evidence: Tests, Architecture Gate and Gnozis Port CI are GREEN at HEAD e68621b9d5b6e6bf93dba5a64d1b06c2a58d858b.


## Cross-table consistency gate

Recovery now verifies the complete durable evidence graph across transition history, provenance, audit chain, and authorization consumption. Independent tampering of candidate, evidence, provenance, or transition bindings is detected fail-closed; audit digest verification remains an earlier integrity barrier.

Adversarial coverage includes independent mutation of each cross-table binding and CI confirmation after the initial assertion was corrected to test the invariant (fail-closed), rather than a particular detection ordering.

CI evidence: Tests, Architecture Gate and Gnozis Port CI all GREEN at HEAD 3ea6ec07a33eadcbd4eac1cb94dcf6c46d1eed72.


## Durable chain continuity gate

Recovery-side durable verification now enforces contiguous transition sequence, genesis predecessor, predecessor state-hash linkage, and predecessor audit-hash linkage. Adversarial coverage exercises first-record deletion, middle-record deletion, sequence uniqueness, and predecessor-hash mutation. SQLite primary-key uniqueness rejects duplicate sequence insertion at the storage boundary; recovery rejects all resulting chain mutations fail-closed.

A CI assertion mismatch was corrected without weakening the invariant: predecessor corruption remains classified as transition-binding failure while the stronger chain-continuity checks remain active.

CI evidence: Architecture Gate and Gnozis Port CI are GREEN on HEAD 6b96c113bf8c987cee6c2ae2ca6903d72540ec15; Tests is still running at the time of this record.
