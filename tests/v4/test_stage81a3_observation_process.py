from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sea_ad_jepa.v4.observation_process import assert_no_provenance_inputs, robust_quality_features


def test_provenance_identifiers_are_forbidden_model_inputs() -> None:
    with pytest.raises(ValueError):
        assert_no_provenance_inputs({"normalized_expression": 1, "donor_id": "x"})
    assert_no_provenance_inputs({"normalized_expression": 1, "measurement_mask": 1})


def test_heldout_family_uses_global_train_statistics() -> None:
    quality, _, unseen = robust_quality_features(
        np.array([100, 200, 10_000]), np.array([10, 20, 100]), np.array([0.9, 0.8, 0.1]),
        np.array(["known", "known", "heldout"]), np.array([True, True, False]),
    )
    assert quality.shape == (3, 6)
    assert unseen.tolist() == [False, False, True]
