from core.execution_contract import ExecutionInput
from core.kernel_network_lifecycle import expand_and_route
from core.kernel_provisioning_contract import KernelProvisionRequest
from core.kernel_registry import KernelRegistry
from core.network_expansion_contract import ExpansionRequest


def test_full_kernel_network_lifecycle():
    expansion = ExpansionRequest("e1", "math", "work", 8, 0, "snapshot")
    provisioning = KernelProvisionRequest(
        "p1", expansion.digest(), "math", 8,
        "core.main", "parent-hash", "gnozis", "product-hash",
    )
    lifecycle = expand_and_route(
        registry=KernelRegistry(()),
        expansion_request=expansion,
        provisioning_request=provisioning,
        kernel_id="kernel.math.2",
        decision_id="d1",
        workload_digest="work",
        execution_input=ExecutionInput("test", "s1", "sd1", "cd1"),
    )
    assert lifecycle.expansion_evidence.expand is True
    assert lifecycle.expansion_evidence.request_digest == lifecycle.expansion_request.digest()
    assert lifecycle.expansion_evidence.snapshot_digest
    assert lifecycle.admission.kernel_id == "kernel.math.2"
    assert lifecycle.binding.kernel_id == "kernel.math.2"


def test_lifecycle_rejects_stale_expansion_request():
    from core.capacity_snapshot import CapacitySnapshot
    from core.expansion_evidence import ExpansionEvidence
    from core.network_expansion_contract import decide_expansion
    request = ExpansionRequest("e1", "math", "work", 8, 0, "stale")
    decision = decide_expansion(request)
    snapshot = CapacitySnapshot("math", (), "fresh")
    try:
        ExpansionEvidence.create(request, snapshot, decision)
    except ValueError as exc:
        assert "snapshot" in str(exc)
        return
    raise AssertionError("stale expansion request must be rejected")
