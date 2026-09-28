from core.distribution_contract import KernelCapacity
from core.in_memory_kernel_runtime import InMemoryKernelRuntimeAdapter
from core.kernel_registry import KernelDescriptor


def descriptor():
    return KernelDescriptor(
        "kernel.math.2", ("math",), KernelCapacity("kernel.math.2", 8, 8), True,
        "gnozis", "product-hash", "core.main", "parent-hash",
        "identity-hash", "provision-digest",
    )


def test_runtime_provision_status_and_terminate():
    adapter = InMemoryKernelRuntimeAdapter()
    handle = adapter.provision(descriptor())
    status = adapter.status(handle)
    assert status.healthy is True
    assert status.kernel_id == "kernel.math.2"
    adapter.terminate(handle)


def test_runtime_rejects_duplicate_provisioning():
    adapter = InMemoryKernelRuntimeAdapter()
    d = descriptor()
    adapter.provision(d)
    try:
        adapter.provision(d)
    except ValueError as exc:
        assert "already provisioned" in str(exc)
        return
    raise AssertionError("duplicate runtime provisioning must be rejected")
