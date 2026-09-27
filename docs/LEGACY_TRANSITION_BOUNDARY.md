# Legacy Transition Boundary

## Status

The canonical fundamental transition path is:

`State -> Psi -> PsiTransition -> Psi' -> State`

`core.engine.Engine` is now canonical and accepts `PsiTransition` only at its execution boundary. Legacy `State -> State` callables are isolated in `core.legacy_engine.LegacyEngine`.

## Rules

1. New core evolution code MUST use `PsiTransition`.
2. Legacy `State -> State` callables MUST use `LegacyEngine` and MUST NOT be presented as proof of canonical Ψ semantics.
3. `Engine.step()` invokes `PsiTransition.on_state()`; a legacy callable supplied to `Engine` cannot execute through the canonical boundary.
4. Compatibility remains explicit and separately named while supported callers are migrated.
5. Any future mutation of either path must preserve its declared contract.

## Evidence

The D-001 audit branch contains explicit regression tests proving:
- canonical `Engine` executes `PsiTransition`;
- a legacy callable cannot execute through canonical `Engine`;
- legacy evolution is routed through `LegacyEngine`;
- the terminal bridge returns `LegacyEngine`, not canonical `Engine`.

Architecture Gate and full Tests CI pass on the audited head.

## Next gate

D-001 final closure requires preserving this separation when the branch is merged.