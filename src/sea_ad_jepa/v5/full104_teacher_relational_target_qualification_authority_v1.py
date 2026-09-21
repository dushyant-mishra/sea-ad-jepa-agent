"""Prospective FULL104 learned-teacher relational target qualification authority V1.

This authority carries forward the strongest surviving target-discovery evidence:
TD56/TD57A/TD57B/TD58/TD59. It does not select a new molecular target. Instead,
it defines what a learned EMA teacher must preserve before its direct cell_state
can be treated as a biologically qualified JEPA target.

The authority is ETL-aware:
- scientific mass is donor-uniform, cell-uniform within donor;
- source is a robustness stratum, not automatic objective mass;
- HVS, NPH52 and SEA_AD must be reported separately so SEA_AD's cell-count
  dominance cannot hide a source failure;
- native-class, disease and rare-state labels are forbidden as target labels;
- rare biology is protected through donor recurrence / preservation diagnostics,
  not supervised target construction.

This module is prospective only and cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


FULL104_READER_FIT_CELLS = 4_553_407
FULL104_READER_FIT_DONORS = 104
FULL104_OPERATORS = 42
FULL104_SOURCE_DONORS = (("HVS", 41), ("NPH52", 17), ("SEA_AD", 46))

APPROVED_STATE_SEMANTICS_IDS: Tuple[str, ...] = (
    "BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
)
APPROVED_TEACHER_STATE_IDS: Tuple[str, ...] = (
    "EMA_DIRECT_CELL_STATE__NO_PROJECTION_HEAD_V1",
)
APPROVED_PRIMARY_WEIGHTING_IDS: Tuple[str, ...] = (
    "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1",
)
APPROVED_SOURCE_POLICY_IDS: Tuple[str, ...] = (
    "SOURCE_IS_ROBUSTNESS_STRATUM__ALL_THREE_SOURCES_REPORTED_SEPARATELY_V1",
)
APPROVED_RELATIONAL_POLICY_IDS: Tuple[str, ...] = (
    "TD57B_GLOBAL_PLUS_TD59_NEAREST_HALF_MESOSCALE__NO_NEW_SEARCH_V1",
)
APPROVED_RARE_BIOLOGY_POLICY_IDS: Tuple[str, ...] = (
    "RARE_BIOLOGY_PROTECTED_BY_DONOR_RECURRENCE__NO_RARE_LABEL_TARGET_V1",
)
APPROVED_LABEL_FIREWALL_IDS: Tuple[str, ...] = (
    "NO_PATHOLOGY_DISEASE_NATIVE_CLASS_OR_RARE_STATE_LABEL_IN_TARGET_CONSTRUCTION_V1",
)
APPROVED_LOCALITY_POLICY_IDS: Tuple[str, ...] = (
    "TD59_NEAREST_HALF_ONLY__TD57C_NEAREST_THIRD_REMAINS_FAILED_V1",
)
APPROVED_PROMOTION_POLICY_IDS: Tuple[str, ...] = (
    "RELATIONAL_CONTINUITY_REQUIRED_BEFORE_TEACHER_CELL_STATE_TARGET_AUTHORITY_V1",
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
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Full104TeacherRelationalTargetQualificationAuthorityV1:
    authority_id: str

    # Current scientific/data roots.
    full104_population_authority_sha256: str
    canonical_address_registry_sha256: str
    operator_address_support_authority_sha256: str
    dataset_etl_atlas_sha256: str
    scientific_weight_law_sha256: str
    teacher_target_semantics_authority_sha256: str

    # Historical qualified relational roots.
    td57b_protocol_sha256: str
    td59_protocol_sha256: str
    td60_legacy_prospective_protocol_sha256: str

    state_semantics_id: str
    teacher_state_id: str
    primary_weighting_id: str
    source_policy_id: str
    relational_policy_id: str
    rare_biology_policy_id: str
    label_firewall_id: str
    locality_policy_id: str
    promotion_policy_id: str

    reader_fit_cells: int = FULL104_READER_FIT_CELLS
    reader_fit_donors: int = FULL104_READER_FIT_DONORS
    operators: int = FULL104_OPERATORS
    source_donors: Tuple[Tuple[str, int], ...] = FULL104_SOURCE_DONORS

    pathology_labels_allowed_in_target: bool = False
    disease_labels_allowed_in_target: bool = False
    native_class_labels_allowed_in_target: bool = False
    rare_state_labels_allowed_in_target: bool = False

    new_gene_panel_search_allowed: bool = False
    new_locality_search_allowed: bool = False
    cell_uniform_population_weighting_allowed: bool = False
    source_cell_mass_weighting_allowed: bool = False

    relational_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        for name in (
            "full104_population_authority_sha256",
            "canonical_address_registry_sha256",
            "operator_address_support_authority_sha256",
            "dataset_etl_atlas_sha256",
            "scientific_weight_law_sha256",
            "teacher_target_semantics_authority_sha256",
            "td57b_protocol_sha256",
            "td59_protocol_sha256",
            "td60_legacy_prospective_protocol_sha256",
        ):
            _sha(getattr(self, name), name)

        _enum(self.state_semantics_id, APPROVED_STATE_SEMANTICS_IDS, "state_semantics_id")
        _enum(self.teacher_state_id, APPROVED_TEACHER_STATE_IDS, "teacher_state_id")
        _enum(
            self.primary_weighting_id,
            APPROVED_PRIMARY_WEIGHTING_IDS,
            "primary_weighting_id",
        )
        _enum(self.source_policy_id, APPROVED_SOURCE_POLICY_IDS, "source_policy_id")
        _enum(
            self.relational_policy_id,
            APPROVED_RELATIONAL_POLICY_IDS,
            "relational_policy_id",
        )
        _enum(
            self.rare_biology_policy_id,
            APPROVED_RARE_BIOLOGY_POLICY_IDS,
            "rare_biology_policy_id",
        )
        _enum(self.label_firewall_id, APPROVED_LABEL_FIREWALL_IDS, "label_firewall_id")
        _enum(self.locality_policy_id, APPROVED_LOCALITY_POLICY_IDS, "locality_policy_id")
        _enum(
            self.promotion_policy_id,
            APPROVED_PROMOTION_POLICY_IDS,
            "promotion_policy_id",
        )

        if self.reader_fit_cells != FULL104_READER_FIT_CELLS:
            raise ValueError("reader_fit_cells drifted from authenticated FULL104 geometry")
        if self.reader_fit_donors != FULL104_READER_FIT_DONORS:
            raise ValueError("reader_fit_donors drifted from authenticated FULL104 geometry")
        if self.operators != FULL104_OPERATORS:
            raise ValueError("operators drifted from authenticated FULL104 geometry")
        if tuple(self.source_donors) != FULL104_SOURCE_DONORS:
            raise ValueError("source donor geometry drifted from authenticated FULL104 geometry")

        for name in (
            "pathology_labels_allowed_in_target",
            "disease_labels_allowed_in_target",
            "native_class_labels_allowed_in_target",
            "rare_state_labels_allowed_in_target",
            "new_gene_panel_search_allowed",
            "new_locality_search_allowed",
            "cell_uniform_population_weighting_allowed",
            "source_cell_mass_weighting_allowed",
            "relational_outcomes_inspected_before_freeze",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_FULL104_TEACHER_RELATIONAL_TARGET_QUALIFICATION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )


def require_source_complete_relational_gate_v1(
    results_by_source: Mapping[str, bool],
) -> None:
    """Fail closed unless all three sources are present and pass separately."""
    expected = {name for name, _ in FULL104_SOURCE_DONORS}
    observed = set(results_by_source)
    if observed != expected:
        raise ValueError(
            f"source-complete gate requires exactly {sorted(expected)!r}; "
            f"observed {sorted(observed)!r}"
        )
    failed = sorted(name for name, passed in results_by_source.items() if passed is not True)
    if failed:
        raise ValueError(f"relational continuity failed or was not estimable for {failed!r}")
