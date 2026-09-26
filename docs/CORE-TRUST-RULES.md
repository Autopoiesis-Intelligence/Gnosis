# Core Trust Rules

1. Trusted state changes only through the explicit verification/commit path.
2. Research-Memory is evidence/context material, never Core authority.
3. Genesis is a producer/orchestrator, never a hidden authority inside Core.
4. External connectors are adapters, never trusted state writers.
5. LLM/AI output is untrusted input until explicitly tested and verified.
6. Persistence, retrieval, consumption and influence are separate operations.
7. Every accepted transition must have deterministic identity and provenance.
8. A context restore may reconstruct authorized working context, but cannot silently restore authority.
9. Downstream repository updates cannot mutate trusted Core state implicitly.
10. Missing evidence blocks a maturity claim; implementation alone is insufficient.


## Evolution influence gate

Candidate generation is not authority. A generated candidate can affect canonical evolution only through the existing proof/admission boundary. A rejected candidate produces no transition result and leaves the input state unchanged. Selection remains endogenous and deterministic; no external candidate selector is consulted.

Adversarial evidence: `tests/test_evolution_selection_boundaries.py` covers rejected-candidate non-commit and endogenous candidate selection. CI at the current test baseline is GREEN.


## Meta-admission anti-bypass gate

Meta-evolution cannot bypass the unified admission contract. A proposed meta-transition must preserve the root invariant on both before/after states and satisfy the closure obligation. A forged refinement predicate alone is insufficient; `MetaAdmission.apply()` fails closed when either gate is false.

Adversarial CI coverage also confirms the ordinary evolution path still requires depth-1 viability; a candidate with no valid continuation is not admitted merely because its selector/test accepts it.

CI evidence at HEAD `edafcd3813772bba176047b8f0b288857b9d9faa`: Tests, Architecture Gate and Gnozis Port CI SUCCESS.
