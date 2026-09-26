namespace Gnozis

structure Psi where
  X : Type
  R : X → X → Prop

structure Sigma where
  psi : Psi
  W : Type
  K : Type

def J (I : Psi → Prop) (root : K → Prop) (s : Sigma) (k : K) : Prop :=
  I s.psi ∧ root k

structure ProofObligation (I : Psi → Prop) (candidate : Psi) where
  passed : Bool
  invariant_ok : I candidate
  viable : Prop

def Admission (I : Psi → Prop) (candidate : Psi)
    (proof : ProofObligation I candidate) : Prop :=
  proof.passed = true ∧ proof.invariant_ok ∧ proof.viable

structure CertifiedTransition
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma) where
  candidate : Psi
  next : Sigma
  nextK : K
  proof : ProofObligation I candidate
  admission : Admission I candidate proof
  commit_psi : next.psi = candidate
  preserves_root : root s.K → root nextK

theorem full_transition_preserves
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma)
    (t : CertifiedTransition I root s)
    (hI : I s.psi)
    (hRoot : root s.K) :
    J I root t.next t.nextK := by
  constructor
  · rw [t.commit_psi]
    exact t.proof.invariant_ok
  · exact t.preserves_root hRoot

end Gnozis


/-- The correct cross-layer boundary keeps K0 on the kernel component:
    a Psi transition may change Psi, but certification must separately prove
    root preservation for the kernel transition. -/
theorem psi_transition_requires_separate_root_certificate
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma)
    (candidate : Psi)
    (proof : ProofObligation I candidate)
    (hAdmission : Admission I candidate proof)
    (nextK : K)
    (hRoot : root s.K)
    (hPreserves : root s.K → root nextK) :
    J I root { psi := candidate, W := s.W, K := nextK } nextK := by
  constructor
  · exact proof.invariant_ok
  · exact hPreserves hRoot
