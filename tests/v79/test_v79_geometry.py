"""V79 weighted geometry: with uniform weights every statistic reduces to the frozen V77 builder's point value
(synthetic data, exact for graph statistics, 1e-10 relative otherwise); integer weights equal a donor-bootstrap
resample; the nested Dirichlet weights are valid and layout-independent when bound to cell identity; T5
qualifies classes by cell count, never by weight. One real-data test (skipped when the corrected TRAIN cache is
absent) reproduces the corrected S174 replay references."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
import v79_geometry as GEO  # noqa: E402
import build_v77_calibration_envelope as ENV  # noqa: E402
import build_v77_topology_calibration as TC  # noqa: E402

GRAPH_KEYS = ("frac_abs_gt_0p3", "mean_degree", "largest_community_frac", "transitivity", "substitute_frac",
              "frac_pos_gt_0p3", "frac_neg_lt_m0p3", "pos_over_neg_ratio")
CONT_KEYS = ("median_abs_corr", "var_top10_pc", "mean_signed_corr")
T5_GRAPH_KEYS = ("n_cells", "fraction_gt_0p3", "mean_degree", "transitivity")
T5_TOP_KEYS = ("pooled_median_abs_corr", "mean_within_class_median_abs_corr", "within_over_pooled_ratio")


def _mismatches(got: dict, ref: dict, rel: float, prefix: str = "") -> list:
    """Graph statistics must be identical; continuous ones within rel. Returns every mismatch, not the first."""
    bad = []
    for k in GRAPH_KEYS:
        if got[k] != ref[k]:
            bad.append((prefix + k, got[k], ref[k]))
    for k in CONT_KEYS:
        if not abs(got[k] - ref[k]) <= rel * abs(ref[k]):
            bad.append((prefix + k, got[k], ref[k]))
    return bad


def _t5_mismatches(got: dict, per_class: dict, top: dict, rel: float) -> list:
    bad = []
    if got["classes_used"] != list(per_class):
        bad.append(("classes_used", got["classes_used"], list(per_class)))
    for c, ref in per_class.items():
        g = got["per_class"][c]
        bad += [(f"{c}.{k}", g[k], ref[k]) for k in T5_GRAPH_KEYS if g[k] != ref[k]]
        if not abs(g["median_abs_corr"] - ref["median_abs_corr"]) <= rel * abs(ref["median_abs_corr"]):
            bad.append((f"{c}.median_abs_corr", g["median_abs_corr"], ref["median_abs_corr"]))
    bad += [(k, got[k], top[k]) for k in T5_TOP_KEYS if not abs(got[k] - top[k]) <= rel * abs(top[k])]
    return bad


def _factor_matrix(rng, n=400, g=150, k=5):
    """Continuous cells x genes with strong shared axes of both signs and a few near-duplicate columns."""
    F = rng.normal(size=(n, k))
    L = rng.normal(size=(k, g)) * rng.uniform(0.2, 1.2, size=(k, 1))
    H = F @ L + rng.normal(size=(n, g)) * rng.uniform(0.5, 2.0, size=g)
    for j in range(0, 20, 2):
        H[:, j + 1] = H[:, j] + 0.2 * rng.normal(size=n)
    return H


def _uniform(n):
    return np.full(n, 1.0 / n)


# ---------------------------------------------------------------- weighted correlation

def test_uniform_weighted_corr_equals_builder_formula_and_corrcoef():
    rng = np.random.default_rng(1)
    H = _factor_matrix(rng, n=300, g=60)
    C = GEO.weighted_corr(H, _uniform(300))
    Z = (H - H.mean(0)) / (H.std(0) + 1e-9)
    np.testing.assert_allclose(C, Z.T @ Z / 300, rtol=0, atol=1e-12)
    # corrcoef has no 1e-9 guard; the guard shrinks each entry by about 2e-9 / sd
    np.testing.assert_allclose(C, np.corrcoef(H, rowvar=False), rtol=0, atol=1e-8)


def test_weighted_corr_is_exactly_symmetric():
    rng = np.random.default_rng(2)
    H = _factor_matrix(rng, n=200, g=40)
    w = rng.random(200)
    C = GEO.weighted_corr(H, w / w.sum())
    assert np.array_equal(C, C.T)


def test_weights_must_sum_to_one_and_be_nonnegative():
    H = np.random.default_rng(3).normal(size=(10, 4))
    with pytest.raises(ValueError):
        GEO.weighted_corr(H, np.full(10, 0.2))
    w = np.full(10, 0.1)
    w[0], w[1] = -0.1, 0.3
    with pytest.raises(ValueError):
        GEO.weighted_corr(H, w)


# ---------------------------------------------------------------- layer statistics

def test_uniform_weights_reproduce_stats_from_logmatrix():
    rng = np.random.default_rng(4)
    Ld = _factor_matrix(rng)
    sel = np.argsort(-Ld.var(0))[:100]
    ref = ENV.stats_from_logmatrix(Ld, sel, 100)
    got = GEO.weighted_layer_stats(Ld[:, sel], _uniform(len(Ld)))
    assert ref["frac_abs_gt_0p3"] > 0.05 and ref["substitute_frac"] > 0 and ref["frac_neg_lt_m0p3"] > 0
    assert _mismatches(got, ref, 1e-10) == []


def test_uniform_weights_reproduce_binary_layer_with_constant_columns():
    rng = np.random.default_rng(5)
    D = (_factor_matrix(rng, n=400, g=80) > 0.8).astype(np.float64)
    D[:, 0] = 1.0   # detected in every cell: the builder's mean is exactly 1, so the column is uncorrelated
    D[:, 1] = 0.0
    ref = ENV.stats_from_logmatrix(D, np.arange(80), 80)
    got = GEO.weighted_layer_stats(D, _uniform(400))
    assert _mismatches(got, ref, 1e-10) == []
    C = GEO.weighted_corr(D, _uniform(400))
    assert not C[0].any() and not C[1].any()


def test_integer_weights_equal_a_resample_of_rows():
    """A donor bootstrap resample is a weight vector of multiplicities; the weighted statistic must equal the
    builder's statistic on the replicated rows."""
    rng = np.random.default_rng(6)
    H = _factor_matrix(rng, n=300, g=90)
    mult = rng.integers(0, 4, size=300)
    ref = ENV.stats_from_logmatrix(np.repeat(H, mult, axis=0), np.arange(90), 90)
    got = GEO.weighted_layer_stats(H, mult / mult.sum())
    assert _mismatches(got, ref, 1e-10) == []


