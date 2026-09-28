# Gnozis Network Architecture — Layered Workload Contract

## Purpose

The public Gnozis layer must not become a computational extension of the protected main Core.

The public layer handles high-volume, low-trust and externally visible work such as Internet research, source collection, normalization, indexing, repository/document generation, presentation, provenance packaging and public evidence publication.

The main Core coordinates the network, enforces trust and policy boundaries, decides admissibility, authorizes execution, and maintains canonical state.

## Core rule

```
PUBLIC / SPECIALIZED WORK
        |
        | candidate evidence / result / request
        v
NETWORK GATE
        |
        | verified, scoped input
        v
MAIN CORE
        |
        | orchestration / authorization
        v
SPECIALIZED CORE(S)
```

Public work is submitted to the network; it is not executed inside the authority-bearing Core merely because it belongs to the same product.

## Workload separation

| Work | Public / specialized layer | Main Core |
|---|---|---|
| Internet retrieval | YES | NO |
| Source parsing | YES | NO |
| Repository generation | YES | NO |
| Large document analysis | YES | NO |
| Evidence packaging | YES | NO |
| Candidate discovery | YES, scoped | coordinates |
| Network orchestration | NO | YES |
| Trust / admission | NO | YES |
| Canonical state transition | NO | YES |
| Execution authorization | NO | YES |
| Core-to-Core routing | NO | YES |
| Evolution governance | NO | YES |

## Specialized Core model

A specialized Core is created when there is a declared need for a distinct capability, not merely because the main Core lacks compute capacity.

```
Need detected
    ↓
Opportunity / capability specification
    ↓
Candidate specialized Core
    ↓
Admission + scope + privacy policy
    ↓
Network registration
    ↓
Bounded operation
```

A specialized Core may perform work independently within its contract and return evidence, candidates, patches or results. It does not automatically acquire authority over the main Core.

## Optimization / patch model

If network analytics identify a useful optimization, the system may generate a patch candidate.

```
Observed inefficiency
      ↓
Analysis
      ↓
Patch candidate
      ↓
Test / regression / security
      ↓
Scoped rollout
      ↓
Runtime evidence
      ↓
Promote or reject
```

A patch is not an immediate rewrite of the main Core.

## Privacy and tenant isolation

A public or partner-facing worker may process data only inside its authorized scope.

```
tenant A data ──> worker A ──> scoped result
tenant B data ──> worker B ──> scoped result
                         X
                 cross-tenant learning
                         X
```

Cross-tenant reuse, learning or publication requires an explicit policy and provenance path.

## Repository topology

The repository network should eventually reflect operational roles rather than arbitrary historical accumulation:

```
Gnozis
  public product / catalogue / evidence
        |
        +-- Research libraries
        |
        +-- Specialized knowledge repositories
        |
        +-- Partner-facing surfaces
        |
        +-- Specialized Core repositories
        |
        +-- protected Genesis / main network Core
```

Public repositories are outputs and work surfaces. They are not trusted Core state.

## Architectural invariant

**The main Core coordinates the network; the network carries the workload.**

This prevents public research, Internet retrieval, repository generation and partner-specific computation from consuming the authority-bearing Core execution path.

## Evidence requirement

For every new network capability, verify:

1. workload executes outside the main Core where appropriate;
2. result crosses an explicit port;
3. result is untrusted until admitted;
4. tenant/privacy scope is preserved;
5. only the main Core authority path can change canonical state;
6. provenance and runtime evidence are retained.
