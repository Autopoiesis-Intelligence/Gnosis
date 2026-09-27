"""Canonical execution owner: Generate -> Proof -> Admission -> Select -> Commit -> History."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .admission import admit
from .commit import commit
from .execution_contract import ExecutionInput, verify_execution_input
from .history import AppendOnlyHistory
from .sqlite_persistence import SQLiteHistoryStore
from .proof import prove_fundamental_transition, prove_transition
from .psi_transition import PsiTransition
from .state import Psi, State

Generator = Callable[[State], Iterable[State]]
Tester = Callable[[State], bool]


@dataclass(frozen=True)
class ExecutionResult:
    psi: Psi
    history: AppendOnlyHistory


@dataclass
class CanonicalExecutor:
    history: AppendOnlyHistory
    kernel_version: str
    durable_store: SQLiteHistoryStore | None = None

    def __post_init__(self):
        if self.durable_store is not None:
            self.history = self.durable_store.load()

    def step(
        self,
        psi: Psi,
        transition: PsiTransition,
        execution_input: ExecutionInput,
        *,
        test: Tester | None = None,
        authorization_digest: str | None = None,
        authorization_state_digest: str | None = None,
    ) -> ExecutionResult:
        """Own one canonical Psi execution step with fail-closed input binding."""
        if not isinstance(psi, Psi):
            raise TypeError("psi must be Psi.")
        if not isinstance(transition, PsiTransition):
            raise TypeError("transition must be PsiTransition.")

        if self.durable_store is not None:
            durable_head = self.history.head
            if durable_head is not None and execution_input.state_digest != durable_head.state_hash:
                raise ValueError("ExecutionInput state does not match durable history head.")

        # Runtime trust boundary: the declared execution input must identify
        # exactly the Psi supplied to this execution. A foreign state_id or
        # state_digest is rejected before transition execution.
        verify_execution_input(execution_input, psi)

        candidate = transition(psi)
        current = State.from_psi(psi)
        next_state = State.from_psi(candidate)

        if test is None:
            test = lambda _: True

        # Canonical candidate source is exclusively the declared ΨTransition.
        # The proof is bound to this exact candidate; no alternate candidate
        # source may enter the admission path.
        proof = prove_fundamental_transition(
            current,
            next_state,
            test,
        )
        admission = admit(next_state.to_psi(), proof)
        if not admission.accepted:
            return ExecutionResult(psi=psi, history=self.history)

        from .canonical_chain import commit_admitted_psi
        committed = commit_admitted_psi(
            self.history, psi, admission,
            kernel_version=self.kernel_version,
            durable_store=self.durable_store,
            authorization_digest=authorization_digest,
            authorization_state_digest=authorization_state_digest,
        )
        self.history = committed.history
        return ExecutionResult(psi=committed.value, history=committed.history)

    def evolve(
        self,
        psi: Psi,
        generate: Generator,
        test: Tester,
    ) -> ExecutionResult:
        """Own one complete canonical evolution step."""
        if not isinstance(psi, Psi):
            raise TypeError("psi must be Psi.")

        current = State.from_psi(psi)
        candidates = list(generate(current))
        if not candidates:
            raise ValueError("Generator must produce at least one candidate state")

        proofs = [
            prove_transition(current, candidate, candidates, test)
            for candidate in candidates
        ]
        admissions = [
            admit(candidate, proof)
            for candidate, proof in zip(candidates, proofs)
        ]
        valid = [item for item in admissions if item.accepted]
        # Rejected candidates are terminal at this boundary: they are never
        # transformed, repaired, re-admitted, or exposed to selection.

        if not valid:
            return ExecutionResult(psi=psi, history=self.history)

        selected = min(
            valid,
            key=lambda item: (
                len(item.candidate.to_psi().relations),
                repr(item.candidate.to_psi()),
            ),
        )
        selected = type(selected)(
            accepted=selected.accepted,
            candidate=selected.candidate.to_psi(),
            proof=selected.proof,
        )

        from .canonical_chain import commit_admitted_psi
        committed = commit_admitted_psi(
            self.history, psi, selected,
            kernel_version=self.kernel_version,
            durable_store=self.durable_store,
        )
        self.history = committed.history
        return ExecutionResult(psi=committed.value, history=committed.history)
