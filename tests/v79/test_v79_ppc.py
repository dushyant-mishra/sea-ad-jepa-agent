"""Held-out-donor posterior predictive checks: source-stratified deterministic donor folds; a split that keeps
operator, class and source codes and re-encodes donors and donor-classes contiguously, refusing a held-out
operator unseen in training; hand-computed statistics; mid-rank predictive quantiles and closed 90% intervals;
new donor effects with the exchangeable parent-mean term. Pure numpy except the last test, which fits a tiny
synthetic world with NumPyro (skipped where NumPyro is absent) and checks that held-out coverage is high when
the model is right and visibly lower for donor heterogeneity when the donor components are left out. No real
data: designs and responses are synthetic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_ppc as PPC  # noqa: E402


def toy_design(seed=0, donors_per_src=(6, 6, 6), ops_per_src=3, n_cls=3):
    """Every donor sits in one source and is seen by every operator of its source (2-4 cells per pair)."""
    rng = np.random.default_rng(seed)
    rows, op0, don0 = [], 0, 0
    for s, n_d in enumerate(donors_per_src):
        for o in range(ops_per_src):
            for d in range(n_d):
                for _ in range(rng.integers(2, 5)):
                    rows.append((s, op0 + o, don0 + d, int(rng.integers(n_cls))))
        op0 += ops_per_src
        don0 += n_d
    src, op, donor, cls = (np.array(c, dtype=np.int64) for c in zip(*rows))
    keys = sorted(set(zip(donor.tolist(), cls.tolist())))
    lut = {k: i for i, k in enumerate(keys)}
    dk = np.array([lut[(a, b)] for a, b in zip(donor.tolist(), cls.tolist())], dtype=np.int64)
    lib = rng.normal(0, 0.3, len(src))
    return dict(n=len(src), cls=cls, src=src, op=op, donor=donor, dk=dk, n_cls=n_cls, n_src=len(donors_per_src),
                n_op=op0, n_donor=don0, n_dk=len(keys), log_lib_centered=lib - lib.mean())


# ---------------------------------------------------------------- folds

def test_donor_folds_are_source_stratified_partitions_and_deterministic():
    d = toy_design(1, donors_per_src=(10, 7, 5))
    k = 3
    folds = PPC.donor_folds(d, k, seed=20261009)
    allf = np.concatenate(folds)
    assert len(allf) == len(set(allf.tolist())) == d["n_donor"]
    dsrc = PPC.donor_source(d)
    for s, n_s in enumerate((10, 7, 5)):
        per = [int((dsrc[f] == s).sum()) for f in folds]
        assert sum(per) == n_s and set(per) <= {n_s // k, -(-n_s // k)}
    sizes = [len(f) for f in folds]
    assert max(sizes) - min(sizes) <= 1
    again = PPC.donor_folds(d, k, seed=20261009)
    assert all(np.array_equal(a, b) for a, b in zip(folds, again))
    other = PPC.donor_folds(d, k, seed=7)
    assert not all(np.array_equal(a, b) for a, b in zip(folds, other))
    with pytest.raises(ValueError):
        PPC.donor_folds(d, 6, seed=1)          # source 2 has 5 donors, fewer than 6 folds


# ---------------------------------------------------------------- split

def test_split_design_keeps_fixed_codes_and_reencodes_donors_contiguously():
    d = toy_design(2)
    held = PPC.donor_folds(d, 2, seed=3)[0]
    tr_di, tr, te, tm = PPC.split_design(d, held)
    assert np.array_equal(np.sort(np.concatenate([tr, te])), np.arange(d["n"]))
    assert set(np.unique(d["donor"][te]).tolist()) == set(held.tolist())
    for x in ("cls", "src", "op"):
        assert np.array_equal(tr_di[x], d[x][tr]) and np.array_equal(tm[x], d[x][te])
        assert tr_di[f"n_{x}"] == d[f"n_{x}"]
    for x in ("donor", "dk"):
        for codes, n_lev, orig in ((tr_di[x], tr_di[f"n_{x}"], d[x][tr]), (tm[x], tm[f"n_{x}"], d[x][te])):
            assert np.array_equal(np.unique(codes), np.arange(n_lev))
            pairs = set(zip(codes.tolist(), orig.tolist()))
            assert len(pairs) == n_lev == len(set(orig.tolist()))          # one-to-one with the original codes
            assert np.all(np.diff([o for _, o in sorted(pairs)]) > 0)      # original code order kept
    assert np.array_equal(tm["donor_src"][tm["donor"]], tm["src"])
    assert np.array_equal(tm["dk_cls"][tm["dk"]], tm["cls"])
    assert np.array_equal(tm["dk_donor"][tm["dk"]], tm["donor"])
    tr_src_of_donor = np.zeros(tr_di["n_donor"], dtype=int)
    tr_src_of_donor[tr_di["donor"]] = tr_di["src"]
    assert np.array_equal(tm["n_train_donor_per_src"], np.bincount(tr_src_of_donor, minlength=d["n_src"]))
    tr_cls_of_dk = np.zeros(tr_di["n_dk"], dtype=int)
    tr_cls_of_dk[tr_di["dk"]] = tr_di["cls"]
    assert np.array_equal(tm["n_train_dk_per_cls"], np.bincount(tr_cls_of_dk, minlength=d["n_cls"]))
    assert abs(tr_di["log_lib_centered"].mean()) < 1e-12
    centre = d["log_lib_centered"][tr].mean()
    assert np.allclose(tm["depth"], d["log_lib_centered"][te] - centre)


def test_split_design_refuses_a_held_out_operator_absent_from_training():
    d = toy_design(3)
    d["op"] = d["op"].copy()
    d["op"][d["donor"] == 0] = d["n_op"]          # a new operator seen only by donor 0
    d["n_op"] += 1
    with pytest.raises(ValueError, match="op levels"):
        PPC.split_design(d, [0])
    PPC.split_design(d, [1])                      # holding out another donor is fine


# ---------------------------------------------------------------- statistics

def test_ppc_statistics_on_a_hand_computed_matrix():
    y = np.array([[1, 2, 1], [2, 4, -1], [3, 6, 1], [4, 8, -1], [5, 10, 1], [6, 12, -1]], dtype=float)
    meta = dict(cls=np.array([0, 0, 0, 1, 1, 1]), donor=np.array([0, 0, 1, 1, 2, 2]),
                op=np.array([0, 1, 0, 1, 0, 1]), src=np.array([0, 0, 0, 0, 1, 1]))
    st = PPC.ppc_statistics(y, meta, detection=True, min_class_cells=3)
    assert np.allclose(st["gene_mean"], [3.5, 7.0, 0.0])
    assert np.allclose(st["gene_var"], [35 / 12, 35 / 3, 1.0])
    assert np.allclose(st["gene_detection"], [1.0, 1.0, 0.5])
    assert np.allclose(st["donor_heterogeneity_gene"], [8 / 3, 32 / 3, 0.0])
    assert np.isclose(st["donor_heterogeneity"], 40 / 9)
    assert np.allclose(st["between_class_dispersion_gene"], [2.25, 9.0, 1 / 9])
    assert np.isclose(st["between_class_dispersion"], (2.25 + 9.0 + 1 / 9) / 3)
    assert np.allclose(st["within_class_dispersion_gene"], [2 / 3, 8 / 3, 8 / 9])
    assert np.isclose(st["within_class_dispersion"], 38 / 27)
    assert np.isclose(st["between_within_ratio"], ((2.25 + 9.0 + 1 / 9) / 3) / (38 / 27))
    assert np.allclose(st["operator_heterogeneity_gene"], [0.25, 1.0, 1.0])
    assert np.isclose(st["operator_heterogeneity"], 0.75)
    assert np.allclose(st["source_heterogeneity_gene"], [2.25, 9.0, 0.0])
    assert np.isclose(st["source_heterogeneity"], 3.75)
    # pooled |corr|: genes 0,1 are collinear (1), gene 2 correlates -3/sqrt(105) with both; median is the latter
    assert np.isclose(st["pooled_median_abs_corr"], 3 / np.sqrt(105), rtol=1e-6)
    # within each class gene 2 is uncorrelated with genes 0 and 1, so each class median is 0
    assert abs(st["within_class_median_abs_corr"]) < 1e-9
    # the 200-cell class floor of the T5 builder leaves no qualifying class here; fewer than 3 genes, no corr
    assert np.isnan(PPC.ppc_statistics(y, meta)["within_class_median_abs_corr"])
    st2 = PPC.ppc_statistics(y[:, :2], meta)
    assert "pooled_median_abs_corr" not in st2 and "gene_detection" not in st2


# ---------------------------------------------------------------- coverage

def test_coverage_quantiles_intervals_ties_and_undefined_values():
    k = np.arange(100, dtype=float)
    reps = [dict(s=k_, g=np.array([k_, 2 * k_]), v=(k_ if k_ % 2 == 0 else np.nan), t=1.0, u=k_) for k_ in k]
    obs = dict(s=50.0, g=np.array([3.0, 200.0]), v=50.0, t=1.0, u=np.nan)
    cov = PPC.coverage(obs, reps, level=0.9)
    s = cov["statistics"]
    assert s["s"]["kind"] == "scalar" and np.isclose(s["s"]["predictive_quantile"], 50.5 / 100)
    assert np.isclose(s["s"]["interval_lo"], 4.95) and np.isclose(s["s"]["interval_hi"], 94.05) and s["s"]["inside"]
    assert s["g"]["kind"] == "per_gene"
    assert np.allclose(s["g"]["predictive_quantile"], [0.035, 1.0]) and s["g"]["inside"] == [False, False]
    assert cov["share_inside"]["g"] == 0.0 and cov["share_inside"]["s"] == 1.0
    # NaN replicates are dropped for that unit: 50 even values 0..98
    assert s["v"]["n_replicates_valid"] == 50 and np.isclose(s["v"]["predictive_quantile"], 25.5 / 50)
    assert np.isclose(s["v"]["interval_lo"], 4.9) and np.isclose(s["v"]["interval_hi"], 93.1)
    # ties: a degenerate predictive at the observed value sits at the mid-rank and inside the closed interval
    assert s["t"]["predictive_quantile"] == 0.5 and s["t"]["inside"]
    # an undefined observed value is never inside and stays in the denominator
    assert s["u"]["inside"] is False and s["u"]["n_undefined"] == 1 and cov["share_inside"]["u"] == 0.0
    json.dumps(cov)


# ---------------------------------------------------------------- prediction

def _fake_samples(S, G, **sites):
    out = dict(mu=np.zeros((S, G)), logsd_res=np.full((S, G), -60.0))
    out.update(sites)
    return out


def test_predict_new_donors_rebuilds_the_fitted_part_exactly():
    S, G = 3, 2
    rng = np.random.default_rng(0)
    mu, b = rng.normal(size=(S, G)), rng.normal(size=(S, G))
    a_cls, a_src, a_op = rng.normal(size=(S, 2, G)), rng.normal(size=(S, 2, G)), rng.normal(size=(S, 1, G))
    samples = _fake_samples(S, G, mu=mu, b_depth=b, a_cls=a_cls, a_src=a_src, a_op=a_op,
                            logsd_donor=np.full((S, G), -60.0), logsd_dk=np.full((S, G), -60.0))
    B = np.array([[1.0], [-1.0]]) / np.sqrt(2)                   # two operators within one source
    tm = dict(n=4, cls=np.array([0, 1, 0, 1]), src=np.array([0, 0, 1, 1]), op=np.array([0, 1, 0, 1]),
              donor=np.array([0, 0, 1, 1]), dk=np.array([0, 1, 2, 3]), n_donor=2, n_dk=4,
              donor_src=np.array([0, 1]), dk_cls=np.array([0, 1, 0, 1]),
              n_train_donor_per_src=np.array([3, 3]), n_train_dk_per_cls=np.array([5, 5]))
    depth = np.array([-0.5, 0.0, 0.5, 1.0])
    yrep = PPC.predict_new_donors(samples, dict(basis=dict(op=B)), tm, depth, "gaussian",
                                  np.random.default_rng(1), n_draws=None)
    op_eff = np.einsum("lk,dkg->dlg", B, a_op)
    eta = (mu[:, None] + b[:, None] * depth[None, :, None] + a_cls[:, tm["cls"]] + a_src[:, tm["src"]]
           + op_eff[:, tm["op"]])
    assert yrep.shape == (S, 4, G) and np.allclose(yrep, eta, atol=1e-12)
    # Bernoulli at |eta| = 50 is deterministic; thinning keeps evenly spaced draws
    big = dict(mu=np.where(np.arange(G) == 0, 50.0, -50.0)[None].repeat(S, 0))
    yb = PPC.predict_new_donors(big, {}, tm, depth, "bernoulli", np.random.default_rng(2), 2, components=())
    assert yb.shape == (2, 4, G) and (yb[..., 0] == 1).all() and (yb[..., 1] == 0).all()
    assert PPC.thin_indices(10, 4).tolist() == [0, 2, 5, 7] and PPC.thin_indices(3, 10).tolist() == [0, 1, 2]


@pytest.mark.parametrize("parent_mean_draw", [True, False])
def test_new_donor_effects_carry_the_parent_mean_uncertainty(parent_mean_draw):
    """sd = 1. Donors 0, 1 are new in a source with 4 training donors, donor 2 in a source with 1: with the
    parent-mean draw the variances are 1 + 1/4 and 1 + 1/1, and new donors of one source covary by 1/4."""
    S = 40_000
    samples = _fake_samples(S, 1, logsd_donor=np.zeros((S, 1)))
    tm = dict(n=3, donor=np.array([0, 1, 2]), n_donor=3, donor_src=np.array([0, 0, 1]),
              n_train_donor_per_src=np.array([4, 1]))
    y = PPC.predict_new_donors(samples, {}, tm, np.zeros(3), "gaussian", np.random.default_rng(5), None,
                               components=("donor",), parent_mean_draw=parent_mean_draw)[:, :, 0]
    c = np.cov(y, rowvar=False)
    want = np.array([[1.25, 0.25, 0], [0.25, 1.25, 0], [0, 0, 2.0]]) if parent_mean_draw else np.eye(3)
    assert np.allclose(c, want, atol=0.05)


# ---------------------------------------------------------------- end to end (NumPyro)

def test_heldout_coverage_is_high_when_right_and_low_for_donor_heterogeneity_when_donors_are_dropped():
    pytest.importorskip("numpyro")
    import v79_simulate as SIM
    d = toy_design(11, donors_per_src=(8, 8, 8))
    scenario = dict(cls=0.6, src=0.3, op=0.4, donor=1.5, dk=0.3, res=1.0)       # heavy donor effects
    y = SIM.simulate(d, scenario, 4, "gaussian", seed=21)["y"]
    kw = dict(k=2, seed=20261009, chains=2, warmup=200, draws=200, n_pred_draws=200, max_tree_depth=6, retry=False)
    right = PPC.run_heldout(d, y, "gaussian", **kw)
    wrong = PPC.run_heldout(d, y, "gaussian", components=("cls", "src", "op"), **kw)
    json.dumps(right), json.dumps(wrong)
    assert right["components"] == list(PPC.COMPONENTS) and wrong["components"] == ["cls", "src", "op"]
    assert len(right["folds"]) == 2 and right["n_genes"] == 4
    assert right["pooled_share_inside"]["gene_mean"]["share_inside"] >= 0.6
    r = right["pooled_share_inside"]["donor_heterogeneity_gene"]["share_inside"]
    w = wrong["pooled_share_inside"]["donor_heterogeneity_gene"]["share_inside"]
    assert w < r and w <= 0.25
    # the failure is in the direction the misspecification implies: observed donor spread above the replicates
    q = [v for f in wrong["folds"] for v in f["coverage"]["statistics"]["donor_heterogeneity_gene"]["predictive_quantile"]]
    assert np.mean(np.asarray(q) > 0.95) >= 0.75


# ---------------------------------------------------------------- positive-count families (Phase C)

@pytest.mark.parametrize("family", ["ztnb", "lognormal"])
def test_positive_replicates_follow_the_scored_distribution(family):
    """The replicate sampler and the scoring pmf describe the same zero-truncated law: replicates are >= 1 and
    their empirical frequencies match exp(positive_logpmf) for the same draw."""
    n = 200_000
    eta = np.full((n, 1), -7.0)
    offset = np.full(n, np.log(8000.0))                              # mean about 7.3 counts
    draw = dict(logphi=np.array([np.log(1.5)]), logsd_res=np.array([np.log(0.8)]))
    rep = PPC.replicate_positive(family, eta, offset, draw, np.random.default_rng(3))[:, 0]
    assert rep.min() >= 1 and np.all(rep == np.round(rep))
    k = np.arange(1, 8, dtype=float)
    pmf = np.exp(PPC.positive_logpmf(family, k[:, None], eta[:7], offset[:7], draw))[:, 0]
    freq = np.array([(rep == v).mean() for v in k])
    assert np.allclose(freq, pmf, atol=0.004), (freq, pmf)


def test_signed_dependence_and_spectrum_on_a_constructed_matrix():
    rng = np.random.default_rng(0)
    z = rng.standard_normal((4000, 1))
    H = np.hstack([z + 0.1 * rng.standard_normal((4000, 1)), z + 0.1 * rng.standard_normal((4000, 1)),
                   -z + 0.1 * rng.standard_normal((4000, 1)), rng.standard_normal((4000, 1))])
    st = PPC._signed_and_spectrum(H)
    # pairs: (0,1) +, (0,2) -, (1,2) -, and three near-zero pairs with gene 3 of either sign
    assert st["median_positive_corr"] > 0 and st["median_negative_corr"] < -0.5
    assert 0.6 < st["top1_eigen_share"] < 0.8 and st["top3_eigen_share"] > 0.99


def test_positive_statistics_use_detected_cells_only():
    counts = np.array([[1, 0], [3, 0], [0, 0], [9, 0]], dtype=float)
    mask = counts > 0
    meta = dict(donor=np.array([0, 0, 1, 1]), op=np.array([0, 1, 0, 1]))
    st = PPC.positive_statistics(counts, mask, meta)
    assert st["pos_q50"][0] == 3 and np.isnan(st["pos_q50"][1])
    assert np.isclose(st["pos_mean_log"][0], np.log(27) / 3)
    assert np.isclose(st["pos_dispersion_index"][0], np.var([1, 3, 9]) / np.mean([1, 3, 9]))
    assert np.isclose(st["pos_tail_ratio_q95_q50"][0], np.quantile([1, 3, 9], 0.95) / 3)
    # donor means of log count: donor 0 (log1+log3)/2, donor 1 log9
    d = np.array([np.log(3) / 2, np.log(9)])
    assert np.isclose(st["pos_donor_heterogeneity_gene"][0], d.var())
    cov = PPC.coverage({"pos_q50": st["pos_q50"]}, [{"pos_q50": np.array([3.0, 1.0])}] * 5)
    assert cov["statistics"]["pos_q50"]["n_undefined"] == 1          # a gene with no detected cell is not inside


# ---------------------------------------------------------------- donor-class support (Q5)

def _lpd_rec(sums, ns, diagnosed=True):
    folds = [dict(heldout_lpd=dict(donor_original_code=[0, 1], per_donor_sum=sums[:2], per_donor_n=ns[:2])),
             dict(heldout_lpd=dict(donor_original_code=[2, 3], per_donor_sum=sums[2:], per_donor_n=ns[2:]))]
    return dict(folds=folds, all_folds_diagnosed=diagnosed)


def test_donor_class_support_uses_the_clustered_two_se_rule():
    ns = [100, 100, 100, 100]
    big = PPC.heldout_lpd_comparison(_lpd_rec([10, 11, 9, 10], ns), _lpd_rec([0, 0, 0, 0], ns))
    assert big["supported"] and np.isclose(big["mean_difference_per_observation"], 40 / 400)
    noisy = PPC.heldout_lpd_comparison(_lpd_rec([10, -9, 8, -8], ns), _lpd_rec([0, 0, 0, 0], ns))
    assert not noisy["supported"]
    undiag = PPC.heldout_lpd_comparison(_lpd_rec([10, 11, 9, 10], ns, diagnosed=False), _lpd_rec([0, 0, 0, 0], ns))
    assert not undiag["supported"]
    with pytest.raises(ValueError):
        PPC.heldout_lpd_comparison(_lpd_rec([1, 1, 1, 1], ns), _lpd_rec([0, 0, 0, 0], [100, 100, 100, 99]))


# ---------------------------------------------------------------- network and conditioned geometry

def test_class_driven_edges_vanish_when_conditioned_on_class():
    rng = np.random.default_rng(4)
    n = 1200
    cls = np.repeat([0, 1], n // 2)
    shift = np.where(cls == 1, 3.0, 0.0)[:, None]
    H = shift + rng.standard_normal((n, 4))                    # 4 genes that differ only by class
    meta = dict(cls=cls, src=np.zeros(n, dtype=int), donor=np.arange(n) % 30, op=np.arange(n) % 5,
                depth=rng.standard_normal(n))
    st = PPC.ppc_statistics(H, meta, min_class_cells=200)
    assert st["pooled_frac_abs_gt_0p3"] == 1.0 and st["pooled_mean_degree"] == 3.0
    assert st["pooled_transitivity"] == pytest.approx(1.0)
    assert st["within_class_frac_abs_gt_0p3"] == 0.0 and st["within_class_mean_degree"] == 0.0
    assert st["within_source_frac_abs_gt_0p3"] == 1.0           # one source: conditioning on it changes nothing
    assert st["within_depth_tertile_frac_abs_gt_0p3"] == 1.0    # depth unrelated to the class shift


def test_network_signed_edges():
    rng = np.random.default_rng(5)
    z = rng.standard_normal((3000, 1))
    H = np.hstack([z, z + 0.1 * rng.standard_normal((3000, 1)), -z + 0.1 * rng.standard_normal((3000, 1))])
    net = PPC._network(H)
    # pairs: (0,1) positive, (0,2) and (1,2) negative; off-diagonal entries counted in both orders
    assert net["frac_pos_gt_0p3"] == pytest.approx(1 / 3) and net["frac_neg_lt_m0p3"] == pytest.approx(2 / 3)
    assert net["mean_degree"] == 2.0 and net["transitivity"] == pytest.approx(1.0)
