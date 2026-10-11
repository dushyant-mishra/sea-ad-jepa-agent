#!/usr/bin/env python3
"""Cheap, cache-only corrected-S174 model-structure replay.

DEVELOPMENT ONLY. This runner never opens the 41K count shards. It consumes only a hash-bound compact analysis
cache produced by build_v79_analysis_cache.py and compares prospectively specified nested fixed structures in
held-out-donor folds. Its purpose is model development before any new Bayesian/NUTS qualification.

Detection candidates, nested in order:
  depth_linear
  depth_quad
  depth_class
  depth_class_source
  depth_class_source_operator

Positive-count candidates use the same nested structures with a Gaussian model on log positive count. Operator
fixed proxies are encoded within source so source+operator is full rank. ZTNB remains a separate challenger.

Random-effect support is assessed cheaply from fixed-structure residuals by restricted permutation:
- donor support after depth+class+source+operator;
- operator support after depth+class+source, after removing donor means and permuting within donor;
- donor×class increment after removing donor means and permuting within donor.
These diagnostics decide what hierarchy deserves a later Bayesian random-effect model; they are not substitutes
for Bayesian posterior estimation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

SEED = 20261011
RIDGE = 1e-4
MODELS = ("depth_linear", "depth_quad", "depth_class", "depth_class_source", "depth_class_source_operator")
OPERATOR_MODEL = "depth_class_source_operator"

# PR #280 controller ruling (2026-10-11T19:40:47Z, before any replay metric existed): operator-within-source
# columns get an explicit ridge penalty, primary lambda = 1 (Gaussian prior SD 1 on the linear predictor), in both
# hurdle parts; intercept, depth, class and source keep their frozen treatment. The sensitivity set is frozen and is
# deliberately not a command-line option, so it cannot be adapted after seeing outcomes.
OPERATOR_LAMBDA_PRIMARY = 1.0
OPERATOR_LAMBDA_SET = (0.25, 1.0, 4.0)
OPERATOR_BOOTSTRAP_RESAMPLES = 2000
OPERATOR_RULING_CONVENTION = (
    "Convention fixed in code before any replay metric existed (Macha, pending controller ratification). At each "
    "lambda the per-gene operator increment is loss(depth_class_source) - loss(operator) for detection (held-out "
    "log loss) and lpd(operator) - lpd(depth_class_source) for positive magnitude (held-out lognormal LPD), so "
    "positive means operator helps. 'Materially present' at a lambda: no failed fit at that lambda, median per-gene "
    "increment > 0, and the 95% gene-bootstrap interval of that median (2000 resamples, fixed seed) excludes 0. "
    "Genes share cells and donors, so the gene bootstrap is optimistic. SUPPORTED: materially present at all three "
    "lambdas. NOT_SUPPORTED: materially present at none. Otherwise PRIOR_SENSITIVE__UNRESOLVED.")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_compact_cache(npz_path, receipt_path) -> dict[str, np.ndarray]:
    npz_path, receipt_path = Path(npz_path), Path(receipt_path)
    rec = json.loads(receipt_path.read_text(encoding="utf-8"))
    if rec.get("schema") != "V79_ANALYSIS_CACHE_RECEIPT_V2":
        raise SystemExit("STOP: compact cache receipt is not V2")
    if rec.get("npz") != npz_path.name or rec.get("npz_sha256") != sha256(npz_path):
        raise SystemExit("STOP: compact cache bytes do not match receipt")
    if rec.get("streaming_passes") != 2 or rec.get("max_count_shards_resident") != 1 or \
            rec.get("global_sparse_assembly") is not False:
        raise SystemExit("STOP: cache receipt does not prove bounded streaming construction")
    with np.load(npz_path, allow_pickle=False) as z:
        required = {"counts_selected", "gene_address_index", "prevalence_selected", "library_cached", "n_detected",
                    "source_library", "cls", "src", "op", "donor", "dk", "log_lib_centered"}
        if not required.issubset(z.files):
            raise SystemExit(f"STOP: cache lacks fields {sorted(required - set(z.files))}")
        out = {k: np.asarray(z[k]) for k in required}
    n = len(out["donor"])
    if out["counts_selected"].shape[0] != n or any(len(out[k]) != n for k in ("cls", "src", "op", "dk", "log_lib_centered")):
        raise SystemExit("STOP: compact cache row dimensions disagree")
    if out["counts_selected"].shape[1] != len(out["prevalence_selected"]):
        raise SystemExit("STOP: cache gene panel and prevalence vector disagree")
    return out


def select_panel_positions(prevalence: np.ndarray, n: int, seed: int = SEED, bins: int = 10) -> np.ndarray:
    """Identity-blind prevalence-spanning subpanel from an already frozen cache panel."""
    p = np.asarray(prevalence, dtype=np.float64)
    m = len(p)
    if n <= 0:
        raise ValueError("n must be positive")
    if n >= m:
        return np.arange(m, dtype=np.int64)
    bins = min(int(bins), n, m)
    order = np.argsort(p, kind="mergesort")
    rank_bins = np.array_split(order, bins)
    base, rem = divmod(n, bins)
    if any(len(b) < base for b in rank_bins):
        raise ValueError("cache panel is too small for balanced subpanel")
    rng = np.random.default_rng(seed)
    extra_order = np.roll(np.arange(bins), int(rng.integers(0, bins)))
    extras = set(extra_order[:rem].tolist())
    picked = []
    for i, b in enumerate(rank_bins):
        take = base + (1 if i in extras else 0)
        if take > len(b):
            raise ValueError("rank bin cannot supply requested balanced subpanel")
        picked.extend(rng.choice(b, size=take, replace=False).tolist())
    if len(picked) != n or len(set(picked)) != n:
        raise RuntimeError("balanced panel selection failed uniqueness/size invariant")
    return np.sort(np.asarray(picked, dtype=np.int64))


def donor_folds(donor: np.ndarray, src: np.ndarray, k: int, seed: int) -> list[np.ndarray]:
    """Source-stratified assignment of whole donors to folds. Returns boolean test masks."""
    donor, src = np.asarray(donor), np.asarray(src)
    if k < 2:
        raise ValueError("k must be at least 2")
    rng = np.random.default_rng(seed)
    assignment: dict[int, int] = {}
    for s in np.unique(src):
        ds = np.unique(donor[src == s])
        ds = np.array([d for d in ds if int(d) not in assignment], dtype=donor.dtype)
        rng.shuffle(ds)
        for i, d in enumerate(ds):
            assignment[int(d)] = i % k
    missing = set(map(int, np.unique(donor))) - set(assignment)
    if missing:
        raise ValueError(f"unassigned donors: {sorted(missing)[:5]}")
    return [np.array([assignment[int(d)] == f for d in donor], dtype=bool) for f in range(k)]


def _one_hot(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v)
    lev = np.unique(v)
    if len(lev) <= 1:
        return np.empty((len(v), 0), dtype=np.float64)
    return np.column_stack([(v == x).astype(np.float64) for x in lev[1:]])


def _nested_child_one_hot(child: np.ndarray, parent: np.ndarray) -> np.ndarray:
    """Reference-coded child-within-parent indicators, full rank beside parent main effects."""
    child, parent = np.asarray(child), np.asarray(parent)
    cols = []
    for p in np.unique(parent):
        levels = np.unique(child[parent == p])
        for level in levels[1:]:
            cols.append((child == level).astype(np.float64))
    return np.column_stack(cols) if cols else np.empty((len(child), 0), dtype=np.float64)


def design_matrix(data: dict, model: str) -> np.ndarray:
    d = np.asarray(data["log_lib_centered"], dtype=np.float64)
    cols = [np.ones(len(d)), d]
    if model != "depth_linear":
        d2 = d * d
        cols.append(d2 - d2.mean())
    if model in ("depth_class", "depth_class_source", "depth_class_source_operator"):
        oh = _one_hot(data["cls"])
        cols.extend(oh.T)
    if model in ("depth_class_source", "depth_class_source_operator"):
        oh = _one_hot(data["src"])
        cols.extend(oh.T)
    if model == "depth_class_source_operator":
        oh = _nested_child_one_hot(data["op"], data["src"])
        cols.extend(oh.T)
    return np.column_stack(cols).astype(np.float64, copy=False)


def operator_column_mask(data: dict, model: str) -> np.ndarray:
    """True for the operator-within-source columns of a model's design (they are the last columns), else False."""
    mask = np.zeros(design_matrix(data, model).shape[1], dtype=bool)
    if model == OPERATOR_MODEL:
        k = _nested_child_one_hot(data["op"], data["src"]).shape[1]
        if k:
            mask[-k:] = True
    return mask


