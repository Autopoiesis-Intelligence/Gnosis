# R2 CI Authority Invariant — 2026-09-26

## Invariant

A production mutation-like surface must be mechanically visible to CI. In particular, `SemanticCommit(...)` construction is permitted only inside `core/commit.py`.

CI inventories production-core occurrences of:

- `SemanticCommit(...)`;
- `commit_once(...)`;
- `.append(...)`.

The purpose is not to infer semantic authority from syntax. The purpose is to ensure that a newly introduced mutation-like surface cannot silently appear outside the audited authority inventory.

## Fail-closed rule

A new `SemanticCommit(...)` constructor outside `core/commit.py` fails CI. New mutation-like surfaces become visible in the deterministic inventory and require an explicit authority audit before the classification can be accepted.

This is a change-detection invariant, not proof that arbitrary Python cannot mutate memory. Semantic authority remains a behavioral contract verified by the canonical gates.
