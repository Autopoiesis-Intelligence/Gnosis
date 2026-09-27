# R2 Runtime Dynamic Authority Boundary — 2026-09-26

## Adversarial target

Static AST inventory cannot reason about every dynamic Python dispatch mechanism. The runtime probe therefore tests whether dynamically obtaining the canonical commit type or an `apply` callable can manufacture authority without a valid `Admission`.

## Result

Dynamic lookup may recover a callable/type, but callable identity alone does not create semantic authority. An uninitialised or unauthorised `SemanticCommit` object is rejected by the admission gate when its mutation path is invoked.

## Boundary

This is runtime evidence for the existing object-level authority gate. It is not a proof against arbitrary hostile Python code with unrestricted process privileges. Such code can bypass application contracts by modifying memory, monkey-patching modules, or using native/OS facilities; that is a process isolation/security boundary rather than the semantic Core contract.