# ---------------------------------------------------------------- T5

def _classed_matrix(rng, sizes):
    cls = np.repeat([f"k{i}" for i in range(len(sizes))], sizes)
    H = np.concatenate([_factor_matrix(rng, n=s, g=70, k=3) + rng.normal(0, 2, size=70) for s in sizes])
    return H, cls


def test_uniform_weights_reproduce_class_conditional_t5():
    rng = np.random.default_rng(7)
    H, cls = _classed_matrix(rng, (260, 230, 200, 120))
    n = len(H)
    sel = np.arange(H.shape[1])
    Z = (H - H.mean(0)) / (H.std(0) + 1e-9)
    per_class, pooled, within = TC.class_conditional_t5(H, sel, Z.T @ Z / n, cls)
    assert list(per_class) == ["k0", "k1", "k2"]
    got = GEO.weighted_t5(H, _uniform(n), cls)
    top = dict(pooled_median_abs_corr=pooled, mean_within_class_median_abs_corr=within,
               within_over_pooled_ratio=within / pooled)
    assert _t5_mismatches(got, per_class, top, 1e-10) == []


def test_t5_floor_counts_cells_not_weights():
    rng = np.random.default_rng(8)
    H, cls = _classed_matrix(rng, (250, 199, 200))
    w = np.where(cls == "k0", 0.01 / 250, np.where(cls == "k1", 0.80 / 199, 0.19 / 200))
    got = GEO.weighted_t5(H, w, cls)
    assert got["classes_used"] == ["k0", "k2"]          # k1 carries 80% of the weight but has 199 cells
    assert got["per_class"]["k0"]["class_mass"] == pytest.approx(0.01, rel=1e-12)
    assert got["per_class"]["k2"]["n_cells"] == 200      # the floor is inclusive, as in the builder


# ---------------------------------------------------------------- abundance and depth

def test_uniform_weights_reproduce_abundance_stats():
    rng = np.random.default_rng(9)
    counts = rng.poisson(rng.lognormal(-1.0, 1.5, size=300)[None, :] * np.ones((250, 1)))
    counts[:, :3] = 0
    ref = ENV.abundance_stats(counts, counts.sum(1)[:, None])
    got = GEO.weighted_abundance(sparse.csr_matrix(counts), _uniform(250))
    for k in ref:
        assert got[k] == pytest.approx(ref[k], rel=1e-12, abs=0)


