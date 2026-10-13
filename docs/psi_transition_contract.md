# Ψ Transition Contract

## Purpose

Define the minimal engineering contract for one endogenous transition of the Gnosis state.

Let the canonical state be:

\[
\Psi = (X,R)
\]

A transition is realized by:

\[
G(\Psi) \rightarrow C
\rightarrow Test(C)
\rightarrow Select(C)
\rightarrow \Psi'
\]

## Contract

1. **Single source of truth** — the current state is `State` and its canonical Ψ projection.
2. **Generation** — `Generate` produces candidate `State` objects from the current state.
3. **Testing** — `Test(candidate)` returns a boolean acceptance decision.
4. **Selection** — selection is deterministic and endogenous; no external selector is supplied to the transition API.
5. **Membership** — the selected next state is one of the generated, accepted candidates.
6. **Order independence** — reordering equivalent candidate inputs must not change the selected Ψ.
7. **No hidden selector channel** — unrelated metadata and object identity must not determine the selected Ψ.
8. **State evolution** — either component may change:
   - `(X,R) -> (X,R')`
   - `(X,R) -> (X',R)`
   - `(X,R) -> (X',R')`
   including the permitted case `R -> ∅`.
9. **No implicit mutation** — the previous `State` remains unchanged after a transition.
10. **Boundary separation** — wire serialization belongs outside the Core and must not alter the canonical immutable state model.

## Formal transition relation

For a state `s` and generator/test pair `(G,T)`, define:

\[
C_s = G(s)
\]

\[
V_s = \{c \in C_s \mid T(c)=True\}
\]

The transition is defined only when `V_s` is non-empty:

\[
T_{G,T}(s) = Select(V_s)
\]

where `Select` is a deterministic function of the candidate state itself and has no external selector argument.

## Current proof surface

The repository contains adversarial tests covering:

- external selector injection;
- candidate-order invariance;
- hidden metadata/object-identity independence;
- `R -> ∅` and `∅ -> R` evolution;
- `X` evolution with fixed `R`;
- `R` evolution with fixed `X`;
- joint `X,R` evolution;
- immutable Core state versus mutable wire representation.

This document is an engineering contract, not a claim that the mathematical theory of Ψ is complete. Further work must establish which properties are axioms, which are derived invariants, and which remain empirical tests.
