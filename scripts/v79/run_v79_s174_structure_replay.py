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

Positive-count candidates use the same nested structures with a Gaussian model on log positive count. This is a
stable development diagnostic, not the final positive-family adjudication; ZTNB remains a separate challenger.
Donor/operator random-effect support is assessed separately and is not replaced by treating IDs as unrestricted
fixed dummies.
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
    return out


def donor_folds(donor: np.ndarray, src: np.ndarray, k: int, seed: int) -> list[np.ndarray]:
    """Source-stratified assignment of whole donors to folds. Returns boolean test masks."""
    donor, src = np.asarray(donor), np.asarray(src)
    if k < 2:
        raise ValueError("k must be at least 2")
    rng = np.random.default_rng(seed)
    assignment: dict[int, int] = {}
    for s in np.unique(src):
        ds = np.unique(donor[src == s])
        # A donor spanning sources is assigned only once; such a design is unusual but fail consistently.
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
        oh = _one_hot(data["op"])
        cols.extend(oh.T)
    return np.column_stack(cols).astype(np.float64, copy=False)


def _logistic_fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    p = X.shape[1]
    def objective(beta):
        eta = X @ beta
        # stable Bernoulli negative log likelihood
        nll = np.logaddexp(0.0, eta).sum() - np.dot(y, eta)
        return float(nll + 0.5 * RIDGE * np.dot(beta[1:], beta[1:]))
    def grad(beta):
        g = X.T @ (expit(X @ beta) - y)
        g[1:] += RIDGE * beta[1:]
        return g
    res = minimize(objective, np.zeros(p), jac=grad, method="L-BFGS-B", options={"maxiter": 300, "ftol": 1e-10})
    if not res.success and np.linalg.norm(grad(res.x), ord=np.inf) > 1e-4:
        raise RuntimeError(f"logistic fit did not converge: {res.message}")
    return np.asarray(res.x)


def _bernoulli_logloss(y: np.ndarray, eta: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    return np.logaddexp(0.0, eta) - y * eta


def _ridge_linear_fit(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    eye = np.eye(X.shape[1]); eye[0, 0] = 0.0
    beta = np.linalg.solve(X.T @ X + RIDGE * eye, X.T @ y)
    resid = y - X @ beta
    sigma = float(np.sqrt(max(np.mean(resid * resid), 1e-8)))
    return beta, sigma


def _normal_lpd(y: np.ndarray, mu: np.ndarray, sigma: float) -> np.ndarray:
    return -0.5 * np.log(2 * np.pi * sigma * sigma) - 0.5 * ((y - mu) / sigma) ** 2


def evaluate_detection_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    y = (np.asarray(data["counts_selected"])[:, gene] > 0).astype(np.float64)
    folds = donor_folds(data["donor"], data["src"], k, seed)
    out = {}
    for model in MODELS:
        X = design_matrix(data, model)
        losses = []
        for test in folds:
            train = ~test
            beta = _logistic_fit(X[train], y[train])
            losses.append(_bernoulli_logloss(y[test], X[test] @ beta))
        loss = np.concatenate(losses)
        out[model] = {"mean_logloss": float(loss.mean()), "n_test_predictions": int(len(loss))}
    return {"gene_position": int(gene), "prevalence": float(y.mean()), "models": out}


def evaluate_positive_gene(data: dict, gene: int, k: int = 3, seed: int = SEED) -> dict:
    counts = np.asarray(data["counts_selected"])[:, gene].astype(np.float64)
    pos = counts > 0
    folds = donor_folds(data["donor"], data["src"], k, seed)
    out = {}
    for model in MODELS:
        X = design_matrix(data, model)
        lpds = []
        for test_donor in folds:
            train = (~test_donor) & pos
            test = test_donor & pos
            if train.sum() <= X.shape[1] or not test.any():
                continue
            beta, sigma = _ridge_linear_fit(X[train], np.log(counts[train]))
            lpds.append(_normal_lpd(np.log(counts[test]), X[test] @ beta, sigma))
        if not lpds:
            out[model] = {"mean_lpd": float("nan"), "n_positive_test_predictions": 0}
        else:
            lpd = np.concatenate(lpds)
            out[model] = {"mean_lpd": float(lpd.mean()), "n_positive_test_predictions": int(len(lpd))}
    return {"gene_position": int(gene), "n_positive": int(pos.sum()), "models": out}


def summarize(per_gene: list[dict], metric: str) -> dict:
    summary = {}
    for model in MODELS:
        vals = np.array([g["models"][model][metric] for g in per_gene], dtype=float)
        good = np.isfinite(vals)
        summary[model] = {"mean": float(vals[good].mean()) if good.any() else None,
                          "median": float(np.median(vals[good])) if good.any() else None,
                          "n_genes": int(good.sum())}
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cache")
    ap.add_argument("receipt")
    ap.add_argument("out")
    ap.add_argument("--genes", type=int, default=200,
                    help="number of already identity-blind cache-panel positions to evaluate")
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    data = load_compact_cache(a.cache, a.receipt)
    n_genes = min(a.genes, data["counts_selected"].shape[1])
    det, pos = [], []
    for g in range(n_genes):
        det.append(evaluate_detection_gene(data, g, a.folds, a.seed))
        pos.append(evaluate_positive_gene(data, g, a.folds, a.seed))
    rec = {
        "schema": "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V1",
        "status": "DEVELOPMENT_ONLY__NOT_CONFIRMATORY__NOT_SYNTHETIC_CONSUMABLE",
        "cache_sha256": sha256(Path(a.cache)),
        "receipt_sha256": sha256(Path(a.receipt)),
        "n_cells": int(len(data["donor"])), "n_donors": int(len(np.unique(data["donor"]))),
        "n_genes": int(n_genes), "folds": int(a.folds), "seed": int(a.seed),
        "models": list(MODELS), "ridge": RIDGE,
        "detection_summary": summarize(det, "mean_logloss"),
        "positive_lognormal_summary": summarize(pos, "mean_lpd"),
        "per_gene_detection": det, "per_gene_positive": pos,
        "boundaries": {"bayesian_posterior_inference": False, "confirmatory_qualification": False,
                       "factorial_execution": False, "training_authorized": False},
        "terminal": "S174_STRUCTURE_REPLAY_COMPLETE__DEVELOPMENT_ONLY__CONTROLLER_REVIEW_REQUIRED"
    }
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "n_cells": rec["n_cells"], "n_genes": n_genes,
                      "detection": rec["detection_summary"], "positive": rec["positive_lognormal_summary"]}))


if __name__ == "__main__":
    main()
