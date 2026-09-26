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
