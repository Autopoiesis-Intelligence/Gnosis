from core.kernel_provisioning_contract import KernelProvisionRequest, decide_provisioning


def test_kernel_provisioning_binds_product_and_parent_identity():
    request = KernelProvisionRequest(
        "p1", "exp1", "math", 8, "core.main", "parent-hash",
        "gnozis", "product-hash",
    )
    decision = decide_provisioning(request)
    assert decision.provision is True
    assert decision.request_digest == request.digest()
    assert decision.kernel_identity_hash


def test_kernel_provisioning_requires_positive_capacity():
    try:
        KernelProvisionRequest(
            "p1", "exp1", "math", 0, "core.main", "parent-hash",
            "gnozis", "product-hash",
        )
    except ValueError:
        return
    raise AssertionError("provisioning with zero capacity must be rejected")
