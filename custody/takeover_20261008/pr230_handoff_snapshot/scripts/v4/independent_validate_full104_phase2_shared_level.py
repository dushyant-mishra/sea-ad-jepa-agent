#!/usr/bin/env python3
"""Independent executable validator for conclusion-bearing shared statistics.

This file intentionally does not import any production shared-statistic code.
It uses symmetric whitening plus numpy.linalg.eigh and reconstructs the matched
view permutations from their frozen compact maps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def seed_from(key: str, *parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join([key, *map(str, parts)]).encode()).digest()[:8], "little")


def fit_independent(mean_rows, within_rows, between_rows, indices, rank):
    mu = np.mean(mean_rows[indices], axis=0, dtype=np.float64)
    cw = np.mean(within_rows[indices], axis=0, dtype=np.float64) - np.outer(mu, mu)
    cb = np.mean(between_rows[indices], axis=0, dtype=np.float64) - np.outer(mu, mu)
    cw, cb = (cw + cw.T) * 0.5, (cb + cb.T) * 0.5
    diagonal = np.clip(np.diag(cw), 0, None)
    positive = diagonal[diagonal > 0]
    floor = max(np.finfo(float).eps, (np.median(positive) if len(positive) else 1.0) * math.sqrt(np.finfo(float).eps))
    scale = np.sqrt(np.maximum(diagonal, floor))
    aw = cw / np.outer(scale, scale); aw = (aw + aw.T) * 0.5
    ab = cb / np.outer(scale, scale); ab = (ab + ab.T) * 0.5
    ridge = math.sqrt(np.finfo(float).eps) * float(np.trace(aw)) / len(scale)
    metric = aw + ridge * np.eye(len(scale))
    mv, muvec = np.linalg.eigh(metric)
    whitening = muvec @ np.diag(1 / np.sqrt(mv)) @ muvec.T
    reduced = whitening @ ab @ whitening; reduced = (reduced + reduced.T) * 0.5
    values, vectors = np.linalg.eigh(reduced)
    order = np.argsort(values)[::-1][:rank]
    values = values[order]
    components = (whitening @ vectors[:, order]) / scale[:, None]
    for column in range(rank):
        pivot = int(np.argmax(np.abs(components[:, column])))
        if components[pivot, column] < 0:
            components[:, column] *= -1
    q, _ = np.linalg.qr(components, mode="reduced")
    return {"mean": mu, "eigenvalues": values, "components": components, "q": q}


def moments(basis, mean, within, between):
    mu, w = basis["mean"], basis["components"]
    centered = mean - mu
    cw = within - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    cb = between - np.outer(mean, mu) - np.outer(mu, mean) + np.outer(mu, mu)
    return centered @ w, (w.T @ cw @ w + w.T @ cw.T @ w) * 0.5, (w.T @ cb @ w + w.T @ cb.T @ w) * 0.5


def heldout_independent(mean_rows, within_rows, between_rows, folds, rank):
    result = np.empty((len(mean_rows), rank), np.float64)
    donors = np.arange(len(mean_rows))
    for fold in sorted(set(folds)):
        train, held = donors[folds != fold], donors[folds == fold]
        basis = fit_independent(mean_rows, within_rows, between_rows, train, rank)
        tw = np.mean([moments(basis, mean_rows[d], within_rows[d], between_rows[d])[1] for d in train], axis=0)
        tb = np.mean([moments(basis, mean_rows[d], within_rows[d], between_rows[d])[2] for d in train], axis=0)
        pvar = (np.diag(tw) + 2 * np.diag(tb)) / 3
        slope = np.diag(tb) / np.maximum(pvar, np.finfo(float).eps)
        for donor in held:
            dm, dw, db = moments(basis, mean_rows[donor], within_rows[donor], between_rows[donor])
            t2, pt = np.diag(dw), np.diag(db); p2 = (t2 + 2 * pt) / 3
            sse = t2 - 2 * slope * pt + slope * slope * p2
            variance = np.maximum(t2 - dm * dm, 0)
            result[donor] = 1 - np.cumsum(sse) / np.maximum(np.cumsum(variance), np.finfo(float).eps)
    return result


def overlap_curve(a, b):
    square = np.square(a.T @ b)
    cumulative = np.cumsum(np.cumsum(square, axis=0), axis=1)
    return np.asarray([cumulative[d - 1, d - 1] / d for d in range(1, a.shape[1] + 1)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--analytic", required=True)
    parser.add_argument("--refit-null", required=True)
    parser.add_argument("--corrected-selection", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    harness, matrix, analytic, refit, corrected, out = map(Path, [args.harness, args.matrix, args.analytic, args.refit_null, args.corrected_selection, args.out])
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((harness / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1.json").read_text())
    if contract["status"] != "FROZEN_PROSPECTIVELY_BEFORE_LEVEL2_SHARED_STATISTICS":
        raise RuntimeError("promotion harness unavailable")
    matrix_audit = json.loads((matrix / "PHASE2_FEATURE_MATRIX_AUDIT.json").read_text())
    level = int(matrix_audit["sample_level"]); rank = 32; reps = 256
    rows = pd.read_csv(matrix / "PHASE2_FEATURE_ROWS.csv", dtype={"donor_id": str})
    donors = sorted(rows.donor_id.unique()); donor_ix = {d: i for i, d in enumerate(donors)}
    base = matrix.parent
    folds_table = pd.read_csv(base / "preexpression_freeze/PHASE2_DONOR_FOLDS.csv", dtype={"donor_id": str}).set_index("donor_id")
    folds = np.asarray([int(folds_table.loc[d, "outer_fold"]) for d in donors])
    sources = np.asarray([rows.loc[rows.donor_id.eq(d), "source"].iloc[0] for d in donors])
    rng_path = base / "preexpression_freeze/PHASE2_RNG_KEYS.json"
    rng = json.loads(rng_path.read_text())["keys"]

    checks, independent_bases, independent_held = [], {}, {}
    for label in "AB":
        stats = analytic / "sufficient_statistics"
        mean = np.asarray(np.load(stats / f"{label}_mean.npy", mmap_mode="r"), np.float64)
        within = np.asarray(np.load(stats / f"{label}_within.npy", mmap_mode="r"), np.float64)
        between = np.asarray(np.load(stats / f"{label}_between.npy", mmap_mode="r"), np.float64)
        alt = fit_independent(mean, within, between, np.arange(len(donors)), rank)
        primary = np.load(analytic / f"SHARED_OVERCOMPLETE_BASIS_{label}.npz", allow_pickle=False)
        eigen_diff = float(np.max(np.abs(alt["eigenvalues"] - primary["eigenvalues"][:rank])))
        q_primary, _ = np.linalg.qr(primary["components"][:, :rank], mode="reduced")
        subspace_loss = float(max(1 - overlap_curve(q_primary, alt["q"])[:8]))
        held_alt = heldout_independent(mean, within, between, folds, rank)
        prod = pd.read_csv(analytic / "SHARED_DONOR_HELDOUT_PREDICTABILITY.csv")
        prod = prod[prod.sketch.eq(label) & prod.dimension.le(rank)].pivot(index="donor_index", columns="dimension", values="heldout_predictability").sort_index(axis=1).to_numpy()
        held_diff = float(np.max(np.abs(held_alt - prod)))
        independent_bases[label], independent_held[label] = alt, held_alt
        checks.append({"statistic": f"analytic_basis_{label}", "eigen_max_abs": eigen_diff, "prefix_subspace_max_loss_D1_8": subspace_loss, "heldout_max_abs": held_diff, "pass": eigen_diff <= 1e-6 and subspace_loss <= 1e-5 and held_diff <= 1e-5})

    strata = pd.read_csv(analytic / "sufficient_statistics/DONOR_OPERATOR_STRATA.csv")
    counts = strata.groupby("donor_index").size()
    weights = np.asarray([1 / (104 * counts[int(d)]) for d in strata.donor_index], np.float64)
    common_scores = {}
    for label in "AB":
        means = np.asarray(np.load(analytic / f"sufficient_statistics/{label}_stratum_mean.npy", mmap_mode="r"), np.float64)
        score = (means - independent_bases[label]["mean"]) @ independent_bases[label]["components"]
        score -= np.average(score, axis=0, weights=weights)
        common_scores[label] = score * np.sqrt(weights[:, None])
    agreement = []
    for d in range(1, rank + 1):
        qa, _ = np.linalg.qr(common_scores["A"][:, :d], mode="reduced"); qb, _ = np.linalg.qr(common_scores["B"][:, :d], mode="reduced")
        agreement.append(float(np.square(qa.T @ qb).sum() / d))
    production_agreement = pd.read_csv(analytic / "TEACHER_DIMENSION_CALIBRATION_SHARED.csv").groupby("dimension").independent_sketch_subspace_agreement.first().loc[range(1, rank + 1)].to_numpy()
    agreement_diff = float(np.max(np.abs(np.asarray(agreement) - production_agreement)))
    checks.append({"statistic": "independent_sketch_agreement", "max_abs": agreement_diff, "pass": agreement_diff <= 1e-5})

    subset = pd.read_csv(refit / "SHARED_REFIT_NULL_VALIDATION_ROWS.csv", dtype={"donor_id": str})
    maps = np.load(refit / "SHARED_REFIT_EMPIRICAL_NULL_MAPS.npz", allow_pickle=False)
    independent_calibration = []
    for label in "AB":
        primary = np.load(analytic / f"SHARED_OVERCOMPLETE_BASIS_{label}.npz", allow_pickle=False)
        feature = np.load(matrix / f"{label}_views.npy", mmap_mode="r")
        component, center = np.asarray(primary["components"][:, :rank], np.float64), np.asarray(primary["mean"], np.float64)
        donor_n = np.zeros(104, np.int64); mean_sum = np.zeros((104, rank)); within_sum = np.zeros((104, rank, rank)); between_sum = np.zeros_like(within_sum)
        donor_parts = [[] for _ in donors]
        order_concat, indptr, offsets = maps[f"{label}_order_concat"], maps[f"{label}_order_indptr"], maps[f"{label}_offsets"]
        for stratum, group in subset.groupby("stratum_index", sort=True):
            d = donor_ix[str(group.donor_id.iloc[0])]; indices = group.row_index.to_numpy(np.int64)
            score = (np.asarray(feature[indices], np.float64) - center) @ component
            n = len(score); donor_n[d] += n; mean_sum[d] += score.sum(axis=(0, 1))
            local_within = sum(score[:, v].T @ score[:, v] for v in range(4)); summed = score.sum(axis=1)
            within_sum[d] += local_within; between_sum[d] += summed.T @ summed - local_within
            order = order_concat[indptr[stratum]:indptr[stratum + 1]].astype(int); score = score[order]
            permuted = np.empty((reps, n, 4, rank), np.float32); positions = np.arange(n)[None]
            for view in range(4): permuted[:, :, view] = score[(positions + offsets[:, stratum, view, None]) % n, view]
            donor_parts[d].append(permuted)
        mean = mean_sum / (donor_n[:, None] * 4); within = within_sum / (donor_n[:, None, None] * 4); between = between_sum / (donor_n[:, None, None] * 12)
        full_observed = fit_independent(mean, within, between, np.arange(104), rank)
        observed_eigen = np.empty((reps, rank)); observed_stability = np.empty((reps, rank)); sampled_all = []
        for rep in range(reps):
            sampled = np.concatenate([np.random.default_rng(seed_from(rng["donor_bootstrap"], level, label, rep, source)).choice(np.flatnonzero(sources == source), size=np.count_nonzero(sources == source), replace=True) for source in sorted(set(sources))])
            sampled_all.append(sampled); fitted = fit_independent(mean, within, between, sampled, rank)
            observed_eigen[rep] = fitted["eigenvalues"]; observed_stability[rep] = overlap_curve(full_observed["q"], fitted["q"])
        null_between = np.zeros((reps, 104, rank, rank), np.float32)
        for d, parts in enumerate(donor_parts):
            permuted = np.concatenate(parts, axis=1).astype(np.float64); cross = np.zeros((reps, rank, rank))
            for v in range(4):
                for w in range(v + 1, 4):
                    product = np.einsum("rni,rnj->rij", permuted[:, :, v], permuted[:, :, w], optimize=True); cross += product + product.transpose(0, 2, 1)
            null_between[:, d] = cross / (donor_n[d] * 12)
        null_eigen = np.empty((reps, rank)); null_stability = np.empty((reps, rank)); null_held = np.empty((reps, 104, rank), np.float32)
        for rep in range(reps):
            fitted = fit_independent(mean, within, null_between[rep], np.arange(104), rank); boot = fit_independent(mean, within, null_between[rep], sampled_all[rep], rank)
            null_eigen[rep] = fitted["eigenvalues"]; null_stability[rep] = overlap_curve(fitted["q"], boot["q"]); null_held[rep] = heldout_independent(mean, within, null_between[rep], folds, rank)
        observed_held = heldout_independent(mean, within, between, folds, rank)
        production = np.load(refit / f"SHARED_REFIT_EMPIRICAL_NULL_{label}.npz", allow_pickle=False)
        diffs = {
            "observed_eigen": float(np.max(np.abs(observed_eigen - production["observed_eigenvalues"]))),
            "null_eigen": float(np.max(np.abs(null_eigen - production["null_eigenvalues"]))),
            "observed_stability": float(np.max(np.abs(observed_stability - production["observed_stability"]))),
            "null_stability": float(np.max(np.abs(null_stability - production["null_stability"]))),
            "observed_heldout": float(np.max(np.abs(observed_held - production["observed_heldout"]))),
            "null_heldout": float(np.max(np.abs(null_held - production["null_heldout"]))),
        }
        checks.append({"statistic": f"refitted_empirical_null_{label}", **diffs, "pass": all(value <= 1e-5 for value in diffs.values())})
        oe_m, oe_se = observed_eigen.mean(0), observed_eigen.std(0, ddof=1) / math.sqrt(reps); ne_m, ne_se = null_eigen.mean(0), null_eigen.std(0, ddof=1) / math.sqrt(reps)
        for j in range(rank):
            signal = bool(np.all((oe_m[:j+1] - oe_se[:j+1]) > (ne_m[:j+1] + ne_se[:j+1])))
            stability = bool(observed_stability[:, j].mean() - observed_stability[:, j].std(ddof=1)/math.sqrt(reps) > null_stability[:, j].mean() + null_stability[:, j].std(ddof=1)/math.sqrt(reps))
            null_donor = null_held[:, :, j].mean(0); predict = bool(observed_held[:, j].mean() - observed_held[:, j].std(ddof=1)/math.sqrt(104) > null_held[:, :, j].mean() + null_donor.std(ddof=1)/math.sqrt(104))
            independent_calibration.append({"sketch": label, "dimension": j+1, "signal": signal, "stability": stability, "predictability": predict, "joint": signal and stability and predict})

    cal = pd.DataFrame(independent_calibration)
    common = cal.groupby("dimension").joint.all()
    # Independent implementation of the frozen leading-prefix rule.  Do not
    # import or call the production selector: the first absent/false dimension
    # terminates eligibility and later true dimensions cannot re-enter.
    supported = []
    for dimension in range(1, rank + 1):
        if dimension not in common.index or not bool(common.loc[dimension]):
            break
        supported.append(dimension)
    paired = (independent_held["A"] + independent_held["B"]) * 0.5; curve_mean, curve_se = paired.mean(0), paired.std(0, ddof=1)/math.sqrt(104)
    candidate, interval = None, []
    if supported:
        best = max(supported, key=lambda d: curve_mean[d-1]); threshold = curve_mean[best-1] - curve_se[best-1]
        interval = [d for d in supported if curve_mean[d-1] >= threshold]; candidate = min(interval)
    selected = json.loads((corrected / "SHARED_DIMENSION_SELECTION_LEVEL_REFIT_CORRECTED.json").read_text())
    selection_pass = candidate == selected["candidate_D_shared"] and ([min(interval), max(interval)] if interval else None) == selected["one_se_dimension_interval"]
    checks.append({"statistic": "one_se_selection", "independent_candidate": candidate, "production_candidate": selected["candidate_D_shared"], "independent_interval": interval, "pass": selection_pass})
    check_table = pd.DataFrame(checks); check_path = out / "INDEPENDENT_SHARED_STATISTIC_AGREEMENT.csv"; check_table.to_csv(check_path, index=False, lineterminator="\n")
    passed = bool(check_table["pass"].all())
    result = {"schema": "full104-independent-shared-validator-v1", "status": "PASS_INDEPENDENT_SHARED_VALIDATOR" if passed else "STOP_INDEPENDENT_SHARED_VALIDATOR", "result_state": "QUALIFIED" if passed else "EXPLORATORY", "sample_level": level, "candidate_D_shared": candidate, "checks": checks, "independent_implementation": "symmetric whitening plus numpy.linalg.eigh; no production statistic import", "input_hashes": {"harness": sha(harness / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1_MANIFEST.csv"), "matrix": sha(matrix / "PHASE2_FEATURE_MATRIX_MANIFEST.csv"), "analytic": sha(analytic / f"SHARED_LEVEL{level}_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"), "refit_null": sha(refit / "SHARED_REFIT_EMPIRICAL_NULL_MANIFEST.csv"), "selection": sha(corrected / "SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv"), "code": sha(Path(__file__))}}
    result_path = out / "INDEPENDENT_SHARED_VALIDATION.json"; result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = out / "INDEPENDENT_SHARED_VALIDATION_MANIFEST.csv"; files = [check_path, result_path, Path(__file__)]
    pd.DataFrame([{"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (out / "INDEPENDENT_SHARED_VALIDATION_ROOT_SHA256.txt").write_text(sha(manifest) + "\n", encoding="ascii")
    print(json.dumps({"status": result["status"], "candidate_D_shared": candidate, "manifest_sha256": sha(manifest)}, indent=2))
    if not passed: raise SystemExit(2)


if __name__ == "__main__":
    main()
