# R2 CI Authority Negative Test — 2026-09-26

The authority invariant is now tested against an intentional forbidden constructor pattern rather than only against the clean repository.

The adversarial fixture represents a future production file attempting to instantiate `SemanticCommit` outside `core/commit.py`. The guard must detect that pattern. A separate assertion ensures comments containing the token are not false positives.

This proves the detector's intended direction: the CI rule is capable of identifying the class of violation it exists to prevent.

The repository remains clean after the adversarial fixture; the forbidden constructor is not committed into production code.
