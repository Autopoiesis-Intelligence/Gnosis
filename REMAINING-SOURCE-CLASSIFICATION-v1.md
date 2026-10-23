# GNOZIS Remaining Source Classification v1

Status: TRANSFER MANIFEST — NO SOURCE DELETION
Source: Gnozis/main
Targets: Gnozis-Core, Gnozis-Research-Memory, Gnozis-Exchange, Gnozis-Genezis, Gnozis

## Classification

| Source path | Target | Treatment |
|---|---|---|
| core/ | Gnozis-Core | IMPLEMENTATION |
| formal/ | Gnozis-Core | FORMAL CONTRACT/EVIDENCE |
| tests/ | Gnozis-Core | TESTS |
| tools/ | Gnozis-Core | DEVELOPMENT TOOLS; review external-facing tools |
| docs/CORE_* and core conformance/proof docs | Gnozis-Core | CORE EVIDENCE |
| docs/ audits/history not required at runtime | Research-Memory | HISTORICAL EVIDENCE |
| research_machine/ | Gnozis-Research-Memory | MACHINE-READABLE RESEARCH/EVIDENCE |
| research/ | Gnozis-Research-Memory | RESEARCH |
| contracts/ | Research-Memory | CONTRACT HISTORY/RESEARCH; Core canonical contracts only after review |
| provenance/ | Research-Memory | PROVENANCE |
| AI_CONTEXT.md | Research-Memory | CONTEXT |
| GNOZIS_MASTER_AUDIT.md | Research-Memory | AUDIT |
| PHILOSOPHY.md | Research-Memory | RESEARCH |
| PROJECT_STATE.md | Research-Memory | HISTORICAL STATE |
| STATE.md | Research-Memory/historical | HISTORICAL |
| CLAIMS.md | Research-Memory/historical | EVIDENCE REVIEW |
| gnosis-terminal-bridge/ | Gnozis-Exchange | EXTERNAL BOUNDARY |
| bot.py | Gnozis-Exchange | EXTERNAL INTERFACE; security review required |
| render.yaml | Gnozis-Exchange | DEPLOYMENT, if bridge deployment remains |
| requirements.txt | split per target | DEPENDENCY REVIEW |
| pyproject.toml | split per target | DEPENDENCY REVIEW |
| .github/workflows/gnozis-port.yml | Gnozis-Exchange | EXTERNAL PORT CI |
| .github/workflows/test.yml | Gnozis-Core | CORE CI, after path correction |
| README.md | Gnozis | PUBLIC PRODUCT |
| DISCOVERY-POLICY | Gnozis | PUBLIC DISCOVERY |
| CITATION | Gnozis | PUBLIC PRODUCT CITATION |
| CONTRIBUTING | Gnozis + target repos | SPLIT |
| CHANGELOG | split | PRODUCT/CORE/HISTORY |
| EVOLUTION.md | split | PRODUCT + CORE + RESEARCH |
| ROADMAP.md | split | PRODUCT + CORE + RESEARCH + Genesis-private |
| MIGRATION-* / LEGAL-MIGRATION-* | temporary migration control | REMOVE/ARCHIVE AFTER FREEZE |
| COMMERCIAL-LICENSE* | legal quarantine | DO NOT MIGRATE AUTOMATICALLY |
| COPYRIGHT* | legal quarantine | DO NOT MIGRATE AUTOMATICALLY |
| TRADEMARKS* | legal quarantine | DO NOT MIGRATE AUTOMATICALLY |

## Non-canonical / unresolved

No source directory is deleted from Gnozis until its target copy is verified and its canonical owner is recorded.

research_machine/ is explicitly Research-Memory, not Core runtime.

gnosis-terminal-bridge/ is explicitly Exchange, not Core.

Public Gnozis must not contain Genesis-private implementation.

## Next transfer order

1. research_machine/ -> Research-Memory
2. gnosis-terminal-bridge/ + bot.py -> Exchange, security review
3. Core implementation/formal/tests/tools -> Core
4. Core/public docs split
5. CI/workflow split
6. final source de-duplication only after verification

> 2026-10-23: `bot.py`, `render.yaml` and `requirements.txt` were removed from Gnosis (old Telegram/OpenRouter bot, out of the active stack). They remain in git history at `935233c`.
