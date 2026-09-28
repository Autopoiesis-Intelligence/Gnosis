from core.execution_contract import ExecutionInput
from core.kernel_network_lifecycle import expand_and_route
from core.kernel_provisioning_contract import KernelProvisionRequest
from core.kernel_registry import KernelRegistry
from core.network_expansion_contract import ExpansionRequest


def test_full_kernel_network_lifecycle():
    expansion = ExpansionRequest("e1", "math", "work", 8, 0, "snapshot")
    provisioning = KernelProvisionRequest(
        "p1", expansion.digest(), "math", 8,
        "core.main", "parent-hash", "gnozis", "product-hash",
    )
    lifecycle = expand_and_route(
        registry=KernelRegistry(()),
        expansion_request=expansion,
        provisioning_request=provisioning,
        kernel_id="kernel.math.2",
        decision_id="d1",
        workload_digest="work",
        execution_input=ExecutionInput("test", "s1", "sd1", "cd1"),
    )
    assert lifecycle.admission.kernel_id == "kernel.math.2"
    assert lifecycle.binding.kernel_id == "kernel.math.2"
