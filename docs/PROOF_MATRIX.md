# Gnozis Proof Matrix — 2026-09-26

Status: reconciled against current main repository evidence.

Legend:
- IMPLEMENTED: code exists and repository evidence directly supports the contract.
- PARTIAL: a boundary/approximation exists, but the full mathematical/architectural contract is not established.
- COMPLETE(scope): evidence covers the declared audited scope, not universal execution safety.
- UNVERIFIED: implementation/tests exist, but this pass did not execute the suite.

This document is an audit map, not a universal proof claim.

| ID | Requirement | Current evidence | Status | Remaining |
|---|---|---|---|---|
| PM-01 | Psi=(X,R) core | core/state.py::Psi | IMPLEMENTED | typed X/R boundary |
| PM-02 | State is adapter | legacy State -> State paths explicitly isolated | PARTIAL | eliminate/fully isolate competing transition paths |
| PM-03 | Deep immutability | recursive freeze | IMPLEMENTED* | custom payload boundary |
| PM-04 | Generate→Test→Proof/Admission→Select→Transition | core/evolution.py, proof/admission stack | PARTIAL | explicit architectural separation |
| PM-05 | Apply cannot bypass Admission | SemanticCommit.apply + canonical regression tests | COMPLETE(scope) | continue regression on new mutation surfaces |
| PM-06 | Selection not external oracle | deterministic endogenous selection | PARTIAL | universal proof |
| PM-07 | Partial-order branches | Branch/ParallelOutcome | COMPLETE(scope) | regression |
| PM-08 | Conflict retained | Conflict/Resolution/DeferredConflict | COMPLETE(scope) | regression |
| PM-09 | Protected K0 | RootInvariant/MetaTransition | COMPLETE(scope) | stronger kernel binding |
| PM-10 | Meta refinement | MetaAdmission + refinement proof | COMPLETE(contract) | machine-proof semantics |
| PM-11 | Gas bound | GasBudget + executor gates | COMPLETE(scope) | prove all future operation paths |
| PM-12 | Append-only history | AppendOnlyHistory + SemanticCommit binding | COMPLETE(scope) | continued adversarial coverage |
| PM-13 | SQLite representation, not truth | SQLiteHistoryStore + durable transaction/recovery tests | COMPLETE(scope) | physical storage guarantees remain out of scope |
| PM-14 | Deterministic replay | replay() + persisted state/causal hash binding | COMPLETE(scope) | broader kernel dispatch proof |
| PM-15 | Snapshot != truth | SnapshotCertificate + replay validation | COMPLETE(scope) | continued invalidation regression |
| PM-16 | Crash atomicity/idempotence | commit_once() + failure injection + recovery/continuation tests | COMPLETE(scope) | physical power-loss guarantees out of scope |
| PM-17 | Kernel/provenance attached | TransitionRecord + provenance binding | COMPLETE(scope) | broader integration |
| PM-18 | Evidence separated from commit | provenance/admission/commit separation | COMPLETE(scope) | broader integration |
| PM-19 | Hard stop unresolved | Safety + Gas gates in canonical paths | NEAR-COMPLETE | prove every public operation path uses required chain |
| PM-20 | External actor no authority | authority/commit boundary + external adapter classification | NEAR-COMPLETE | maintain public caller inventory |
| PM-21 | Protected kernel/workspace | protected memory boundary remains separate from commit chain | NEAR-COMPLETE | bind protected state/persistence |
| PM-22 | Machine-checked proof | formal/MinimalCore.lean target | PARTIAL | replace placeholder propositions with actual Core definitions/invariant proofs |

## Reconciliation result

The previous matrix contained stale claims, notably PM-13 saying that SQLite was absent even though current main contains SQLiteHistoryStore, transaction failure injection, recovery, replay and continuation evidence.

Current evidence supports closing PM-13/14/15/16 at the audited application scope. This does not prove physical storage behavior or universal no-bypass.

### Remaining critical gaps

1. PM-02: competing legacy State -> State transition surfaces remain.
2. PM-04 and PM-06: architectural/formal contracts are not yet universal.
3. PM-19–PM-21: authority and protected-workspace coverage still require broader public-path integration.
4. PM-22: machine proof still requires real Core definitions and invariant preservation.
5. Test execution status must be obtained from CI/local execution before claiming runtime-suite verification.

The matrix is intentionally evidence-scoped rather than marked universally complete.
