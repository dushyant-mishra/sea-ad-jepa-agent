from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.foundation_transfer import cosine_knn_transfer


def test_knn_transfer_excludes_same_donor() -> None:
    reference = np.vstack([np.tile([1.0, 0.0], (20, 1)), np.tile([0.0, 1.0], (20, 1))])
    labels = np.array(["A"] * 20 + ["B"] * 20)
    donors = np.array([f"r-{index}" for index in range(40)])
    result = cosine_knn_transfer(reference, labels, donors, np.array([[1.0, 0.0], [0.0, 1.0]]), np.array(["A", "B"]), np.array(["q1", "q2"]), 15)
    assert result["balanced_accuracy"] == 1.0
    assert result["n_queries"] == 2


def test_incompatible_label_vocabularies_are_not_scored_as_failure() -> None:
    result = cosine_knn_transfer(np.eye(3), np.array(["A", "B", "C"]), np.array(["1", "2", "3"]),
                                 np.eye(2, 3), np.array(["X", "Y"]), np.array(["4", "5"]), 1)
    assert result["status"] == "not_identifiable_incompatible_label_vocabularies"
    assert np.isnan(result["balanced_accuracy"])
