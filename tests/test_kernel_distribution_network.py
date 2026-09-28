from core.distribution_contract import KernelCapacity
from core.kernel_distribution_network import KernelDistributionNetwork
from core.kernel_registry import KernelDescriptor, KernelRegistry


def test_distribution_network_routes_to_highest_capacity():
    registry = KernelRegistry((
        KernelDescriptor("kernel.b", ("math",), KernelCapacity("kernel.b", 3, 10)),
        KernelDescriptor("kernel.a", ("math",), KernelCapacity("kernel.a", 8, 10)),
    ))
    network = KernelDistributionNetwork(registry)
    decision = network.route(decision_id="d1", capability="math", workload_digest="w1")
    assert decision.selected_kernel_id == "kernel.a"


def test_distribution_network_is_deterministic_on_tie():
    registry = KernelRegistry((
        KernelDescriptor("kernel.b", ("math",), KernelCapacity("kernel.b", 5, 10)),
        KernelDescriptor("kernel.a", ("math",), KernelCapacity("kernel.a", 5, 10)),
    ))
    network = KernelDistributionNetwork(registry)
    assert network.route(decision_id="d1", capability="math", workload_digest="w1").selected_kernel_id == "kernel.a"
