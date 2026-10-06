from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any

from .canonical import canonical_digest


APPROVED_V3_GOVERNANCE_DIGEST = "ab0603b0a9c92c3680badc252205ddd27fa74ae83ef3ada4019b4dcf637b7611"
APPROVED_REPRESENTATION_FAMILIES = {
    "GLOBAL_CELL_STATE",
    "QUERY_LOCAL_STATE",
    "PROGRAM_STATE",
    "STRUCTURED_COMBINED_STATE",
}
APPROVED_ESTIMAND_CANDIDATES = {
    "UNSET_REQUIRES_APPROVAL",
    "CELL_WEIGHTED_EMPIRICAL",
    "DONOR_WEIGHTED",
    "SOURCE_BALANCED_DONOR_WEIGHTED",
    "HIERARCHICAL_TEMPERED",
}


class ExecutionMode(str, Enum):
    ZERO_UPDATE_QUALIFICATION = "ZERO_UPDATE_QUALIFICATION"
    BOUNDED_MUTATION_REHEARSAL = "BOUNDED_MUTATION_REHEARSAL"


class ThresholdStatus(str, Enum):
    UNSET_REQUIRES_APPROVAL = "UNSET_REQUIRES_APPROVAL"
    EXPLORATORY_ONLY = "EXPLORATORY_ONLY"
    FROZEN_DECIDING = "FROZEN_DECIDING"


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an explicit nonempty string")
    return value


@dataclass(frozen=True)
class QualificationProtocolV1:
    governance_digest: str
    qualification_contract_version: str
    runtime_interface_version: str
    representation_family: str
    target_evidence_construction_id: str
    q_safety_policy_id: str
    observation_operator_policy_id: str
    biological_evidence_operator_id: str
    measurement_depth_operator_id: str
    split_resampling_protocol_id: str
    representation_stability_protocol_id: str
    transport_ood_axes: tuple[str, ...]
    diagnostic_readout_firewall_id: str
    unit_of_inference: str
    estimand_spec: str
    threshold_status: ThresholdStatus
    deciding_numeric_thresholds: Any
    exploratory_thresholds: tuple[tuple[str, float], ...]
    execution_mode: ExecutionMode
    claim_ceiling: str

    def validate(self) -> None:
        if self.governance_digest != APPROVED_V3_GOVERNANCE_DIGEST:
            raise ValueError("governance digest does not match the approved V3 state")
        for name in (
            "qualification_contract_version",
            "runtime_interface_version",
            "target_evidence_construction_id",
            "q_safety_policy_id",
            "observation_operator_policy_id",
            "biological_evidence_operator_id",
            "measurement_depth_operator_id",
            "split_resampling_protocol_id",
            "representation_stability_protocol_id",
            "diagnostic_readout_firewall_id",
            "unit_of_inference",
            "claim_ceiling",
        ):
            _nonempty(getattr(self, name), name)
        if self.representation_family not in APPROVED_REPRESENTATION_FAMILIES:
            raise ValueError("representation family is not approved by V3 governance")
        if self.estimand_spec not in APPROVED_ESTIMAND_CANDIDATES:
            raise ValueError("estimand_spec is not an approved candidate or explicit UNSET")
        if not isinstance(self.execution_mode, ExecutionMode):
            raise ValueError("execution_mode must be explicit")
        if not isinstance(self.threshold_status, ThresholdStatus):
            raise ValueError("threshold status must be explicit")
        if not isinstance(self.transport_ood_axes, tuple) or not self.transport_ood_axes:
            raise ValueError("transport_ood_axes must be an explicit nonempty tuple")
        if not all(isinstance(axis, str) and axis for axis in self.transport_ood_axes):
            raise ValueError("transport_ood_axes entries must be nonempty strings")
        if not isinstance(self.exploratory_thresholds, tuple):
            raise ValueError("exploratory thresholds must be an explicit tuple")
        for item in self.exploratory_thresholds:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or isinstance(item[1], bool)
                or not isinstance(item[1], (int, float))
                or not math.isfinite(float(item[1]))
            ):
                raise ValueError("exploratory thresholds must contain finite named numeric values")

        unset = self.deciding_numeric_thresholds == "UNSET_REQUIRES_APPROVAL"
        if self.threshold_status is ThresholdStatus.UNSET_REQUIRES_APPROVAL:
            if not unset:
                raise ValueError("threshold status is UNSET but deciding thresholds were supplied")
            if self.exploratory_thresholds:
                raise ValueError("threshold status is UNSET but exploratory thresholds were supplied")
        elif self.threshold_status is ThresholdStatus.EXPLORATORY_ONLY:
            if not unset:
                raise ValueError("exploratory thresholds cannot populate deciding threshold state")
        elif self.threshold_status is ThresholdStatus.FROZEN_DECIDING:
            if unset:
                raise ValueError("FROZEN_DECIDING requires explicit deciding thresholds")

        if self.claim_ceiling != "RNA_REPRESENTATION":
            raise ValueError("claim ceiling exceeds current Stage-A governance")

    def digest(self) -> str:
        self.validate()
        return canonical_digest(self)
