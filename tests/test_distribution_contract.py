from core.distribution_contract import KernelCapacity, decide_distribution


def test_distribution_is_deterministic_and_capacity_aware():
    decision = decide_distribution(
        decision_id="dist-1",
        capability="math",
        workload_digest="work-1",
        capacities=(
            KernelCapacity("kernel-b", 2, 10),
            KernelCapacity("kernel-a", 7, 10),
        ),
    )
    assert decision.selected_kernel_id == "kernel-a"
    assert decision.capacity_snapshot_digest
    assert decision.digest()


def test_distribution_tie_breaks_by_kernel_id():
    decision = decide_distribution(
        decision_id="dist-2",
        capability="physics",
        workload_digest="work-2",
        capacities=(
            KernelCapacity("kernel-b", 5, 10),
            KernelCapacity("kernel-a", 5, 10),
        ),
    )
    assert decision.selected_kernel_id == "kernel-a"


def test_distribution_rejects_invalid_capacity():
    try:
        decide_distribution(
            decision_id="dist-3",
            capability="cad",
            workload_digest="work-3",
            capacities=(KernelCapacity("kernel-a", 11, 10),),
        )
    except ValueError:
        return
    raise AssertionError("invalid capacity must be rejected")


def test_distribution_uses_registry_capability_boundary():
    from core.kernel_registry import KernelDescriptor, KernelRegistry

    registry = KernelRegistry(
        (
            KernelDescriptor("math", ("math",), KernelCapacity("math", 3, 10)),
            KernelDescriptor("physics", ("physics",), KernelCapacity("physics", 9, 10)),
        )
    )
    decision = decide_distribution(
        decision_id="dist-registry",
        capability="physics",
        workload_digest="work",
        registry=registry,
    )
    assert decision.selected_kernel_id == "physics"