def operator_penalty_vector(data: dict, model: str, operator_lambda: float) -> np.ndarray:
    """Per-column ridge penalty: intercept 0, the frozen RIDGE elsewhere, operator_lambda on operator columns only."""
    mask = operator_column_mask(data, model)
    pen = np.full(mask.shape, RIDGE, dtype=np.float64)
    pen[0] = 0.0
    pen[mask] = float(operator_lambda)
    return pen


def _logistic_fit(X: np.ndarray, y: np.ndarray, penalty: np.ndarray | None = None) -> np.ndarray:
    """penalty=None is the original frozen path (RIDGE on every non-intercept column), unchanged."""
    y = np.asarray(y, dtype=np.float64)
    p = X.shape[1]
    if penalty is None:
        def objective(beta):
            eta = X @ beta
            nll = np.logaddexp(0.0, eta).sum() - np.dot(y, eta)
            return float(nll + 0.5 * RIDGE * np.dot(beta[1:], beta[1:]))
        def grad(beta):
            g = X.T @ (expit(X @ beta) - y)
            g[1:] += RIDGE * beta[1:]
            return g
    else:
        pen = np.asarray(penalty, dtype=np.float64)
        if pen.shape != (p,):
            raise ValueError("penalty vector must have one entry per design column")
        def objective(beta):
            eta = X @ beta
            nll = np.logaddexp(0.0, eta).sum() - np.dot(y, eta)
            return float(nll + 0.5 * np.dot(pen * beta, beta))
        def grad(beta):
            return X.T @ (expit(X @ beta) - y) + pen * beta
    res = minimize(objective, np.zeros(p), jac=grad, method="L-BFGS-B", options={"maxiter": 300, "ftol": 1e-10})
    if not res.success and np.linalg.norm(grad(res.x), ord=np.inf) > 1e-4:
        raise RuntimeError(f"logistic fit did not converge: {res.message}")
    return np.asarray(res.x)


