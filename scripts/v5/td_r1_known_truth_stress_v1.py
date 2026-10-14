"""Known-truth/adversarial stress mechanics for real-TD R1.

This is a test-of-test layer. It does not read current human candidate outcomes,
does not set a biological threshold, and cannot authorize R1 PASS/FAIL.

The stress envelope is informed by frozen foundation ETL summaries and the
historical TD57B semantic lineage, while deliberately importing no TD57B outcome
margin or production threshold.
"""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence


class R1StressError(ValueError):
    pass


NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}

_ROW_FIELDS = {
    "donor_id",
    "relation_id",
    "source",
    "operator_x",
    "operator_y",
    "support_stratum_x",
    "support_stratum_y",
    "q_x",
    "q_y",
    "eligible",
    "cell_weight",
}


def _finite_number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R1StressError(f"{label} must be finite numeric")
    out = float(value)
    if not math.isfinite(out):
        raise R1StressError(f"{label} must be finite numeric")
    return out


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise R1StressError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def anchored_triplet_order(d_ij, d_ik) -> int:
    """Return q(i;j,k)=sign(d(i,j)-d(i,k)), preserving exact ties."""
    a = _finite_number(d_ij, "d_ij")
    b = _finite_number(d_ik, "d_ik")
    if a > b:
        return 1
    if a < b:
        return -1
    return 0


