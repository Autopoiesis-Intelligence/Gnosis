from core.capacity_snapshot import CapacitySnapshot
from core.distribution_contract import KernelCapacity
from core.expansion_evidence import ExpansionEvidence
from core.kernel_registry import KernelDescriptor, KernelRegistry
from core.network_expansion_contract import decide_expansion
from core.registry_capacity_expansion import build_expansion_request


def registry():
    return KernelRegistry((
        KernelDescriptor("k1", ("math",), KernelCapacity("k1", 4, 4)),
        KernelDescriptor("k2", ("math",), KernelCapacity("k2", 3, 3)),
    ))


def test_expansion_evidence_binds_snapshot_request_and_decision():
    reg = registry()
    snapshot = CapacitySnapshot.from_registry(reg, "math")
    request = build_expansion_request(
        reg, request_id="e1", capability="math",
        workload_digest="work", required_units=10,
        capacity_snapshot_digest="ignored",
    )
    decision = decide_expansion(request)
    evidence = ExpansionEvidence.create(request, snapshot, decision)
    assert evidence.snapshot_digest == snapshot.digest
    assert evidence.request_digest == request.digest()
    assert evidence.deficit_units == 3
    assert evidence.expand is True
    assert evidence.evidence_digest


def test_expansion_evidence_rejects_stale_snapshot():
    reg = registry()
    request = build_expansion_request(
        reg, request_id="e1", capability="math",
        workload_digest="work", required_units=10,
        capacity_snapshot_digest="ignored",
    )
    decision = decide_expansion(request)
    stale = CapacitySnapshot("math", (("k1", 1, True), ("k2", 3, True)), "stale")
    try:
        ExpansionEvidence.create(request, stale, decision)
    except ValueError as exc:
        assert "snapshot" in str(exc)
        return
    raise AssertionError("stale snapshot must be rejected")