def _bernoulli_logloss(y: np.ndarray, eta: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    return np.logaddexp(0.0, eta) - y * eta


def _ridge_linear_fit(X: np.ndarray, y: np.ndarray, penalty: np.ndarray | None = None) -> tuple[np.ndarray, float]:
    """penalty=None is the original frozen path (RIDGE on every non-intercept column), unchanged."""
    if penalty is None:
        eye = np.eye(X.shape[1]); eye[0, 0] = 0.0
        beta = np.linalg.solve(X.T @ X + RIDGE * eye, X.T @ y)
    else:
        pen = np.asarray(penalty, dtype=np.float64)
        if pen.shape != (X.shape[1],):
            raise ValueError("penalty vector must have one entry per design column")
        beta = np.linalg.solve(X.T @ X + np.diag(pen), X.T @ y)
    resid = y - X @ beta
    sigma = float(np.sqrt(max(np.mean(resid * resid), 1e-8)))
    return beta, sigma


def _normal_lpd(y: np.ndarray, mu: np.ndarray, sigma: float) -> np.ndarray:
    return -0.5 * np.log(2 * np.pi * sigma * sigma) - 0.5 * ((y - mu) / sigma) ** 2


def _between_group_stat(residual: np.ndarray, groups: np.ndarray) -> float:
    residual, groups = np.asarray(residual, dtype=np.float64), np.asarray(groups)
    overall = float(residual.mean())
    total, n = 0.0, 0
    for g in np.unique(groups):
        x = residual[groups == g]
        if len(x) == 0:
            continue
        total += len(x) * (float(x.mean()) - overall) ** 2
        n += len(x)
    return float(total / max(n, 1))


def permutation_group_support(residual: np.ndarray, groups: np.ndarray, strata: np.ndarray,
                              seed: int = SEED, n_perm: int = 99) -> dict:
    """Test residual group organization against residual permutations restricted within strata."""
    residual = np.asarray(residual, dtype=np.float64)
    groups, strata = np.asarray(groups), np.asarray(strata)
    if not (len(residual) == len(groups) == len(strata)):
        raise ValueError("residual/groups/strata lengths disagree")
    if n_perm < 1:
        raise ValueError("n_perm must be positive")
    observed = _between_group_stat(residual, groups)
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=np.float64)
    idx_by_stratum = [np.where(strata == s)[0] for s in np.unique(strata)]
    for i in range(n_perm):
        perm = residual.copy()
        for ix in idx_by_stratum:
            perm[ix] = residual[rng.permutation(ix)]
        null[i] = _between_group_stat(perm, groups)
    q95 = float(np.quantile(null, 0.95))
    return {"observed": observed, "null_mean": float(null.mean()), "null_q95": q95,
            "n_perm": int(n_perm), "supported": bool(observed > q95)}


