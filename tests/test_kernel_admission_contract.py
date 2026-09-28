from core.kernel_admission_contract import admit_kernel
from core.kernel_provisioning_contract import KernelProvisionRequest, decide_provisioning


def test_kernel_admission_requires_matching_provenance():
    request = KernelProvisionRequest("p1", "exp1", "math", 8, "core.main", "parent-hash", "gnozis", "product-hash")
    decision = decide_provisioning(request)
    admission = admit_kernel(request, decision, kernel_id="kernel.math.2")
    assert admission.kernel_id == "kernel.math.2"
    assert admission.product_hash == "product-hash"
    assert admission.parent_core_hash == "parent-hash"
    assert admission.kernel_identity_hash == decision.kernel_identity_hash


def test_kernel_admission_rejects_tampered_request_digest():
    request = KernelProvisionRequest("p1", "exp1", "math", 8, "core.main", "parent-hash", "gnozis", "product-hash")
    decision = decide_provisioning(request)
    try:
        admit_kernel(
            KernelProvisionRequest("p1", "tampered", "math", 8, "core.main", "parent-hash", "gnozis", "product-hash"),
            decision,
            kernel_id="kernel.math.2",
        )
    except ValueError as exc:
        assert "digest" in str(exc)
        return
    raise AssertionError("tampered provisioning request must be rejected")