def _relation_sign(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in {-1, 0, 1}:
        raise R1StressError(f"{label} must be one of -1, 0, 1")
    return value


def summarize_recurrence(rows, *, minimum_informative_relations_per_donor: int) -> dict:
    """Donor-primary exact relation agreement under strict stratum matching.

    Rows marked ineligible are abstentions caused by support/estimability and are
    not converted into disagreements. Cell weights are retained only to expose
    how a forbidden cell-weighted summary could differ; they have no authority.
    """
    minimum = minimum_informative_relations_per_donor
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum <= 0:
        raise R1StressError("minimum_informative_relations_per_donor must be a positive integer")
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise R1StressError("rows must be a sequence")

    eligible_by_donor: dict[str, list[tuple[int, int, float]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or set(raw) != _ROW_FIELDS:
            raise R1StressError(f"rows[{index}] fields differ from frozen stress schema")
        donor = _token(raw["donor_id"], "donor_id")
        relation = _token(raw["relation_id"], "relation_id")
        _token(raw["source"], "source")
        operator_x = _token(raw["operator_x"], "operator_x")
        operator_y = _token(raw["operator_y"], "operator_y")
        if operator_x != operator_y:
            raise R1StressError("operator mismatch would violate donor/source/operator/support pairing")
        support_x = _token(raw["support_stratum_x"], "support_stratum_x")
        support_y = _token(raw["support_stratum_y"], "support_stratum_y")
        if support_x != support_y:
            raise R1StressError("support mismatch would violate donor/source/operator/support pairing")
        key = (donor, relation)
        if key in seen:
            raise R1StressError(f"duplicate donor/relation identity: {donor}/{relation}")
        seen.add(key)
        q_x = _relation_sign(raw["q_x"], "q_x")
        q_y = _relation_sign(raw["q_y"], "q_y")
        if not isinstance(raw["eligible"], bool):
            raise R1StressError("eligible must be boolean")
        weight = _finite_number(raw["cell_weight"], "cell_weight")
        if weight <= 0:
            raise R1StressError("cell_weight must be positive")
        if raw["eligible"]:
            eligible_by_donor[donor].append((q_x, q_y, weight))

    donor_agreement: dict[str, float] = {}
    weighted_num = 0.0
    weighted_den = 0.0
    for donor in sorted(eligible_by_donor):
        values = eligible_by_donor[donor]
        if len(values) < minimum:
            continue
        exact = [1.0 if qx == qy else 0.0 for qx, qy, _ in values]
        donor_agreement[donor] = sum(exact) / len(exact)
        for (qx, qy, weight) in values:
            weighted_num += weight * (1.0 if qx == qy else 0.0)
            weighted_den += weight

    if not donor_agreement:
        return {
            "status": "NOT_ESTIMABLE_SUPPORT",
            "donor_agreement": {},
            "donor_mean_agreement": None,
            "cell_weighted_agreement": None,
            "cell_weighted_agreement_has_authority": False,
            "failed_biology": False,
            "human_candidate_pass_authorized": False,
            "authority": dict(NO_AUTHORITY),
        }

    return {
        "status": "STRESS_SUMMARY_EXECUTABLE",
        "donor_agreement": donor_agreement,
        "donor_mean_agreement": sum(donor_agreement.values()) / len(donor_agreement),
        "cell_weighted_agreement": (weighted_num / weighted_den if weighted_den else None),
        "cell_weighted_agreement_has_authority": False,
        "failed_biology": False,
        "human_candidate_pass_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }


def td57b_semantic_fixture() -> dict:
    """Historical semantic compatibility only; no historical effect cutoff."""
    return {
        "historical_lineage": "TD57B",
        "relation_object": "ANCHORED_CELL_TRIPLET_ORDER",
        "distance_views": "DISJOINT_MOLECULAR_VIEWS",
        "donor_primary": True,
        "matched_null_preserves": ["donor", "operator", "depth", "detection"],
        "imports_historical_threshold": False,
        "fine_locality_authorized": False,
        "td59_nearest_half_promoted": False,
    }


def foundation_distribution_stress_profile() -> dict:
    """Frozen ETL envelope used only to choose adversarial stress geometry."""
    return {
        "calibration_bundle_sha256": "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
        "fit_cells": 4_553_407,
        "fit_donors": 104,
        "heldout_donors": 45,
        "operators": 42,
        "donor_cells_min": 81,
        "donor_cells_max": 174_111,
        "operator_cells_min": 179,
        "operator_cells_max": 732_360,
        "address_operator_support_min": 0,
        "address_operator_support_max": 42,
        "HVS_measured_scalar_fraction": 0.454338,
        "NPH52_measured_scalar_fraction": 0.807054,
        "SEA_AD_measured_scalar_fraction": 0.850575,
        "population_geometry_mechanic_prior": "V73_PRESERVE_SOURCE_OPERATOR_DONOR_OPERATOR_SUPPORT",
        "biological_threshold_authority": False,
    }


def qualify_r1_known_truth_stress() -> dict:
    """Qualify stress mechanics, not biology or a human decision threshold."""
    worlds: dict[str, str] = {}

    q = anchored_triplet_order(0.2, 0.8)
    q_mono = anchored_triplet_order(math.exp(0.2), math.exp(0.8))
    worlds["STRICT_MONOTONE_SCALE_INVARIANCE"] = "PASS" if q == q_mono else "FAIL"

    imbalanced = [
        {
            "donor_id": "D_BIG", "relation_id": f"R{i}", "source": "SEA_AD",
            "operator_x": "opA", "operator_y": "opA", "support_stratum_x": "S",
            "support_stratum_y": "S", "q_x": 1, "q_y": 1, "eligible": True,
            "cell_weight": 1000,
        }
        for i in range(100)
    ]
    imbalanced.append({
        "donor_id": "D_SMALL", "relation_id": "R100", "source": "SEA_AD",
        "operator_x": "opA", "operator_y": "opA", "support_stratum_x": "S",
        "support_stratum_y": "S", "q_x": 1, "q_y": -1, "eligible": True,
        "cell_weight": 1,
    })
    summary = summarize_recurrence(imbalanced, minimum_informative_relations_per_donor=1)
    worlds["DONOR_PRIMARY_EXTREME_IMBALANCE"] = (
        "PASS" if summary["donor_mean_agreement"] == 0.5 else "FAIL"
    )

    sparse = summarize_recurrence([
        {
            "donor_id": "D1", "relation_id": "R1", "source": "HVS",
            "operator_x": "op1", "operator_y": "op1", "support_stratum_x": "S",
            "support_stratum_y": "S", "q_x": 1, "q_y": -1, "eligible": False,
            "cell_weight": 1,
        }
    ], minimum_informative_relations_per_donor=1)
    worlds["SPARSE_SUPPORT_ABSTAINS"] = (
        "PASS" if sparse["status"] == "NOT_ESTIMABLE_SUPPORT" and sparse["failed_biology"] is False else "FAIL"
    )

    fixture = td57b_semantic_fixture()
    worlds["TD57B_OBJECT_COMPATIBILITY"] = (
        "PASS" if fixture["relation_object"] == "ANCHORED_CELL_TRIPLET_ORDER" and not fixture["imports_historical_threshold"] else "FAIL"
    )
    passed = all(value == "PASS" for value in worlds.values())
    return {
        "schema": "JEPA_TD_R1_KNOWN_TRUTH_STRESS_QUALIFICATION_V1",
        "status": "PASS_R1_KNOWN_TRUTH_STRESS_MECHANICS" if passed else "FAIL_R1_KNOWN_TRUTH_STRESS_MECHANICS",
        "worlds": worlds,
        "stress_profile": foundation_distribution_stress_profile(),
        "human_candidate_pass_authorized": False,
        "historical_threshold_imported": False,
        "authority": dict(NO_AUTHORITY),
    }
