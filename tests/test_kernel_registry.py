from core.distribution_contract import KernelCapacity
from core.kernel_registry import KernelDescriptor, KernelRegistry


def test_registry_filters_by_capability_and_disabled_state():
    registry = KernelRegistry(
        (
            KernelDescriptor("physics", ("physics",), KernelCapacity("physics", 5, 10)),
            KernelDescriptor("math", ("math",), KernelCapacity("math", 8, 10)),
            KernelDescriptor("disabled-math", ("math",), KernelCapacity("disabled-math", 9, 10), enabled=False),
        )
    )
    assert tuple(k.kernel_id for k in registry.candidates("math")) == ("math",)
    assert tuple(k.kernel_id for k in registry.candidates("physics")) == ("physics",)


def test_registry_rejects_duplicate_kernel_ids():
    try:
        KernelRegistry(
            (
                KernelDescriptor("math", ("math",), KernelCapacity("math", 1, 2)),
                KernelDescriptor("math", ("math",), KernelCapacity("math", 1, 2)),
            )
        )
    except ValueError:
        return
    raise AssertionError("duplicate kernel_id must be rejected")
