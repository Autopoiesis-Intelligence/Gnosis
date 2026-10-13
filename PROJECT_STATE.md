# GNOSIS — PROJECT STATE

**State version:** 2026-09-10 / Audit baseline 1.2
**Public baseline:** Ψ-Core v33, 2026-09-03
**Detailed audit:** `GNOSIS_MASTER_AUDIT.md`
**Recovery ledger:** `RECOVERY_GAPS_2026-09-10.md`

## Current status
Gnosis is a research project investigating whether a minimal endogenous computational architecture can support recursive state evolution, model construction, autonomous hypothesis generation/testing/selection, and eventually broader machine reasoning and discovery.

The project now has two coupled tracks: the Ψ research core and a protected operational interoperability layer (memory/context, secure bridge, Internet Port, external-model adapters).

**Current stage:** consolidation of the September research record, adversarial validation, and preparation for protected internal memory. The memory subsystem is deliberately parked until the exact earlier specification is recovered; no reconstructed cryptographic design is to be treated as historical fact.

## Fundamental model
The working mathematical lineage has converged toward:

```text
Ψ = (X, R)
```

`X` is system state; `R` is relation structure. Auxiliary representation may exist, but `(X,R)` must not be claimed universally complete: the hidden-state audit established a counterexample showing that unrepresented information can invalidate extensionality.

The central requirement is endogenous evolution: the next state should arise from the current state and internal transition machinery rather than a permanently external correction operator.

## Evolution mechanism
```text
Current State → Generate candidates → Test → Select → Next State → Repeat
```

Selection must operate only on tested/accepted candidates. Rule evolution may require an explicit extended state such as `Y=(X,ρ)` rather than a hidden external rule updater.

## Current invariants
1. Fundamental working projection is Ψ=(X,R), subject to the hidden-state limitation.
2. Evolution is state-transition based.
3. Accepted candidates must pass the relevant test.
4. Selection occurs inside the evolutionary transition path.
5. Repeated steps can execute without a new external command after construction.
6. Fundamental transition behavior should be extensional over declared state; hidden metadata cannot silently control it.
7. Locality must be explicit and tested rather than assumed.
8. Memory is a derived historical representation unless explicitly promoted into the dynamical state.
9. External claims do not automatically have authority over the core.
10. Scientific claims remain separate from software behavior.
11. Reproducibility and negative results are first-class.
12. Minimum necessary complexity is preferred.

## Verified repository implementation
- `core/state.py`: `Psi(x, relations)` and immutable `State` wrapper.
- `core/engine.py`: deterministic transition, finite run and trajectory.
- `core/evolution.py`: Generate → Test → Select transition.
- `core/contract.py`: extensionality checks over the Ψ projection.
- `core/uroboros.py`: recursive wrapper and evolutionary constructor.
- `gnosis-terminal-bridge`: protected bridge/Internet Port and security contracts.
- Recent regression stages through Stage 7A are recorded as GREEN in `GNOSIS_MASTER_AUDIT.md`.

## Memory / protected context frontier
Working semantic principle:

`M = H(trajectory)`

Memory is a transformed trace of the past, not an undeclared external controller. If memory affects future evolution, that dependency must be explicit in the state/dynamics.

A protected internal memory subsystem was developed conceptually during the September conversations, including a remembered goal of fast recovery after context/memory damage. However, the exact primary-source specification and adversarial damage/recovery test set have not yet been recovered. This remains **GAP / PLANNED**, not COMPLETE.

Recovery target is recorded in `RECOVERY_GAPS_2026-09-10.md`. Do not invent or silently substitute a new cryptographic construction.

## Secure bridge / Internet Port
The operational track includes challenge binding, replay protection, expiration, fail-closed behavior, identity/provenance propagation, protocol/session/channel boundaries and the trust rule:

`Peer Claim ≠ Authority`

The bridge is a transport/security boundary, not a hidden semantic operator on Ψ.

## Interoperability
A working conceptual port is:

`P_Ψ = (Schema, Mapping, Contract, Evidence)`

Interoperability is relation-preserving translation, not an assumption of shared ontology. Uncertainty/loss must be explicit where translation is not exact.

## Not established
The repository does not establish general intelligence, consciousness, physical theory validity, Born-rule derivation, Bell nonlocality derivation, Lorentz invariance/emergence, holographic-bound derivation, Standard Model gauge-group emergence, alpha≈137 derivation, a universal theory of reality, or strong biological autopoiesis. These remain research questions unless explicit reproducible evidence exists.

## Historical convergence
```text
phenomenological intuition
→ Ψ information/process model
→ Ψ=(X,R) minimalization
→ endogenous evolution E
→ extended state/rule-state ideas
→ Generate/Test/Select
→ adversarial audits
→ hidden-state counterexample + extensionality
→ UROBOROS / Ψ-Core
→ GNOSIS v33
→ secure bridge / Internet Port
→ Living Context + protected-memory direction
→ interoperability / external-model coordination
→ current minimal-effective-core + living-state phase
```

## Current research frontier
1. Preserve the September recovery ledger and exact historical evidence.
2. Recover exact protected-memory mathematics and the fast-recovery/damage test protocol.
3. Verify implemented bridge and memory code against executable tests rather than relying on documentation.
4. Audit bridge ↔ memory ↔ Ψ trust boundaries.
5. Continue adversarial tests for extensionality, autonomy, reproducibility, locality and Generate/Test/Select integrity.
6. Keep mathematical/physics experiments in separate evidence tracks.
7. After reconciliation, remove obsolete/misleading documentation and consolidate the canonical architecture.

## Model handoff order
```text
PROJECT_STATE.md
GNOSIS_MASTER_AUDIT.md
RECOVERY_GAPS_2026-09-10.md
PHILOSOPHY.md
EVOLUTION.md
ARCHITECTURE.md
CLAIMS.md
ROADMAP.md
CHANGELOG
code + tests
```

Repository evidence overrides conversational assumptions.

## Update rule
Every material decision must update this state, preserve historical evidence, classify claims, and update the roadmap when the next experiment changes. Failed and abandoned approaches must remain traceable rather than silently deleted.