def evaluate_detection_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    y = (np.asarray(data["counts_selected"])[:, gene] > 0).astype(np.float64)
    folds = donor_folds(data["donor"], data["src"], k, seed)
    out = {}
    for model in MODELS[:-1]:  # non-operator models: the original frozen path, unchanged
        X = design_matrix(data, model)
        losses = []
        for test in folds:
            train = ~test
            beta = _logistic_fit(X[train], y[train])
            losses.append(_bernoulli_logloss(y[test], X[test] @ beta))
        loss = np.concatenate(losses)
        out[model] = {"mean_logloss": float(loss.mean()), "n_test_predictions": int(len(loss))}
    X = design_matrix(data, OPERATOR_MODEL)
    sens = {}
    for lam in OPERATOR_LAMBDA_SET:
        pen = operator_penalty_vector(data, OPERATOR_MODEL, lam)
        losses, failed = [], 0
        for test in folds:
            train = ~test
            try:
                beta = _logistic_fit(X[train], y[train], penalty=pen)
            except RuntimeError:
                if lam == OPERATOR_LAMBDA_PRIMARY:
                    raise  # every primary fit must converge, or the replay fails closed
                failed += 1
                continue
            losses.append(_bernoulli_logloss(y[test], X[test] @ beta))
        if failed:
            sens[str(lam)] = {"mean_logloss": None, "n_test_predictions": 0, "converged": False, "failed_folds": failed}
        else:
            loss = np.concatenate(losses)
            sens[str(lam)] = {"mean_logloss": float(loss.mean()), "n_test_predictions": int(len(loss)),
                              "converged": True, "failed_folds": 0}
    out[OPERATOR_MODEL] = sens[str(OPERATOR_LAMBDA_PRIMARY)]
    return {"gene_position": int(gene), "prevalence": float(y.mean()), "models": out,
            "operator_penalty_sensitivity": sens}


