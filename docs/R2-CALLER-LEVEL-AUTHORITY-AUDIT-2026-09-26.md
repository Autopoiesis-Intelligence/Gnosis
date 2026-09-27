# R2 Caller-Level Authority Audit — 2026-09-26

## Enumerated production surfaces

The caller audit distinguishes canonical Ψ execution from legacy/compatibility callers instead of treating every `Engine(State -> State)` use as semantic authority.

| Caller/surface | Classification | Authority status |
|---|---|---|
| `core/uroboros.py -> CanonicalExecutor` | canonical Ψ orchestration | canonical |
| `core/evolution.py::evolutionary_psi_transition` | canonical Ψ evolution | canonical; commit delegated to boundary |
| `core/resolution.py::commit_resolution` | resolution-to-commit bridge | canonical only after matching Admission |
| `core/psi_engine.py::PsiEngine` | canonical Ψ adapter | canonical |
| `core/legacy_engine.py::LegacyEngine` | State→State compatibility | non-canonical |
| `core/evolution.py::evolutionary_transition` | deprecated State→State compatibility | non-canonical |
| `gnosis-terminal-bridge` | external compatibility adapter | non-canonical |
| `CoreChat`/adapter surfaces | adapter | non-canonical |
| tests/examples | development surfaces | no production authority |

## Critical result

Production `SemanticCommit(...)` construction remains confined to `core/commit.py`. The direct production commit path is explicitly inventoried rather than discovered implicitly.

The legacy `State -> State` transition remains callable for compatibility but is deprecated and cannot be used as evidence of canonical Ψ authority.

The terminal bridge creates a compatibility `Engine` and does not construct or invoke `SemanticCommit` directly.

## Remaining gap

This audit establishes caller classification and regression protection. It does **not** prove that every future external/public adapter will remain within the classification automatically. CI must retain the caller-inventory regression tests, and additions of new mutation surfaces require re-audit.
