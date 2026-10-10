#!/usr/bin/env python3
"""V79 held-out-donor posterior predictive checks (contract BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1, validation).

Donors are split into k folds stratified by source with a frozen seed. For each fold the variance-component
model is fitted on the remaining donors; the held-out cells are then replicated from the posterior with their
operator, class and source effects taken from the fit and NEW donor and donor-class effects drawn from the
fitted spreads. For every statistic the observed held-out value's position in its central 90% predictive
interval is reported; a model that fails a check is reported as inadequate for that statistic, never tuned to
pass it. The correlation checks are expected to fail for phases A-C (no gene-gene residual dependence).

New donor and donor-class effects. In v79_models a donor effect is B theta with theta ~ N(0, sd) on an
orthonormal within-source sum-to-zero basis B, so the realized effects have the law of n iid N(0, sd^2) donor
values centred on their source mean, the mean itself being absorbed into the source (fixed) effect. Read as
that exchangeable superpopulation, a new donor j in source s has effect u_j - ubar_s relative to the fitted
source effect, u_j ~ N(0, sd^2) and ubar_s ~ N(0, sd^2 / n_s) (n_s = training donors in s; with a flat source
prior the data leave ubar_s at its prior), drawn once per draw, source and gene and shared by every new donor
of that source. That is the default (parent_mean_draw=True): marginal variance sd^2 (1 + 1/n_s), covariance
sd^2 / n_s between new donors of one source. parent_mean_draw=False gives the plain N(0, sd^2) draw. The same
holds for donor-class effects within class. Operators, classes and sources of held-out cells must all occur in
training: their effects are taken from the fit, never invented.

Genes are positions in the fitted matrix; nothing here reads or writes gene, address or donor identity (donors
appear only as integer design codes). numpy (and scipy through v79_geometry) at import; JAX/NumPyro are
imported only inside run_heldout.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import v79_geometry as GEO  # noqa: E402  the builders' correlation (constant column -> 0, 1e-9 guard)

COMPONENTS = ("cls", "src", "op", "donor", "dk")      # checked against v79_models.COMPONENTS in run_heldout
LEVEL = 0.9                                            # contract: central 90% predictive interval
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)             # distribution checks (depth, detected features, counts)
MIN_CLASS_CELLS = GEO.TC.MIN_CLASS_CELLS               # T5 builder: a class qualifies by cell count (200)
GROUPINGS = (("donor", "donor_heterogeneity"), ("op", "operator_heterogeneity"),
             ("src", "source_heterogeneity"), ("cls", "between_class_dispersion"))
NOTES = ("class composition is conditioned on (class is a covariate), so it is reproduced by construction and "
         "is not a check of these models",
         "correlation statistics are expected to fail for the variance-component models (no gene-gene residual "
         "dependence; contract validation.expected_failure); that failure is reported, never hidden",
         "per-gene coverage indicators within a fold share the replicated design and new-effect draws, so the "
         "share inside is not a binomial proportion")


# ---------------------------------------------------------------- folds and split

def donor_source(di: dict) -> np.ndarray:
    """Source code of every donor code (-1 for a code with no cells). A donor in two sources is an error."""
    don, src = np.asarray(di["donor"], dtype=np.int64), np.asarray(di["src"], dtype=np.int64)
    pairs = np.unique(np.stack([don, src], 1), axis=0)
    if len(np.unique(pairs[:, 0])) != len(pairs):
        raise ValueError("a donor sits in two sources; folds stratified by source are undefined")
    out = np.full(int(di["n_donor"]), -1, dtype=np.int64)
    out[pairs[:, 0]] = pairs[:, 1]
    return out


def donor_folds(di: dict, k: int, seed: int) -> list:
    """k folds of donor codes, stratified by source: each source's donors are permuted with one generator
    (sources in code order) and dealt round-robin, continuing the deal across sources so that fold sizes
    differ by at most one overall and each fold holds floor or ceil of n_s / k donors of every source.
    Donor codes come from sorted donor ids (v79_data.encode), so folds depend on donor identity, not row order."""
    if int(k) < 2:
        raise ValueError("k must be at least 2")
    dsrc = donor_source(di)
    rng = np.random.default_rng(seed)
    fold_of = np.full(len(dsrc), -1, dtype=np.int64)
    offset = 0
    for s in range(int(di["n_src"])):
        donors = np.where(dsrc == s)[0]
        if len(donors) == 0:
            continue
        if len(donors) < k:
            raise ValueError(f"source {s} has {len(donors)} donors, fewer than k={k} folds")
        perm = rng.permutation(donors)
        fold_of[perm] = (offset + np.arange(len(perm))) % k
        offset += len(perm)
    return [np.sort(np.where(fold_of == f)[0]) for f in range(k)]


def _parent_of(child: np.ndarray, parent: np.ndarray, n_child: int) -> np.ndarray:
    out = np.full(n_child, -1, dtype=np.int64)
    for c, p in zip(child.tolist(), parent.tolist()):
        if out[c] not in (-1, p):
            raise ValueError("a child level belongs to two parents")
        out[c] = p
    return out


def split_design(di: dict, held_out_donors) -> tuple:
    """(train_di, train_cells_index, test_cells_index, test_maps).

    train_di keeps class, source and operator codes and level counts, re-encodes donor and donor-class codes
    contiguously over the training cells (in original code order), and re-centres log depth on the training
    cells. Every class, source and operator must occur in training cells (else ValueError): held-out cells take
    those effects from the fit. test_maps gives each held-out cell its class, source and operator codes, a
    held-out donor index and a held-out donor-class index (0..n-1, original code order), the parent of each new
    level, the number of training levels per parent (for the parent-mean draw) and the held-out depth on the
    training centring."""
    held = np.unique(np.asarray(held_out_donors, dtype=np.int64))
    don, dk = np.asarray(di["donor"], dtype=np.int64), np.asarray(di["dk"], dtype=np.int64)
    is_test = np.isin(don, held)
    if not is_test.any() or is_test.all():
        raise ValueError("held-out donors must leave both training and held-out cells")
    tr, te = np.where(~is_test)[0], np.where(is_test)[0]
    keep = {}
    for x, n_key in (("cls", "n_cls"), ("src", "n_src"), ("op", "n_op")):
        codes = np.asarray(di[x], dtype=np.int64)
        in_train = np.zeros(int(di[n_key]), dtype=bool)
        in_train[codes[tr]] = True
        missing = np.setdiff1d(np.unique(codes[te]), np.where(in_train)[0])
        if missing.size:
            raise ValueError(f"{x} levels {missing.tolist()} occur in held-out cells but not in training cells")
        if not in_train.all():
            raise ValueError(f"{x} levels {np.where(~in_train)[0].tolist()} have no training cells")
        keep[x] = codes
    tr_don_orig, tr_don = np.unique(don[tr], return_inverse=True)
    tr_dk_orig, tr_dk = np.unique(dk[tr], return_inverse=True)
    te_don_orig, te_don = np.unique(don[te], return_inverse=True)
    te_dk_orig, te_dk = np.unique(dk[te], return_inverse=True)
    if np.intersect1d(tr_dk_orig, te_dk_orig).size:
        raise ValueError("a donor-class level occurs in both training and held-out cells")
    dsrc = donor_source(di)
    dk_cls = _parent_of(dk, keep["cls"], int(di["n_dk"]))
    dk_don = _parent_of(dk, don, int(di["n_dk"]))
    llc = np.asarray(di["log_lib_centered"], dtype=np.float64)
    centre = float(llc[tr].mean())
    train_di = dict(n=int(len(tr)), cls=keep["cls"][tr], src=keep["src"][tr], op=keep["op"][tr],
                    donor=tr_don.astype(np.int64), dk=tr_dk.astype(np.int64),
                    n_cls=int(di["n_cls"]), n_src=int(di["n_src"]), n_op=int(di["n_op"]),
                    n_donor=int(len(tr_don_orig)), n_dk=int(len(tr_dk_orig)),
                    log_lib_centered=llc[tr] - centre,
                    donor_original_code=tr_don_orig, dk_original_code=tr_dk_orig)
    if "log_lib" in di:
        train_di["log_lib"] = np.asarray(di["log_lib"], dtype=np.float64)[tr]
    for key in ("class_levels", "source_levels"):
        if key in di:
            train_di[key] = di[key]
    te_dk_don = np.searchsorted(te_don_orig, dk_don[te_dk_orig])
    test_maps = dict(n=int(len(te)), cls=keep["cls"][te], src=keep["src"][te], op=keep["op"][te],
                     donor=te_don.astype(np.int64), dk=te_dk.astype(np.int64),
                     n_donor=int(len(te_don_orig)), n_dk=int(len(te_dk_orig)),
                     donor_src=dsrc[te_don_orig], dk_cls=dk_cls[te_dk_orig], dk_donor=te_dk_don.astype(np.int64),
                     n_train_donor_per_src=np.bincount(dsrc[tr_don_orig], minlength=int(di["n_src"])),
                     n_train_dk_per_cls=np.bincount(dk_cls[tr_dk_orig], minlength=int(di["n_cls"])),
                     depth=llc[te] - centre, depth_centre=centre,
                     donor_original_code=te_don_orig, dk_original_code=te_dk_orig)
    return train_di, tr, te, test_maps


# ---------------------------------------------------------------- posterior prediction

def thin_indices(n_total: int, n_draws) -> np.ndarray:
    """n_draws evenly spaced distinct indices of 0..n_total-1 (all of them when n_draws is None or larger)."""
    if n_draws is None or int(n_draws) >= n_total:
        return np.arange(n_total)
    if int(n_draws) < 1:
        raise ValueError("n_draws must be positive")
    return (np.arange(int(n_draws)) * n_total) // int(n_draws)


def predict_new_donors(samples: dict, train_design: dict, test_maps: dict, depth_test, likelihood: str,
                       rng: np.random.Generator, n_draws, components=COMPONENTS,
                       parent_mean_draw: bool = True) -> np.ndarray:
    """Posterior predictive replicate (draws x held-out cells x genes) from flattened posterior samples.

    eta = mu + b_depth * depth + a_cls[cls] + a_src[src] + (basis_op @ a_op)[op] + new donor + new donor-class;
    the Gaussian adds N(0, exp(logsd_res)), the Bernoulli draws y ~ Bernoulli(sigmoid(eta)). Components not
    in `components` contribute nothing (they were not fitted). New effects: see the module docstring.
    The positive-count families need the offset and the detected cells: see positive_logpmf, replicate_positive."""
    eta, sel = heldout_eta(samples, train_design, test_maps, depth_test, rng, n_draws, components, parent_mean_draw)
    if likelihood == "gaussian":
        sd = np.exp(np.asarray(samples["logsd_res"], dtype=np.float64)[sel])
        return eta + rng.standard_normal(eta.shape) * sd[:, None, :]
    if likelihood == "bernoulli":
        p = 0.5 * (1.0 + np.tanh(0.5 * eta))                                      # sigmoid, overflow-free
        return (rng.random(eta.shape) < p).astype(np.float64)
    raise ValueError(f"unknown likelihood {likelihood!r}")


def heldout_eta(samples: dict, train_design: dict, test_maps: dict, depth_test, rng: np.random.Generator, n_draws,
                components=COMPONENTS, parent_mean_draw: bool = True) -> tuple:
    """(eta, selected draw indices): the linear predictor of the held-out cells (draws x cells x genes) with the
    fitted fixed and operator effects and new donor and donor-class effects (module docstring)."""
    mu = np.asarray(samples["mu"], dtype=np.float64)
    if mu.ndim != 2:
        raise ValueError("samples must be flattened (draws x genes); use v79_models.flatten_chains")
    sel = thin_indices(mu.shape[0], n_draws)
    D, G, N = len(sel), mu.shape[1], int(test_maps["n"])
    depth = np.asarray(depth_test, dtype=np.float64)
    if depth.shape != (N,):
        raise ValueError(f"depth_test has shape {depth.shape}, expected ({N},)")
    tm = test_maps

    def site(name):
        return np.asarray(samples[name], dtype=np.float64)[sel]

    eta = np.repeat(mu[sel][:, None, :], N, axis=1)
    if "b_depth" in samples:
        eta += site("b_depth")[:, None, :] * depth[None, :, None]
    for x in ("cls", "src"):
        if x in components:
            eta += site(f"a_{x}")[:, np.asarray(tm[x]), :]
    if "op" in components:
        B = np.asarray(train_design["basis"]["op"], dtype=np.float64)
        eta += np.einsum("lk,dkg->dlg", B, site("a_op"))[:, np.asarray(tm["op"]), :]
    for x, parent_of_new, n_train in (("donor", "donor_src", "n_train_donor_per_src"),
                                      ("dk", "dk_cls", "n_train_dk_per_cls")):
        if x not in components:
            continue
        sd = np.exp(site(f"logsd_{x}"))                                           # draws x genes
        new = rng.standard_normal((D, int(tm[f"n_{x}"]), G)) * sd[:, None, :]
        if parent_mean_draw:
            n_par = np.maximum(np.asarray(tm[n_train], dtype=np.float64), 1.0)
            bar = rng.standard_normal((D, len(n_par), G)) * sd[:, None, :] / np.sqrt(n_par)[None, :, None]
            new = new - bar[:, np.asarray(tm[parent_of_new]), :]
        eta += new[:, np.asarray(tm[x]), :]
    return eta, sel


def positive_logpmf(family: str, y, eta, offset, draw: dict):
    """log P(Y = y | Y > 0) of held-out positive counts for one posterior draw, on the count scale for both
    families (v79_phase_c). eta: cells x genes for that draw; offset: cells; draw: that draw's per-gene
    parameters (logsd_res for the log-normal, logphi for the zero-truncated negative binomial)."""
    import v79_phase_c as PC
    m = eta + np.asarray(offset, dtype=np.float64)[:, None]
    if family == "ztnb":
        return PC.ztnb_logpmf(y, np.exp(m), np.exp(np.asarray(draw["logphi"], dtype=np.float64))[None, :])
    if family == "lognormal":
        return PC.lognormal_count_logpmf(y, m, np.exp(np.asarray(draw["logsd_res"], dtype=np.float64))[None, :])
    raise ValueError(f"unknown positive family {family!r}")


def replicate_positive(family: str, eta, offset, draw: dict, rng: np.random.Generator) -> np.ndarray:
    """One replicate of positive counts (cells x genes) from the zero-truncated family by inverse CDF above the
    zero mass, so every value is at least 1; the caller holds the detected-cell pattern fixed."""
    from scipy.stats import nbinom, norm
    m = eta + np.asarray(offset, dtype=np.float64)[:, None]
    if family == "ztnb":
        phi = np.exp(np.asarray(draw["logphi"], dtype=np.float64))[None, :]
        p = phi / (phi + np.exp(m))
        p0 = p ** phi
        u = p0 + (1.0 - p0) * rng.random(m.shape)
        return np.maximum(nbinom.ppf(np.minimum(u, 1.0 - 1e-12), phi, p), 1.0)
    if family == "lognormal":
        sd = np.exp(np.asarray(draw["logsd_res"], dtype=np.float64))[None, :]
        lo = norm.cdf((np.log(0.5) - m) / sd)
        u = lo + (1.0 - lo) * rng.random(m.shape)
        return np.maximum(np.floor(np.exp(m + sd * norm.ppf(np.minimum(u, 1.0 - 1e-12))) + 0.5), 1.0)
    raise ValueError(f"unknown positive family {family!r}")


# ---------------------------------------------------------------- statistics

def make_plan(cells_meta: dict) -> dict:
    """Group-averaging matrices for the statistics (reused across replicates of the same cells)."""
    if cells_meta.get("_plan"):
        return cells_meta
    plan = dict(_plan=True)
    for x, _ in GROUPINGS:
        codes = np.asarray(cells_meta[x])
        _, inv, cnt = np.unique(codes, return_inverse=True, return_counts=True)
        A = np.zeros((len(cnt), len(codes)))
        A[inv, np.arange(len(codes))] = 1.0 / cnt[inv]
        plan[x] = dict(A=A, inv=inv)
    cls = np.asarray(cells_meta["cls"])
    plan["class_cells"] = [np.where(cls == c)[0] for c in np.unique(cls)]
    return plan


def _median_abs_corr(H: np.ndarray) -> float:
    """Median |off-diagonal correlation| as the frozen builders compute it (v79_geometry, uniform weights)."""
    n = H.shape[0]
    C = GEO.weighted_corr(H, np.full(n, 1.0 / n))
    return float(np.quantile(np.abs(C[~np.eye(C.shape[0], dtype=bool)]), 0.5))


def _signed_and_spectrum(H: np.ndarray) -> dict:
    """Signed dependence and eigenspectrum of the pooled correlation (builders' convention): share of gene pairs
    correlated positively, median positive and median negative correlation, and the share of the trace carried
    by the largest eigenvalue and by the top three."""
    n = H.shape[0]
    C = GEO.weighted_corr(H, np.full(n, 1.0 / n))
    off = C[~np.eye(C.shape[0], dtype=bool)]
    pos, neg = off[off > 0], off[off < 0]
    ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    tr = float(ev.sum())
    return dict(share_positive_corr=float((off > 0).mean()),
                median_positive_corr=float(np.median(pos)) if pos.size else float("nan"),
                median_negative_corr=float(np.median(neg)) if neg.size else float("nan"),
                top1_eigen_share=float(ev[0] / tr) if tr > 0 else float("nan"),
                top3_eigen_share=float(ev[:3].sum() / tr) if tr > 0 else float("nan"))


def positive_statistics(counts, mask, cells_meta: dict) -> dict:
    """Phase C statistics over each gene's detected cells only (the detected pattern is held fixed): per gene
    the positive-count quantiles and mean log count, and the donor and operator heterogeneity of the mean log
    positive count (variance across groups with at least one detected cell, unweighted, ddof 0). A gene with no
    detected cell gives NaN, which coverage counts as not inside."""
    y = np.asarray(counts, dtype=np.float64)
    w = np.asarray(mask, dtype=bool)
    G = y.shape[1]
    out = {f"pos_q{int(round(q * 100)):02d}": np.full(G, np.nan) for q in QUANTILES}
    out["pos_mean_log"] = np.full(G, np.nan)
    for name in ("donor", "op"):
        out[f"pos_{name}_heterogeneity_gene"] = np.full(G, np.nan)
    for g in range(G):
        v = y[w[:, g], g]
        if v.size == 0:
            continue
        for q in QUANTILES:
            out[f"pos_q{int(round(q * 100)):02d}"][g] = np.quantile(v, q)
        lv = np.log(v)
        out["pos_mean_log"][g] = lv.mean()
        for name in ("donor", "op"):
            codes = np.asarray(cells_meta[name])[w[:, g]]
            _, inv = np.unique(codes, return_inverse=True)
            means = np.bincount(inv, weights=lv) / np.bincount(inv)
            out[f"pos_{name}_heterogeneity_gene"][g] = means.var()
    return out


def ppc_statistics(y, cells_meta: dict, detection: bool = False, min_class_cells: int = MIN_CLASS_CELLS) -> dict:
    """Statistics of a cells x genes matrix. Per gene (arrays over gene positions): gene_mean, gene_var
    (ddof 0), gene_detection (share of cells > 0; only when detection=True), and <name>_gene for each grouping
    below. Scalars (averaged over genes):
      donor_heterogeneity        variance across donors of the donor mean
      operator_heterogeneity     variance across operators of the operator mean
      source_heterogeneity       variance across sources of the source mean
      between_class_dispersion   variance across classes of the class mean
      within_class_dispersion    mean over cells of (y - own class mean)^2 (pooled within-class variance)
      between_within_ratio       between_class_dispersion / within_class_dispersion
    Group variances are unweighted over the groups present, ddof 0. With at least 3 genes:
      pooled_median_abs_corr          median |corr| over gene pairs, all cells
      within_class_median_abs_corr    unweighted mean over classes with >= min_class_cells cells of the
                                      per-class median |corr| (NaN when no class qualifies)
    Correlations use the builders' convention (a constant gene correlates 0 with every other)."""
    y = np.asarray(y, dtype=np.float64)
    plan = make_plan(cells_meta)
    out = dict(gene_mean=y.mean(0), gene_var=y.var(0))
    for q in QUANTILES:
        out[f"gene_q{int(round(q * 100)):02d}"] = np.quantile(y, q, axis=0)
    if detection:
        out["gene_detection"] = (y > 0).mean(0)
    for x, name in GROUPINGS:
        per_gene = (plan[x]["A"] @ y).var(0)
        out[f"{name}_gene"] = per_gene
        out[name] = float(per_gene.mean())
        if x == "cls":
            class_means = plan[x]["A"] @ y
            within = ((y - class_means[plan[x]["inv"]]) ** 2).mean(0)
            out["within_class_dispersion_gene"] = within
            out["within_class_dispersion"] = float(within.mean())
    w = out["within_class_dispersion"]
    out["between_within_ratio"] = float(out["between_class_dispersion"] / w) if w > 0 else float("nan")
    if y.shape[1] >= 3:
        out["pooled_median_abs_corr"] = _median_abs_corr(y)
        out.update(_signed_and_spectrum(y))
        meds = [_median_abs_corr(y[idx]) for idx in plan["class_cells"] if len(idx) >= max(int(min_class_cells), 2)]
        out["within_class_median_abs_corr"] = float(np.mean(meds)) if meds else float("nan")
    return out


# ---------------------------------------------------------------- coverage

def _num(v):
    v = float(v)
    return v if np.isfinite(v) else None


def coverage(observed_stats: dict, replicated_stats_list, level: float = LEVEL) -> dict:
    """For each statistic (each gene position of a per-gene statistic): the observed value's predictive
    quantile (mid-rank: share of replicates below it plus half the share equal to it) and whether it lies in
    the closed central `level` interval [q_lo, q_hi] of the replicates (numpy linear quantiles). Replicates
    with an undefined (NaN) value are dropped for that unit; an undefined observed value or a unit with no
    defined replicate counts as NOT inside and is reported in n_undefined, so share_inside always has every
    unit in its denominator."""
    reps = list(replicated_stats_list)
    if not reps:
        raise ValueError("no replicated statistics")
    q_lo, q_hi = (1.0 - level) / 2.0, 1.0 - (1.0 - level) / 2.0
    stats, share = {}, {}
    for key in observed_stats:
        obs = np.asarray(observed_stats[key], dtype=np.float64)
        rep = np.stack([np.asarray(r[key], dtype=np.float64) for r in reps])
        if rep.shape[1:] != obs.shape:
            raise ValueError(f"{key}: replicate shape {rep.shape[1:]} differs from observed {obs.shape}")
        o1, r2 = obs.reshape(-1), rep.reshape(len(reps), -1)
        quant, lo, hi, inside, n_valid = [], [], [], [], []
        for j in range(o1.size):
            r = r2[:, j][np.isfinite(r2[:, j])]
            o = o1[j]
            n_valid.append(int(r.size))
            if r.size == 0 or not np.isfinite(o):
                quant.append(None), lo.append(None), hi.append(None), inside.append(False)
                continue
            a, b = np.quantile(r, [q_lo, q_hi])
            quant.append(float(((r < o).sum() + 0.5 * (r == o).sum()) / r.size))
            lo.append(float(a)), hi.append(float(b)), inside.append(bool(a <= o <= b))
        n_units = int(o1.size)
        n_inside = int(sum(inside))
        undefined = int(sum(1 for qv in quant if qv is None))
        scalar = obs.ndim == 0
        stats[key] = dict(kind="scalar" if scalar else "per_gene",
                          observed=_num(o1[0]) if scalar else [_num(v) for v in o1],
                          predictive_quantile=quant[0] if scalar else quant,
                          interval_lo=lo[0] if scalar else lo, interval_hi=hi[0] if scalar else hi,
                          inside=inside[0] if scalar else inside,
                          n_replicates_valid=n_valid[0] if scalar else n_valid,
                          n_units=n_units, n_inside=n_inside, n_undefined=undefined,
                          share_inside=n_inside / n_units if n_units else None)
        share[key] = stats[key]["share_inside"]
    return dict(level=level, n_replicates=len(reps), statistics=stats, share_inside=share)


# ---------------------------------------------------------------- orchestration

def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_jsonable(v) for v in obj.tolist()]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return _num(obj)
    return obj


