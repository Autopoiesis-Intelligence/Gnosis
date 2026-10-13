# Gnosis Architecture Boundaries

## Canonical layers

- Gnosis-Core: minimal trusted runtime and authority for trusted state transitions.
- Gnosis-Genesis: separate private repository; its production, deployment, and authority responsibilities are unresolved until verified against current implementation and deployment evidence.
- Gnosis-Memory: machine-readable research, evidence, provenance and context-transfer material.
- Public Gnosis surfaces: user/product/research/opportunity interfaces.

## Trust rule

Core is authoritative for trusted state. Downstream repositories and external services may receive or update material only through explicit controlled interfaces. They are never authority sources for Core.

## Context continuity

Authorized user/project context may move across sessions, devices and connected AI interfaces through explicit identity, permissions, project/context, version and provenance contracts. Continuity does not require exposing private runtime internals.

## Dependency rule

Core MUST NOT depend on external factories, research/context repositories, LLMs, connectors, UI, or commercial services. Any production layer may consume Core contracts only through explicit interfaces; its repository role must be verified rather than assumed. Gnosis-Memory and external surfaces are downstream evidence/work surfaces.
