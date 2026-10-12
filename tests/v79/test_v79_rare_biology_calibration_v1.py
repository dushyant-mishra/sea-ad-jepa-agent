from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import derive_v79_rare_biology_calibration_v1 as C  # noqa: E402


def fixture():
    # rows: [1,0,2,0], [0,3,0,0], [1,1,0,4], [0,0,5,1]
    indices = np.array([0, 2, 1, 0, 1, 3, 2, 3], dtype=np.int32)
    indptr = np.array([0, 2, 3, 6, 8], dtype=np.int32)
    data = np.array([1, 2, 3, 1, 1, 4, 5, 1], dtype=np.float64)
    weights = np.array([1.0, 2.0, 3.0, 4.0])
    meta = pd.DataFrame({
        "sample_row": [0, 1, 2, 3],
        "source": ["A", "A", "B", "B"],
        "matrix_id": ["a1", "a1", "b1", "b2"],
        "operator_index": [0, 0, 1, 2],
        "donor_id": ["d1", "d2", "d3", "d4"],
        "native_class": ["MG", "X", "MG", "MG"],
    })
    return indices, indptr, data, weights, meta


def test_scores_and_source_conditioning_are_deterministic():
    indices, indptr, data, weights, meta = fixture()
    scores = C.score_csr_rows(indices, indptr, data, weights)
    assert np.allclose(scores, [7.0, 6.0, 19.0, 19.0])
    a = C.build_summary(meta, scores, {"A": ["MG"], "B": ["MG"]})
    b = C.build_summary(meta, scores, {"A": ["MG"], "B": ["MG"]})
    assert a == b
    assert a["population"]["cells"] == 4
    assert a["population"]["donors"] == 4
    assert set(a["by_source"]) == {"A", "B"}
    assert a["lineage"]["cells"] == 3


def test_pathology_like_metadata_is_rejected():
    *_, meta = fixture()
    meta["diagnosis"] = ["x"] * len(meta)
    with pytest.raises(ValueError, match="pathology"):
        C.validate_metadata(meta)


def test_global_tail_is_diagnostic_only_not_truth():
    indices, indptr, data, weights, meta = fixture()
    scores = C.score_csr_rows(indices, indptr, data, weights)
    with pytest.raises(ValueError, match="global threshold"):
        C.build_summary(meta, scores, {"A": ["MG"], "B": ["MG"]}, truth_from_global_threshold=True)


def test_weight_length_must_cover_all_indices():
    indices, indptr, data, _, _ = fixture()
    with pytest.raises(ValueError, match="weight"):
        C.score_csr_rows(indices, indptr, data, np.ones(3))


def test_lineage_tail_reports_positive_donors_without_promoting_thresholds():
    indices, indptr, data, weights, meta = fixture()
    scores = C.score_csr_rows(indices, indptr, data, weights)
    out = C.build_summary(meta, scores, {"A": ["MG"], "B": ["MG"]}, tail_quantiles=(0.5,))
    tail = out["lineage"]["tail_diagnostics"]["q500"]
    assert tail["diagnostic_only"] is True
    assert tail["positive_cells"] == 2
    assert tail["positive_donors"] == 2
