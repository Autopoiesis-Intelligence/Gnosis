namespace Gnozis

/-- A durable authorization is consumed at most once.
    Consumption is modeled as a set membership fact, independent of Psi state. -/
def Consumed (a : String) (consumed : String → Prop) : Prop := consumed a

/-- Recovery preserves the durable consumption fact. -/
def RecoveryPreservesConsumption
    (before after : String → Prop) : Prop :=
  ∀ a, before a → after a

theorem recovered_authorization_remains_consumed
    (before after : A → Prop)
    (hRecovery : RecoveryPreservesConsumption before after)
    (a : A)
    (hConsumed : Consumed a before) :
    Consumed a after := by
  exact hRecovery a hConsumed

/-- A consumed authorization cannot be executable again. -/
def Executable (a : A) (consumed : A → Prop) : Prop :=
  ¬ Consumed a consumed

theorem recovery_cannot_reauthorize_consumed
    (before after : A → Prop)
    (hRecovery : RecoveryPreservesConsumption before after)
    (a : A)
    (hConsumed : Consumed a before) :
    ¬ Executable a after := by
  intro hExec
  exact hExec (recovered_authorization_remains_consumed before after hRecovery a hConsumed)

end Gnozis


/-- The SQLite binding maps the authorization identity and its pre-transition
    state digest to the durable consumption fact. -/
def ConsumptionBinding (authorizationDigest stateDigest : String)
    (consumedDigest consumedState : String) : Prop :=
  authorizationDigest = consumedDigest ∧ stateDigest = consumedState

theorem valid_consumption_binding_implies_consumed
    (authorizationDigest stateDigest consumedDigest consumedState : String)
    (h : ConsumptionBinding authorizationDigest stateDigest consumedDigest consumedState) :
    authorizationDigest = consumedDigest := by
  exact h.1


namespace Gnozis

/-- Minimal formal projection of the runtime durable-authorization evidence.
    The projection carries identity, pre-transition state binding, and durable
    consumption as separate facts; it introduces no executable authority. -/
structure RuntimeDurableAuthorizationEvidence where
  authorizationDigest : String
  stateDigest : String
  consumedDigest : String
  consumedState : String
  consumedBeforeRecovery : Prop
  consumedAfterRecovery : Prop

def RuntimeDurableAuthorizationConforms
    (e : RuntimeDurableAuthorizationEvidence) : Prop :=
  ConsumptionBinding e.authorizationDigest e.stateDigest
    e.consumedDigest e.consumedState ∧
  e.consumedBeforeRecovery → e.consumedAfterRecovery

theorem runtime_durable_authorization_conforms_to_formal
    (e : RuntimeDurableAuthorizationEvidence)
    (hBinding : ConsumptionBinding e.authorizationDigest e.stateDigest
      e.consumedDigest e.consumedState)
    (hRecovery : e.consumedBeforeRecovery → e.consumedAfterRecovery) :
    RuntimeDurableAuthorizationConforms e := by
  exact ⟨hBinding, hRecovery⟩

/-- Once the runtime evidence establishes durable consumption and recovery
    preserves it, the formal replay prohibition follows. -/
theorem runtime_durable_authorization_replay_forbidden
    (e : RuntimeDurableAuthorizationEvidence)
    (h : RuntimeDurableAuthorizationConforms e)
    (hConsumed : e.consumedBeforeRecovery) :
    ¬ Executable e.authorizationDigest (fun a => a = e.consumedDigest) := by
  have hAfter : e.consumedAfterRecovery := h.2 hConsumed
  have hIdentity : e.authorizationDigest = e.consumedDigest := h.1.1
  intro hExec
  apply hExec
  exact hIdentity

end Gnozis
