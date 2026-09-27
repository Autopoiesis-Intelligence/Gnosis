# Mathematical Reverse Mapping Contract — MRM-01

**Date:** 2026-09-24  
**Status:** ACTIVE — analytical, evidence-gated  
**Purpose:** mathematically map the current Gnozis ecosystem, its participants, project-state dimensions, dependencies and tensions before optimizing the next execution contracts.

## 1. Principle

This contract does **not** build a mathematical economy or assign permanent economic value to participants.

It creates a minimal formal reverse map:

`CurrentState + Actors + Contributions + Constraints + Evidence -> DevelopmentGraph`

The output must be sufficient to determine which contracts can proceed in parallel, which are blocked, and which missing invariants must be implemented before the next transition.

## 2. Actor model

For actor `i` record:

`A_i = (Role_i, Contribution_i, Evidence_i, Authority_i, Dependencies_i)`

Actors are evaluated by their role and verified contribution within a contract graph, not by personal worth or a global ranking.

Candidate classes include owner, developer, AI platform, auditor, researcher, partner, tester, user, external service, independent Core and future agent.

## 3. Project state vector

Maintain separate dimensions rather than collapsing maturity into one score:

`G = (K,L,C,P,A,I,M)`

- `K` Core integrity/completeness
- `L` Self-Learning evidence
- `C` Contract maturity
- `P` Provenance
- `A` Authority/security
- `I` Integration readiness
- `M` Market readiness

Every value must be backed by repository evidence, tests, CI evidence, or an explicitly marked UNVERIFIED/THEORETICAL state.

## 4. Relationship weight

For a relationship between actors/domains `i,j`:

`W_ij = f(Evidence, Authority, Dependency, Risk, Contribution, ContractStatus)`

The result is a dependency/trust/permission map, not a political, personal or financial ranking.

## 5. Contract transition

Every proposed development transition must be representable as:

`S_t -> S_(t+1)`

with Preconditions, Contract, Required Evidence, Acceptance criteria, Dependencies, and Rollback/failure condition.

No roadmap step is credited as implemented merely because it is documented.

## 6. Tension reverse map

For each material contradiction:

`Tension -> Constraints -> CandidateProposals -> Verification -> SelectableTransition`

Hard constraints remain non-negotiable. Optimization occurs only inside the permitted solution space.

## 7. Contribution provenance

Where contribution hashing is applicable:

`Contribution -> Evidence -> Hash -> Parent/Dependency Graph -> Verified Result`

A contribution hash is evidence of provenance, not an automatic claim of legal ownership, future value or revenue.

## 8. Parallelism rule

Contracts may execute in parallel only when their dependency sets do not require an unverified predecessor:

`CanParallel(C_i,C_j) = Dependencies(C_i) ∩ Blockers(C_j) = ∅`

Shared mutable boundaries, authority issuance, schema migrations and other non-commutative operations require explicit sequencing.

## 9. Required output

The reverse analysis must produce:

1. Actor Weight Map
2. Project State Vector
3. Contradiction/Gap Map
4. Dependency Graph
5. Parallelizable Contract Set
6. Blocked Contract Set
7. Minimal next-state route
8. Evidence gaps preventing stronger conclusions

## 10. Acceptance

MRM-01 is complete only when the route can explain **why** each next contract is required, what it depends on, what evidence will close it, and which contracts can proceed concurrently.

No single global percentage may substitute for this map.

## 11. Next

After MRM-01 reaches VERIFIED status, optimize the existing contract registry against the resulting dependency graph. Do not introduce a new economic scoring system before this reverse map is complete.


## 12. Stage-7 runtime-to-formal mapping

| Runtime contract | Formal target | Executable evidence | Status |
|---|---|---|---|
| Canonical K0 authority | `RootInvariant.lean` | root-invariant/admission adversarial tests | VERIFIED at runtime; formal refinement pending |
| Proof-before-commit | `AdmissionCommit.lean` | admission/commit tests | VERIFIED at runtime; formal refinement pending |
| Admission boundary | `AdmissionCommit.lean` | no-bypass tests | VERIFIED at runtime; formal refinement pending |
| Persistence != authority | no complete formal theorem yet | restart/persisted-evidence tests | RUNTIME VERIFIED |
| Authorization != replay permission | no complete formal theorem yet | durable replay tests | RUNTIME VERIFIED |
| Runtime/formal semantic projection | `RuntimeConformance.lean` | no complete executable bridge theorem | THEORETICAL/BRIDGE PENDING |

### Stage-7 acceptance rule

A row may move to VERIFIED only when the same semantic proposition is represented in the formal layer and connected to executable evidence. Existing Lean files are therefore treated as proof targets, not as evidence that the full architecture has already been formally verified.

