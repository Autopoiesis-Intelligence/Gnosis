# GNOSIS

## Public registry of machine-generated opportunities, contracts and evidence

**Gnosis** is the public product and evidence surface of a system designed to turn technical requirements into specialized, testable modules and partner-ready opportunities.

A separate private repository, **Gnosis-Genesis**, exists. Its factory, production, deployment, and authority responsibilities are not confirmed by the inspected repository contents.

Gnosis is where selected outputs become inspectable: proposals, contracts, modules, evidence, provenance and partnership opportunities.

> **Gnosis exposes selected public outputs and evidence. Private production and authority boundaries remain under reconciliation.**

---

## Product model

```text
                    GNOSIS-GENESIS
                private repository
                  role unresolved
                           │
              ┌────────────┴────────────┐
              │                         │
       module creation             adaptation /
       and proposals                 learning
              │                         │
              └────────────┬────────────┘
                           ▼
                    verification
                           │
                           ▼
                        GNOSIS
                 public product surface
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     RESEARCH           VALIDATED         COMMERCIAL
     proposals           modules          candidates
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    contracts / evidence
                           │
                           ▼
                       partners
```

The public repository is therefore not intended to expose the protected factory itself. It exposes the **results and evidence that are appropriate to share**.

---

## What Gnosis is building

The long-term product direction is a controlled machine-production cycle:

```text
Technical brief
      ↓
Requirement formalization
      ↓
Specialized module creation
      ↓
Adaptation / learning
      ↓
Independent evaluation
      ↓
Regression and security gates
      ↓
Controlled release
      ↓
Runtime evidence
      ↓
Commercial / partner opportunity
```

The four levels must remain distinct:

1. **Factory creation** — a future factory workflow may create specialized candidates; the responsibility of `Gnosis-Genesis` is not yet confirmed.
2. **Module adaptation** — the candidate may be configured, trained, supplied with knowledge, or otherwise adapted within an authorized scope.
3. **Module operation** — the released module performs bounded tasks.
4. **Factory/Core evolution** — changes to the protected factory or its governing mechanisms require a separate authority and evidence chain.

Creating autonomous modules does **not** automatically grant the factory permission to rewrite its own protected core.

---

## Public opportunity catalogue

Gnosis is intended to expose machine-generated opportunities in a form that testers, researchers, partners and potential investors can inspect.

A proposal can progress through evidence stages such as:

```text
EARLY
  ↓
RESEARCH
  ↓
VALIDATED
  ↓
COMMERCIAL
```

These are **maturity/evidence stages, not rankings**. A higher stage means that a different level of evidence and readiness has been established; it does not mean that one proposal is inherently more valuable than another.

Example catalogue entry:

```text
GZ-C-0042
Data Normalization Module

TYPE
Data Processing

STAGE
Validated

EVIDENCE
✓ Functional evaluation
✓ Holdout evaluation
✓ Regression checks
✓ Provenance

STATUS
Open for pilot

CAPABILITIES
• structured data transformation
• schema validation

LIMITATIONS
• bounded execution environment
• no unrestricted external network
```

The exact registry schema and status vocabulary are part of the evolving product contracts.

---

## Contracts

A Gnosis contract is a machine-readable description of a proposed capability, module, partnership or other bounded commitment.

A contract may include:

- contract identifier and version;
- requirements and acceptance criteria;
- allowed capabilities;
- limitations and budgets;
- provenance;
- evaluation evidence;
- artifact identifiers;
- status and lifecycle;
- applicable trust and data boundaries.

Where appropriate, contracts and evidence can be represented by cryptographic hashes so that a particular version can be independently identified.

Example:

```text
Contract ID:       GZ-C-0042
Contract version:  1.2
Module artifact:   <hash>
Evidence root:     <hash>
Provenance root:   <hash>
```

A hash identifies a specific artifact or evidence state. It does not by itself prove that the underlying claim is true; the evidence and verification process remain separate.

---

## Evidence before claims

Gnosis separates:

```text
Documentation
    ≠
Source
    ≠
Test
    ≠
CI evidence
    ≠
Runtime evidence
    ≠
Audit
```

Likewise:

```text
CHANGE
  ≠
IMPROVEMENT
```

A candidate module must not be presented as improved merely because its code changed or because it passed a known test set.

The intended evaluation model includes:

- preserved baselines;
- independent or hidden holdout cases where practical;
- adversarial cases;
- regression checks;
- security and capability boundaries;
- resource limits;
- runtime observations;
- provenance linking source → learning → artifact → evaluation.

Failed candidates are evidence too. A rejected candidate should remain traceable rather than silently replacing the baseline.

---

## Partner data boundary

Partner data is not automatically global learning material.

```text
ACCESS
  ≠
COPY
  ≠
TRAIN
  ≠
PUBLISH
  ≠
REUSE
```

Partner information may remain private to an agreed trust boundary. Eligibility for learning, reuse or publication requires an explicit policy and provenance path.

