# R2 Indirect Mutation Guard — 2026-09-26

## Gap

The first CI guard detects direct `SemanticCommit(...)` syntax. That is insufficient as a universal detector because Python permits aliases and attribute indirection.

## Added evidence

The regression test now uses Python AST analysis to identify mutation-like call shapes, including:

- aliased `SemanticCommit` constructor calls;
- `commit_once(...)` attribute calls;
- `.apply(...)`, `.commit(...)`, `.append(...)` mutation-like calls.

The test suite uses an adversarial alias fixture to prove that the inventory can see an aliased semantic-commit constructor.

## Boundary

AST inventory is a detection mechanism, not a proof of runtime behavior. Dynamic `getattr`, reflection, imported callables, monkey-patching, and arbitrary `eval/exec` remain outside static proof and require runtime sandbox/trust-boundary controls if those facilities are permitted.

Therefore this change strengthens CI detection without claiming universal static no-bypass.
