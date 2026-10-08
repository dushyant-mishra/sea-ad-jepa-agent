from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "v77" / "run_v77_class_propagation_tournament.py"
FULL_OBSERVER_PATH = ROOT / "scripts" / "v77" / "build_v77_class_aware_fullscale_rna_observer.py"


def _load_path(path: Path, name: str):
    assert path.exists(), f"missing preregistered implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _load():
    return _load_path(RUNNER_PATH, "v77_class_tournament")


def test_fullscale_bridge_is_registry_compatible_and_outcome_blind():
    O = _load_path(FULL_OBSERVER_PATH, "v77_class_fullscale")
    assert O.N_ADDRESSES == 41238
    assert O.CLASS_PROGRAM_SCALE == 0.55
    assert O.WITHIN_CLASS_DIM_SCALE == pytest.approx(0.55 / np.sqrt(2))
    z = {
        "broad_class_index": np.array([0, 1, 1, 2], dtype=np.int16),
        "z_within_class": np.array([[0.1, -0.2], [0.3, 0.4], [-0.5, 0.2], [0.7, -0.1]], dtype=np.float32),
        "donor_index": np.array([0, 0, 1, 1]),
        "source_index": np.array([0, 1, 2, 0]),
        "operator_index": np.array([3, 4, 5, 6]),
    }
    c1 = O.class_program_contribution(z, 7302, 3)
    w1 = O.within_class_contribution(z, 7302, 3)
    z2 = dict(z)
    z2["donor_index"] = z["donor_index"][::-1]
    z2["source_index"] = z["source_index"][::-1]
    z2["operator_index"] = z["operator_index"][::-1]
    assert np.array_equal(c1, O.class_program_contribution(z2, 7302, 3))
    assert np.array_equal(w1, O.within_class_contribution(z2, 7302, 3))
    assert c1.shape == w1.shape == (4, 41238)


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
