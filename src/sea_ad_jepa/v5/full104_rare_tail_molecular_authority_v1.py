"""Prospective FULL104 rare-tail molecular prequalification authority V1.

Frozen AFTER the metadata-only structural preflight passed and BEFORE any
rare-tail Z/X/Y molecular outcome is opened.

This authority adapts the already-frozen TD59 molecular mechanics to the current
105,553-cell FULL104 qualification sample:
- two completely fixed TD59 Z/X/Y panels;
- Z nearest-half locality;
- q95 isolation tail within donor x operator;
- >=256 informative pair coordinates;
- <=64 sampled local triplets per donor x operator;
- >=20 resolved observed X/Y triplets per donor;
- 64 matched wrong-cell Y nulls;
- current authenticated source-stratified four-fold donor partition;
- all 2 x 3 x 4 = 24 panel/source/fold cases must pass.

It authorizes only the molecular prequalification run. It cannot authorize
teacher-tail claims, TD60, pathology, or training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

STRUCTURAL_PREFLIGHT_SHA256 = (
    "f0d71c9b2f25d31a0b277b9a55f2a31f44d9084b924c3c14c67ef0c4c4a4bc89"
)
STRUCTURAL_PREFLIGHT_SOURCE_SHA = (
    "5503cd8c99506d172616b1e2edd8090eeaa41a05"
)
STRUCTURAL_TERMINAL = "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN"
SAMPLE_RECEIPT_SHA256 = (
    "7220654284fe07c1abcf97a77d818700b46e3fe577fca4fd5bc4b99df6a4d6f6"
)
FULL104_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
OUTER_SPLIT_RECEIPT_SHA256 = (
    "5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4"
)

PAIR_COUNT_PER_VIEW = 2048
MIN_INFORMATIVE_PAIR_COORDINATES = 256
LOCALITY_NUMERATOR = 1
LOCALITY_DENOMINATOR = 2
TAIL_NUMERATOR = 1
TAIL_DENOMINATOR = 20
MIN_TAIL_ANCHORS_PER_DONOR = 5
TRIPLETS_PER_STRATUM_CAP = 64
MIN_RESOLVED_TRIPLETS_PER_DONOR = 20
NULL_REPLICATES = 64
NULL_P95_SORTED_INDEX = 60
MIN_MEASURABLE_DONORS_PER_CASE = 4
PANELS = 2
SOURCES = 3
FOLDS = 4
REQUIRED_CASES = PANELS * SOURCES * FOLDS

PANEL_VIEW_RANK_SLICES = {
    0: {
        "Z": (6144, 6656),
        "X": (6656, 7168),
        "Y": (7168, 7680),
    },
    1: {
        "Z": (7680, 8192),
        "X": (8192, 8704),
        "Y": (8704, 9216),
    },
}
PANEL_GENE_SHA256 = {
    0: {
        "Z": "f09455c4f5c120785608eda0c870bb299951814e895bbb7ff9d4dcf94b5680b2",
        "X": "a365be9aa9ccfc80adddfeb080f8fc6b0c0bc515554bace7076b5cf31a990ae5",
        "Y": "124246edc85f082477fb354f6f20c09752a08a1e079c509a6f94648658b31bd3",
    },
    1: {
        "Z": "2e1b171e833e248c9107b3f619df66f8ea33677bec7832aad58c6885ba4ae7be",
        "X": "8ef683be715f471f2a0f95531183416d75613eac43c745aa0ab10c7b59db6fa5",
        "Y": "e3dc6ad8c685155458c978d7c5127f26536098a88a10a5d87a6ac127b1689959",
    },
}
PANEL_PAIR_ADDRESS_SHA256 = {
    0: {
        "Z": "806553cdacc4d1e3214a2d61880b8795ca4a0637f3762280750cfb502dcd36ed",
        "X": "5d9f539d723117bffebfbcd57feefb9b880c50bc4c0aaab55dc9c9f9411a99fd",
        "Y": "eb6182759465df0e719bc793781ce0964e9a766761508ebe7bb192eda05defad",
    },
    1: {
        "Z": "960741f9b74118e8991cb859e3f044176afa8151eed3dace3f7b98102198db84",
        "X": "d28d1bd09181bbfd24ca3d737a95a6d911ace6906a5e94d6bbdf133bbc33e0da",
        "Y": "bc81c334afdcf169a0e4636ec5f76da51e248b4ac35821e26b2a71b8dbe4599f",
    },
}

GENE_RANK_NAMESPACE = "TD56S|gene|<address>"
PAIR_RANK_NAMESPACE = "TD59|panel|P|view|V|g0|min|g1|max"
TRIPLET_SAMPLE_NAMESPACE = (
    "V5_FULL104_RARE_TAIL|triplet|panel|P|source|S|fold|F|"
    "donor|D|operator|O|counter|C"
)
NULL_NAMESPACE = (
    "V5_FULL104_RARE_TAIL|null|panel|P|q|Q|source|S|fold|F|"
    "donor|D|operator|O|block|B"
)

TAIL_SELECTOR_ID = "Q95_FINITE_Z_NEAREST_HALF_BOUNDARY_ISOLATION_V1"
TAIL_TIEBREAK_ID = "ISOLATION_DESC__SELECTION_ROW_ASC_V1"
DISTANCE_ID = "TD59_PAIR_SIGN_CONCORDANCE_DISTANCE__MIN256_INFORMATIVE_V1"
TRIPLET_ID = "Z_LOCALITY_FIXED__X_BASE_RELATION__Y_TESTED_RELATION_V1"
NULL_ID = "MATCHED_WRONG_CELL_Y_ONLY__64_NONZERO_CYCLIC_SHIFTS_V1"
NULL_BLOCK_ID = "TD59_DONOR_OPERATOR_DEPTH_DETECTION_MATCHING_BLOCKS_V1"
CASE_ID = "PANEL_X_SOURCE_X_AUTHENTICATED_FOLD__24_CASES_V1"
PASS_RULE_ID = "OBSERVED_MEDIAN_DONOR_GT_HALF_AND_GT_NULL_P95__ALL24_V1"
PASS_TERMINAL = (
    "FULL104_LABEL_FREE_Q95_MOLECULAR_ISOLATION_TAIL_RELATIONAL_RECURRENCE_SURVIVES"
)
FAIL_TERMINAL = (
    "FULL104_LABEL_FREE_Q95_RARE_TAIL_MOLECULAR_PREQUALIFICATION_FAIL"
)
NOT_ESTIMABLE_TERMINAL = (
    "FULL104_LABEL_FREE_Q95_RARE_TAIL_MOLECULAR_PREQUALIFICATION_NOT_ESTIMABLE"
)


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


@dataclass(frozen=True)
class Full104RareTailMolecularAuthorityV1:
    authority_id: str

    structural_preflight_sha256: str = STRUCTURAL_PREFLIGHT_SHA256
    structural_preflight_source_sha: str = STRUCTURAL_PREFLIGHT_SOURCE_SHA
    structural_terminal: str = STRUCTURAL_TERMINAL
    sample_receipt_sha256: str = SAMPLE_RECEIPT_SHA256
    full104_manifest_sha256: str = FULL104_MANIFEST_SHA256
    outer_split_receipt_sha256: str = OUTER_SPLIT_RECEIPT_SHA256

    pair_count_per_view: int = PAIR_COUNT_PER_VIEW
    min_informative_pair_coordinates: int = MIN_INFORMATIVE_PAIR_COORDINATES
    locality_numerator: int = LOCALITY_NUMERATOR
    locality_denominator: int = LOCALITY_DENOMINATOR
    tail_numerator: int = TAIL_NUMERATOR
    tail_denominator: int = TAIL_DENOMINATOR
    min_tail_anchors_per_donor: int = MIN_TAIL_ANCHORS_PER_DONOR
    triplets_per_stratum_cap: int = TRIPLETS_PER_STRATUM_CAP
    min_resolved_triplets_per_donor: int = MIN_RESOLVED_TRIPLETS_PER_DONOR
    null_replicates: int = NULL_REPLICATES
    null_p95_sorted_index: int = NULL_P95_SORTED_INDEX
    min_measurable_donors_per_case: int = MIN_MEASURABLE_DONORS_PER_CASE
    panels: int = PANELS
    sources: int = SOURCES
    folds: int = FOLDS
    required_cases: int = REQUIRED_CASES

    tail_selector_id: str = TAIL_SELECTOR_ID
    tail_tiebreak_id: str = TAIL_TIEBREAK_ID
    distance_id: str = DISTANCE_ID
    triplet_id: str = TRIPLET_ID
    null_id: str = NULL_ID
    null_block_id: str = NULL_BLOCK_ID
    case_id: str = CASE_ID
    pass_rule_id: str = PASS_RULE_ID

    expression_selection_allowed: bool = False
    pathology_labels_allowed: bool = False
    disease_labels_allowed: bool = False
    native_class_labels_allowed: bool = False
    broad_class_labels_allowed: bool = False
    rare_state_labels_allowed: bool = False

    molecular_execution_authorized: bool = True
    teacher_tail_evaluation_authorized: bool = False
    td60_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = {
            "structural_preflight_sha256": STRUCTURAL_PREFLIGHT_SHA256,
            "structural_preflight_source_sha": STRUCTURAL_PREFLIGHT_SOURCE_SHA,
            "sample_receipt_sha256": SAMPLE_RECEIPT_SHA256,
            "full104_manifest_sha256": FULL104_MANIFEST_SHA256,
            "outer_split_receipt_sha256": OUTER_SPLIT_RECEIPT_SHA256,
        }
        for name, expected in roots.items():
            if _sha(getattr(self, name), name) != expected:
                raise ValueError(f"{name} drifted from verified pre-molecular authority")
        if self.structural_terminal != STRUCTURAL_TERMINAL:
            raise ValueError("structural terminal must remain molecular-estimability-unproven")

        expected = {
            "pair_count_per_view": PAIR_COUNT_PER_VIEW,
            "min_informative_pair_coordinates": MIN_INFORMATIVE_PAIR_COORDINATES,
            "locality_numerator": LOCALITY_NUMERATOR,
            "locality_denominator": LOCALITY_DENOMINATOR,
            "tail_numerator": TAIL_NUMERATOR,
            "tail_denominator": TAIL_DENOMINATOR,
            "min_tail_anchors_per_donor": MIN_TAIL_ANCHORS_PER_DONOR,
            "triplets_per_stratum_cap": TRIPLETS_PER_STRATUM_CAP,
            "min_resolved_triplets_per_donor": MIN_RESOLVED_TRIPLETS_PER_DONOR,
            "null_replicates": NULL_REPLICATES,
            "null_p95_sorted_index": NULL_P95_SORTED_INDEX,
            "min_measurable_donors_per_case": MIN_MEASURABLE_DONORS_PER_CASE,
            "panels": PANELS,
            "sources": SOURCES,
            "folds": FOLDS,
            "required_cases": REQUIRED_CASES,
            "tail_selector_id": TAIL_SELECTOR_ID,
            "tail_tiebreak_id": TAIL_TIEBREAK_ID,
            "distance_id": DISTANCE_ID,
            "triplet_id": TRIPLET_ID,
            "null_id": NULL_ID,
            "null_block_id": NULL_BLOCK_ID,
            "case_id": CASE_ID,
            "pass_rule_id": PASS_RULE_ID,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from frozen rare-tail molecular design")

        if self.required_cases != self.panels * self.sources * self.folds:
            raise ValueError("required_cases must remain exactly panels x sources x folds")
        if self.null_p95_sorted_index != 60 or self.null_replicates != 64:
            raise ValueError("null p95 semantics drifted")
        if (self.locality_numerator, self.locality_denominator) != (1, 2):
            raise ValueError("nearest-half is the only authorized locality")
        if (self.tail_numerator, self.tail_denominator) != (1, 20):
            raise ValueError("q95 top-tail fraction drifted")

        for name in (
            "expression_selection_allowed",
            "pathology_labels_allowed",
            "disease_labels_allowed",
            "native_class_labels_allowed",
            "broad_class_labels_allowed",
            "rare_state_labels_allowed",
            "teacher_tail_evaluation_authorized",
            "td60_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")
        if self.molecular_execution_authorized is not True:
            raise ValueError("verified structural preflight is required to authorize molecular execution")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_FULL104_RARE_TAIL_MOLECULAR_AUTHORITY_V1",
                    **asdict(self),
                    "panel_view_rank_slices": PANEL_VIEW_RANK_SLICES,
                    "panel_gene_sha256": PANEL_GENE_SHA256,
                    "panel_pair_address_sha256": PANEL_PAIR_ADDRESS_SHA256,
                    "gene_rank_namespace": GENE_RANK_NAMESPACE,
                    "pair_rank_namespace": PAIR_RANK_NAMESPACE,
                    "triplet_sample_namespace": TRIPLET_SAMPLE_NAMESPACE,
                    "null_namespace": NULL_NAMESPACE,
                    "pass_terminal": PASS_TERMINAL,
                    "fail_terminal": FAIL_TERMINAL,
                    "not_estimable_terminal": NOT_ESTIMABLE_TERMINAL,
                }
            )
        ).hexdigest()


def case_pass(*, observed_median_donor_agreement: float, null_values: Tuple[float, ...]) -> bool:
    """Exact case gate: observed > 0.5 and observed > sorted(null)[60]."""
    if len(null_values) != NULL_REPLICATES:
        raise ValueError("case requires exactly 64 null values")
    values = tuple(float(x) for x in null_values)
    if not all(x == x and x not in (float("inf"), float("-inf")) for x in values):
        raise ValueError("all null values must be finite")
    observed = float(observed_median_donor_agreement)
    if not (observed == observed and observed not in (float("inf"), float("-inf"))):
        raise ValueError("observed case statistic must be finite")
    p95 = sorted(values)[NULL_P95_SORTED_INDEX]
    return bool(observed > 0.5 and observed > p95)


def full_gate_terminal(case_states: Tuple[str, ...]) -> str:
    """Require exactly 24 PASS cases; NOT_ESTIMABLE is never treated as FAIL/PASS."""
    if len(case_states) != REQUIRED_CASES:
        raise ValueError("full rare-tail gate requires exactly 24 case states")
    allowed = {"PASS", "FAIL", "NOT_ESTIMABLE"}
    if any(x not in allowed for x in case_states):
        raise ValueError("unknown rare-tail case state")
    if any(x == "NOT_ESTIMABLE" for x in case_states):
        return NOT_ESTIMABLE_TERMINAL
    if all(x == "PASS" for x in case_states):
        return PASS_TERMINAL
    return FAIL_TERMINAL
