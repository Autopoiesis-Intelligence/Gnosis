from core.distribution_contract import KernelCapacity
from core.kernel_registry import KernelDescriptor, KernelRegistry
from core.registry_capacity_expansion import build_expansion_request


def registry():
    return KernelRegistry((
        KernelDescriptor("k1", ("math",), KernelCapacity("k1", 4, 4)),
        KernelDescriptor("k2", ("math",), KernelCapacity("k2", 3, 3)),
    ))


def test_expansion_request_uses_registry_capacity():
    request = build_expansion_request(
        registry(), request_id="e1", capability="math",
        workload_digest="work", required_units=10,
        capacity_snapshot_digest="snap",
    )
    assert request.available_units == 7
    assert request.deficit_units == 3


def test_expansion_request_with_sufficient_registry_capacity_has_no_deficit():
    request = build_expansion_request(
        registry(), request_id="e1", capability="math",
        workload_digest="work", required_units=7,
        capacity_snapshot_digest="snap",
    )
    assert request.available_units == 7
    assert request.deficit_units == 0
