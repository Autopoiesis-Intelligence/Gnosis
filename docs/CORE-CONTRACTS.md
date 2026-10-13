# Gnosis-Core Contracts

## Purpose

These contracts define the minimum boundary that every higher layer must use when interacting with Gnosis-Core.

## State

A trusted state has an explicit state_id, canonical representation, digest, version and provenance reference.

## ExecutionInput runtime binding

ExecutionInput is a mandatory runtime identity for canonical CanonicalExecutor.step().

The runtime contract is:

1. Construct ExecutionInput(input_type, state_id, state_digest, content_digest) for the state intended for execution.
2. Before invoking the declared transition, derive the actual state_digest and deterministic state_id from the supplied canonical Psi.
3. Reject execution if either declared identity or digest differs from the supplied Psi.
4. Only after successful verification may the transition enter proof, admission and commit.
5. A rejected binding must not invoke the transition and must not mutate history.

The state digest is the SHA-256 digest of the canonical runtime representation already used by commit history:

SHA256(repr((psi.x, psi.relations))).

The state identity is:

SHA256("gnozis-state-id-v1:" || state_digest).

Execution-input identity is:

SHA256(input_type || state_id || state_digest || content_digest).

This binding closes state substitution at the canonical execution boundary. It does not make content_digest proof of content by itself; content provenance and evidence remain separate contracts.

## Transition

A transition is an explicit candidate operation from one trusted state to another. It carries input identity and evidence. No implicit clock, global selector, hidden model call or external repository is authoritative.

## Context

Context is explicit data: identity reference, project reference, session/task context, selected knowledge/evidence references, permissions, version and provenance. Context can be restored without exposing Core internals.

## Evidence

Evidence records what was observed, tested, verified and committed. Persistence is not itself proof of correctness.

## External update

Core may emit a governed update request for a downstream repository or service. The downstream result is recorded as an external artifact/evidence item; it does not become Core authority automatically.

## Authority

Only the Core verification/commit path can change trusted state.
