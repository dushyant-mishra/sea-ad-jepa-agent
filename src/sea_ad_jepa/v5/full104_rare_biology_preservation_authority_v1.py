"""Prospective FULL104 label-free rare-biology preservation authority V1.

This authority does NOT define a disease/rare-cell target. It defines a lawful
way to ask whether donor-recurrent molecularly isolated tail cells are preserved.

The tail is selected without pathology or cell-type labels:
- reuse TD59's independent Z-view nearest-half locality;
- define per-anchor isolation by the Z nearest-half boundary distance;
- select the top q95 isolation tail within donor×operator strata;
- select q95 within donor×operator strata, then require at least 5 tail anchors
  per donor after pooling strata. The minimum is NOT applied per operator, so
  small operators/classes do not receive artificial scientific mass.

Before any learned-teacher rare-tail claim, the same tail construction must first
earn molecular X/Y recurrence on FULL104. Teacher evaluation is forbidden until
that molecular prequalification is frozen.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


TAIL_QUANTILE = 0.95
MIN_TAIL_ANCHORS = 5
MIN_RESOLVED_TRIPLETS_PER_DONOR = 20
MIN_MEASURABLE_DONORS_PER_HALF = 4
NULL_REPLICATES = 64

APPROVED_SELECTOR_IDS: Tuple[str, ...] = (
    "TD59_Z_NEAREST_HALF_BOUNDARY_DISTANCE_V1",
)
APPROVED_STRATIFICATION_IDS: Tuple[str, ...] = (
    "WITHIN_DONOR_OPERATOR__OPERATOR_DOES_NOT_SET_OBJECTIVE_MASS_V1",
)
APPROVED_TAIL_IDS: Tuple[str, ...] = (
    "Q95_ISOLATION_TAIL__MIN5_ANCHORS_PER_DONOR_V1",
)
APPROVED_MOLECULAR_GATE_IDS: Tuple[str, ...] = (
    "FULL104_XY_RELATIONAL_RECURRENCE_REQUIRED_BEFORE_TEACHER_TAIL_CLAIM_V1",
)
APPROVED_NULL_IDS: Tuple[str, ...] = (
    "TD59_MATCHED_WRONG_CELL_Y_NULL__64_REPLICATES_V1",
)
APPROVED_WEIGHTING_IDS: Tuple[str, ...] = (
    "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1",
)
APPROVED_EVALUATION_PARTITION_IDS: Tuple[str, ...] = (
    "AUTHENTICATED_FULL104_SOURCE_STRATIFIED_FOUR_FOLD_V1",
)
APPROVED_LABEL_FIREWALL_IDS: Tuple[str, ...] = (
    "NO_PATHOLOGY_DISEASE_NATIVE_CLASS_OR_RARE_STATE_LABEL_IN_TAIL_SELECTION_V1",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Full104RareBiologyPreservationAuthorityV1:
    authority_id: str
    full104_population_authority_sha256: str
    dataset_etl_atlas_sha256: str
    td59_protocol_sha256: str
    teacher_relational_target_authority_sha256: str
    outer_split_receipt_sha256: str
    qualification_sample_authority_sha256: str

    selector_id: str
    stratification_id: str
    tail_id: str
    molecular_gate_id: str
    null_id: str
    primary_weighting_id: str
    evaluation_partition_id: str
    label_firewall_id: str

    tail_quantile: float = TAIL_QUANTILE
    min_tail_anchors: int = MIN_TAIL_ANCHORS
    min_resolved_triplets_per_donor: int = MIN_RESOLVED_TRIPLETS_PER_DONOR
    min_measurable_donors_per_half: int = MIN_MEASURABLE_DONORS_PER_HALF
    null_replicates: int = NULL_REPLICATES

    pathology_labels_used: bool = False
    disease_labels_used: bool = False
    native_class_labels_used: bool = False
    rare_state_labels_used: bool = False

    molecular_prequalification_complete: bool = False
    teacher_tail_evaluation_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name in (
            "full104_population_authority_sha256",
            "dataset_etl_atlas_sha256",
            "td59_protocol_sha256",
            "teacher_relational_target_authority_sha256",
            "outer_split_receipt_sha256",
            "qualification_sample_authority_sha256",
        ):
            _sha(getattr(self, name), name)

        _enum(self.selector_id, APPROVED_SELECTOR_IDS, "selector_id")
        _enum(self.stratification_id, APPROVED_STRATIFICATION_IDS, "stratification_id")
        _enum(self.tail_id, APPROVED_TAIL_IDS, "tail_id")
        _enum(self.molecular_gate_id, APPROVED_MOLECULAR_GATE_IDS, "molecular_gate_id")
        _enum(self.null_id, APPROVED_NULL_IDS, "null_id")
        _enum(self.primary_weighting_id, APPROVED_WEIGHTING_IDS, "primary_weighting_id")
        _enum(
            self.evaluation_partition_id,
            APPROVED_EVALUATION_PARTITION_IDS,
            "evaluation_partition_id",
        )
        _enum(self.label_firewall_id, APPROVED_LABEL_FIREWALL_IDS, "label_firewall_id")

        if self.tail_quantile != TAIL_QUANTILE:
            raise ValueError("tail_quantile is frozen at q95")
        if self.min_tail_anchors != MIN_TAIL_ANCHORS:
            raise ValueError("min_tail_anchors is frozen at 5")
        if self.min_resolved_triplets_per_donor != MIN_RESOLVED_TRIPLETS_PER_DONOR:
            raise ValueError("min_resolved_triplets_per_donor drifted")
        if self.min_measurable_donors_per_half != MIN_MEASURABLE_DONORS_PER_HALF:
            raise ValueError("min_measurable_donors_per_half drifted")
        if self.null_replicates != NULL_REPLICATES:
            raise ValueError("null_replicates drifted")

        for name in (
            "pathology_labels_used",
            "disease_labels_used",
            "native_class_labels_used",
            "rare_state_labels_used",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

        # V1 is intentionally pre-molecular-outcome. Promotion happens only through
        # a successor authority after the FULL104 molecular gate is frozen and passes.
        if self.molecular_prequalification_complete is not False:
            raise ValueError("V1 cannot self-declare molecular prequalification complete")
        if self.teacher_tail_evaluation_authorized is not False:
            raise ValueError("teacher tail evaluation is forbidden in V1")
        if self.training_authorized is not False:
            raise ValueError("rare-biology preservation authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_FULL104_RARE_BIOLOGY_PRESERVATION_AUTHORITY_V1",
                **asdict(self),
                "teacher_tail_evaluation_authorized": False,
                "training_authorized": False,
            }
        )
