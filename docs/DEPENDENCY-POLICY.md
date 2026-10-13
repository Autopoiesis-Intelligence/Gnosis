# Dependency Policy

## Allowed

Production/factory layer -> Core contracts
Product -> Core contracts
Product -> explicitly defined production/factory interfaces
Gnosis-Memory / Research -> explicit evidence/context interfaces
External adapters -> public interfaces

## Forbidden

Core -> external production/factory layer
Core -> Gnosis-Memory
Core -> LLM/API/connector
Core -> Product/Commercial/UI
External repository -> direct Core database mutation
Research/Knowledge -> implicit authority

## Enforcement

The policy must be represented by structural tests and reviewed whenever a new package or connector is introduced.


## Legacy contract aliases

The historical contract-consistency test still expects the exact labels `Core -> Genesis` and `Core -> Research-Memory`. They are retained here as compatibility aliases for the forbidden dependency directions; they do not assert that a current production factory exists or define the current name of the research/context layer.
