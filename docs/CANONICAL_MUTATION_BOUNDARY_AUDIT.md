# Canonical Mutation Boundary — reconciled 2026-09-26

## Finding

The previous architecture exposed two related commit layers:

1. `core/canonical_chain.py::admit_transition()` — generic SafetyGate + GasBudget + Provenance + idempotent commit.
2. `core/commit.py::SemanticCommit.apply()` — Ψ-specific semantic commit.

The two layers were previously separate implementations of overlapping pre-commit responsibility.

## Architectural change

They are now explicitly composed:

`SemanticCommit.apply()`
→ `canonical_chain.commit_admitted_psi()`
→ `canonical_chain.admit_transition()`
→ `guard_transition()`
→ `commit_once()`

The Ψ layer remains responsible for:

- requiring an admitted candidate;
- canonicalizing Ψ;
- verifying previous-state continuity;
- constructing the causal TransitionRecord and evidence hash.

The universal canonical boundary remains responsible for:

- SafetyGate;
- GasBudget;
- Provenance binding;
- idempotent history commit.

Therefore the mathematical separation is:

[
	ext{Ψ semantic validity}

eq
	ext{runtime authorization/safety}

eq
	ext{durable commit}
]

while the architecture now guarantees their required order:

[
	ext{Ψ Admission}
ightarrow
	ext{Canonical Guard}
ightarrow
	ext{Commit}
]

## Invariant

No accepted Ψ transition may cross the semantic commit boundary without passing the shared canonical guard.

This closes the previously documented architectural split without weakening Ψ-specific candidate/proof/selection semantics.

## Remaining boundary

SQLite persistence remains a separate durable substrate. It is not promoted to semantic authority merely by being called from a commit path.
