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


## Evidence/provenance authority gate

Evidence and provenance are descriptive inputs, not admission authority. A proof carrying trusted-looking source identifiers, attestation metadata, evidence hashes, or attached provenance remains rejected when `passed`/`invariant` are false. Provenance attachment validates identity binding only; it does not mutate the candidate or create an Admission.

Adversarial evidence: `tests/test_admission_boundary.py` covers trusted-looking evidence attempting to upgrade rejection and provenance attempting to create admission authority. CI at HEAD `615925dba19e352603de98fa52c619a67a3da793`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.


## Persistence-to-authority gate

Persisted evidence/provenance remains descriptive after restart. `verify_cross_table_consistency()` validates durable binding, then the recovered provenance is supplied to a rejected `ProofObligation`; it does not create an Admission. This explicitly tests `Persistence ≠ Authority` across process restart.

CI evidence at HEAD `7d9ac8c8049b9bac598453464a8ec2e81abc6159`: Tests, Architecture Gate, and Gnozis Port CI SUCCESS.