def run_heldout(di: dict, y, likelihood: str, k: int, seed: int, chains: int, warmup: int, draws: int,
                n_pred_draws: int = 1000, components=None, target_accept: float = 0.9, max_tree_depth: int = 10,
                retry: bool = True, depth: bool = True, parent_mean_draw: bool = True, level: float = LEVEL,
                min_class_cells: int = MIN_CLASS_CELLS, only_folds=None) -> dict:
    """Held-out-donor posterior predictive checks over k source-stratified donor folds (fold seed `seed`).

    Per fold: fit vc_model on the training cells with v79_models.run_nuts (NUTS seed seed + 1 + fold; with
    retry=True the contract's rule: any divergence -> refit at the next target_accept of
    run_v79_inference.RETRY_ACCEPT), replicate the held-out cells from n_pred_draws evenly thinned posterior
    draws (one replicate per draw; draw i uses numpy generator [seed, fold, i], so results do not depend on
    batching), and compute coverage. The default of 1,000 replicates follows the contract's D1 precision
    rationale (quantile Monte Carlo error about 0.7 percentile points at the 5th and 95th). Diagnostics use
    run_v79_inference.diagnose and its thresholds; a fold that misses them is marked NOT_DIAGNOSED and its
    coverage must not be interpreted. only_folds runs a subset (one process per fold); merge_heldout pools the
    per-fold records. Returns a JSON-serializable record with genes as positions only."""
    import jax.numpy as jnp
    import v79_models as M
    import run_v79_inference as RI
    if tuple(M.COMPONENTS) != COMPONENTS:
        raise RuntimeError("v79_ppc.COMPONENTS disagrees with v79_models.COMPONENTS")
    comps = tuple(M.COMPONENTS if components is None else components)
    y = np.asarray(y, dtype=np.float32)
    if y.ndim != 2 or y.shape[0] != int(di["n"]):
        raise ValueError(f"y must be cells x genes with {di['n']} rows")
    detection = likelihood == "bernoulli"
    accepts = tuple(RI.RETRY_ACCEPT) if retry else (float(target_accept),)
    folds = donor_folds(di, k, seed)
    t_all = time.time()
    fold_recs, pooled = [], {}
    for f, held in enumerate(folds):
        if only_folds is not None and f not in set(only_folds):
            continue
        train_di, tr, te, tm = split_design(di, held)
        des = M.design_arrays(train_di)
        attempts, run = [], None
        for ta in accepts:
            kw = dict(design=des, y=jnp.asarray(y[tr]), likelihood=likelihood, components=comps, depth=depth)
            run = M.run_nuts(kw, n_chains=chains, warmup=warmup, draws=draws, seed=seed + 1 + f,
                             target_accept=ta, max_tree_depth=max_tree_depth)
            diag = RI.diagnose(run["samples"], likelihood, comps)
            ok = sum(run["divergences"]) == 0 and diag["worst_rhat"] <= RI.RHAT_MAX and diag["worst_ess"] >= RI.ESS_MIN
            attempts.append(dict(target_accept=ta, seconds=run["seconds"], divergences=run["divergences"],
                                 mean_steps=run["mean_steps"], worst_rhat=diag["worst_rhat"],
                                 worst_ess=diag["worst_ess"], diagnosed=bool(ok)))
            if sum(run["divergences"]) == 0:
                break
        flat = M.flatten_chains(run["samples"])
        sel = thin_indices(flat["mu"].shape[0], n_pred_draws)
        plan = make_plan(tm)
        obs = ppc_statistics(y[te], plan, detection, min_class_cells)
        reps = []
        t0 = time.time()
        yte = y[te].astype(np.float64)
        acc = None
        for i in sel.tolist():
            sub = {key: v[i:i + 1] for key, v in flat.items()}
            rng = np.random.default_rng([seed, f, i])
            # same generator order as predict_new_donors: new effects, then the observation draw
            eta, _ = heldout_eta(sub, des, tm, tm["depth"], rng, 1, comps, parent_mean_draw)
            if likelihood == "gaussian":
                sd = np.exp(np.asarray(sub["logsd_res"], dtype=np.float64))[:, None, :]
                yr = (eta + rng.standard_normal(eta.shape) * sd)[0]
                lp = -0.5 * ((yte - eta[0]) / sd[0]) ** 2 - np.log(sd[0]) - 0.5 * np.log(2 * np.pi)
            elif likelihood == "bernoulli":
                pr = 0.5 * (1.0 + np.tanh(0.5 * eta))
                yr = (rng.random(eta.shape) < pr).astype(np.float64)[0]
                lp = -(yte * np.logaddexp(0.0, -eta[0]) + (1.0 - yte) * np.logaddexp(0.0, eta[0]))
            else:
                raise ValueError(f"unknown likelihood {likelihood!r}")
            acc = lp if acc is None else np.logaddexp(acc, lp)
            reps.append(ppc_statistics(yr, plan, detection, min_class_cells))
        pointwise = acc - np.log(len(sel))
        n_te_don = int(tm["n_donor"])
        lpd = dict(mean=float(pointwise.mean()), n_observations=int(pointwise.size),
                   donor_original_code=tm["donor_original_code"],
                   per_donor_sum=np.bincount(tm["donor"], weights=pointwise.sum(1), minlength=n_te_don),
                   per_donor_n=np.bincount(tm["donor"], minlength=n_te_don) * pointwise.shape[1])
        cov = coverage(obs, reps, level)
        for key, st in cov["statistics"].items():
            acc = pooled.setdefault(key, [0, 0, 0])
            acc[0] += st["n_inside"]
            acc[1] += st["n_units"]
            acc[2] += st["n_undefined"]
        diagnosed = attempts[-1]["diagnosed"]
        fold_recs.append(dict(
            fold=f, held_out_donor_codes=held, n_train_cells=len(tr), n_test_cells=len(te),
            n_test_donors=tm["n_donor"], n_test_donor_classes=tm["n_dk"],
            n_train_donor_per_src=tm["n_train_donor_per_src"], n_train_dk_per_cls=tm["n_train_dk_per_cls"],
            attempts=attempts, diagnosed=diagnosed,
            interpretation="coverage may be read" if diagnosed else
            "NOT_DIAGNOSED: coverage is recorded but must not be interpreted",
            posterior_draws=int(flat["mu"].shape[0]), replicates=int(len(sel)), heldout_lpd=lpd,
            predict_seconds=time.time() - t0, coverage=cov))
    summary = {key: dict(n_inside=a[0], n_units=a[1], n_undefined=a[2], share_inside=a[0] / a[1] if a[1] else None)
               for key, a in pooled.items()}
    rec = dict(schema="V79_HELDOUT_PPC_V1", likelihood=likelihood, components=list(comps),
               settings=dict(k=k, seed=seed, chains=chains, warmup=warmup, draws=draws, n_pred_draws=n_pred_draws,
                             target_accept=list(accepts), max_tree_depth=max_tree_depth, retry=retry, depth=depth,
                             parent_mean_draw=parent_mean_draw, level=level, min_class_cells=min_class_cells),
               n_genes=int(y.shape[1]), n_folds=len(folds), folds=fold_recs, pooled_share_inside=summary,
               all_folds_diagnosed=all(r["diagnosed"] for r in fold_recs), notes=list(NOTES),
               wall_seconds=time.time() - t_all)
    return _jsonable(rec)


