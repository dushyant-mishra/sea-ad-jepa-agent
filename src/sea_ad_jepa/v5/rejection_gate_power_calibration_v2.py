"""Authority-bound wrapper for V5 rejection-gate power qualification.

V1 binds each positive control to the exact gate artifact, gate authority,
design context and checkpoint. V2 additionally gives the aggregate power
qualification its own explicit authority identity so a final bundle can verify
the parent row instead of trusting an unrelated label supplied at packaging.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .rejection_gate_power_calibration_v1 import (
    REJECTION_CAPABLE_POST_GATES,
    RejectionGatePowerAuthorityV1,
    qualify_rejection_gate_power,
)


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


@dataclass(frozen=True)
class RejectionGatePowerAuthorityV2:
    power_qualification_authority_id: str
    expected_gate_ids: tuple[str, ...]
    control_design_authority_id: str
    minimum_relevant_effect_authority_id: str
    controls_frozen_before_checkpoint_outcome: bool
    same_sampling_geometry_required: bool
    threshold_provenance: str

    def validate(self) -> None:
        _id(self.power_qualification_authority_id, "power_qualification_authority_id")
        self.as_v1().validate()

    def as_v1(self) -> RejectionGatePowerAuthorityV1:
        return RejectionGatePowerAuthorityV1(
            expected_gate_ids=self.expected_gate_ids,
            control_design_authority_id=self.control_design_authority_id,
            minimum_relevant_effect_authority_id=self.minimum_relevant_effect_authority_id,
            controls_frozen_before_checkpoint_outcome=self.controls_frozen_before_checkpoint_outcome,
            same_sampling_geometry_required=self.same_sampling_geometry_required,
            threshold_provenance=self.threshold_provenance,
        )


def qualify_rejection_gate_power_v2(
    reports_by_gate: Mapping[str, Mapping[str, object]],
    *,
    gate_evidence_by_id: Mapping[str, Mapping[str, object]],
    authority: RejectionGatePowerAuthorityV2,
    design_context_sha256: str,
    qualification_checkpoint_sha256: str,
) -> dict[str, object]:
    authority.validate()
    out = qualify_rejection_gate_power(
        reports_by_gate,
        gate_evidence_by_id=gate_evidence_by_id,
        authority=authority.as_v1(),
        design_context_sha256=design_context_sha256,
        qualification_checkpoint_sha256=qualification_checkpoint_sha256,
    )
    return {
        **out,
        "schema": "JEPA_V5_REJECTION_GATE_POWER_QUALIFICATION_V2",
        "authority_id": authority.power_qualification_authority_id,
        "canonical_rejection_gate_set": REJECTION_CAPABLE_POST_GATES,
        "training_authorized": False,
    }
