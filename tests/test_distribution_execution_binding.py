from core.distribution_contract import DistributionDecision
from core.distribution_execution_binding import bind_distribution_to_execution
from core.execution_contract import ExecutionInput
from core.kernel_execution_contract import KernelExecutionContract


def test_distribution_execution_binding_is_deterministic():
    decision = DistributionDecision("d1", "kernel.math.1", "math", "w1", "c1")
    contract = KernelExecutionContract("kernel.math.1", "math", "d1", "test", 10)
    execution_input = ExecutionInput("test", "s1", "sd1", "cd1")
    binding = bind_distribution_to_execution(decision, contract, execution_input)
    assert binding.decision_digest == decision.digest()
    assert binding.kernel_id == "kernel.math.1"
    assert binding.execution_identity == contract.identity(execution_input, decision)


def test_distribution_execution_binding_rejects_kernel_mismatch():
    decision = DistributionDecision("d1", "kernel.physics.1", "math", "w1", "c1")
    contract = KernelExecutionContract("kernel.math.1", "math", "d1", "test", 10)
    execution_input = ExecutionInput("test", "s1", "sd1", "cd1")
    try:
        bind_distribution_to_execution(decision, contract, execution_input)
    except ValueError as exc:
        assert "selected kernel" in str(exc)
        return
    raise AssertionError("mismatched distribution target must be rejected")
