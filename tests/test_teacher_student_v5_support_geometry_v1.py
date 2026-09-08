from __future__ import annotations
import pytest

from sea_ad_jepa.v5.support_geometry_v1 import (
    balanced_block_sizes,
    fixed_visible_evidence,
)


def test_fixed_visible_budget_equalizes_universe_relative_evidence():
    hvs=fixed_visible_evidence(
        measured_count=18_736,visible_genes=10_000,vocabulary_size=41_238
    )
    sea=fixed_visible_evidence(
        measured_count=35_076,visible_genes=10_000,vocabulary_size=41_238
    )
    assert hvs["visible_fraction_of_universe"]==pytest.approx(
        sea["visible_fraction_of_universe"]
    )
    assert hvs["visible_fraction_within_measured"]!=pytest.approx(
        sea["visible_fraction_within_measured"]
    )


def test_block_count_is_derived_from_hidden_support_not_frozen():
    hvs=balanced_block_sizes(hidden_count=7_494,target_genes_per_block=512)
    sea=balanced_block_sizes(hidden_count=14_030,target_genes_per_block=512)
    assert len(hvs)==15
    assert len(sea)==28
    assert max(hvs)<=512 and max(sea)<=512
    assert sum(hvs)==7_494 and sum(sea)==14_030


def test_support_geometry_has_no_implicit_budget():
    with pytest.raises(TypeError):
        balanced_block_sizes(hidden_count=100)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        fixed_visible_evidence(
            measured_count=100,vocabulary_size=1000
        )  # type: ignore[call-arg]


def test_support_geometry_fails_if_visible_budget_exceeds_data():
    with pytest.raises(ValueError):
        fixed_visible_evidence(
            measured_count=18_736,visible_genes=18_737,vocabulary_size=41_238
        )
