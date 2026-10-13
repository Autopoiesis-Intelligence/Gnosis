# Gnosis Architecture Boundaries

## Canonical layers

- Gnosis-Core: minimal trusted runtime and authority for trusted state transitions.
- Gnosis-Genesis: private Module Factory and governed evolution/production layer.
- Gnosis-Memory: machine-readable research, evidence, provenance and context-transfer material.
- Public Gnosis surfaces: user/product/research/opportunity interfaces.

## Trust rule

Core is authoritative for trusted state. Downstream repositories and external services may receive or update material only through explicit controlled interfaces. They are never authority sources for Core.

## Context continuity

Authorized user/project context may move across sessions, devices and connected AI interfaces through explicit identity, permissions, project/context, version and provenance contracts. Continuity does not require exposing private runtime internals.

## Dependency rule

Core MUST NOT depend on Genesis, Research-Memory, LLMs, connectors, UI, or commercial services. Genesis and product layers may consume Core contracts. Research and external surfaces are downstream evidence/work surfaces.
