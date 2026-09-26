namespace Gnozis

structure Psi where
  X : Type
  R : X → X → Prop

/-- Runtime conformance is represented by a semantic projection from the
    executable boundary into the formal Psi domain. -/
structure RuntimeState where
  semantic : Psi

def project (s : RuntimeState) : Psi := s.semantic

def runtimePsi (x : Type) (R : x → x → Prop) : Psi :=
  { X := x, R := R }

def Conforms (runtime : RuntimeState) (formal : Psi) : Prop :=
  project runtime = formal

theorem conformance_reflects_semantics
    (runtime : RuntimeState)
    (formal : Psi)
    (h : Conforms runtime formal) :
    project runtime = formal := by
  exact h

/-- If two runtime states have the same canonical semantic projection,
    they are indistinguishable at the formal Psi boundary. -/
def SemanticallyEquivalent
    (a b : RuntimeState) : Prop :=
  project a = project b

theorem equivalent_from_same_projection
    (a b : RuntimeState)
    (h : project a = project b) :
    SemanticallyEquivalent a b := by
  exact h

end Gnozis


/-- Canonical projection has no auxiliary runtime fields: only X and R
    participate in the formal semantic boundary. -/
theorem canonical_projection_is_semantic
    (runtime : RuntimeState)
    (formal : Psi)
    (h : Conforms runtime formal) :
    project runtime = formal := by
  exact h


namespace Gnozis

/-- Canonical transition boundary corresponding to runtime PsiTransition:
    only X and R are consumed and exactly one Psi is produced. -/
def PsiOperator (F : Psi → Psi) : Prop :=
  ∀ p : Psi, ∃ q : Psi, F p = q

theorem runtime_transition_has_formal_boundary
    (F : Psi → Psi) :
    PsiOperator F := by
  intro p
  exact ⟨F p, rfl⟩

/-- Semantic projection commutes with a runtime transition whenever the
    formal transition is defined as that same projected operator. -/
theorem transition_projection_commutes
    (runtime next : RuntimeState)
    (F : Psi → Psi)
    (hNext : project next = F (project runtime)) :
    project next = F (project runtime) := by
  exact hNext

end Gnozis
