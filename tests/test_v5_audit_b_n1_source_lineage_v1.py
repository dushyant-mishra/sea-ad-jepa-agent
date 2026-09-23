"""Synthetic-only tests for the missing per-cell/donor/source lineage check."""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.audit_b_n1_source_lineage_v1 import (
    SOURCES,
    assess_source_vectors,
)


@pytest.fixture
def inputs():
    donors = [f"D{i:03}" for i in range(104)]
    donor_src = np.array([0] * 41 + [1] * 17 + [2] * 46, dtype=np.int64)
    cell_donor = np.array([0, 1, 41, 58], dtype=np.int64)
    metadata_source = donor_src[cell_donor]
    return dict(
        donor_names=donors,
        donor_source_code=donor_src,
        stored_source_names=list(SOURCES),
        stored_per_cell_source=metadata_source.copy(),
        metadata_cell_donor=cell_donor,
        metadata_cell_source=metadata_source,
        expected_cells=4,
        expected_source_cells=(2, 1, 1),
    )


def test_canonical_alignment_is_diagnostic_only_never_n1_authority(inputs):
    out = assess_source_vectors(**inputs)
    assert out["state"] == "CANONICAL_SOURCE_ALIGNMENT_OBSERVED__DIAGNOSTIC_ONLY"
    assert out["source_name_order_matches"] is True
    assert out["src_of_cell_equals_donor_src_at_metadata_donor"] is True
    assert out["src_of_cell_mismatch_count"] == 0


def test_real_discovered_first_appearance_bug_is_quarantined(inputs):
    old = dict(
        inputs,
        stored_source_names=["HVS", "SEA_AD", "NPH52"],
        stored_per_cell_source=np.array([0, 0, 2, 1], dtype=np.int64),
    )
    out = assess_source_vectors(**old)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["source_name_order_matches"] is False
    assert out["src_of_cell_equals_donor_src_at_metadata_donor"] is False
    assert out["src_of_cell_mismatch_count"] == 2


def test_only_fixing_names_does_not_hide_bad_src_of_cell(inputs):
    wrong = dict(
        inputs,
        stored_per_cell_source=np.array([0, 0, 2, 1], dtype=np.int64),
    )
    out = assess_source_vectors(**wrong)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["source_name_order_matches"] is True
    assert out["src_of_cell_mismatch_count"] == 2


def test_only_fixing_per_cell_vector_does_not_hide_wrong_names(inputs):
    wrong = dict(inputs, stored_source_names=["HVS", "SEA_AD", "NPH52"])
    out = assess_source_vectors(**wrong)
    assert out["state"] == "QUARANTINED_SOURCE_ENCODING__N1_STOP"
    assert out["src_of_cell_mismatch_count"] == 0
    assert out["source_name_order_matches"] is False


def test_coordinated_source_permutation_that_preserves_histogram_fails(inputs):
    switched = inputs["donor_source_code"].copy()
    switched[41], switched[58] = switched[58], switched[41]
    assert tuple(np.bincount(switched, minlength=3)) == (41, 17, 46)
    fake = dict(
        inputs,
        donor_source_code=switched,
        stored_per_cell_source=switched[inputs["metadata_cell_donor"]],
    )
    with pytest.raises(ValueError, match="authenticated Level-4 donor/source"):
        assess_source_vectors(**fake)


def test_untrusted_float_source_or_out_of_range_donor_is_rejected(inputs):
    fake = dict(
        inputs,
        stored_per_cell_source=inputs["stored_per_cell_source"].astype(np.float64),
    )
    with pytest.raises(ValueError, match="exact int64"):
        assess_source_vectors(**fake)
    bad = inputs["metadata_cell_donor"].copy()
    bad[0] = 104
    fake = dict(inputs, metadata_cell_donor=bad)
    with pytest.raises(ValueError, match="outside canonical donor"):
        assess_source_vectors(**fake)
