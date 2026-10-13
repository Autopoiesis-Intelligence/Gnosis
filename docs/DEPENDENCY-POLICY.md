# Dependency Policy

## Allowed

Private production layer -> Core contracts, through explicit reviewed interfaces only
Product -> Core contracts
Product -> reviewed production-layer interfaces
Research/Knowledge -> explicit evidence/context interfaces
External adapters -> public interfaces

## Forbidden

Core -> private production/factory layer
Core -> research/context repositories
Core -> LLM/API/connector
Core -> Product/Commercial/UI
External repository -> direct Core database mutation
Research/Knowledge -> implicit authority

## Enforcement

The policy must be represented by structural tests and reviewed whenever a new package or connector is introduced.


## Historical compatibility labels

`Genesis` and `Research-Memory` are retained here only as historical labels used by earlier architecture records and consistency checks. Their presence does not establish a current repository, production deployment, or authority role. Confirm current roles from repository and deployment evidence.
