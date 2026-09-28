from core.evolution_evaluation import EvolutionDecision, EvolutionEvaluation


def test_evolution_evaluation_binds_observed_result():
    evaluation = EvolutionEvaluation(
        "patch-1",
        "parent-state",
        "candidate-state",
        "expected-effect",
        "observed-effect",
        "verification",
        EvolutionDecision.CANARY,
    )
    assert evaluation.digest()


def test_evolution_evaluation_requires_identity():
    try:
        EvolutionEvaluation(
            "", "parent", "candidate", "expected",
            "observed", "verification", EvolutionDecision.REJECT,
        )
    except ValueError:
        return
    raise AssertionError("missing patch identity must be rejected")
