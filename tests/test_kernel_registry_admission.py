from core.kernel_admission_contract import admit_kernel
from core.kernel_provisioning_contract import KernelProvisionRequest, decide_provisioning
from core.kernel_registry import KernelRegistry
from core.kernel_registry_admission import admit_into_registry


def _admission():
    request = KernelProvisionRequest("p1", "exp1", "math", 8, "core.main", "parent-hash", "gnozis", "product-hash")
    return admit_kernel(request, decide_provisioning(request), kernel_id="kernel.math.2")


def test_admitted_kernel_becomes_routable():
    registry = KernelRegistry(())
    registry = admit_into_registry(registry, _admission())
    assert registry.candidates("math")[0].kernel_id == "kernel.math.2"


def test_duplicate_kernel_admission_is_rejected():
    registry = KernelRegistry(())
    admission = _admission()
    registry = admit_into_registry(registry, admission)
    try:
        admit_into_registry(registry, admission)
    except ValueError as exc:
        assert "already admitted" in str(exc)
        return
    raise AssertionError("duplicate kernel admission must be rejected")


def test_registry_descriptor_retains_kernel_provenance():
    kernel = _admission()
    registry = admit_into_registry(KernelRegistry(()), kernel)
    descriptor = registry.candidates("math")[0]
    assert descriptor.product_id == kernel.product_id
    assert descriptor.product_hash == kernel.product_hash
    assert descriptor.parent_core_hash == kernel.parent_core_hash
    assert descriptor.kernel_identity_hash == kernel.kernel_identity_hash