def test_uniform_weighted_quantile_equals_numpy_linear():
    rng = np.random.default_rng(10)
    x = np.round(rng.normal(size=501), 1)      # with ties
    qs = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)
    np.testing.assert_allclose(GEO.weighted_quantile(x, _uniform(501), qs), np.quantile(x, qs), rtol=0, atol=1e-12)
    w = np.r_[_uniform(501), 0.0, 0.0]
    np.testing.assert_allclose(GEO.weighted_quantile(np.r_[x, 99.0, -99.0], w, qs), np.quantile(x, qs),
                               rtol=0, atol=1e-12)


# ---------------------------------------------------------------- nested Dirichlet weights

def _donors():
    sizes = (1, 2, 5, 17, 40, 3)
    return np.repeat([f"d{i}" for i in range(len(sizes))], sizes)


def test_nested_dirichlet_weights_are_a_valid_distribution():
    don = _donors()
    for seed in range(20):
        w = GEO.nested_dirichlet_weights(don, np.random.default_rng(seed))
        assert w.shape == don.shape and (w > 0).all()
        assert abs(w.sum() - 1.0) < 1e-12
        mass = {d: w[don == d].sum() for d in np.unique(don)}
        assert all(m > 0 for m in mass.values())


def test_nested_dirichlet_weights_are_deterministic_given_rng():
    don = _donors()
    a = GEO.nested_dirichlet_weights(don, np.random.default_rng(11))
    b = GEO.nested_dirichlet_weights(don, np.random.default_rng(11))
    c = GEO.nested_dirichlet_weights(don, np.random.default_rng(12))
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_nested_dirichlet_donor_mass_is_flat_dirichlet():
    don = _donors()
    rng = np.random.default_rng(13)
    levels = np.unique(don)
    M = np.array([[w[don == d].sum() for d in levels]
                  for w in (GEO.nested_dirichlet_weights(don, rng) for _ in range(4000))])
    # Dirichlet(1,...,1): every donor's mass has mean 1/D regardless of its cell count
    np.testing.assert_allclose(M.mean(0), 1.0 / len(levels), rtol=0.10)


def test_nested_dirichlet_bound_to_cell_identity_ignores_storage_layout():
    don = _donors()
    keys = np.array([f"cell{i:03d}" for i in range(len(don))])
    perm = np.random.default_rng(14).permutation(len(don))
    a = GEO.nested_dirichlet_weights(don, np.random.default_rng(15), cell_keys=keys)
    b = GEO.nested_dirichlet_weights(don[perm], np.random.default_rng(15), cell_keys=keys[perm])
    assert np.array_equal(a[perm], b)
    keys[1] = keys[2]                                    # d1 holds cells 1 and 2
    with pytest.raises(ValueError):
        GEO.nested_dirichlet_weights(don, np.random.default_rng(15), cell_keys=keys)


# ---------------------------------------------------------------- row order and the whole pipeline

def test_builder_order_sorts_by_counts_file_name_not_stem():
    design = dict(stem=np.array(["abc", "abc", "abc-1", "0ff", "0ff"]), row=np.array([0, 1, 0, 1, 0]))
    # "abc-1.counts.npz" < "abc.counts.npz" because "-" < ".", although the stem "abc" < "abc-1"
    assert GEO.builder_order(design).tolist() == [4, 3, 2, 0, 1]


def _synthetic_counts(rng, sizes=(260, 240, 210, 90), g=500):
    cls = np.repeat([f"c{i}" for i in range(len(sizes))], sizes)
    n = len(cls)
    base = rng.lognormal(-2.0, 1.8, size=g)
    prog = rng.normal(0, 1.0, size=(len(sizes), g))
    fac = rng.normal(size=(n, 2)) @ (rng.normal(size=(2, g)) * (rng.random(g) < 0.3))
    depth = rng.lognormal(0, 0.4, size=n)
    rate = base[None, :] * np.exp(prog[np.searchsorted(np.unique(cls), cls)] + 0.8 * fac) * depth[:, None] * 3
    return sparse.csr_matrix(rng.poisson(rate).astype(np.int32)), cls


