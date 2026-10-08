from __future__ import annotations

import math

from discovery_atlas.discovery_logic import (
    assign_shortlist_tier,
    classify_manifold_qc,
    shortlist_deprioritization_reason,
    shortlist_graph_interpretation,
)


CLEANER = {
    "tau_lowering_neuron_preserving",
    "dual_pathology_lowering_neuron_preserving",
}


def base_row(**updates):
    row = {
        "pathology_axis_class": "tau_lowering_neuron_preserving",
        "therapeutic_like_score_percentile": 98.0,
        "tau_lowering_score_percentile": 95.0,
        "neuron_preservation_score_percentile": 80.0,
        "gliosis_penalty_percentile": 20.0,
        "broad_shift_score_percentile": 40.0,
        "prior_candidate_flag": False,
    }
    row.update(updates)
    return row


def test_manifold_qc_classification():
    assert classify_manifold_qc(0.00) == "manifold_safe"
    assert classify_manifold_qc(0.05) == "manifold_safe"
    assert classify_manifold_qc(0.07) == "borderline_manifold_shift"
    assert classify_manifold_qc(0.20) == "manifold_violation_warning"
    assert classify_manifold_qc(math.nan) == "not_computed"


def test_tier_assignment():
    assert (
        assign_shortlist_tier(base_row(), CLEANER)
        == "scorecard_supported_isolated_hypothesis"
    )
    assert (
        assign_shortlist_tier(base_row(broad_shift_score_percentile=98), CLEANER)
        == "broad_state_caution"
    )
    assert (
        assign_shortlist_tier(
            base_row(
                pathology_axis_class="mixed_or_unclear",
                therapeutic_like_score_percentile=60,
                prior_candidate_flag=True,
            ),
            CLEANER,
        )
        == "biological_anchor_prior_candidate"
    )
    assert (
        assign_shortlist_tier(
            base_row(
                pathology_axis_class="mixed_or_unclear",
                therapeutic_like_score_percentile=40,
            ),
            CLEANER,
        )
        == "unsupported_or_deprioritized"
    )


def test_deprioritization_reasons():
    broad = base_row(
        final_tier="unsupported_or_deprioritized",
        broad_shift_score_percentile=95,
    )
    assert (
        shortlist_deprioritization_reason(broad)
        == "high_score_but_broad_shift_penalized"
    )
    gliosis = base_row(
        final_tier="unsupported_or_deprioritized",
        therapeutic_like_score_percentile=90,
        gliosis_penalty_percentile=70,
    )
    assert shortlist_deprioritization_reason(gliosis) == "gliosis_penalty"
    neuron = base_row(
        final_tier="broad_state_caution",
        pathology_axis_class="neuron_risk",
    )
    assert shortlist_deprioritization_reason(neuron) == "neuron_risk_penalty"


def test_graph_interpretation():
    assert (
        shortlist_graph_interpretation("isolated_high_score_gene")
        == "isolated_high_score_no_fdr_supported_neighborhood"
    )
    assert (
        shortlist_graph_interpretation("no_graph_support")
        == "no_supportive_one_hop_enrichment"
    )
