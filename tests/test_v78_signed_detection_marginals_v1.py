from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "v77" / "run_v78_signed_detection_marginal_tournament.py"
SIGNED = ROOT / "scripts" / "v77" / "v78_signed_detection.py"
OBSERVER = ROOT / "scripts" / "v77" / "build_v78_fullscale_rna_observer.py"
BASE_OBSERVER = ROOT / "scripts" / "v77" / "build_v77_fullscale_rna_observer_v2.py"
E2_RECEIPT = ROOT / "results" / "v77" / "V77_CLASS_PROPAGATION_TOURNAMENT_V1.json"


def _load(path: Path, name: str):
    assert path.exists(), f"missing V78 implementation surface: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _load_runner():
    return _load(RUNNER, "v78_tournament")


def test_f0_f1_surface_is_frozen_and_e4_fails_closed():
    R = _load_runner()
    assert R.ARMS == ("F0", "F1", "F2", "F3")
    assert R.DEFAULT_SEED == 7302
    assert R.DEFAULT_MEASUREMENT_SEED == 7302
    assert R.CLASS_PROGRAM_SCALE == 0.55
    assert R.arm_config("F0")["background"] == "v1"
    assert R.arm_config("F1")["background"] == "v2"
    for key in ("truth_arm", "class_scale", "seed", "measurement_seed"):
        assert R.arm_config("F0")[key] == R.arm_config("F1")[key]
    with pytest.raises(PermissionError):
        R.validate_arm("E4")


def test_f0_binds_exact_committed_e2_reference():
    R = _load_runner()
    rec = R.load_e2_reference(E2_RECEIPT)
    assert rec["seed"] == 7302
    assert rec["cells"] == 2500
    assert rec["class_authority_sha256"] == "a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014"
    assert rec["evaluation_universe"]["sha256"] == "e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763"
    assert R.extract_e2_score(rec) == rec["results"]["E2"]["score"]


def test_f0_reference_missing_or_mismatched_fails_closed(tmp_path):
    R = _load_runner()
    with pytest.raises(FileNotFoundError):
        R.load_e2_reference(tmp_path / "missing.json")
    bad = json.loads(E2_RECEIPT.read_text())
    bad["seed"] = 7303
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(RuntimeError):
        R.load_e2_reference(p)


def test_f1_inherits_background_v2_constants():
    R = _load_runner()
    cfg = R.background_v2_contract()
    assert cfg == {
        "broad": {"n": 8, "frac": 0.62, "scale": 0.85},
        "mid": {"n": 40, "frac": 0.12, "scale": 0.55},
        "narrow": {"n": 220, "frac": 0.012, "scale": 0.45},
        "paralog": {"group_frac": 0.22, "group_size": 6, "jitter": 0.12, "scale": 0.70},
    }


def test_2k_operator_support_is_preserved():
    R = _load_runner()
    rec = R.operator_support_2k()
    assert rec["n_cells"] == 2000
    assert rec["n_operators"] == 42
    assert rec["operators_present"] == 42
    assert rec["minimum_operator_count"] >= 1


def test_current_v77_selection_is_log_rel_plus_gumbel_only():
    text = BASE_OBSERVER.read_text()
    assert "score = np.where(sup[i], np.log(np.maximum(rel[i], 1e-30)), -np.inf)" in text
    assert "score = score + 0.35 * (-np.log(-np.log" in text
    assert "signed_detection" not in text


def test_signed_detection_geometry_inherits_background_v2_without_paralog():
    S = _load(SIGNED, "v78_signed_geometry")
    assert S.family_geometry() == {
        "broad": {"n": 8, "frac": 0.62, "scale": 0.85},
        "mid": {"n": 40, "frac": 0.12, "scale": 0.55},
        "narrow": {"n": 220, "frac": 0.012, "scale": 0.45},
    }
    assert S.MEMBERSHIP_STREAM_START == 12000
    assert S.CELL_FACTOR_STREAM_START == 13000


def test_signed_loadings_are_deterministic_balanced_and_near_centered():
    S = _load(SIGNED, "v78_signed_loadings")
    W1 = S.loading_matrix(7302, 512)
    W2 = S.loading_matrix(7302, 512)
    assert np.array_equal(W1, W2)
    assert W1.shape[0] == 8 + 40 + 220
    for row, meta in zip(W1, S.factor_manifest(512)):
        nz = row[row != 0]
        assert len(nz) == meta["support_size"]
        assert np.any(nz > 0) and np.any(nz < 0)
        assert abs(int((nz > 0).sum()) - int((nz < 0).sum())) <= 1
        assert np.sqrt(np.mean(nz.astype(np.float64) ** 2)) == pytest.approx(meta["scale"], rel=1e-6)
        assert abs(float(nz.mean())) <= float(meta["scale"]) / max(len(nz), 1) + 1e-7