def merge_heldout(records) -> dict:
    """Pool per-fold records of one run (same likelihood, components and settings) into one record; refuses a
    missing or duplicated fold."""
    recs = list(records)
    if not recs:
        raise ValueError("no records")
    keys = {(r["likelihood"], tuple(r["components"]), r["n_folds"], r["n_genes"],
             json.dumps(r["settings"], sort_keys=True)) for r in recs}
    if len(keys) != 1:
        raise ValueError("records come from different runs")
    folds = sorted((f for r in recs for f in r["folds"]), key=lambda f: f["fold"])
    got = [f["fold"] for f in folds]
    if got != list(range(recs[0]["n_folds"])):
        raise ValueError(f"folds present {got}, expected 0..{recs[0]['n_folds'] - 1} once each")
    pooled = {}
    for f in folds:
        for key, st in f["coverage"]["statistics"].items():
            acc = pooled.setdefault(key, [0, 0, 0])
            acc[0] += st["n_inside"]
            acc[1] += st["n_units"]
            acc[2] += st["n_undefined"]
    out = dict(recs[0])
    out.update(folds=folds, all_folds_diagnosed=all(f["diagnosed"] for f in folds),
               pooled_share_inside={k: dict(n_inside=a[0], n_units=a[1], n_undefined=a[2],
                                            share_inside=a[0] / a[1] if a[1] else None) for k, a in pooled.items()},
               wall_seconds=sum(r["wall_seconds"] for r in recs))
    return out