def evaluate_positive_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene].astype(np.float64)
    pos = counts > 0
    folds = donor_folds(data["donor"], data["src"], k, seed)

    def run(X, penalty=None):
        lpds = []
        for test_donor in folds:
            train = (~test_donor) & pos
            test = test_donor & pos
            if train.sum() <= X.shape[1] or not test.any():
                continue
            beta, sigma = _ridge_linear_fit(X[train], np.log(counts[train]), penalty=penalty)
            lpds.append(_normal_lpd(np.log(counts[test]), X[test] @ beta, sigma))
        if not lpds:
            return {"mean_lpd": float("nan"), "n_positive_test_predictions": 0}
        lpd = np.concatenate(lpds)
        return {"mean_lpd": float(lpd.mean()), "n_positive_test_predictions": int(len(lpd))}

    out = {model: run(design_matrix(data, model)) for model in MODELS[:-1]}  # original frozen path, unchanged
    X = design_matrix(data, OPERATOR_MODEL)
    sens = {str(lam): run(X, operator_penalty_vector(data, OPERATOR_MODEL, lam)) for lam in OPERATOR_LAMBDA_SET}
    out[OPERATOR_MODEL] = sens[str(OPERATOR_LAMBDA_PRIMARY)]
    return {"gene_position": int(gene), "n_positive": int(pos.sum()), "models": out,
            "operator_penalty_sensitivity": sens}


def _center_within(x: np.ndarray, groups: np.ndarray) -> np.ndarray:
    out = np.asarray(x, dtype=np.float64).copy()
    for g in np.unique(groups):
        ix = groups == g
        out[ix] -= out[ix].mean()
    return out


def operator_support_after_donor_centering(residual: np.ndarray, operator: np.ndarray, donor: np.ndarray,
                                           source: np.ndarray, seed: int = SEED, n_perm: int = 99) -> dict:
    """Operator support beyond donor: center donor means, then permute within donor.

    Donors are expected to be source-specific in S174, so within-donor permutation also respects source nesting.
    `source` is accepted and checked to make that assumption explicit.
    """
    residual, operator, donor, source = map(np.asarray, (residual, operator, donor, source))
    for d in np.unique(donor):
        if len(np.unique(source[donor == d])) != 1:
            raise ValueError("operator support requires each donor to belong to one source")
    centered = _center_within(residual, donor)
    return permutation_group_support(centered, operator, donor, seed, n_perm)


def residual_support_for_gene(data: dict, gene: int, seed: int = SEED, n_perm: int = 99) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene].astype(np.float64)
    y = (counts > 0).astype(np.float64)

    X_full = design_matrix(data, "depth_class_source_operator")
    pen_full = operator_penalty_vector(data, OPERATOR_MODEL, OPERATOR_LAMBDA_PRIMARY)
    b_full = _logistic_fit(X_full, y, penalty=pen_full)
    det_full_resid = y - expit(X_full @ b_full)
    X_noop = design_matrix(data, "depth_class_source")
    b_noop = _logistic_fit(X_noop, y)
    det_noop_resid = y - expit(X_noop @ b_noop)
    det_dc_resid = _center_within(det_full_resid, data["donor"])

    det = {
        "donor": permutation_group_support(det_full_resid, data["donor"], data["src"], seed + 1, n_perm),
        "operator": operator_support_after_donor_centering(det_noop_resid, data["op"], data["donor"], data["src"], seed + 2, n_perm),
        "donor_class_increment": permutation_group_support(det_dc_resid, data["dk"], data["donor"], seed + 3, n_perm),
    }

    pos = counts > 0
    positive = None
    if int(pos.sum()) > X_full.shape[1] + 5:
        z = np.log(counts[pos])
        bf, _ = _ridge_linear_fit(X_full[pos], z, penalty=pen_full)
        pos_full_resid = z - X_full[pos] @ bf
        bn, _ = _ridge_linear_fit(X_noop[pos], z)
        pos_noop_resid = z - X_noop[pos] @ bn
        donor_pos = data["donor"][pos]
        pos_dc_resid = _center_within(pos_full_resid, donor_pos)
        positive = {
            "donor": permutation_group_support(pos_full_resid, donor_pos, data["src"][pos], seed + 11, n_perm),
            "operator": operator_support_after_donor_centering(pos_noop_resid, data["op"][pos], donor_pos, data["src"][pos], seed + 12, n_perm),
            "donor_class_increment": permutation_group_support(pos_dc_resid, data["dk"][pos], donor_pos, seed + 13, n_perm),
        }
    return {"gene_position": int(gene), "detection": det, "positive": positive}


