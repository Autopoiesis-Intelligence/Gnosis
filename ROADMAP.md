# GNOSIS — ROADMAP

## Stage 0 — Project memory
**Status: completed in this audit.**

- establish authoritative `PROJECT_STATE.md`;
- establish philosophy and evolution records;
- classify claims;
- prevent obsolete `STATE.md` from competing with current state.

## Stage 1 — Core reconciliation
**Status: next.**

- inspect every current `core/` module and all tests;
- map each implementation element to a current invariant;
- identify dead, duplicated or misleading abstractions;
- verify deep immutability and absence of hidden state leakage;
- verify that `with_relations()` actually changes/configures the fundamental state as intended;
- audit the bridge/agent layer separately from the mathematical core.

## Stage 2 — Adversarial proof suite

Build tests for:

- extensionality under arbitrary hidden metadata;
- repeated endogenous evolution;
- rejection of untested candidates;
- deterministic reproducibility;
- candidate-generation dependence on current state;
- selector integrity;
- absence of required external intervention after initialization;
- regression against accidental reintroduction of external control.

## Stage 3 — Minimal effective core

Reduce the implementation to the smallest architecture that preserves the experimentally supported invariants. Every removed component must be checked against tests and historical claims before deletion.

## Stage 4 — Internal memory/model research

Only after the core is clean, investigate whether memory, internal models, trajectory comparison and contradiction handling can be derived as state transformations rather than bolted-on external services.

## Stage 5 — Intelligence / discovery experiments

Test whether the architecture can generate useful hypotheses, compare alternative models, learn from failed tests and continue autonomous exploration. Benchmark against competing architectures rather than only against itself.

## Stage 6 — Independent scientific tracks

Maintain separate research tracks for mathematical/physical hypotheses. No physics claim becomes part of the core merely because a simulation produces a suggestive pattern.

## Version discipline

`Ψ-Core v33` remains the public historical reference baseline. Later work must be clearly marked as experimental or assigned a later version. The public baseline must remain reproducible.

## Definition of success

The project succeeds at this stage if a new model can open the repository and, without relying on old chat history, determine:

1. what Gnosis currently is;
2. what it used to be;
3. why major changes occurred;
4. what is actually implemented;
5. what has failed;
6. what remains hypothetical;
7. what experiment must be run next.
