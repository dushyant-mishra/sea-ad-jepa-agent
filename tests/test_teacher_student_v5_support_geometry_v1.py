from __future__ import annotations
import pytest

from sea_ad_jepa.v5.support_geometry_v1 import (
    balanced_block_sizes,
    fixed_visible_evidence,
    max_fixed_visible_for_support,
    validate_fixed_visible_across_support,
)


def test_fixed_visible_budget_equalizes_universe_relative_evidence():
    hvs=fixed_visible_evidence(measured_count=18_736,visible_genes=10_000,vocabulary_size=41_238)
    sea=fixed_visible_evidence(measured_count=35_076,visible_genes=10_000,vocabulary_size=41_238)
    assert hvs["visible_fraction_of_universe"]==pytest.approx(sea["visible_fraction_of_universe"])
    assert hvs["visible_fraction_within_measured"]!=pytest.approx(sea["visible_fraction_within_measured"])
    assert hvs["measured_fraction_of_universe"] < sea["measured_fraction_of_universe"]


def test_block_count_is_derived_from_hidden_support_not_frozen():
    hvs=balanced_block_sizes(hidden_count=7_494,target_genes_per_block=512)
    sea=balanced_block_sizes(hidden_count=14_030,target_genes_per_block=512)
    assert len(hvs)==15 and len(sea)==28
    assert max(hvs)<=512 and max(sea)<=512
    assert sum(hvs)==7_494 and sum(sea)==14_030


def test_support_geometry_has_no_implicit_budget():
    with pytest.raises(TypeError): balanced_block_sizes(hidden_count=100)  # type: ignore[call-arg]
    with pytest.raises(TypeError): fixed_visible_evidence(measured_count=100,vocabulary_size=1000)  # type: ignore[call-arg]
    with pytest.raises(TypeError): max_fixed_visible_for_support([18_736,35_076])  # type: ignore[call-arg]


def test_support_geometry_fails_if_visible_budget_exceeds_data():
    with pytest.raises(ValueError):
        fixed_visible_evidence(measured_count=18_736,visible_genes=18_737,vocabulary_size=41_238)


def test_hvs_minimum_support_binds_equal_visible_evidence_feasibility():
    measured=[18_736,30_294,32_445,34_405,35_076]
    assert max_fixed_visible_for_support(measured,minimum_hidden_target_genes=1)==18_735
    assert max_fixed_visible_for_support(measured,minimum_hidden_target_genes=512)==18_224
    report=validate_fixed_visible_across_support(measured,visible_genes=17_186,minimum_hidden_target_genes=512)
    assert report=={
        "minimum_measured_support":18_736,
        "minimum_hidden_target_genes":512,
        "maximum_feasible_visible_genes":18_224,
        "proposed_visible_genes":17_186,
        "minimum_realized_hidden_genes":1_550,
    }


def test_evidence_and_target_support_are_jointly_fail_closed():
    measured=[18_736,35_076]
    with pytest.raises(ValueError,match="violates minimum hidden-target support"):
        validate_fixed_visible_across_support(measured,visible_genes=18_500,minimum_hidden_target_genes=512)
    with pytest.raises(ValueError,match="leaves no visible evidence"):
        max_fixed_visible_for_support(measured,minimum_hidden_target_genes=18_736)
