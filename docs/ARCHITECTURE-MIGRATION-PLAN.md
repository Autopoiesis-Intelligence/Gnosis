# Architecture Migration Plan

1. Freeze canonical boundaries and schemas.
2. Confirm current repository identities and public/private roles from repository and deployment evidence.
3. Build Core contracts before moving implementation.
4. Add structural dependency tests.
5. Add context/provenance continuity contracts.
6. Migrate reusable evidence and research to Gnosis-Memory in small batches.
7. Keep private production implementation separate; define its repository role and interfaces from current implementation/deployment evidence rather than assuming them from a codename.
8. Preserve old implementations until replacement evidence exists.
9. Remove obsolete paths only after verification and rollback evidence.

Migration is incremental. No whole-repository copy is considered architectural migration.
