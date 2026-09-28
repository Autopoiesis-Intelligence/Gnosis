from core.kernel_registry import KernelDescriptor
from core.distribution_contract import KernelCapacity
from core.kernel_runtime_contract import KernelRuntimeHandle, bind_runtime


def descriptor():
    return KernelDescriptor(
        "kernel.math.2", ("math",), KernelCapacity("kernel.math.2", 8, 8), True,
        "gnozis", "product-hash", "core.main", "parent-hash",
        "identity-hash", "provision-digest",
    )


def test_runtime_binding_requires_matching_provenance():
    d = descriptor()
    bind_runtime(d, KernelRuntimeHandle("kernel.math.2", "runtime-1", "product-hash", "identity-hash"))


def test_runtime_binding_rejects_wrong_kernel():
    d = descriptor()
    try:
        bind_runtime(d, KernelRuntimeHandle("kernel.math.other", "runtime-1", "product-hash", "identity-hash"))
    except ValueError as exc:
        assert "kernel identity" in str(exc)
        return
    raise AssertionError("wrong runtime kernel must be rejected")
