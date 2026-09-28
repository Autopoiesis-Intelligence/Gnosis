from core.distribution_contract import KernelCapacity
from core.kernel_registry import KernelDescriptor, KernelRegistry
from core.kernel_runtime_contract import KernelRuntimeStatus
from core.runtime_registry_feedback import RuntimeCapacityObservation, apply_runtime_observation


def registry():
    d = KernelDescriptor(
        "kernel.math.2", ("math",), KernelCapacity("kernel.math.2", 8, 8), True,
        "gnozis", "product-hash", "core.main", "parent-hash",
        "identity-hash", "provision-digest",
    )
    return KernelRegistry((d,))


def test_healthy_runtime_updates_capacity():
    status = KernelRuntimeStatus("kernel.math.2", "runtime:kernel.math.2", 12, True)
    updated = apply_runtime_observation(registry(), RuntimeCapacityObservation.from_status(status))
    assert updated.candidates("math")[0].capacity.available_units == 12


def test_unhealthy_runtime_is_removed_from_routing():
    status = KernelRuntimeStatus("kernel.math.2", "runtime:kernel.math.2", 0, False)
    updated = apply_runtime_observation(registry(), RuntimeCapacityObservation.from_status(status))
    assert updated.candidates("math") == ()
