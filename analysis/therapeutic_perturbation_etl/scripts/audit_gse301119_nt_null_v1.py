#!/usr/bin/env python3
"""GSE301119 outcome-blind *design* qualification; development-data NT-vs-NT test.

This script must run on the authenticated GPU laptop's existing neutral export.
It never needs FULL104 or protected outcomes. It tests the *published estimator*
on genuine non-targeting guides partitioned into pseudo-target and remaining-NT
groups, matched within donor for guide-group count and approximate cell count.

A synthetic CI PASS qualifies implementation only. Physical null results, even
if negative, cannot establish causal or adult-brain transport validity. A
median-centered sensitivity analysis below is NOT edgeR TMM or DESeq2.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

PSEUDOCOUNT = 1.0
EXPECTED_SOURCE = {
    "CRISPRi": "e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549",
    "CRISPRa": "9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90",
}
FOCUS = ("CLU", "CCL22", "MMP12", "CXCL10", "CXCL11", "MT1H", "MT1G")
DONORS = ("D1", "D2")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def lines(path):
    return [s.strip() for s in Path(path).read_text(encoding="utf-8-sig").splitlines()]


def load_modality(root, mod, export):
    """Validate known RDS provenance, counted bytes, dimensions, group identity."""
    e = export.get("exports", {}).get(mod)
    if not isinstance(e, dict):
        raise ValueError(f"{mod}: missing neutral export receipt")
    if e.get("source_rds_sha256_after_export") != EXPECTED_SOURCE[mod]:
        raise ValueError(f"{mod}: source-RDS SHA does not match frozen physical producer")
    root = Path(root)
    paths = {suffix: root / f"{mod}_{suffix}" for suffix in
             ("counts_int32.bin", "shape.txt", "features.txt", "gd_meta.csv")}
    for p in paths.values():
        if not p.is_file():
            raise ValueError(f"{mod}: missing {p}")
    count_path = paths["counts_int32.bin"]
    if sha256(count_path) != e.get("counts_bin_sha256"):
        raise ValueError(f"{mod}: count binary SHA mismatch against exporter receipt")
    shape = lines(paths["shape.txt"])
    if len(shape) != 2:
        raise ValueError(f"{mod}: malformed shape")
    nf, ng = map(int, shape)
    if nf <= 0 or ng <= 0 or count_path.stat().st_size != nf * ng * 4:
        raise ValueError(f"{mod}: truncated, padded, or empty raw count file")
    if [nf, ng] != e.get("dim"):
        raise ValueError(f"{mod}: export receipt dimension mismatch")
    features = lines(paths["features.txt"])
    with paths["gd_meta.csv"].open(encoding="utf-8-sig", newline="") as fh:
        meta = list(csv.DictReader(fh))
    required = {"guide_donor", "donor", "crispr", "Gene_Targeted", "n_cells"}
    if len(features) != nf or len(meta) != ng or len(set(features)) != nf:
        raise ValueError(f"{mod}: feature or metadata shape/identity mismatch")
    if not meta or not required.issubset(meta[0]):
        raise ValueError(f"{mod}: required metadata missing")
    keys = [x["guide_donor"] for x in meta]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{mod}: duplicate guide-donor identities")
    if {x["donor"] for x in meta} != set(DONORS):
        raise ValueError(f"{mod}: unexpected donor set")
    if {x["crispr"] for x in meta} != {"NT", "Perturbed"}:
        raise ValueError(f"{mod}: unexpected or absent group roles")
    for x in meta:
        if not x["guide_donor"] or int(x["n_cells"]) <= 0:
            raise ValueError(f"{mod}: invalid cell count or group key")
        if x["crispr"] == "Perturbed" and not x["Gene_Targeted"]:
            raise ValueError(f"{mod}: perturbed guide lacks target")
    counts = np.memmap(count_path, dtype="<i4", mode="r",
                       shape=(nf, ng), order="F")
    # Scan by bounded columns: a single negative count cannot pass unnoticed.
    if any(np.any(counts[:, a:b] < 0) for a in range(0, ng, 32)
           for b in [min(a + 32, ng)]):
        raise ValueError(f"{mod}: negative raw count")
    if any(np.any(counts[:, a:b].sum(axis=0, dtype=np.int64) <= 0)
           for a in range(0, ng, 32) for b in [min(a + 32, ng)]):
        raise ValueError(f"{mod}: zero-depth guide group")
    return counts, features, meta, {k: sha256(v) for k, v in paths.items()}


def logcpm(raw):
    raw = np.asarray(raw, dtype=np.float64)
    total = raw.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValueError("nonpositive pseudobulk library")
    return np.log2(raw * (1e6 / total) + PSEUDOCOUNT)


def group_raw(counts, indices):
    if not len(indices):
        raise ValueError("no guide groups")
    return np.asarray(counts[:, indices], dtype=np.int64).sum(axis=1, dtype=np.int64)


def lfc(counts, group, controls):
    return logcpm(group_raw(counts, group)) - logcpm(group_raw(counts, controls))


def median_centered_sensitivity(effect, group, controls, counts):
    """Diagnostic only: center the logCPM effect on genes detected on both sides.

    NOT an edgeR TMM estimate, NOT DESeq2 median-of-ratios, and not a
    correction for target-vs-NT cell-state mixture differences.
    """
    a, b = group_raw(counts, group), group_raw(counts, controls)
    shared = (a > 0) & (b > 0)
    if shared.sum() < 100:
        return None
    return effect - float(np.median(effect[shared]))


def select_matched_nt(nt_indices, ncell, n_guides, target_cells, rng,
                      attempts=128, max_rel_error=0.40, min_control_guides=10):
    """Sample *whole NT guide groups*, never fractionate cells within a guide.

    Selection is conditional on the real target's guide and cell count, not its
    effect. The remaining guides, disjoint from the pseudo-target, form the NT
    reference. A failure to match is MISSING, not a zero effect.
    """
    nt_indices = np.asarray(nt_indices, dtype=np.int64)
    if n_guides <= 0 or n_guides > len(nt_indices) - min_control_guides:
        return None
    if target_cells <= 0:
        return None
    best, best_err = None, float("inf")
    for _ in range(attempts):
        chosen = np.sort(rng.choice(nt_indices, size=n_guides, replace=False))
        c = int(ncell[chosen].sum())
        err = abs(c - target_cells) / target_cells
        if err < best_err:
            best, best_err = chosen, err
            if err == 0:
                break
    if best_err > max_rel_error:
        return None
    remaining = nt_indices[~np.isin(nt_indices, best)]
    if remaining.size < min_control_guides:
        raise ValueError("internal disjoint NT partition failure")
    return best, remaining, float(best_err)


def top_down(effect, k=25):
    if not np.all(np.isfinite(effect)):
        raise ValueError("nonfinite estimator output")
    return np.argsort(effect, kind="stable")[:min(k, effect.size)]


def _ranks(a):
    """Tie-averaged ranks without scipy; NaN handled by caller."""
    a = np.asarray(a, dtype=float)
    idx = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), dtype=float)
    start = 0
    while start < len(a):
        stop = start + 1
        while stop < len(a) and a[idx[stop]] == a[idx[start]]:
            stop += 1
        ranks[idx[start:stop]] = (start + stop - 1) / 2.0
        start = stop
    return ranks


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y)
    if keep.sum() < 3 or len(set(x[keep])) < 2 or len(set(y[keep])) < 2:
        return None
    return float(np.corrcoef(_ranks(x[keep]), _ranks(y[keep]))[0, 1])


def analyse(counts, features, meta, *, seed=40119, reps=80, max_rel_error=.40):
    """Cross-donor effects only when both donors are supported and null matched."""
    if reps < 40:
        raise ValueError("at least 40 predeclared null partitions required")
    rng = np.random.default_rng(seed)
    role = np.array([m["crispr"] for m in meta])
    donor = np.array([m["donor"] for m in meta])
    target = np.array([m["Gene_Targeted"] for m in meta])
    ncell = np.array([int(m["n_cells"]) for m in meta], dtype=np.int64)
    nt = {d: np.flatnonzero((role == "NT") & (donor == d)) for d in DONORS}
    if any(len(nt[d]) < 20 for d in DONORS):
        raise ValueError("too few NT guide groups in a donor")
    all_targets = sorted(set(target[role == "Perturbed"]))
    focus_idx = {name: features.index(name) for name in FOCUS if name in features}
    obs_down, null_down = Counter(), Counter()
    observed_effects = {}
    null_effects = {}
    records = []
    for t in all_targets:
        groups = {d: np.flatnonzero((role == "Perturbed") &
                                   (donor == d) & (target == t)) for d in DONORS}
        # Cross-donor target matrix requires ≥10 target cells in *each* donor.
        sizes = {d: int(ncell[groups[d]].sum()) for d in DONORS}
        if any(sizes[d] < 10 for d in DONORS):
            records.append({"target": t, "status": "NOT_CROSS_DONOR_ESTIMABLE",
                            "target_cells": sizes})
            continue
        real_by_donor = {d: lfc(counts, groups[d], nt[d]) for d in DONORS}
        real = (real_by_donor["D1"] + real_by_donor["D2"]) / 2.0
        observed_effects[t] = real
        for i in top_down(real):
            obs_down[features[i]] += 1
        null_by_rep = []
        matches = 0
        rel_errors = []
        for _ in range(reps):
            draw = {}
            for d in DONORS:
                match = select_matched_nt(nt[d], ncell, len(groups[d]),
                                          sizes[d], rng,
                                          max_rel_error=max_rel_error)
                if match is None:
                    break
                pseudo, remaining, err = match
                draw[d] = lfc(counts, pseudo, remaining)
                rel_errors.append(err)
            if len(draw) == len(DONORS):
                fake = (draw["D1"] + draw["D2"]) / 2.0
                null_by_rep.append(fake)
                for i in top_down(fake):
                    null_down[features[i]] += 1
                matches += 1
        row = {"target": t, "status": "MATCHED" if matches >= reps // 2
               else "INSUFFICIENT_NT_MATCHES",
               "target_cells": sizes,
               "target_guide_groups": {d: len(groups[d]) for d in DONORS},
               "control_cells": {d: int(ncell[nt[d]].sum()) for d in DONORS},
               "control_guide_groups": {d: int(len(nt[d])) for d in DONORS},
               "null_matches": matches, "null_reps_requested": reps,
               "median_relative_cell_match_error": (
                   float(np.median(rel_errors)) if rel_errors else None),
               "observed_top25_mean_abs_log2fc": float(
                   np.mean(np.abs(real[np.argsort(-np.abs(real))[:25]]))),
               "observed_top25_down": [features[i] for i in top_down(real)],
               "focus": {}}
        for name, ix in focus_idx.items():
            fake_values = np.array([a[ix] for a in null_by_rep])
            real_value = float(real[ix])
            row["focus"][name] = {
                "observed_log2fc": real_value,
                "null_median": float(np.median(fake_values)) if len(fake_values) else None,
                "null_q025": float(np.quantile(fake_values, .025)) if len(fake_values) else None,
                "null_q975": float(np.quantile(fake_values, .975)) if len(fake_values) else None,
                "diagnostic_two_sided_exceedance": (
                    float((1 + np.sum(np.abs(fake_values) >= abs(real_value))) /
                          (1 + len(fake_values))) if len(fake_values) else None),
            }
        # Alternative centering does not cure compositional cell-state shifts.
        centered = {d: median_centered_sensitivity(real_by_donor[d],
                         groups[d], nt[d], counts) for d in DONORS}
        if all(v is not None for v in centered.values()):
            alt = (centered["D1"] + centered["D2"]) / 2
            row["median_centered_top25_down"] = [features[i] for i in top_down(alt)]
            row["median_centered_focus"] = {g: float(alt[i])
                                             for g, i in focus_idx.items()}
        else:
            row["median_centered_top25_down"] = None
            row["median_centered_focus"] = None
        null_effects[t] = null_by_rep
        records.append(row)
    matched = [r for r in records if r["status"] == "MATCHED"]
    eligible = [r for r in records if r["status"] != "NOT_CROSS_DONOR_ESTIMABLE"]
    n_draws = sum(len(x) for x in null_effects.values())
    obs_sizes = [min(r["target_cells"].values()) for r in matched]
    obs_ampl = [r["observed_top25_mean_abs_log2fc"] for r in matched]
    return {
        "schema": "GSE301119_NT_VS_NT_MATCHED_NULL_V1",
        "estimator": "log2(CPM_target+1) - log2(CPM_donor_NT+1), pooled raw guide counts",
        "null": "within-donor random NT whole-guide pseudo-target, matched guide count and approximate cell count, remaining NT as disjoint controls",
        "limitations": [
            "Diagnostic re-use of finite NT pool; empirical exceedance is NOT a biological p-value.",
            "NT null can reveal estimator artifacts, but its absence cannot prove a targeting effect.",
            "Approximate matching and potential targeting-specific cell-state composition remain.",
            "Median centering is sensitivity only; neither edgeR TMM nor DESeq2.",
            "Two donors: population generalization and adult-brain transport not identifiable."],
        "declared": {"seed": seed, "null_reps": reps,
                     "max_relative_cell_match_error": max_rel_error,
                     "min_target_cells_per_donor": 10},
        "targets_total": len(all_targets),
        "cross_donor_eligible": len(eligible),
        "targets_with_at_least_half_null_reps": len(matched),
        "all_null_replicates_obtained": n_draws,
        "min_cell_count_vs_effect_spearman_matched": spearman(obs_sizes, obs_ampl),
        "top25_down_recurrence_observed": dict(obs_down.most_common(40)),
        "top25_down_recurrence_nt_null": dict(null_down.most_common(40)),
        "focus_gene_presence": {g: g in focus_idx for g in FOCUS},
        "focus_top25_down_frequency": {
            g: {"observed_targets": obs_down[g],
                "null_partitions": null_down[g],
                "null_partition_denominator": n_draws} for g in FOCUS},
        "per_target": records,
        "verdict": ("MATCHING_DIAGNOSTIC_READY" if
                    len(eligible) > 0 and len(matched) >= .75 * len(eligible)
                    else "STOP_INSUFFICIENT_NT_MATCHING"),
        "training_authorized": False,
        "protected_outcomes_opened": False,
        "therapeutic_ranking_authorized": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--neutral-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=80)
    ap.add_argument("--seed", type=int, default=40119)
    ap.add_argument("--max-cell-relative-error", type=float, default=.40)
    args = ap.parse_args(argv)
    if args.out_dir.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS; use a NEW versioned directory")
    if not (0 < args.max_cell_relative_error <= .5):
        raise SystemExit("STOP_MATCH_ERROR_BOUND_INVALID")
    rec_path = args.neutral_dir / "NEUTRAL_EXPORT_RECEIPT_V1.json"
    export = json.loads(rec_path.read_text(encoding="utf-8-sig"))
    if export.get("schema") != "GSE301119_NEUTRAL_ARRAY_EXPORT_V1":
        raise SystemExit("STOP_WRONG_NEUTRAL_EXPORT_SCHEMA")
    modalities = {}
    for mod in ("CRISPRi", "CRISPRa"):
        c, feats, meta, hashes = load_modality(args.neutral_dir, mod, export)
        result = analyse(c, feats, meta, reps=args.reps,
                         seed=args.seed + (0 if mod == "CRISPRi" else 1),
                         max_rel_error=args.max_cell_relative_error)
        result["neutral_input_sha256"] = hashes
        result["source_rds_sha256"] = EXPECTED_SOURCE[mod]
        modalities[mod] = result
    report = {"schema": "GSE301119_NT_NULL_CROSS_MODAL_V1",
              "status": ("DIAGNOSTIC_READY" if all(
                  m["verdict"] == "MATCHING_DIAGNOSTIC_READY"
                  for m in modalities.values()) else "STOP_INSUFFICIENT_NT_MATCHING"),
              "scope": "DEVELOPMENT_ONLY; real physical input required",
              "modalities": modalities,
              "jepa_prediction_used": False, "training_authorized": False}
    args.out_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nt-null-stage-",
                                     dir=args.out_dir.parent) as td:
        path = Path(td) / "GSE301119_NT_NULL_RECEIPT_V1.json"
        path.write_text(json.dumps(report, indent=2, allow_nan=False),
                        encoding="utf-8")
        os.rename(td, args.out_dir)
    print(report["status"], args.out_dir)
    return 0 if report["status"] == "DIAGNOSTIC_READY" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, MemoryError) as exc:
        print(f"STOP_NT_NULL_INVALID_INPUT_OR_EXECUTION: {exc}", file=sys.stderr)
        sys.exit(2)
