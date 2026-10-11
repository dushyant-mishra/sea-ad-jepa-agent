"""Prospective contract for the cheap corrected-S174 model-structure replay.

Synthetic arrays only. The replay must consume a compact cache, keep donors intact across folds, preserve a
prevalence-spanning panel when subsetting a larger cache, use a full-rank operator-within-source basis, and support
residual permutation diagnostics without opening the 41K shards.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import run_v79_s174_structure_replay as R  # noqa: E402


def _cache(tmp: Path):
    rng = np.random.default_rng(4)
    n_donor, per = 18, 18
    donor = np.repeat(np.arange(n_donor), per)
    src_by_donor = np.repeat(np.arange(3), 6)
    src = src_by_donor[donor]
    cls = np.tile(np.repeat(np.arange(3), 6), n_donor)
    op = (src * 2 + (donor % 2)).astype(np.int64)
    depth = rng.normal(size=len(donor))
    eta0 = -0.3 + 1.8 * (cls == 1) - 1.4 * (cls == 2) + 0.4 * depth
    eta1 = -0.2 + 0.8 * depth
    p = 1 / (1 + np.exp(-np.c_[eta0, eta1]))
    detected = rng.uniform(size=p.shape) < p
    positive = np.exp(1.0 + 0.3 * depth[:, None] + 0.8 * (cls[:, None] == 1) + rng.normal(scale=.12, size=p.shape))
    counts = detected * np.maximum(1, np.rint(positive)).astype(np.int32)
    npz = tmp / "cache.npz"
    np.savez(npz, counts_selected=counts, gene_address_index=np.array([11, 22]), prevalence_selected=(counts > 0).mean(0),
             library_cached=np.full(len(donor), 1000), n_detected=np.full(len(donor), 100), source_library=np.full(len(donor), 1000),
             cls=cls, src=src, op=op, donor=donor, dk=donor * 3 + cls, log_lib_centered=depth)
    rec = tmp / "receipt.json"
    rec.write_text(json.dumps({"schema":"V79_ANALYSIS_CACHE_RECEIPT_V2", "npz":npz.name,
                               "npz_sha256":hashlib.sha256(npz.read_bytes()).hexdigest(),
                               "streaming_passes":2,"max_count_shards_resident":1,"global_sparse_assembly":False}), encoding="utf-8")
    return npz, rec


def test_cache_receipt_is_hash_bound(tmp_path):
    npz, rec = _cache(tmp_path)
    data = R.load_compact_cache(npz, rec)
    assert data["counts_selected"].shape[1] == 2
    b = bytearray(npz.read_bytes()); b[-1] ^= 1; npz.write_bytes(bytes(b))
    with pytest.raises(SystemExit):
        R.load_compact_cache(npz, rec)


def test_donor_folds_never_split_a_donor(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    folds = R.donor_folds(d["donor"], d["src"], k=3, seed=20261011)
    seen = {}
    for f, test in enumerate(folds):
        for donor in np.unique(d["donor"][test]):
            assert donor not in seen
            seen[int(donor)] = f
            assert np.all(test[d["donor"] == donor])
    assert len(seen) == len(np.unique(d["donor"]))


def test_operator_within_source_design_is_full_rank(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    X = R.design_matrix(d, "depth_class_source_operator")
    assert np.linalg.matrix_rank(X) == X.shape[1]


def test_nested_detection_replay_detects_strong_class_signal(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    out = R.evaluate_detection_gene(d, gene=0, k=3, seed=20261011)
    assert out["models"]["depth_class"]["mean_logloss"] < out["models"]["depth_quad"]["mean_logloss"]


def test_positive_replay_uses_only_positive_counts(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    out = R.evaluate_positive_gene(d, gene=0, k=3, seed=20261011)
    assert out["n_positive"] == int((d["counts_selected"][:, 0] > 0).sum())
    assert np.isfinite(out["models"]["depth_class_source_operator"]["mean_lpd"])


def test_subpanel_stays_prevalence_stratified():
    p = np.array([.05,.85,.15,.65,.25,.45,.35,.75,.55,.95] * 5)
    pos = R.select_panel_positions(p, 20, seed=17)
    chosen = p[pos]
    assert len(pos) == 20 and len(np.unique(pos)) == 20
    assert chosen.min() <= .15 and chosen.max() >= .85
    hist, _ = np.histogram(chosen, bins=[0,.2,.4,.6,.8,1.01])
    assert np.all(hist > 0)


def test_residual_group_permutation_detects_strong_group_structure():
    rng = np.random.default_rng(8)
    groups = np.repeat(np.arange(12), 20)
    strata = np.repeat(np.arange(3), 80)
    effects = np.array([-2.0,-1.2,-.7,-.2,.2,.7,1.2,2.0,-1.5,1.5,-.9,.9])
    residual = effects[groups] + rng.normal(scale=.15, size=len(groups))
    out = R.permutation_group_support(residual, groups, strata, seed=11, n_perm=99)
    assert out["supported"] is True
    assert out["observed"] > out["null_q95"]


def test_operator_support_removes_pure_donor_residual():
    rng = np.random.default_rng(12)
    # Each donor spans two operators; only donor effects are planted.
    donor = np.repeat(np.arange(18), 20)
    src = np.repeat(np.arange(3), 120)
    within = np.tile(np.repeat([0, 1], 10), 18)
    op = src * 2 + within
    donor_effect = rng.normal(scale=1.0, size=18)
    residual = donor_effect[donor] + rng.normal(scale=.05, size=len(donor))
    out = R.operator_support_after_donor_centering(residual, op, donor, src, seed=15, n_perm=99)
    assert out["observed"] <= out["null_q95"]


# --- Controller repair (PR #280 ruling, 2026-10-11T19:40Z): explicit operator-within-source penalty --------------

def _separated_operator_data():
    rng = np.random.default_rng(7)
    n_donor, per = 24, 20
    donor = np.repeat(np.arange(n_donor), per)
    src = np.repeat(np.arange(3), 8)[donor]
    op = (src * 3 + (donor % 3)).astype(np.int64)
    cls = rng.integers(0, 3, size=len(donor))
    depth = rng.normal(size=len(donor))
    p = 1 / (1 + np.exp(-(-0.2 + 0.5 * depth + 0.6 * (cls == 1))))
    y = (rng.uniform(size=len(donor)) < p).astype(np.float64)
    y[op == 4] = 0.0            # one operator level with no detections at all (quasi-separation)
    y[op == 7] = 1.0            # one operator level detected in every cell
    counts = (y[:, None] * np.maximum(1, rng.poisson(4.0, size=(len(donor), 1)))).astype(np.int32)
    return dict(counts_selected=counts, cls=cls, src=src, op=op, donor=donor, dk=donor * 3 + cls,
                log_lib_centered=depth, prevalence_selected=(counts > 0).mean(0)), y


def test_operator_penalty_set_is_frozen_and_not_a_cli_option():
    assert R.OPERATOR_LAMBDA_PRIMARY == 1.0
    assert R.OPERATOR_LAMBDA_SET == (0.25, 1.0, 4.0)
    assert R.OPERATOR_LAMBDA_PRIMARY in R.OPERATOR_LAMBDA_SET
    opts = [s for a in R.build_parser()._actions for s in a.option_strings]
    assert not any(("lambda" in s or "penalty" in s or "ridge" in s) for s in opts), opts


def test_only_operator_within_source_columns_receive_the_operator_penalty():
    d, _ = _separated_operator_data()
    X = R.design_matrix(d, "depth_class_source_operator")
    mask = R.operator_column_mask(d, "depth_class_source_operator")
    n_op_contrasts = sum(len(np.unique(d["op"][d["src"] == s])) - 1 for s in np.unique(d["src"]))
    assert mask.dtype == bool and mask.shape == (X.shape[1],) and mask.sum() == n_op_contrasts
    assert mask[-n_op_contrasts:].all() and not mask[:-n_op_contrasts].any()
    for lam in R.OPERATOR_LAMBDA_SET:
        pen = R.operator_penalty_vector(d, "depth_class_source_operator", lam)
        assert pen[0] == 0.0                                   # intercept unpenalized, as before
        assert np.all(pen[1:][~mask[1:]] == R.RIDGE)           # depth, class, source keep the frozen tiny ridge
        assert np.all(pen[mask] == lam)                        # operator-within-source columns only
    for model in R.MODELS[:-1]:
        assert not R.operator_column_mask(d, model).any()


def test_penalized_operator_design_stays_full_rank():
    d, _ = _separated_operator_data()
    X = R.design_matrix(d, "depth_class_source_operator")
    assert np.linalg.matrix_rank(X) == X.shape[1]


def test_separated_operator_levels_converge_at_primary_lambda():
    d, y = _separated_operator_data()
    X = R.design_matrix(d, "depth_class_source_operator")
    beta = R._logistic_fit(X, y, penalty=R.operator_penalty_vector(d, "depth_class_source_operator", R.OPERATOR_LAMBDA_PRIMARY))
    assert np.all(np.isfinite(beta)) and np.abs(beta).max() < 10.0
    z = np.log(np.maximum(d["counts_selected"][:, 0], 1).astype(float))
    pos = d["counts_selected"][:, 0] > 0
    b, sigma = R._ridge_linear_fit(X[pos], z[pos], penalty=R.operator_penalty_vector(d, "depth_class_source_operator", 1.0)[None, :][0])
    assert np.all(np.isfinite(b)) and sigma > 0


def test_non_operator_nested_outputs_are_unchanged_by_the_repair(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    folds = R.donor_folds(d["donor"], d["src"], 3, 20261011)
    for gene in (0, 1):
        det = R.evaluate_detection_gene(d, gene, 3, 20261011)
        pos = R.evaluate_positive_gene(d, gene, 3, 20261011)
        y = (d["counts_selected"][:, gene] > 0).astype(np.float64)
        c = d["counts_selected"][:, gene].astype(np.float64)
        for model in R.MODELS[:-1]:                    # legacy computation, exactly as before the repair
            X = R.design_matrix(d, model)
            loss = np.concatenate([R._bernoulli_logloss(y[t], X[t] @ R._logistic_fit(X[~t], y[~t])) for t in folds])
            assert det["models"][model]["mean_logloss"] == float(loss.mean())
            lp = []
            for t in folds:
                tr, te = (~t) & (c > 0), t & (c > 0)
                b, s = R._ridge_linear_fit(X[tr], np.log(c[tr]))
                lp.append(R._normal_lpd(np.log(c[te]), X[te] @ b, s))
            assert pos["models"][model]["mean_lpd"] == float(np.concatenate(lp).mean())


def test_operator_sensitivities_are_recorded_for_exactly_the_frozen_set(tmp_path):
    npz, rec = _cache(tmp_path)
    d = R.load_compact_cache(npz, rec)
    det = R.evaluate_detection_gene(d, 0, 3, 20261011)
    pos = R.evaluate_positive_gene(d, 0, 3, 20261011)
    for out in (det, pos):
        sens = out["operator_penalty_sensitivity"]
        assert set(sens) == {str(lam) for lam in R.OPERATOR_LAMBDA_SET}
        assert out["models"]["depth_class_source_operator"] == sens[str(R.OPERATOR_LAMBDA_PRIMARY)]
