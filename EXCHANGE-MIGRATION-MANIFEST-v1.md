# EXCHANGE-MIGRATION-MANIFEST-v1

Status: PREPARED / NOT MIGRATED
Source: Gnozis/main
Target: Gnozis-Exchange/main
Rule: source remains untouched until target verification passes.

## Safe boundary batch

- bot.py
- render.yaml
- gnosis-terminal-bridge/README.md
- gnosis-terminal-bridge/INTERNET_PORT.md
- gnosis-terminal-bridge/src/internet_port.py
- gnosis-terminal-bridge/src/core_adapter.py

## Classification

bot.py -> Exchange external bot adapter; credentials must remain environment-provided.
render.yaml -> Exchange deployment metadata; environment values must not contain literal secrets.
gnosis-terminal-bridge/README.md -> public Exchange documentation.
gnosis-terminal-bridge/INTERNET_PORT.md -> public protocol specification.
gnosis-terminal-bridge/src/internet_port.py -> Exchange Internet boundary implementation.
gnosis-terminal-bridge/src/core_adapter.py -> Exchange-to-Core adapter.

## Verification gates

1. Target repository exists and is writable.
2. Every listed source file exists on main.
3. Target content equals source content after transfer.
4. No literal credentials are introduced.
5. Imports/path references are compatible with Exchange.
6. Exchange tests pass or failures are explicitly recorded.
7. Only after 1-6 may source deletion/relocation be considered.

## Explicit exclusions

- Core internals
- Genesis-private implementation
- Research-Memory
- unreviewed bridge files
- credentials/secrets
- automatic deletion from Gnozis

## Migration state

Physical transfer: BLOCKED by target write access.
Source preservation: REQUIRED.

> 2026-10-23: `bot.py`, `render.yaml` and `requirements.txt` were removed from Gnosis (old Telegram/OpenRouter bot, out of the active stack). They remain in git history at `935233c`.