Current conclusion: runtime trust-boundary evidence is stronger than the current formal correspondence. The remaining Stage-7 work is to close that correspondence without introducing a second authority or state model.


### Stage-7 formal bridge update

`formal/RootInvariant.lean` now contains an explicit `Kernel`/`canonicalK0` target corresponding to the runtime sealed-kernel condition, plus a preservation theorem. This is a formal proof target and correspondence anchor; it is not yet a proof that arbitrary Python runtime states are represented by this Lean `Kernel`. That runtime representation theorem remains pending.


### Stage-7 admission formal bridge

`formal/AdmissionCommit.lean` now exposes `RuntimeAdmissionEquivalent` and proves that the formal semantic commit requires the same proof/invariant/viability conditions represented by the runtime admission boundary. CI at HEAD `6d777739fe7db8b7e7f7b46982133f00fdf8544f` is GREEN. Full executable runtime-to-Lean state representation remains a separate pending bridge.


### Stage-7 transition bridge

`core/psi_transition.py::PsiTransition` is now explicitly bounded to the canonical `Psi=(X,R)` projection. The formal layer records the corresponding `PsiOperator` boundary and projection-commutation obligation. Adversarial runtime coverage confirms auxiliary State metadata cannot enter the fundamental transition. CI at HEAD `20809811a7bc5741ea915ffc8f600b97109b6847`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS. Full theorem-level correspondence of arbitrary Python `PsiTransition.function` with a Lean function remains pending.


### Stage-7 K0/Ψ boundary result

Reverse-analysis found an important type-boundary correction: canonical K0 is a kernel authority, not a predicate over Ψ. The formal model therefore keeps `Ψ` transition and K0 kernel preservation as separate components of `Sigma`; a certified transition must carry an explicit root-preservation certificate. This avoids collapsing the two state domains into a second authority model. CI at HEAD `0b6e4f95a517761c0c67c913359a177aac27023a`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


### Stage-7 Ψ/K0 runtime separation evidence

Adversarial tests now establish that `PsiTransition` can change only the canonical `Ψ=(X,R)` projection and cannot self-authorize a kernel/K0 change. A valid K0 before/after pair requires the explicit canonical invariant and `preserve_root`; a forged `sealed=False` kernel remains outside authority regardless of a successful Ψ transition. CI at HEAD `b0cb6320a2a6914d661b3db84c700f984cf2cf94`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


### Stage-7 evidence/proof authority gate

Evidence and provenance are now explicitly non-constructive with respect to certification. Runtime regression rejects evidence-rich but failed proof; formal `CertifiedTransition` can only exist with explicit `Admission` and `preserves_root` fields. The formal theorem `evidence_does_not_imply_certified_transition` captures the boundary. CI at HEAD `99e8b793d0c223232368c5d6195eed2ed28bc8aa`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


### Stage-7 fundamental/evolutionary admission bridge

The runtime distinction is now explicitly represented in the formal layer: `FundamentalAdmission` requires only `passed ∧ invariant_ok`; `EvolutionaryAdmission` additionally requires `viable`. Regression tests prove the same distinction at runtime (`fundamental + viable=False` accepted; `evolutionary + viable=False` rejected). This closes the semantic mismatch without strengthening the fundamental regime artificially. CI at HEAD `ef98b97465e692441158fa5983f517491d5c6972`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


### Stage-7 end-to-end certification gate

The runtime end-to-end gate now covers both regimes: `fundamental` with `viable=False` is admitted; `evolutionary` requires viability; both accepted paths require an independent valid K0 `MetaTransition`; a valid K0 certificate cannot upgrade a rejected Ψ admission. This closes the runtime authority composition boundary. CI at HEAD `f955b52444dde7ac38363420f38e7c3e7e5df87c`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


### Stage-8 gate definition

Stage 7 is closed only for the scoped certification boundary above. Stage 8 remains gated pending a repository-wide contract inventory and formal/runtime consistency audit. No new mathematical contract or architecture is to be introduced until existing formal targets, runtime evidence, persistence/replay boundaries, and the MRM-01 registry are reconciled against the current HEAD.


### Stage-8 reconciliation checkpoint — 10%

Current HEAD reconciliation establishes:

| Boundary | Runtime evidence | Formal status | Stage-8 action |
|---|---|---|---|
| K0 authority | VERIFIED | correspondence target exists | reconcile historical status |
| Admission / commit | VERIFIED | regime-aware target exists | reconcile historical status |
| Ψ projection / transition | VERIFIED | projection boundary exists | identify remaining theorem gap |
| Evidence / certification | VERIFIED | non-construction theorem exists | retain |
| Persistence / restart replay | VERIFIED | no complete formal theorem | formal target required only if Stage-8 contract selects it |
| Authorization / replay | VERIFIED | no complete formal theorem | formal target required only if Stage-8 contract selects it |

