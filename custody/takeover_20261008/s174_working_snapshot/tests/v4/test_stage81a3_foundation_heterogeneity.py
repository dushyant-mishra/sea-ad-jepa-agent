from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.foundation_heterogeneity import (
    complementary_count_split,
    deterministic_score,
    effective_number,
    normalize_counts,
    sampling_weights,
    state_retention,
    weighted_center,
)


CONFIG = ROOT / "configs/v4/stage81a3_foundation_heterogeneity_reality_audit.yaml"
SCRIPT = ROOT / "scripts/v4/stage81a3_foundation_heterogeneity_reality_audit.py"


def test_normalization_reproduces_contract() -> None:
    counts = np.asarray([0, 2, 8])
    expected = np.log1p(counts * 10_000 / 10)
    np.testing.assert_allclose(normalize_counts(counts), expected)


def test_normalization_uses_full_library_total_when_supplied() -> None:
    observed = normalize_counts(np.asarray([2, 8]), library_total=20)
    np.testing.assert_allclose(observed, np.log1p(np.asarray([2, 8]) * 500))


def test_count_split_preserves_integer_counts() -> None:
    counts = np.asarray([0, 1, 2, 10])
    first, second = complementary_count_split(counts, 7)
    assert np.array_equal(first + second, counts)
    assert np.issubdtype(first.dtype, np.integer)


def test_count_split_is_deterministic() -> None:
    counts = np.arange(20)
    assert np.array_equal(complementary_count_split(counts, 9)[0], complementary_count_split(counts, 9)[0])


def test_count_split_rejects_normalized_values() -> None:
    with pytest.raises(ValueError, match="integer"):
        complementary_count_split(np.asarray([0.5, 1.5]), 1)


def test_deterministic_score_is_stable() -> None:
    assert deterministic_score(1, "a") == deterministic_score(1, "a")


def test_matrix_equal_weight_centering() -> None:
    values = np.asarray([[0.0], [2.0], [10.0]])
    centered, mean, weights = weighted_center(values, np.asarray(["a", "a", "b"]))
    assert mean.item() == 5.5
    np.testing.assert_allclose(weights, [0.25, 0.25, 0.5])
    assert abs(np.sum(centered[:, 0] * weights)) < 1e-12


def test_state_retention_is_exact_for_complete_basis() -> None:
    values = np.eye(3)
    assert state_retention(values, np.eye(3), 3) == 1.0


def test_sampling_rules_are_normalized() -> None:
    counts = {"a": 100, "b": 25}
    for rule in ("cell_proportional", "dataset_uniform", "sqrt_cell_count"):
        assert sum(sampling_weights(counts, rule).values()) == pytest.approx(1.0)


def test_effective_number_uniform() -> None:
    assert effective_number(np.ones(4)) == pytest.approx(4.0)


def test_canonical_inventory_is_13_by_36() -> None:
    report = json.loads((ROOT / "results/v4/stage81a2_freeze_report.json").read_text(encoding="utf-8"))
    assert report["foundation_dataset_count"] == 13
    assert report["foundation_matrix_count"] == 36


def test_train_donor_contract_is_149() -> None:
    frame = pd.read_csv(ROOT / "results/v4/stage81a2_split_registry.csv")
    selected = frame[frame.split_domain.eq("foundation") & frame.split.eq("train")]
    assert len(selected) == 149


def test_no_donor_split_overlap() -> None:
    frame = pd.read_csv(ROOT / "results/v4/stage81a2_split_registry.csv")
    selected = frame[frame.split_domain.eq("foundation")]
    assert selected.groupby("split_group_id").split.nunique().max() == 1


def test_pca_cap_is_at_most_2048() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["bounds"]["pca_cells_per_matrix"] <= 2048


def test_forward_cap_is_at_most_64() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["bounds"]["forward_cells"] <= 64


def test_script_does_not_physically_concatenate_source_matrices() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "anndata.concat" not in text
    assert "scanpy.concat" not in text


def test_no_checkpoint_save_in_audit() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert "save" not in names
