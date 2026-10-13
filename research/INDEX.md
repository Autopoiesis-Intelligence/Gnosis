# Gnosis Research Library — Machine-Readable Index

## Repository role
This repository is the public research library for Gnosis. It preserves research, reverse-analysis, mathematical models, experiments, historical implementations and provenance. It is not the canonical production Core.

## Canonical lineage
Research Library → Gnosis Core → specialized research kernels → user/commercial versions.

## Admission rule
Research does not become Core functionality merely by being documented. The engineering path is:
Observation → Pattern → Formalization → Evidence → Engineering Consequence → Core Requirement → Task → Implementation → Test/CI → Audit → Acceptance.

## Stable record schema
Each research record should use a stable ID and, where applicable, fields:
- ID
- TYPE
- PARENT
- QUESTION
- OBSERVATION
- DERIVATION
- RESULT
- EVIDENCE
- ENGINEERING_CONSEQUENCE
- GAP
- CORE_ADMISSIBILITY
- STATUS
- NEXT

## Status vocabulary
RESEARCH
HYPOTHESIS
FORMALIZED
EVIDENCE_PENDING
ENGINEERING_CANDIDATE
IMPLEMENTED
TESTED
CI_VERIFIED
AUDITED
ACCEPTED
REJECTED
SUPERSEDED

These statuses must not be conflated.

## Existing research continuity
The historical AI_CONTEXT.md remains a source document. Its mathematical and reverse-analysis material is being normalized into stable research records rather than duplicated into Core.

## Priority
Preserve provenance and useful discovery context; remove ambiguity and duplicate operational instructions.

## Current engineering bridge
Research should reference engineering tasks when a concrete consequence exists. Engineering tasks should reference source files, tests and audit evidence.

## Next
Normalize the existing E-series/reverse-analysis sequence into this index and record format.
## Reverse-analysis continuity

The current reverse-analysis sequence is preserved in historical `AI_CONTEXT.md` and is being normalized into stable research records. Current indexed block: RME 126–140.

### Current frontier

`F_t → F_{t+1}` as a proof-preserving refinement/conservative extension.

Open questions:
1. Define the minimum semantic contract M(F).
2. Define admissible refinement/conservative extension.
3. Construct adversarial counterexamples.
4. Determine whether M(F) is preserved.
5. Record exact assumptions for any preservation result.

### Non-claims
- Proof continuity is not semantic continuity.
- Local proof validity does not imply global semantic safety.
- K-preservation does not prove contract preservation.
- Trusted-kernel status is an explicit assumption.
- M(F) is OPEN.
- Semantic-drift prevention is NOT VERIFIED.

### Current engineering bridge
Determine the explicit semantic Invariant provider for canonical execution. Preserve Ψ=(X,R), do not reuse RootInvariant for ordinary Ψ semantics, avoid a second state model, and fail closed rather than using an always-true invariant.

Research status vocabulary: DEFINITION / OBSERVED / DERIVED / VERIFIED / REJECTED / OPEN.

## Archive record contract

Machine-readable Research Machine records are governed by **Research Machine Record Schema v1**:

- schema: `research_machine/schema/record.schema.json`
- version: `1.0.0`
- record directory: `research_machine/records/`
- Research Machine index: `research_machine/INDEX.yaml`

The existing research index remains a research-navigation layer. It is not itself evidence of verification or acceptance.