Important distinction: Stage-7's 100% is scoped to the defined trust-boundary certification contract; it does not mean that every persistence/replay property is formally verified in Lean.

The repository therefore enters Stage 8 with **reconciliation, not expansion** as the active operation. The next contract must be selected from an evidence-backed remaining gap, with no duplicate state/authority model.


### Stage-8 durable authorization formal target — 30%

Added `formal/DurableAuthorization.lean`. The first minimal theorem target is intentionally narrower than full persistence verification: durable consumption is an independent fact keyed by authorization identity; recovery must preserve that fact; a consumed authorization therefore cannot become executable again after recovery. This does not yet claim equivalence with SQLite implementation. Runtime restart tests remain the implementation evidence.


### Stage-8 authorization ↔ SQLite mapping — 40%

Reverse mapping exposed and closed a real binding gap: `authorization_consumption.state_digest` was persisted but not validated against the transition's pre-state (`previous_hash`). It is now fail-closed checked. The mapping is: `authorization_digest → consumed identity`; `state_digest → pre-transition state`; `candidate_hash → committed candidate`; `sequence → durable transition`. An adversarial test rejects forged `state_digest` after restart. Formal `ConsumptionBinding` records the identity/state binding without creating a second authority model.


### Stage-8 genesis authorization binding correction — 45%

CI exposed that `authorization_state_digest` is the canonical digest of the actual pre-transition Ψ, while `TransitionRecord.previous_hash` intentionally remains the history-chain sentinel `genesis` for sequence 0. The correct bridge is therefore `sequence=0 → initial_state_digest supplied by recovery`, and `sequence>0 → previous durable state_hash`. Recovery now supplies `state_digest(genesis)` to the persistence verifier. This preserves the existing history-chain semantics and closes the authorization binding without changing the state model.


### Stage-8 consistency-context distinction

`verify_cross_table_consistency()` remains a structural/durable consistency check when no initial Ψ digest is supplied. Full genesis authorization-state binding is performed when recovery supplies `initial_state_digest`; then `sequence=0` is bound to the actual recovered initial Ψ digest. This avoids conflating structural persistence validation with contextual authorization verification and preserves existing callers without weakening the recovery trust boundary.


### Stage-8 atomicity matrix — 60% pending CI

The durable commit path is now tested across every pre-COMMIT failure injection point: `before_transaction`, `before_insert`, `after_history_before_audit`, `after_history_before_provenance`, `after_provenance_before_audit`, `after_authorization_before_audit`, and `after_audit_before_commit`. Each case requires rollback of transition history, provenance, audit, and authorization consumption, and leaves the authorization reusable. `after_commit` remains a separate post-commit invariant because rollback is no longer possible after SQLite COMMIT.


### Stage-8 pre-COMMIT atomicity — VERIFIED / 60%

CI is GREEN on `e753179a`: the pre-COMMIT failure matrix passes. Every injected failure before COMMIT leaves no partial history/provenance/audit/authorization consumption. Next boundary is post-COMMIT failure: the durable artifacts must remain present and authorization must remain consumed exactly once.


### Stage-8 post-COMMIT durability — 70% pending CI

CI is GREEN on `9135093f`: post-COMMIT failure leaves the durable history/provenance/audit/authorization set intact and authorization remains consumed. Added the final restart bridge test: after a post-COMMIT injected failure, recovery reconstructs the committed Ψ and a fresh executor rejects replay of the same authorization. This is the direct durable-restart adversarial path.


### Stage-8 durable restart/replay gate — 100% VERIFIED

The complete adversarial persistence/restart authorization contract is verified by the GREEN Tests, Architecture Gate, and Gnozis Port CI on `ecf74f5f`. The verified chain covers pre-COMMIT rollback, post-COMMIT durability, restart recovery, authorization replay rejection, durable authorization tamper rejection, durable history/provenance/audit tamper rejection, and observational recovery. Recovery does not create or consume authority.


### R2-MATH↔RUNTIME — Admission/Commit mapping: 40%

Formal `Admission`/`SemanticCommit` is mapped to the runtime boundary: `PsiTransition` is a pure candidate-producing operator; `prove_transition` creates proof obligations; `admit` filters candidates; `CanonicalExecutor` owns durable SemanticCommit. The formal model therefore assigns commit authority only after admission, while transition/evolution remains non-authoritative.


### R2-MATH↔RUNTIME — Admission/Select boundary: 50%

Runtime evidence confirms rejected candidates terminate before selection. `admit()` produces immutable accepted/rejected results; `CanonicalExecutor.evolve()` constructs `valid = [admission for admission if accepted]` and only then applies deterministic `min(...)`. Therefore Select has no path to revive or repair a rejected candidate. Commit receives only the selected admitted candidate. This maps formal admission as a prerequisite to semantic selection/commit rather than making Select an authority source.
