# Gnosis Open Defects

Updated: 2026-09-12

This is the active engineering defect ledger. A defect is closed only when code and executable regression evidence agree.

| ID | Defect | Current status | Next action |
|---|---|---|---|
| D-001 | Canonical Ψ transition is not yet the sole live Engine/Evolution path | PARTIALLY CLOSED | canonical `PsiTransition` is now executable through `Engine` and `Uroboros.evolutionary`; next remove or formally constrain the legacy State-callable compatibility path |
| D-002 | Relation/State canonical representation needs final consolidation | OPEN | define one typed representation for X and R and migrate boundary code |
| D-003 | Default `Uroboros()` previously performed identity evolution | FIXED | keep fail-closed regression test |
| D-004 | `Test` previously accepted truthy non-bools | FIXED | keep strict bool regression test |
| D-005 | `Engine.run/trajectory` previously accepted bool as int | FIXED | keep strict integer regression test |
| D-006 | State deep immutability | FIXED for built-in nested containers | expand only if custom mutable payloads become part of State contract |
| D-007 | Bridge hidden mutable session/message state | OPEN | complete bridge concurrency/session audit |
| D-008 | Threaded bridge shared state risk | OPEN | isolate per-session state and prove concurrent isolation |
| D-009 | Bridge identity/authentication fail-open risk | OPEN until current implementation is re-audited | verify current security tests and code path |
| D-010 | `/health` may not prove actual Core availability | OPEN | make health semantics explicit and test against live Core dependency |
| D-011 | Latest commit CI evidence | OPEN | verify actual GitHub Actions run for current HEAD |
| D-012 | Protected/encrypted internal memory historical specification | GAP | recover primary-source design before implementing |
| D-013 | Interoperability contract | PLANNED | implement after Core canonicalization |
| D-014 | Mathematical/physics research claims | SEPARATE | preserve as hypothesis/evidence tracks; do not mix with Core conformance |

## 2026-09-12 reconciliation update

The canonical boundary was repaired and verified at the code level:

```text
State
  ↓ to_psi()
Psi=(X,R)
  ↓ PsiTransition
Psi'
  ↓ State.from_psi()
State'
```

`Engine` recognizes `PsiTransition` as the canonical fundamental path, while the older State-callable transition remains explicitly marked as a compatibility boundary. `Uroboros.evolutionary()` constructs the canonical `PsiTransition`, and targeted integration tests cover both direct Engine execution and Uroboros evolution.

This update is evidence of implementation progress, not full D-001 closure. Full closure still requires full-suite CI verification and a decision on the legacy State-callable compatibility path.

## Closure rule

A defect moves to FIXED only after:

1. implementation change;
2. targeted regression test;
3. full-suite verification;
4. repository documentation update.
