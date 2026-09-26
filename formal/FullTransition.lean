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

def FundamentalAdmission (I : Psi → Prop) (candidate : Psi)
    (proof : ProofObligation I candidate) : Prop :=
  proof.passed = true ∧ proof.invariant_ok

def EvolutionaryAdmission (I : Psi → Prop) (candidate : Psi)
    (proof : ProofObligation I candidate) : Prop :=
  proof.passed = true ∧ proof.invariant_ok ∧ proof.viable

inductive AdmissionRegime
  | fundamental
  | evolutionary

def Admission (regime : AdmissionRegime) (I : Psi → Prop) (candidate : Psi)
    (proof : ProofObligation I candidate) : Prop :=
  match regime with
  | .fundamental => FundamentalAdmission I candidate proof
  | .evolutionary => EvolutionaryAdmission I candidate proof

structure CertifiedTransition
    (regime : AdmissionRegime)
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma) where
  candidate : Psi
  next : Sigma
  nextK : K
  proof : ProofObligation I candidate
  admission : Admission regime I candidate proof
  commit_psi : next.psi = candidate
  preserves_root : root s.K → root nextK

theorem full_transition_preserves
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma)
    (t : CertifiedTransition regime I root s)
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


/-- Evidence is not a constructor for certification.  The only way to obtain
    a CertifiedTransition is to supply its explicit Admission and
    root-preservation fields. -/
theorem evidence_does_not_imply_certified_transition
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma)
    (candidate : Psi)
    (proof : ProofObligation I candidate) :
    ¬ Admission I candidate proof →
    ¬ ∃ t : CertifiedTransition I root s, t.candidate = candidate := by
  intro hNoAdmission hExists
  rcases hExists with ⟨t, hCandidate⟩
  exact hNoAdmission t.admission


theorem certified_transition_supports_fundamental_or_evolutionary
    (regime : AdmissionRegime)
    (I : Psi → Prop) (root : K → Prop)
    (s : Sigma)
    (t : CertifiedTransition regime I root s)
    (hRoot : root s.K) :
    J I root t.next t.nextK := by
  constructor
  · rw [t.commit_psi]
    exact t.proof.invariant_ok
  · exact t.preserves_root hRoot

