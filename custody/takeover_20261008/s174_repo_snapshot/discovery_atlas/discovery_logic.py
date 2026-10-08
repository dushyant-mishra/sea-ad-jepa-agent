from __future__ import annotations

from collections.abc import Container, Mapping
import math
from typing import Any


def classify_manifold_qc(
    value: float | None, *, missing_label: str = "not_computed"
) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return missing_label
    if float(value) <= 0.05:
        return "manifold_safe"
    if float(value) <= 0.10:
        return "borderline_manifold_shift"
    return "manifold_violation_warning"


def assign_shortlist_tier(
    row: Mapping[str, Any], cleaner_classes: Container[str]
) -> str:
    class_name = str(row["pathology_axis_class"])
    clean_scorecard = (
        class_name in cleaner_classes
        and float(row["therapeutic_like_score_percentile"]) >= 95
        and float(row["tau_lowering_score_percentile"]) >= 90
        and float(row["neuron_preservation_score_percentile"]) >= 50
        and float(row["gliosis_penalty_percentile"]) < 60
        and float(row["broad_shift_score_percentile"]) < 90
    )
    broad_caution = (
        class_name
        in {"broad_reactive_state_shift", "gliosis_inflating", "neuron_risk"}
        or float(row["gliosis_penalty_percentile"]) >= 90
        or float(row["broad_shift_score_percentile"]) >= 95
    )
    if clean_scorecard:
        return "scorecard_supported_isolated_hypothesis"
    if bool(row["prior_candidate_flag"]) and not broad_caution:
        return "biological_anchor_prior_candidate"
    if broad_caution:
        return "broad_state_caution"
    return "unsupported_or_deprioritized"


def shortlist_deprioritization_reason(row: Mapping[str, Any]) -> str:
    tier = str(row["final_tier"])
    class_name = str(row["pathology_axis_class"])
    therapeutic = float(row["therapeutic_like_score_percentile"])
    broad = float(row["broad_shift_score_percentile"])
    gliosis = float(row["gliosis_penalty_percentile"])

    if tier == "scorecard_supported_isolated_hypothesis":
        return "none"
    if tier == "biological_anchor_prior_candidate":
        return "prior_candidate_not_globally_enriched"
    if class_name == "neuron_risk":
        return "neuron_risk_penalty"
    if broad >= 90:
        if therapeutic >= 95:
            return "high_score_but_broad_shift_penalized"
        return "broad_shift_penalty"
    if gliosis >= 60:
        return "gliosis_penalty"
    if tier == "broad_state_caution":
        return "broad_shift_penalty"
    return "not_supported_by_scorecard_or_graph"


def shortlist_graph_interpretation(label: str) -> str:
    return {
        "isolated_high_score_gene": (
            "isolated_high_score_no_fdr_supported_neighborhood"
        ),
        "no_graph_support": "no_supportive_one_hop_enrichment",
        "broad_reactive_neighborhood": "broad_neighbor_context_not_fdr_supported",
    }.get(str(label), "graph_support_not_testable")