def summarize(per_gene: list[dict], metric: str) -> dict:
    summary = {}
    for model in MODELS:
        vals = np.array([g["models"][model][metric] for g in per_gene], dtype=float)
        good = np.isfinite(vals)
        summary[model] = {"mean": float(vals[good].mean()) if good.any() else None,
                          "median": float(np.median(vals[good])) if good.any() else None,
                          "n_genes": int(good.sum())}
    return summary


def summarize_support(per_gene: list[dict], part: str) -> dict:
    out = {}
    for component in ("donor", "operator", "donor_class_increment"):
        recs = [g[part][component] for g in per_gene if g.get(part) is not None]
        out[component] = {
            "supported_genes": int(sum(r["supported"] for r in recs)),
            "eligible_genes": int(len(recs)),
            "mean_observed_minus_null_q95": (float(np.mean([r["observed"] - r["null_q95"] for r in recs]))
                                               if recs else None),
        }
    return out


def operator_increment_ruling(per_gene: list[dict], metric: str, higher_is_better: bool, seed: int = SEED) -> dict:
    """Operator increment over depth_class_source at each frozen lambda, and the pre-registered robustness ruling
    (OPERATOR_RULING_CONVENTION). Never selects a lambda."""
    rng = np.random.default_rng(seed + 9000)
    by_lambda, material = {}, {}
    for lam in OPERATOR_LAMBDA_SET:
        key = str(lam)
        failed = sum(1 for g in per_gene if g["operator_penalty_sensitivity"][key].get("converged") is False)
        deltas = []
        for g in per_gene:
            base = g["models"]["depth_class_source"][metric]
            op = g["operator_penalty_sensitivity"][key][metric]
            if base is None or op is None or not (np.isfinite(base) and np.isfinite(op)):
                continue
            deltas.append(op - base if higher_is_better else base - op)
        d = np.asarray(deltas, dtype=np.float64)
        if d.size:
            boot = np.median(rng.choice(d, size=(OPERATOR_BOOTSTRAP_RESAMPLES, d.size), replace=True), axis=1)
            lo, hi = (float(x) for x in np.quantile(boot, [0.025, 0.975]))
            med = float(np.median(d))
        else:
            lo = hi = med = None
        mat = bool(failed == 0 and d.size and med > 0 and lo > 0)
        material[key] = mat
        by_lambda[key] = {"n_genes": int(d.size), "failed_genes": int(failed), "median_increment": med,
                          "mean_increment": float(d.mean()) if d.size else None,
                          "fraction_genes_improved": float((d > 0).mean()) if d.size else None,
                          "median_increment_bootstrap_95": [lo, hi], "materially_present": mat}
    n_material = sum(material.values())
    ruling = ("SUPPORTED" if n_material == len(OPERATOR_LAMBDA_SET) else
              "NOT_SUPPORTED" if n_material == 0 else "PRIOR_SENSITIVE__UNRESOLVED")
    return {"primary_lambda": OPERATOR_LAMBDA_PRIMARY, "lambda_set": list(OPERATOR_LAMBDA_SET),
            "by_lambda": by_lambda, "ruling": ruling, "convention": OPERATOR_RULING_CONVENTION}


def build_parser() -> argparse.ArgumentParser:
    """Command line. The operator penalty and its sensitivity set are frozen constants, deliberately not options."""
    ap = argparse.ArgumentParser()
    ap.add_argument("cache")
    ap.add_argument("receipt")
    ap.add_argument("out")
    ap.add_argument("--genes", type=int, default=200)
    ap.add_argument("--support-genes", type=int, default=50)
    ap.add_argument("--permutations", type=int, default=99)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=SEED)
    return ap


