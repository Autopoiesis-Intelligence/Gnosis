# CORE-MIGRATION-MANIFEST-v1

Status: PREPARED / NOT MIGRATED
Source: Gnozis/main
Target: Gnozis-Core/main
Rule: source remains untouched until target verification passes.

## Core source sets

- core/ -> Core operational implementation
- formal/ -> Core formal contracts and mathematical evidence
- tests/ -> Core tests
- tools/ -> development/diagnostic tools; external-facing tools require review
- core-specific docs -> Core evidence/documentation

## Separation rules

Research-only material belongs to Gnozis-Research-Memory.
External internet/bot boundary belongs to Gnozis-Exchange.
Genesis-private commercial implementation must not enter public Core.
Public product/discovery material remains in Gnozis.

## Verification gates

1. Target repository exists and is writable.
2. Source tree is inventoried.
3. All candidate files are transferred without omission.
4. Source/target content and Git object identity are verified.
5. Imports and paths are rewritten only where required by the new repository boundary.
6. Core tests and formal verification pass, or failures are recorded as explicit gaps.
7. CI workflows are split and validated.
8. No external selector, hidden clock, LLM, second state model, or GitHub state is introduced into Core.
9. Persistence, audit, provenance, evolution and trust-boundary contracts remain intact.
10. Source deletion/relocation is considered only after all preceding gates pass.

## Explicit exclusions

- research_machine/
- research/
- gnosis-terminal-bridge/
- bot.py
- Genesis-private implementation
- credentials/secrets
- unreviewed public product documents

## Migration state

Physical transfer: BLOCKED until Gnozis-Core is writable/available.
Source preservation: REQUIRED.

> 2026-10-23: `bot.py`, `render.yaml` and `requirements.txt` were removed from Gnosis (old Telegram/OpenRouter bot, out of the active stack). They remain in git history at `935233c`.
