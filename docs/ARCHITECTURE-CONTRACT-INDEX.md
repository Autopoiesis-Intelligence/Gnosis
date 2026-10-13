# Gnosis Architecture Contract Index

This is the canonical entry point for the current architecture.

## 1. Repository boundaries
- [Architecture Boundaries](ARCHITECTURE-BOUNDARIES.md)
- [Migration Plan](ARCHITECTURE-MIGRATION-PLAN.md)

## 2. Core authority
- [Core Contracts](CORE-CONTRACTS.md)
- [Core Schemas](CORE-SCHEMAS.md)
- [Core Trust Rules](CORE-TRUST-RULES.md)
- [Dependency Policy](DEPENDENCY-POLICY.md)

## 3. Context and continuity
- [Context Continuity Contract](CONTEXT-CONTINUITY-CONTRACT.md)
- [Provenance Contract](PROVENANCE-CONTRACT.md)

## 4. External surfaces
- [External Write/Update Contract](EXTERNAL-WRITE-UPDATE-CONTRACT.md)

## 5. Enforcement
- [Architecture Test Plan](ARCHITECTURE-TEST-PLAN.md)
- `tests/test_architecture_policy.py`
- `tests/test_core_import_boundaries.py`
- `tests/test_dependency_direction.py`
- `tests/test_context_contract.py`
- `tests/test_external_update_contract.py`

## Canonical rule

If another document conflicts with this contract set, the conflict must be resolved explicitly before implementation continues. No repository migration is considered complete until the relevant contract and its enforcement evidence are updated.

## Current architecture in one sentence

Core owns trusted state and verification; Genesis produces/governs modules; Research-Memory carries machine-readable research/evidence/context; public surfaces expose authorized results; external systems interact only through explicit contracts.