def test_signed_surface_has_no_nuisance_or_gene_metadata_inputs():
    S = _load(SIGNED, "v78_signed_signature")
    assert list(inspect.signature(S.loading_matrix).parameters) == ["seed", "n_addresses"]
    assert list(inspect.signature(S.cell_factors).parameters) == ["seed", "global_cell_index"]
    assert list(inspect.signature(S.field).parameters) == ["seed", "global_cell_index", "n_addresses"]
    ids = np.array([3, 7, 11, 19], dtype=np.int64)
    assert np.array_equal(S.cell_factors(7302, ids), S.cell_factors(7302, ids))


def test_zero_signed_field_exactly_reproduces_v77_sparse_counts_and_totals():
    O = _load(OBSERVER, "v78_observer_counts")
    B = _load(BASE_OBSERVER, "v77_observer_counts")
    n = 3
    g = int(B.N)
    rel = np.full((n, g), 0.01, dtype=np.float32)
    rel[:, :64] = np.linspace(0.1, 2.0, 64, dtype=np.float32)[None, :]
    sup = np.zeros((n, g), dtype=bool)
    sup[:, :64] = True
    ids = np.array([1, 2, 3], dtype=np.int64)
    lib = np.array([100, 110, 120], dtype=np.int64)
    det = np.array([10, 11, 12], dtype=np.int64)
    base = B.sparse_counts(rel, sup, ids, lib, det, 7302)
    got = O.sparse_counts_separated(rel, sup, ids, lib, det, 7302, signed_field=np.zeros_like(rel))
    for a, b in zip(base, got):
        assert np.array_equal(a, b)
    _idx, vals, indptr = got
    assert np.array_equal(np.diff(indptr), det)
    for i in range(n):
        assert int(vals[indptr[i]:indptr[i + 1]].sum()) == int(lib[i])


def test_nonzero_signed_field_changes_selection_without_changing_cell_totals():
    O = _load(OBSERVER, "v78_observer_signed")
    B = _load(BASE_OBSERVER, "v77_observer_signed")
    g = int(B.N)
    rel = np.ones((1, g), dtype=np.float32)
    sup = np.zeros((1, g), dtype=bool); sup[:, :40] = True
    ids = np.array([9], dtype=np.int64)
    lib = np.array([80], dtype=np.int64)
    det = np.array([8], dtype=np.int64)
    zero = O.sparse_counts_separated(rel, sup, ids, lib, det, 7302, signed_field=np.zeros_like(rel))
    field = np.zeros_like(rel); field[:, 20:40] = 100.0
    signed = O.sparse_counts_separated(rel, sup, ids, lib, det, 7302, signed_field=field)
    assert not np.array_equal(zero[0], signed[0])
    assert int(signed[1].sum()) == 80
    assert int(np.diff(signed[2])[0]) == 8


def test_f3_replaces_only_positive_count_baseline_geometry():
    O = _load(OBSERVER, "v78_observer_f3_weights")
    rel = np.array([[2.0, 8.0, 4.0], [1.0, 4.0, 2.0]], dtype=np.float64)
    old_baseline = np.array([1.0, 4.0, 2.0], dtype=np.float64)
    new_baseline = np.array([4.0, 2.0, 1.0], dtype=np.float64)
    w = O.f3_positive_count_weights(rel, old_baseline, new_baseline)
    expected_multiplier = rel / old_baseline[None, :]
    assert np.allclose(w, expected_multiplier * new_baseline[None, :])
    assert np.allclose(O.f3_positive_count_weights(rel, old_baseline, old_baseline), rel)


def test_f3_count_weights_cannot_change_f2_selected_gene_identities():
    O = _load(OBSERVER, "v78_observer_f3_isolation")
    B = _load(BASE_OBSERVER, "v77_observer_f3_isolation")
    g = int(B.N)
    rel = np.ones((1, g), dtype=np.float32)
    sup = np.zeros((1, g), dtype=bool); sup[:, :48] = True
    ids = np.array([17], dtype=np.int64)
    lib = np.array([120], dtype=np.int64)
    det = np.array([12], dtype=np.int64)
    field = np.zeros_like(rel); field[:, 24:48] = 3.0
    f2 = O.sparse_counts_separated(rel, sup, ids, lib, det, 7302, signed_field=field)
    weight_rel = np.ones_like(rel); weight_rel[:, :48] = np.linspace(0.2, 4.0, 48)[None, :]
    f3 = O.sparse_counts_separated(rel, sup, ids, lib, det, 7302, signed_field=field, weight_rel=weight_rel)
    assert np.array_equal(f2[0], f3[0])
    assert int(f3[1].sum()) == 120
    assert int(np.diff(f3[2])[0]) == 12
