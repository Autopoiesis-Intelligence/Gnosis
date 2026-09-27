# PM-05 Semantic Apply Path Audit — 2026-09-18

## Classification

| Path | Classification | Semantic Ψ authority |
|---|---|---|
| core/psi_engine.py PsiEngine(PsiTransition) | CANONICAL Ψ | Yes |
| core/engine.py Engine(PsiTransition) | CANONICAL Ψ execution boundary | Yes |
| core/uroboros.py Uroboros.canonical | CANONICAL Ψ adapter | Yes, through PsiTransition and CanonicalExecutor |
| core/legacy_engine.py LegacyEngine(State -> State) | LEGACY/GENERIC COMPATIBILITY | No |
| gnosis-terminal-bridge/src/core_evolution.py | BRIDGE/COMPATIBILITY | No |
| CoreChat | BRIDGE/ADAPTER | No |

## Evidence

`core/psi_transition.py` defines the canonical `Psi -> Psi` boundary and its State adapter.
`core/engine.py` accepts `PsiTransition` and executes only `PsiTransition.on_state()`.
`core/legacy_engine.py` is the explicitly named compatibility surface for `State -> State`.
`core/uroboros.py::evolutionary()` and the terminal bridge use `LegacyEngine`, keeping compatibility separate from canonical Ψ execution.
`core/evolution.py::evolutionary_psi_transition()` constructs Admission objects before selection.
`core/admission.py` provides `admit()` and fail-closed `require_admitted()`.

## Result

The D-001 audit branch removes the previous ambiguity where `Engine` itself accepted both canonical and legacy transition forms.

The canonical execution boundary is now explicit: `Engine -> PsiTransition`. Compatibility is explicit: `LegacyEngine -> State -> State`.

This does **not** claim that every possible State mutation in the repository is globally canonical Ψ semantics. Compatibility surfaces remain intentionally non-canonical.

## Acceptance evidence

- canonical Ψ execution uses `PsiTransition`;
- compatibility callers are routed through `LegacyEngine`;
- adversarial regression tests distinguish the two paths;
- Architecture Gate passes;
- full Tests workflow passes.

## Scope

PM-05 remains scoped to the canonical semantic surface. Global claims about every State mutation remain excluded unless independently proven.