def main() -> None:
    a = build_parser().parse_args()
    data = load_compact_cache(a.cache, a.receipt)
    panel = select_panel_positions(data["prevalence_selected"], min(a.genes, data["counts_selected"].shape[1]), a.seed)
    support_panel_local = select_panel_positions(data["prevalence_selected"][panel], min(a.support_genes, len(panel)), a.seed + 101)
    support_panel = panel[support_panel_local]

    det, pos = [], []
    for g in panel.tolist():
        det.append(evaluate_detection_gene(data, g, a.folds, a.seed))
        pos.append(evaluate_positive_gene(data, g, a.folds, a.seed))
    support = [residual_support_for_gene(data, int(g), a.seed + int(i) * 100, a.permutations)
               for i, g in enumerate(support_panel.tolist())]

    operator_robustness = {
        "detection": operator_increment_ruling(det, "mean_logloss", higher_is_better=False, seed=a.seed),
        "positive_lognormal": operator_increment_ruling(pos, "mean_lpd", higher_is_better=True, seed=a.seed + 1),
    }
    rec = {
        "schema": "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3",
        "operator_penalty": {
            "decision": "PR #280 controller ruling 2026-10-11T19:40:47Z (before any replay metric)",
            "primary_lambda": OPERATOR_LAMBDA_PRIMARY, "sensitivity_set": list(OPERATOR_LAMBDA_SET),
            "applies_to": "operator-within-source columns only, in both hurdle parts; intercept unpenalized; "
                          "depth, class and source keep RIDGE",
            "primary_fits_must_converge": True, "sensitivity_failures_recorded_not_rescued": True},
        "operator_increment_robustness": operator_robustness,
        "operator_support_lambda_invariant": (
            "operator support is computed from depth+class+source residuals (no operator columns), donor-centred and "
            "permuted within donor, exactly as frozen; the operator penalty cannot change it, so its result is the "
            "same at every lambda in the frozen set"),
        "donor_and_donor_class_support_lambda": OPERATOR_LAMBDA_PRIMARY,
        "status": "DEVELOPMENT_ONLY__NOT_CONFIRMATORY__NOT_SYNTHETIC_CONSUMABLE",
        "cache_sha256": sha256(Path(a.cache)), "receipt_sha256": sha256(Path(a.receipt)),
        "n_cells": int(len(data["donor"])), "n_donors": int(len(np.unique(data["donor"]))),
        "n_cache_genes": int(data["counts_selected"].shape[1]), "n_replay_genes": int(len(panel)),
        "n_support_genes": int(len(support_panel)), "folds": int(a.folds), "seed": int(a.seed),
        "permutations": int(a.permutations), "models": list(MODELS), "ridge": RIDGE,
        "operator_encoding": "REFERENCE_CODED_WITHIN_SOURCE__FULL_RANK_WITH_SOURCE_MAIN_EFFECT",
        "operator_support_null": "DONOR_CENTERED_RESIDUALS__PERMUTED_WITHIN_DONOR",
        "panel_positions_internal": panel.tolist(), "support_panel_positions_internal": support_panel.tolist(),
        "panel_prevalence_range": [float(data["prevalence_selected"][panel].min()), float(data["prevalence_selected"][panel].max())],
        "detection_summary": summarize(det, "mean_logloss"),
        "positive_lognormal_summary": summarize(pos, "mean_lpd"),
        "random_effect_support": {"detection": summarize_support(support, "detection"),
                                  "positive": summarize_support(support, "positive")},
        "per_gene_detection": det, "per_gene_positive": pos, "per_gene_random_effect_support": support,
        "boundaries": {"bayesian_posterior_inference": False, "confirmatory_qualification": False,
                       "factorial_execution": False, "training_authorized": False},
        "terminal": ("EXACT_S174_STRUCTURE_REPLAY_COMPLETE__PRIMARY_OPERATOR_LAMBDA_1__FROZEN_SENSITIVITY_0p25_1_4__"
                     "DEVELOPMENT_ONLY__CONTROLLER_MODEL_FREEZE_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF")
    }
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "n_cells": rec["n_cells"], "n_replay_genes": len(panel),
                      "n_support_genes": len(support_panel), "detection": rec["detection_summary"],
                      "positive": rec["positive_lognormal_summary"], "support": rec["random_effect_support"]}))


if __name__ == "__main__":
    main()
