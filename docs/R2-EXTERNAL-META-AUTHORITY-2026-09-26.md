# R2 External Adapter + Meta Authority Boundary — 2026-09-26

## Findings

The inspected external-adaptation boundary is classified correctly: external connectors/adapters are not trusted state writers. Research-Memory is evidence/context, not Core authority.

`MetaTransition.apply()` is also fail-closed through `MetaAdmission`: a transition cannot apply unless its refinement proof, exact before/after binding, and root-invariant closure are admissible.

## Authority graph

External input
-> adapter
-> explicit canonical input
-> Proof
-> Admission
-> SemanticCommit
-> TransitionRecord
-> durable persistence

Meta self-change
-> MetaTransition
-> RefinementProof
-> MetaAdmission
-> apply

Neither path allows an external adapter or an unproved meta-transition to write canonical semantic history.

## Remaining limitation

The repository still contains compatibility and generic layers (`State -> State`, generic canonical-chain governance). They are explicitly classified rather than silently promoted into the canonical Ψ authority. Full universal no-bypass remains unproven until every public caller is enumerated and routed or permanently isolated.
