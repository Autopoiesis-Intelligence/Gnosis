# Research Machine Record Schema v1

**Version:** 1.0.0  
**Status:** CANONICAL

## Purpose

Schema v1 defines the minimum machine-readable identity and provenance contract for Gnosis Research Machine records.

## Required fields

- `id` — immutable globally unique research machine record identifier.
- `type` — canonical record class.
- `status` — current epistemic/lifecycle status.
- `title` — concise human-readable label.
- `scope` — explicit applicability boundary.
- `statement` — the record's primary content/claim.
- `source` — provenance information.
- `relations` — explicit links to other records.
- `evidence` — evidence references or an explicit empty set.
- `engineering` — engineering consequence state; absence is represented explicitly.
- `created_at` — creation timestamp.
- `schema_version` — must be `1.0.0`.

## Evidence rule

No record may imply verification merely because evidence fields exist.

Evidence status and claim status are separate.

## Supersession rule

Superseded records remain immutable historical records. A new record is created and linked using `SUPERSEDES` / `SUPERSEDED_BY`.

## Relation rule

Relations are typed. Free-form references are not canonical.

## Engineering boundary

`engineering.consequence` may be `null` when no demonstrated engineering consequence exists.

A research result without an engineering consequence remains research.

## Current Core boundary

Research Machine records do not authorize source changes, activation, governance, or deployment.
