"""Fail-closed V5 QC qualification authority.

Cross-cell technical association is warning-only. Production QC closure requires
independently frozen invalid-observation rules, causal same-cell measurement
qualification, held-out biology, and donor-level recurrence. No numeric threshold
is defined here and this module never grants training authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


_ALLOWED_THRESHOLD_PROVENANCE = frozenset({
    "PROSPECTIVE_PREMODEL",
    "INDEPENDENT_CALIBRATION",
})


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty authority ID")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _exact_schema(report: Mapping[str, object], expected: str, name: str) -> None:
    if report.get("schema") != expected:
        raise ValueError(f"{name} has unexpected schema")


def _bind(report: Mapping[str, object], expected_id: str, name: str) -> None:
    if report.get("authority_id") != expected_id:
        raise ValueError(f"{name} authority binding mismatch")


@dataclass(frozen=True)
class QCQualificationAuthorityV1:
    valid_observation_authority_id: str
    association_diagnostic_authority_id: str
    same_cell_intervention_authority_id: str
    same_cell_threshold_authority_id: str
    heldout_biology_authority_id: str
    donor_recurrence_authority_id: str
    thresholds_frozen_before_candidate_model_outcome: bool
    threshold_provenance: str
    association_has_rejection_authority: bool
    blind_qc_residualization_enabled: bool

    def validate(self) -> None:
        for field in (
            "valid_observation_authority_id",
            "association_diagnostic_authority_id",
            "same_cell_intervention_authority_id",
            "same_cell_threshold_authority_id",
            "heldout_biology_authority_id",
            "donor_recurrence_authority_id",
        ):
            _id(getattr(self, field), field)
        if self.thresholds_frozen_before_candidate_model_outcome is not True:
            raise ValueError("QC thresholds must be frozen before candidate-model outcome")
        if self.threshold_provenance not in _ALLOWED_THRESHOLD_PROVENANCE:
            raise ValueError("QC threshold provenance must be prospective or independently calibrated")
        if self.association_has_rejection_authority is not False:
            raise ValueError("cross-cell QC association must be warning-only")
        if self.blind_qc_residualization_enabled is not False:
            raise ValueError("blind QC residualization is forbidden")


def qualify_v5_qc_pretraining(
    *,
    valid_observation_report: Mapping[str, object],
    association_report: Mapping[str, object],
    same_cell_report: Mapping[str, object],
    heldout_biology_report: Mapping[str, object],
    donor_recurrence_report: Mapping[str, object],
    authority: QCQualificationAuthorityV1,
) -> dict[str, object]:
    """Close the V5 QC pretraining gate without granting training authority."""
    authority.validate()
    valid = _mapping(valid_observation_report, "valid_observation_report")
    assoc = _mapping(association_report, "association_report")
    same = _mapping(same_cell_report, "same_cell_report")
    hold = _mapping(heldout_biology_report, "heldout_biology_report")
    donor = _mapping(donor_recurrence_report, "donor_recurrence_report")

    _exact_schema(valid, "JEPA_V5_VALID_OBSERVATION_QC_V1", "valid_observation_report")
    _exact_schema(assoc, "JEPA_V5_QC_ASSOCIATION_DIAGNOSTIC_V1", "association_report")
    _exact_schema(same, "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V1", "same_cell_report")
    _exact_schema(hold, "JEPA_V5_HELDOUT_BIOLOGY_QUALIFICATION_V1", "heldout_biology_report")
    _exact_schema(donor, "JEPA_V5_DONOR_RECURRENCE_QUALIFICATION_V1", "donor_recurrence_report")

    _bind(valid, authority.valid_observation_authority_id, "valid_observation_report")
    _bind(assoc, authority.association_diagnostic_authority_id, "association_report")
    _bind(same, authority.same_cell_intervention_authority_id, "same_cell_report")
    _bind(hold, authority.heldout_biology_authority_id, "heldout_biology_report")
    _bind(donor, authority.donor_recurrence_authority_id, "donor_recurrence_report")

    if valid.get("exclusions_only_from_frozen_invalidity_rules") is not True:
        raise RuntimeError("STOP_V5_QC_INVALID_OBSERVATION_AUTHORITY")
    if valid.get("passed") is not True:
        raise RuntimeError("STOP_V5_QC_INVALID_OBSERVATION_FAILURE")

    # Association can be arbitrarily strong. It remains diagnostic only.
    if assoc.get("warning_only") is not True or assoc.get("rejection_authority") is not False:
        raise RuntimeError("STOP_V5_QC_ASSOCIATION_ESCALATED_TO_REJECTION")

    if same.get("threshold_authority_id") != authority.same_cell_threshold_authority_id:
        raise ValueError("same-cell threshold authority binding mismatch")
    if same.get("passed") is not True:
        raise RuntimeError("STOP_V5_QC_SAME_CELL_MEASUREMENT_FAILURE")

    overlap = hold.get("selection_feature_overlap")
    if isinstance(overlap, bool) or not isinstance(overlap, int) or overlap != 0:
        raise RuntimeError("STOP_V5_QC_HELDOUT_BIOLOGY_NOT_INDEPENDENT")
    if hold.get("passed") is not True:
        raise RuntimeError("STOP_V5_QC_HELDOUT_BIOLOGY_FAILURE")

    if donor.get("biological_replicate_unit") != "DONOR":
        raise RuntimeError("STOP_V5_QC_DONOR_RECURRENCE_UNIT_INVALID")
    if donor.get("cells_treated_as_independent_replicates") is not False:
        raise RuntimeError("STOP_V5_QC_PSEUDOREPLICATION")
    if donor.get("passed") is not True:
        raise RuntimeError("STOP_V5_QC_DONOR_RECURRENCE_FAILURE")

    return {
        "schema": "JEPA_V5_QC_PRETRAINING_CLOSURE_V1",
        "qc_pretraining_closed": True,
        "association_warning_only": True,
        "same_cell_measurement_qualified": True,
        "heldout_biology_qualified": True,
        "donor_recurrence_qualified": True,
        "threshold_provenance": authority.threshold_provenance,
        "training_authorized": False,
    }
