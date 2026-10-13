# Context Continuity Contract

## Goal

An authorized user can continue work across sessions, devices and connected AI interfaces without manually rebuilding the working context.

## Context layers

1. Identity — identifies the principal and authorization scope.
2. Project — identifies the project/workspace being continued.
3. Task — identifies the active task and its current state.
4. Knowledge — references relevant durable knowledge and evidence.
5. Session — contains transient interaction state.
6. Provenance — records where restored context came from and which version produced it.

## Rules

- Context is explicit and versioned.
- Only authorized context is restored.
- Restoring context does not restore trusted authority.
- Missing or conflicting context must be represented explicitly, not silently guessed.
- A connected AI is a consumer/orchestrator of context, not the owner of Core authority.
- Context references may point to Gnosis-Memory or downstream surfaces without making those surfaces trusted Core sources.