def heldout_lpd_comparison(with_rec: dict, without_rec: dict, n_se: float = 2.0) -> dict:
    """Held-out-donor lpd of the model with a component minus the model without it, on the same observations:
    mean difference per observation and its donor-clustered standard error from per-donor sums. 'supported'
    only when the difference exceeds n_se standard errors (the contract's labelled convention) and both runs
    have every fold diagnosed."""
    def per_donor(rec):
        out = {}
        for f in rec["folds"]:
            L = f["heldout_lpd"]
            for code, s_, n_ in zip(L["donor_original_code"], L["per_donor_sum"], L["per_donor_n"]):
                if code in out:
                    raise ValueError(f"donor {code} held out twice")
                out[code] = (float(s_), int(n_))
        return out
    a, b = per_donor(with_rec), per_donor(without_rec)
    if set(a) != set(b) or any(a[k][1] != b[k][1] for k in a):
        raise ValueError("the two runs were scored on different held-out observations")
    codes = sorted(a)
    d = np.array([a[k][0] - b[k][0] for k in codes])
    n = np.array([a[k][1] for k in codes], dtype=np.float64)
    N = n.sum()
    mean = float(d.sum() / N)
    se = float(np.sqrt(len(codes) / (len(codes) - 1) * ((d - mean * n) ** 2).sum()) / N)
    both = bool(with_rec["all_folds_diagnosed"] and without_rec["all_folds_diagnosed"])
    return dict(mean_difference_per_observation=mean, donor_clustered_se=se, n_donors=len(codes),
                n_observations=int(N), threshold_se=n_se, both_runs_diagnosed=both,
                supported=bool(both and mean > n_se * se),
                rule="supported only when the difference exceeds two standard errors (labelled convention)")
