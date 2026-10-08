from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "v77" / "run_v77_class_propagation_tournament.py"


def _load():
    assert RUNNER_PATH.exists(), "class-propagation tournament runner is not implemented"
    spec = importlib.util.spec_from_file_location("v77_class_tournament", RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_tournament_surface_is_frozen_and_e4_rejected():
    R = _load()
    assert R.ARMS == ("E0", "E1", "E2", "E3")
    assert R.REAL_REFERENCE_STATUS == "DESCRIPTIVE_ONLY__S159_NOT_BINARY_AUTHORITY"
    with pytest.raises(PermissionError):
        R.validate_arm("E4")


def test_2k_operator_support_retains_all_42():
    R = _load()
    rec = R.operator_support_2k(seed=7302)
    assert rec["n_cells"] == 2000
    assert rec["n_operators"] == 42
    assert rec["operators_present"] == 42
    assert rec["minimum_operator_count"] >= 1


def test_universe_digest_is_enforced(tmp_path):
    R = _load()
    p = tmp_path / "u.npz"
    np.savez_compressed(p, evaluation_universe=np.arange(32, dtype=np.int64),
                        name=np.array("TEST_UNIVERSE"))
    digest = R.sha256_file(p)
    assert np.array_equal(R.load_universe(p, digest, "TEST_UNIVERSE"), np.arange(32))
    with pytest.raises(RuntimeError):
        R.load_universe(p, "0" * 64, "TEST_UNIVERSE")


def test_receipt_has_no_binary_s159_ruling():
    R = _load()
    rec = R.make_receipt(
        authority_sha="a" * 64,
        universe_sha="b" * 64,
        universe_name="TRAIN_PREVALENCE05_19569",
        seed=20261008,
        cells=2500,
        results={"E0": {"t5": {"within_over_pooled": 1.0}}},
        operator_support={"n_operators": 42, "operators_present": 42, "minimum_operator_count": 1},
        executor_digests={"x.py": "c" * 64},
    )
    assert rec["statistical_ruling"]["real_point_estimates"] == "descriptive references"
    assert rec["statistical_ruling"]["s159_binary_gate"] is False
    assert "pass" not in json.dumps(rec["results"]).lower()


def test_result_panel_contract_names_all_required_metrics():
    R = _load()
    fields = set(R.REQUIRED_PANEL_FIELDS)
    assert fields == {
        "expression.median_abs_corr", "expression.frac_abs_gt_0p3", "expression.var_top10_pc",
        "detection.median_abs_corr", "detection.frac_abs_gt_0p3", "detection.mean_degree",
        "detection.transitivity", "detection.largest_community_frac",
        "t5.within_over_pooled", "abundance.abundance_max_over_median_nonzero",
        "abundance.top1pct_count_share", "median_detected_per_cell",
    }
