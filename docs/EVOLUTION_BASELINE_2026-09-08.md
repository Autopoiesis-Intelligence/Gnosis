# Gnosis Evolution Baseline — 2026-09-08

## Purpose

This document freezes the currently evidenced Gnozis core baseline before further evolution. Evolution work must preserve the properties listed here unless a deliberate experiment explicitly falsifies and replaces one of them.

## Baseline invariants

1. **Core state is endogenous.** The evolution loop operates on the internal state/model rather than requiring a permanently external correction operator.
2. **Generate → Test → Select is the evolutionary gate.** A generated candidate is not accepted merely because it exists; selection is constrained by testing.
3. **Only tested candidates may be selected.** A candidate that does not pass the relevant test must not become the next accepted state.
4. **Selection is internal.** The architecture contains an internal selection path rather than making the human administrator a required selector at every evolutionary step.
5. **Autopoietic continuation is preserved.** After the required initial context/agency conditions are established, subsequent evolution can proceed through the endogenous engine without requiring a new external command for each step.
6. **Proof status must remain traceable.** Existing tests/evidence are part of the baseline and must not be silently removed, weakened, or replaced by generated claims.
7. **AI is not the core definition.** An AI model may be an interface/reasoning component, but it must not be represented as the complete Gnozis system or as proof of the core's endogenous properties.
8. **Repository claims require repository evidence.** No component, test, integration, capability, or result is considered present merely because an AI response says so.

## Evolution safety rule

Before changing the core, record the current implementation and tests. After each change, rerun the relevant proof/evidence suite and compare the result against this baseline. If a change improves conversational or interface behavior but weakens endogenous evolution, Generate/Test/Select integrity, or proof traceability, it is not an acceptable evolution of the core.

## Known implementation evidence

The baseline investigation identified implementation/evidence associated with:

- UROBOROS / Ψ-Core lineage.
- Endogenous evolution through an engine step after agency context is established.
- Generate/Test/Select evolutionary flow.
- Tests checking selection of tested candidates and rejection of untested states.
- Tests checking multiple endogenous evolution steps without external input.
- CoreChat as an interface into the engine/state machinery.

These names are recorded as evidence targets, not as permission to assume that every referenced file remains unchanged. The repository must be checked again before modifying any of them.

## Next evolution target

The next task is not to invent a new intelligence layer. It is to inspect the current implementation and determine the smallest change that increases autonomous evolutionary capability while preserving the proven invariants above.
