from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "v5"
sys.path.insert(0, str(SCRIPTS))


def _modules():
    geometry_path = SCRIPTS / "td_relational_successor_geometry_v1.py"
    executor_path = SCRIPTS / "td_relational_successor_observed_executor_v1.py"
    assert geometry_path.is_file(), "TD-owned concordance geometry module is not implemented"
    assert executor_path.is_file(), "TD-owned observed-view executor is not implemented"
    return (
        importlib.import_module("td_relational_successor_geometry_v1"),
        importlib.import_module("td_relational_successor_observed_executor_v1"),
    )


def test_pair_selection_is_deterministic_and_production_width_is_2048():
    G, _ = _modules()
    feature_ids = [f"F{i:04d}" for i in range(512)]
    a = G.select_pair_coordinates(feature_ids, panel_id="P0", view_id="X")
    b = G.select_pair_coordinates(feature_ids, panel_id="P0", view_id="X")
    assert a == b
    assert len(a) == 2048
    assert len(set(a)) == 2048
    assert all(g0 < g1 for g0, g1 in a)


def test_concordance_distance_preserves_measured_zero_and_excludes_unmeasured():
    G, _ = _modules()
    feature_ids = ["a", "b", "c", "d"]
    pairs = [("a", "b"), ("a", "c"), ("b", "c"), ("c", "d")]
    values = np.array([
        [0.0, 0.0, 2.0, 1.0],
        [1.0, 0.0, 0.0, 2.0],
        [1.0, 0.0, 0.0, 2.0],
    ])
    measured = np.ones_like(values, dtype=bool)
    measured[2, 2] = False
    dist = G.build_concordance_distance_matrix(
        values,
        measured,
        feature_ids,
        pairs,
        min_informative=1,
    )
    assert np.isfinite(dist[0, 1])
    assert np.isfinite(dist[0, 2])
    assert dist[1, 1] == 0.0
    assert not np.isnan(dist[2, 2])

    measured_all_missing = measured.copy()
    measured_all_missing[2, :] = False
    dist2 = G.build_concordance_distance_matrix(
        values,
        measured_all_missing,
        feature_ids,
        pairs,
        min_informative=1,
    )
    assert np.isnan(dist2[0, 2])


def test_null_maps_are_deterministic_nonzero_within_td37a_blocks_and_never_cross_donor_operator():
    G, _ = _modules()
    donor_ids = np.array(["D1"] * 10 + ["D2"] * 10, dtype=object)
    operator_ids = np.array(["O1"] * 5 + ["O2"] * 5 + ["O1"] * 5 + ["O2"] * 5, dtype=object)
    rows = np.arange(20, dtype=np.int64)
    library = np.array([100, 90, 80, 70, 60, 50, 40, 30, 20, 10] * 2, dtype=float)
    detected = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100] * 2, dtype=int)
    maps, blocks = G.build_td37a_matched_y_null_maps(
        source="S",
        panel_id="P0",
        donor_ids=donor_ids,
        operator_ids=operator_ids,
        global_rows=rows,
        source_library=library,
        detected_genes=detected,
    )
    assert maps.shape == (64, 20)
    assert np.array_equal(maps, G.build_td37a_matched_y_null_maps(
        source="S",
        panel_id="P0",
        donor_ids=donor_ids,
        operator_ids=operator_ids,
        global_rows=rows,
        source_library=library,
        detected_genes=detected,
    )[0])
    for mapping in maps:
        assert np.array_equal(np.sort(mapping), np.arange(20))
        assert np.all(donor_ids[mapping] == donor_ids)
        assert np.all(operator_ids[mapping] == operator_ids)
        for block in blocks:
            idx = np.array(block, dtype=int)
            assert set(mapping[idx].tolist()) == set(idx.tolist())
            if len(idx) >= 2:
                assert np.all(mapping[idx] != idx)


def test_observed_executor_requires_512_disjoint_features_and_computes_td_geometry_itself():
    _, X = _modules()
    rng = np.random.default_rng(44)
    cells_per_donor = 12
    donors = np.repeat([f"D{i}" for i in range(5)], cells_per_donor)
    n = len(donors)
    operators = np.array(["O1"] * n, dtype=object)
    rows = np.arange(n, dtype=np.int64)
    latent = np.tile(np.linspace(-2.0, 2.0, cells_per_donor), 5)
    loadings = rng.normal(size=512)
    base = latent[:, None] * loadings[None, :] + 0.15 * rng.normal(size=(n, 512))
    z = base + 0.05 * rng.normal(size=base.shape)
    x = base + 0.05 * rng.normal(size=base.shape)
    y = base + 0.05 * rng.normal(size=base.shape)
    measured = np.ones((n, 512), dtype=bool)
    receipt = X.evaluate_observed_relational_profile(
        source="S",
        panel_id="P0",
        profile_id="opaque-profile",
        z_values=z,
        x_values=x,
        y_values=y,
        z_measured=measured,
        x_measured=measured,
        y_measured=measured,
        z_feature_ids=[f"Z{i:04d}" for i in range(512)],
        x_feature_ids=[f"X{i:04d}" for i in range(512)],
        y_feature_ids=[f"Y{i:04d}" for i in range(512)],
        donor_ids=donors,
        operator_ids=operators,
        global_rows=rows,
        source_library=np.full(n, 1000.0),
        detected_genes=np.full(n, 512),
        focal_mask=np.ones(n, dtype=bool),
        neighbor_pool_mask=np.ones(n, dtype=bool),
        min_focal_anchors_per_donor=1,
    )
    assert receipt.source == "S"
    assert tuple(receipt.scale_results) == ("1/8", "1/6", "1/4", "1/3", "1/2")
    assert receipt.scale_results["1/2"].status in {"PASS", "FAIL", "NOT_ESTIMABLE"}
    assert all(v is False for v in receipt.authority.values())


def test_observed_executor_rejects_overlapping_views_and_non512_feature_width():
    _, X = _modules()
    n = 4
    values = np.zeros((n, 4))
    measured = np.ones_like(values, dtype=bool)
    kwargs = dict(
        source="S", panel_id="P0", profile_id="p",
        z_values=values, x_values=values, y_values=values,
        z_measured=measured, x_measured=measured, y_measured=measured,
        z_feature_ids=["a", "b", "c", "d"],
        x_feature_ids=["e", "f", "g", "h"],
        y_feature_ids=["i", "j", "k", "l"],
        donor_ids=np.array(["D"] * n, dtype=object),
        operator_ids=np.array(["O"] * n, dtype=object),
        global_rows=np.arange(n),
        source_library=np.ones(n), detected_genes=np.ones(n, dtype=int),
        focal_mask=np.ones(n, dtype=bool), neighbor_pool_mask=np.ones(n, dtype=bool),
        min_focal_anchors_per_donor=1,
    )
    with pytest.raises(X.ObservedExecutorError, match="exactly 512"):
        X.evaluate_observed_relational_profile(**kwargs)
