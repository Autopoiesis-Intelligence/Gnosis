namespace Gnozis

structure Psi where
  X : Type
  R : X → X → Prop

def Invariant (I : Psi → Prop) (p : Psi) : Prop := I p

structure ProofObligation (I : Psi → Prop) (candidate : Psi) where
  passed : Bool
  invariant_ok : I candidate
  viable : Prop

def FundamentalAdmission (I : Psi → Prop) (candidate : Psi) (proof : ProofObligation I candidate) : Prop :=
  proof.passed = true ∧ proof.invariant_ok

def EvolutionaryAdmission (I : Psi → Prop) (candidate : Psi) (proof : ProofObligation I candidate) : Prop :=
  proof.passed = true ∧ proof.invariant_ok ∧ proof.viable

def Admission (I : Psi → Prop) (candidate : Psi) (proof : ProofObligation I candidate) : Prop :=
  EvolutionaryAdmission I candidate proof

def SemanticCommit (I : Psi → Prop) (previous candidate : Psi)
    (proof : ProofObligation I candidate) : Prop :=
  Admission I candidate proof ∧ I previous

theorem commit_requires_admission
    (I : Psi → Prop)
    (previous candidate : Psi)
    (proof : ProofObligation I candidate)
    (h : SemanticCommit I previous candidate proof) :
    Admission I candidate proof := by
  exact h.1

theorem admitted_commit_preserves_invariant
    (I : Psi → Prop)
    (previous candidate : Psi)
    (proof : ProofObligation I candidate)
    (h : SemanticCommit I previous candidate proof) :
    I candidate := by
  exact h.2.2

end Gnozis


/-- Runtime semantic contract: a commit-capable transition cannot exist
    without the same three boolean admission conditions used by Core. -/
def RuntimeAdmissionEquivalent
    (proofPassed proofInvariant proofViable : Bool) : Prop :=
  proofPassed = true ∧ proofInvariant = true ∧ proofViable = true

theorem runtime_admission_implies_commit_admission
    (I : Psi → Prop)
    (candidate : Psi)
    (proof : ProofObligation I candidate)
    (h : RuntimeAdmissionEquivalent proof.passed proof.invariant_ok
      (decide proof.viable)) :
    EvolutionaryAdmission I candidate proof := by
  exact ⟨h.1, h.2.1, proof.viable⟩

theorem runtime_commit_cannot_bypass_admission
    (I : Psi → Prop)
    (previous candidate : Psi)
    (proof : ProofObligation I candidate)
    (h : SemanticCommit I previous candidate proof) :
    proof.passed = true ∧ I candidate ∧ proof.viable := by
  exact ⟨h.2.1, h.2.2.2, h.2.2.2⟩


/-- Fundamental admission is intentionally weaker than evolutionary admission:
    viability is not an input to the fundamental regime. -/
theorem fundamental_does_not_require_viability
    (I : Psi → Prop)
    (candidate : Psi)
    (proof : ProofObligation I candidate)
    (hPassed : proof.passed = true)
    (hInvariant : proof.invariant_ok) :
    FundamentalAdmission I candidate proof := by
  exact ⟨hPassed, hInvariant⟩

/-- Evolutionary admission retains the stronger continuation requirement. -/
theorem evolutionary_requires_viability
    (I : Psi → Prop)
    (candidate : Psi)
    (proof : ProofObligation I candidate)
    (h : EvolutionaryAdmission I candidate proof) :
    proof.viable := by
  exact h.2.2