The intended learning boundary is:

```text
Partner / Research Material
            ↓
     Eligibility Check
            ↓
       Authorized scope
            ↓
      Learning / Adaptation
            ↓
       Independent evaluation
            ↓
        Evidence / result
```

Unknown provenance or unknown permission is not treated as permission by default.

---

## Gnosis-Memory

**Gnosis-Memory** is the machine-readable research and context layer associated with the product.

Its role is to preserve and organize:

- research material;
- historical project context;
- mathematical models;
- formal definitions and contracts;
- evidence and provenance;
- AI-readable context;
- candidate knowledge for future implementation.

Gnosis-Memory is **not itself an authority for changing protected code**. It supplies structured context and candidate material subject to the relevant contracts and gates.

The intended relationship is:

```text
Gnosis-Memory
          ↓
 candidate knowledge / evidence
          ↓
      eligibility
          ↓
Gnosis-Core / Gnosis-Genesis boundaries remain subject to explicit implementation and authority evidence. Selected, verified outputs may be exposed through Gnosis.
```

---

## Public repository vs protected factory

The product deliberately separates public visibility from protected execution.

### Public: Gnosis

- opportunity catalogue;
- contracts;
- selected modules;
- evidence;
- provenance;
- research-facing materials;
- partnership surface.

### Research: Gnosis-Memory

- machine-readable research;
- historical context;
- mathematical corpus;
- evidence archive;
- development context.

### Private: Gnosis-Genesis

The repository exists and is private, but its exact factory, production, deployment, and authority responsibilities are not established by the inspected root contents. Do not infer a working factory or privileged execution path from the repository name or this product target document.

---

## Commercial pathway

The intended commercial path is:

```text
Machine-generated proposal
        ↓
Evidence
        ↓
Partner review
        ↓
Pilot
        ↓
Validated module
        ↓
Commercial contract
        ↓
Deployment / partnership
```

The public repository is designed to answer practical questions before a partnership:

- What was proposed?
- What was actually tested?
- Which version produced the evidence?
- What capabilities are allowed?
- What limitations exist?
- What failed?
- What was learned?
- Which contract is being offered?
- What can a partner test?

Commercial readiness is not inferred from the existence of documentation or a repository. It requires evidence from the relevant pilot, evaluation and contractual process.

---

## Current status

This repository describes the **target public product architecture** as it is being formalized. Some parts of the public registry, autonomous module factory, learning pipeline, partner workflow and commercial lifecycle remain under implementation and verification.

Do not interpret the presence of a documented workflow as proof that the complete end-to-end workflow is already operational.

For implementation status and evidence, consult the current repository artifacts and project contracts.


## Getting started

This repository is the public product and evidence surface, not a packaged hosted service by default.

1. Browse the repository's source, contracts, tests, and current [open issues](https://github.com/Autopoiesis-Intelligence/Gnosis/issues).
2. Before relying on a proposed capability, inspect the exact source version and the relevant test/CI evidence.
3. If you are evaluating a module or opportunity, review its scope, limitations, provenance, and evidence rather than relying on a name or maturity label alone.
4. If you want to contribute, start with [CONTRIBUTING.md](CONTRIBUTING.md).

No universal installation or production deployment command is promised here: the available entry point depends on the specific component and its implementation status.

## Current capabilities and limitations

This repository contains product documentation and engineering artifacts for an evolving system. The complete end-to-end factory, registry, partner, and commercial workflow is **not asserted to be fully operational** merely because it is described here.

Use these distinctions when evaluating a claim:

- **Documented** means described in repository content.
- **Implemented** means the relevant code exists at the inspected commit.
- **Tested** means a specific test run exercised the behavior.
- **CI-proven** means the relevant checks passed for an exact commit.
- **Runtime-proven** means the behavior was observed in the relevant runtime and evidence was retained.

A generated proposal, passing synthetic test, README statement, or open pull request does not by itself prove a production capability. See the [current implementation and issues](https://github.com/Autopoiesis-Intelligence/Gnosis/issues) for work in progress and unresolved questions.

## Feedback and communication

- [Report a bug](https://github.com/Autopoiesis-Intelligence/Gnosis/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/Autopoiesis-Intelligence/Gnosis/issues/new?template=feature_request.md)
- [Browse open issues](https://github.com/Autopoiesis-Intelligence/Gnosis/issues)
- Read [support and feedback guidance](SUPPORT.md) or [contribution guidance](CONTRIBUTING.md).

When possible, include reproducible steps, the affected commit, and public test/CI evidence. Do not post secrets, credentials, or private partner data. Requests are not automatically accepted, scheduled, or implemented.

---

## Development principle

> Produce a bounded candidate. Preserve its provenance. Test it independently. Record what happened. Only then promote it.

```text
FACTORY → produces candidates
EVIDENCE → establishes what happened
CONTRACT → defines what is allowed
GNOSIS → exposes verified opportunities
PARTNERS → decide what to adopt
```
