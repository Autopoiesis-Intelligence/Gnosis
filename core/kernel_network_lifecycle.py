"""End-to-end deterministic kernel network lifecycle contract."""

from __future__ import annotations

from dataclasses import dataclass

from core.distribution_execution_binding import DistributionExecutionBinding, bind_distribution_to_execution
from core.execution_contract import ExecutionInput
from core.kernel_admission_contract import KernelAdmission, admit_kernel
from core.kernel_distribution_network import KernelDistributionNetwork
from core.kernel_execution_contract import KernelExecutionContract
from core.kernel_provisioning_contract import KernelProvisionRequest, decide_provisioning
from core.kernel_registry import KernelRegistry
from core.kernel_registry_admission import admit_into_registry
from core.network_expansion_contract import ExpansionRequest, decide_expansion


@dataclass(frozen=True)
class KernelLifecycle:
    expansion_request: ExpansionRequest
    admission: KernelAdmission
    binding: DistributionExecutionBinding


def expand_and_route(
    *,
    registry: KernelRegistry,
    expansion_request: ExpansionRequest,
    provisioning_request: KernelProvisionRequest,
    kernel_id: str,
    decision_id: str,
    workload_digest: str,
    execution_input: ExecutionInput,
) -> KernelLifecycle:
    expansion = decide_expansion(expansion_request)
    if not expansion.expand:
        raise ValueError("kernel expansion is not required")
    if provisioning_request.expansion_request_digest != expansion.request_digest:
        raise ValueError("provisioning request is not bound to expansion decision")

    provisioning = decide_provisioning(provisioning_request)
    admission = admit_kernel(provisioning_request, provisioning, kernel_id=kernel_id)
    admitted_registry = admit_into_registry(registry, admission)

    distribution = KernelDistributionNetwork(admitted_registry).route(
        decision_id=decision_id,
        capability=provisioning_request.capability,
        workload_digest=workload_digest,
    )
    contract = KernelExecutionContract(
        kernel_id=distribution.selected_kernel_id,
        capability=distribution.capability,
        distribution_decision_id=distribution.decision_id,
        execution_contract_id=decision_id,
        max_capacity=provisioning_request.required_capacity_units,
    )
    binding = bind_distribution_to_execution(distribution, contract, execution_input)
    return KernelLifecycle(expansion_request, admission, binding)
