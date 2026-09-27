# R2 No-Bypass Mutation Matrix — 2026-09-26

## Purpose

Inventory the known state-changing or state-producing surfaces and distinguish semantic mutation authority from compatibility, reconstruction, candidate construction, and observation surfaces.

| Surface | Produces/changes state | Semantic authority | Required gate | R2 status |
|---|---:|---:|---|---|
| `core/execution.py::CanonicalExecutor.step` | yes | yes | ExecutionInput -> Proof -> Admission -> `commit().apply()` | BOUND |
| `core/execution.py::CanonicalExecutor.evolve` | yes | yes | Proof -> Admission -> deterministic Select -> `commit().apply()` | BOUND; generic-chain composition remains separate |
| `core/commit.py::SemanticCommit.apply` | yes | yes | `require_admitted` + canonicalization + guard + commit_once | BOUND |
| `core/resolution.py::commit_resolution` | creates commit object | no by itself | ResolutionCandidate + matching Admission | BOUND |
| `core/merge.py::merge` | candidate/conflict only | no | Admission required before semantic commit | NON-AUTHORITATIVE |
| `core/replay.py::replay` | reconstructed state | no | persisted hash binding | NON-AUTHORITATIVE |
| `core/snapshot.py` | cache/observation | no | replay certificate | NON-AUTHORITATIVE |
| `core/sqlite_persistence.py::commit_once` | durable history | persistence only | causal record checks + SQLite transaction | DURABLE SUBSTRATE |
| `core/legacy_engine.py::LegacyEngine` | State -> State | no canonical Ψ authority | explicit compatibility classification | ISOLATED |
| `core/evolution.py::evolutionary_transition` | State -> State | no canonical Ψ authority | legacy compatibility boundary | ISOLATED |
| `core/meta_transition.py::MetaTransition.apply` | meta-state value | scoped meta authority | refinement proof | SEPARATE META BOUNDARY |
| `core/canonical_chain.py::admit_transition` | commit result | generic canonical layer | Safety/Gas/Provenance | SEPARATE BOUNDARY |

## Critical architectural finding

`CanonicalExecutor` currently calls `commit()` directly. `canonical_chain.admit_transition()` is a separate generic boundary. This is not currently a demonstrated bypass because `SemanticCommit.apply()` itself invokes `guard_transition()` and `commit_once()`, but the two boundaries are not compositionally identical.

Therefore the safe claim is **not** “one universal mutation entrypoint”. The safe claim is that the inspected canonical Ψ path is fail-closed at `SemanticCommit`, while generic canonical-chain governance is a separate layer.

## Legacy boundary

Legacy `State -> State` APIs remain executable compatibility surfaces. They are explicitly excluded from canonical Ψ semantic authority and must not be used as evidence that all mutation surfaces are canonicalized.

## Remaining audit target

The next audit must inventory external adapters/bridges and meta-transition application, then verify that no external/public surface writes canonical history or invokes semantic mutation without entering an authoritative gate.
