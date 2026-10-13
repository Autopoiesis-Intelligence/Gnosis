# Gnosis Research Machine

## Role

Gnosis Research Machine is the machine-readable development memory and evidence base for Gnosis.

It is not the current Gnosis Core, not an alternative implementation, and not an authority source for Core mutation.

## Authority boundary

```
Research Machine → retrieve / inform / provide provenance
Research Machine -X→ direct Core mutation or authorization
```

Any influence on Gnosis Core must pass through the explicit engineering admission path:

```
Research Machine record
→ scope/evidence review
→ engineering consequence
→ requirement
→ bounded task
→ implementation
→ test/CI
→ audit
→ acceptance
```

## Record identity

Every canonical archive record has a permanent unique ID. IDs are never reused.

Record content may be superseded, but historical identity and provenance are preserved.

## Canonical record classes

- R — research
- C — claim
- E — evidence
- X — counterexample
- D — decision
- A — audit
- T — transition

The schema is defined in `research_machine/schema/record.schema.json`.

## Historical artifacts

Historical source files, implementations, commits and other artifacts may be retained for provenance. They are evidence sources/artifacts, not current Core authority.

## Current Core

The current executable and verified system is maintained separately in the Gnosis Core repository.

## Integrity rule

Research Machine records must distinguish:

```
stored ≠ canonical
canonical ≠ verified
verified ≠ accepted
```

A record must never claim a stronger evidence state than its recorded evidence supports.
