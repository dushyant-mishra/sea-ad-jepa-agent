"""Tests the exact frozen PR328 world as a measurement-availability fixture.

These are not JEPA, target or biological performance claims. Source methods,
latent biology, perturbation, observation operator and original receipt are
unaltered. Historical negative tests/synthetic tournaments are not repeated.
"""
from pathlib import Path
import numpy as np
import pytest

from scripts.v79.audit_frozen_measured_panel_observability_v1 import (
    OTHER_GENE_PANEL, QUERY_INDEX, analyze_frozen_fixture, measured_panel_target,
)

ROOT = Path(__file__).resolve().parents[2]


def test_q_other_8_panel_support_on_frozen_world():
    result = analyze_frozen_fixture(ROOT)
    assert result["n_cells"] == 480
    assert result["query_address_index"] == 0
    assert result["other_gene_panel_address_indices"] == list(range(1, 9))
    assert result["q_scalar_invariance"] is True
    assert result["controller_truth_used"] is False
    assert result["fitted_any_model"] is False
    assert result["selected_any_target"] is False
    assert result["human_query_rights_authenticated"] is False
    assert result["source_labels_are_synthetic"] is True
    assert not any(result["authority"].values())

    src = result["per_synthetic_source"]
    assert set(src) == {"HVS", "NPH52", "SEA_AD"}
    assert sum(row["cells"] for row in src.values()) == 480
    assert 1 in src["HVS"]["panel_missing_addresses"]
    assert 7 in src["SEA_AD"]["panel_missing_addresses"]
    assert src["NPH52"]["panel_missing_addresses"] == []
    assert src["HVS"]["fully_measured_8_gene_rows"] == 0
    assert src["SEA_AD"]["fully_measured_8_gene_rows"] == 0
    assert src["NPH52"]["fully_measured_8_gene_rows"] == src["NPH52"]["cells"]
    for row in src.values():
        assert row["positive_denominator_rows"] <= row["fully_measured_8_gene_rows"]
        assert row["positive_denominator_rows"] + row["not_estimable_rows"] == row["cells"]


def test_teacher_measurement_excludes_query_scalar_and_support_is_not_zero():
    counts = np.asarray([[2, 3, 1, 1, 2, 3, 4, 5, 6],
                         [0, 3, 1, 1, 2, 3, 4, 5, 6],
                         [1, 3, 1, 1, 2, 3, 4, 5, 0]], dtype=np.int64)
    support = np.ones_like(counts, dtype=np.bool_)
    support[2, 8] = False
    eligible, target = measured_panel_target(counts, support)
    assert eligible.tolist() == [True, True, False]
    assert np.array_equal(target[0], target[1])
    assert np.isnan(target[2]).all()
    altered = counts.copy()
    altered[:, QUERY_INDEX] += 1000
    other_eligible, other_target = measured_panel_target(altered, support)
    assert np.array_equal(eligible, other_eligible)
    assert np.array_equal(target, other_target, equal_nan=True)


def test_strict_measurement_refuses_nonmeasurements_and_address_aliasing():
    c = np.ones((2, 9), dtype=np.int64)
    s = np.ones((2, 9), dtype=np.bool_)
    cases = (
        dict(query_index=True),
        dict(query_index="0"),
        dict(query_index=0.0),
        dict(panel=(True, 2, 3, 4, 5, 6, 7, 8)),
        dict(panel=(0, 2, 3, 4, 5, 6, 7, 8)),
        dict(panel=(1, 1, 3, 4, 5, 6, 7, 8)),
        dict(panel=list(OTHER_GENE_PANEL)),
    )
    for kwargs in cases:
        with pytest.raises(ValueError, match="SYNTHETIC_PANEL_MEASUREMENT_REFUSED"):
            measured_panel_target(c, s, **kwargs)
    with pytest.raises(ValueError, match="raw integer"):
        measured_panel_target(c.astype(np.float64), s)
    with pytest.raises(ValueError, match="Boolean support"):
        measured_panel_target(c, s.astype(np.int64))
    neg = c.copy()
    neg[0, 2] = -1
    with pytest.raises(ValueError, match="negative"):
        measured_panel_target(neg, s)
    absent = s.copy()
    absent[0, 2] = False
    with pytest.raises(ValueError, match="unmeasured entries"):
        measured_panel_target(c, absent)


def test_zero_denominator_is_not_estimable_not_measured_zero():
    c = np.zeros((1, 9), dtype=np.int64)
    s = np.ones_like(c, dtype=np.bool_)
    eligible, target = measured_panel_target(c, s)
    assert not eligible.any()
    assert np.isnan(target).all()


def test_original_frozen_receipt_refuses_alternative_seed(monkeypatch):
    import scripts.v79.audit_frozen_measured_panel_observability_v1 as A
    monkeypatch.setattr(A, "WORLD_SEED", 20261012)
    with pytest.raises(ValueError, match="frozen world SHA"):
        A.analyze_frozen_fixture(ROOT)
