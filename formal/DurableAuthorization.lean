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
    Identity/state binding and recovery preservation remain separate facts. -/
structure RuntimeDurableAuthorizationEvidence where
  authorizationDigest : String
  stateDigest : String
  consumedDigest : String

def RuntimeDurableAuthorizationConforms
    (e : RuntimeDurableAuthorizationEvidence)
    (before after : String → Prop) : Prop :=
  ConsumptionBinding e.authorizationDigest e.stateDigest
    e.consumedDigest e.stateDigest ∧
  RecoveryPreservesConsumption before after

theorem runtime_durable_authorization_conforms_to_formal
    (e : RuntimeDurableAuthorizationEvidence)
    (before after : String → Prop)
    (hBinding : ConsumptionBinding e.authorizationDigest e.stateDigest
      e.consumedDigest e.stateDigest)
    (hRecovery : RecoveryPreservesConsumption before after) :
    RuntimeDurableAuthorizationConforms e before after := by
  exact ⟨hBinding, hRecovery⟩

/-- Runtime evidence plus recovery preservation yields the same formal
    replay prohibition used by the durable-authorization model. -/
theorem runtime_durable_authorization_replay_forbidden
    (e : RuntimeDurableAuthorizationEvidence)
    (before after : String → Prop)
    (h : RuntimeDurableAuthorizationConforms e before after)
    (hConsumed : Consumed e.authorizationDigest before) :
    ¬ Executable e.authorizationDigest after := by
  exact recovery_cannot_reauthorize_consumed before after h.2
    e.authorizationDigest hConsumed

end Gnozis