def test_prepare_and_geometry_reproduce_the_builders_end_to_end():
    rng = np.random.default_rng(16)
    X, cls = _synthetic_counts(rng)
    n, n_hvg = X.shape[0], 120
    lib = np.asarray(X.sum(1)).ravel()
    keep = np.where(np.asarray((X > 0).sum(0)).ravel() / n > 0.05)[0]
    C, hvg, Ld, sel = TC.hvg_correlation(X, lib, keep, n_hvg)
    prep = GEO.prepare(X, cls, n_hvg=n_hvg)
    assert 0 < len(keep) < X.shape[1]
    assert np.array_equal(prep["keep"], keep) and np.array_equal(prep["sel"], sel)
    assert np.array_equal(prep["hvg_address_index"], hvg) and np.array_equal(prep["lib"], lib)
    assert np.array_equal(prep["Ld_sel"], Ld[:, sel])
    Db = (np.asarray(X[:, keep].todense()) > 0).astype(np.float64)
    assert np.array_equal(prep["D_sel"], Db[:, sel])

    g = GEO.geometry(prep, _uniform(n))
    bad = _mismatches(g["expression_cp10k_log1p"], ENV.stats_from_logmatrix(Ld, sel, n_hvg), 1e-10, "expr.")
    bad += _mismatches(g["detection_binary"], ENV.stats_from_logmatrix(Db, sel, n_hvg), 1e-10, "det.")
    per_class, pooled, within = TC.class_conditional_t5(Ld, sel, C, cls)
    top = dict(pooled_median_abs_corr=pooled, mean_within_class_median_abs_corr=within,
               within_over_pooled_ratio=within / pooled)
    bad += _t5_mismatches(g["t5_class_conditional"], per_class, top, 1e-10)
    ref_ab = ENV.abundance_stats(np.asarray(X[:, keep].todense()), lib[:, None])
    bad += [(k, g["abundance"][k], v) for k, v in ref_ab.items() if not abs(g["abundance"][k] - v) <= 1e-12 * abs(v)]
    assert bad == []
    assert g["t5_class_conditional"]["classes_used"] == ["c0", "c1", "c2"]
    dep = g["depth"]["log_library_cached_address_sum"]
    assert dep["q50"] == pytest.approx(np.quantile(np.log(np.maximum(lib, 1)), 0.5), rel=1e-12)


# ---------------------------------------------------------------- real corrected TRAIN (skipped without the cache)

CACHE = Path("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1")
BRIDGE = ROOT / "results" / "v78" / "V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
REPLAY = ROOT / "results" / "v77" / "s174_replay"


@pytest.mark.skipif(not CACHE.is_dir() or not BRIDGE.is_file(), reason="corrected S174 TRAIN cache not present")
def test_uniform_weights_reproduce_the_corrected_s174_replay():
    import build_v77_real_calibration as RC
    expr_ref = json.loads((REPLAY / "V77_REAL_CALIBRATION_ENVELOPE_V1.json").read_text(encoding="utf-8"))
    det_ref = json.loads((REPLAY / "V77_REAL_DETECTION_ENVELOPE_V1.json").read_text(encoding="utf-8"))
    topo_ref = json.loads((REPLAY / "V77_REAL_TRAIN_TOPOLOGY_CALIBRATION_V1.json").read_text(encoding="utf-8"))
    ab_ref = json.loads((REPLAY / "V77_REAL_ABUNDANCE_ENVELOPE_V1.json").read_text(encoding="utf-8"))

    X, design = GEO.load_builder_ordered(CACHE, BRIDGE)
    # the permuted lane load IS load_real, row for row, and the bytes are those the references were built from
    Xr, cls_r, don_r, src_r, digests = RC.load_real(CACHE)
    assert all(np.array_equal(getattr(X, a), getattr(Xr, a)) for a in ("indptr", "indices", "data"))
    assert np.array_equal(design["raw_class"], cls_r.astype(str)) and np.array_equal(design["donor_id"], don_r.astype(str))
    assert np.array_equal(design["source_library"], src_r.astype(np.int64))
    for ref in (expr_ref, det_ref, topo_ref, ab_ref):
        assert ref["source"]["shard_digests"] == digests
    del Xr

    prep = GEO.prepare(X, design["raw_class"], source_library=design["source_library"])
    assert prep["n_cells"] == topo_ref["cohort"]["n_cells"] == 4726
    assert len(prep["keep"]) == topo_ref["cohort"]["genes_above_det_floor"] == 14417
    g = GEO.geometry(prep, _uniform(prep["n_cells"]))

    point = lambda ref: {k: v["point"] for k, v in ref["ACCEPTANCE_ENVELOPES"].items()}  # noqa: E731
    bad = _mismatches(g["expression_cp10k_log1p"], point(expr_ref), 1e-9, "expr.")
    bad += _mismatches(g["detection_binary"], point(det_ref), 1e-9, "det.")
    t5 = topo_ref["T5_class_conditional_structure"]
    bad += _t5_mismatches(g["t5_class_conditional"], t5["per_class"], t5, 1e-9)
    bad += [(f"abundance.{k}", g["abundance"][k], v) for k, v in point(ab_ref).items()
            if not abs(g["abundance"][k] - v) <= 1e-9 * abs(v)]
    assert bad == [], bad
