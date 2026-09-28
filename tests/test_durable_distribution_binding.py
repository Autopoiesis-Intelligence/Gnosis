from core.distribution_execution_binding import DistributionExecutionBinding
from core.durable_distribution_binding import DurableDistributionBinding


def test_durable_distribution_binding_round_trip():
    binding = DistributionExecutionBinding("d1", "digest-1", "kernel.math.1", "exec-1")
    durable = DurableDistributionBinding(3, binding)
    restored = DurableDistributionBinding.from_row(durable.row())
    assert restored == durable


def test_durable_distribution_binding_rejects_negative_sequence():
    binding = DistributionExecutionBinding("d1", "digest-1", "kernel.math.1", "exec-1")
    try:
        DurableDistributionBinding(-1, binding)
    except ValueError:
        return
    raise AssertionError("negative sequence must be rejected")
