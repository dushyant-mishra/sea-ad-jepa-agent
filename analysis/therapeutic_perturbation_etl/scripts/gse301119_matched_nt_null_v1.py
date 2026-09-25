#!/usr/bin/env python3
"""Predeclared GSE301119 development-only NT-versus-NT negative control.

For each observed target/donor group, form synthetic pseudo-targets by sampling
the SAME NUMBER of donor-matched NT guide groups, selecting on CELL COUNT only.
Each pseudo-target is excluded from its own NT reference. Apply the EXACT legacy
log2(CPM+1) estimator. Compare the seven prospectively specified recurrent genes
and full-transcriptome top/bottom-25 recurrence. No protected data touched.

Null repeats share NT units: they are Monte Carlo references, NOT independent
donors, biological replicates, p-values, or proof that effects are causal.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

EXPECTED_RDS = {
    "CRISPRi": "e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549",
    "CRISPRa": "9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90",
}
SENTINELS = ("CLU", "CCL22", "MMP12", "CXCL10", "CXCL11", "MT1H", "MT1G")
DONORS = ("D1", "D2")
MODALITIES = ("CRISPRi", "CRISPRa")
MIN_CELLS = 10
PSEUDOCOUNT = 1.0
TOP_K = 25
SEED = 301119


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def effects(raw_target, raw_control):
    """The existing producer's log2(raw / all-transcript-counts * 1e6 + 1)."""
    t = np.asarray(raw_target, dtype=np.float64)
    c = np.asarray(raw_control, dtype=np.float64)
    if (t < 0).any() or (c < 0).any() or t.sum() <= 0 or c.sum() <= 0:
        raise ValueError("INVALID_COUNTS_OR_ZERO_DEPTH")
    return np.log2(t / t.sum() * 1e6 + PSEUDOCOUNT) - np.log2(
        c / c.sum() * 1e6 + PSEUDOCOUNT)


def median_ratio_sensitivity(raw_target, raw_control):
    """Exploratory two-sample median-centred log ratio, NOT DESeq2 or TMM.

    Requires positivity in BOTH groups. Missing/zero genes remain NaN, NEVER 0.
    Relies on a majority-unchanged assumption; cannot establish biological truth.
    """
    t, c = np.asarray(raw_target, dtype=np.float64), np.asarray(raw_control, dtype=np.float64)
    both = (t > 0) & (c > 0)
    result = np.full(t.shape, np.nan, dtype=np.float64)
    if int(both.sum()) < 100:  # fail the sensitivity rather than reporting an unstable median
        return result, int(both.sum())
    log_ratios = np.log2(t[both]) - np.log2(c[both])
    result[both] = log_ratios - np.median(log_ratios)
    return result, int(both.sum())


def matched_subset(nt_indices, cell_counts, n_guides, target_cells, rng,
                   trials=256, max_cell_ratio=1.5):
    """Choose ONLY on guide count and cell count, never RNA/depth/effect values."""
    if n_guides < 1 or n_guides >= len(nt_indices) or target_cells < MIN_CELLS:
        return None, None
    n = np.asarray(nt_indices, dtype=np.int64)
    cell = np.asarray(cell_counts, dtype=np.int64)
    best, error, best_cells = None, float("inf"), None
    for _ in range(trials):
        pick = rng.choice(len(n), size=n_guides, replace=False)
        selected_cells = int(cell[pick].sum())
        if selected_cells <= 0:
            continue
        discrepancy = abs(np.log(selected_cells / target_cells))
        if discrepancy < error:
            best, error, best_cells = n[pick], discrepancy, selected_cells
    if best is None or max(best_cells / target_cells, target_cells / best_cells) > max_cell_ratio:
        return None, None
    return np.sort(best), best_cells


def depth_only_null(full_nt, target_depth, rng):
    """Binomially thin the SAME pooled NT transcript counts to target-depth expectation.

    This preserves the aggregate NT molecular composition in expectation and changes
    only read sampling/depth. It is a diagnostic, not an independent sample.
    """
    full_nt = np.asarray(full_nt, dtype=np.int64)
    total = int(full_nt.sum())
    if target_depth <= 0 or total <= 0 or target_depth >= total:
        return None
    p = float(target_depth / total)
    thinned = rng.binomial(full_nt, p).astype(np.int64)
    if int(thinned.sum()) <= 0:
        return None
    return thinned


def top_extremes(effect, gene_indices):
    k = min(TOP_K, len(effect))
    down = set(np.argpartition(effect, k - 1)[:k].tolist())
    up = set(np.argpartition(effect, -k)[-k:].tolist())
    return {gene: {"down": index in down, "up": index in up}
            for gene, index in gene_indices.items()}


def verify_identity_cert(root, mod, v1_receipt_path, cert):
    """Require a *separately rederived* original-RDS identity certification.

    Metadata hashes alone do not establish biological truth; the v2 R certifier
    must have reconstructed all four neutral files from the authenticated RDS.
    The CPU fixtures exercise this contract using synthetic certificates only.
    """
    if (cert.get("schema") != "GSE301119_NEUTRAL_IDENTITY_CERTIFICATION_V2"
        or cert.get("v1_export_receipt_sha256") != sha256(v1_receipt_path)
        or cert.get("protected_outcome_opened") is not False
        or cert.get("training_authorized") is not False
        or cert.get("therapeutic_ranking") is not False):
        raise ValueError("STOP_NEUTRAL_IDENTITY_CERT_SCHEMA_OR_SCOPE_UNBOUND")
    entry = cert.get("file_validation", {}).get(mod, {})
    if (entry.get("source_rds_sha256") != EXPECTED_RDS[mod]
        or entry.get("equality") !=
            "ALL_FOUR_NEUTRAL_EXPORT_FILES_RECONSTRUCTED_BYTE_IDENTICAL_FROM_ORIGINAL_RDS"):
        raise ValueError(f"{mod}: STOP_NEUTRAL_IDENTITY_CERT_SOURCE_UNBOUND")
    paths = {
        "counts_bin": root / f"{mod}_counts_int32.bin",
        "shape": root / f"{mod}_shape.txt",
        "features": root / f"{mod}_features.txt",
        "gd_meta": root / f"{mod}_gd_meta.csv",
    }
    expected_hashes = entry.get("exported_file_sha256", {})
    if set(expected_hashes) != set(paths):
        raise ValueError(f"{mod}: STOP_NEUTRAL_IDENTITY_FILES_INCOMPLETE")
    for name, path in paths.items():
        if not path.is_file() or sha256(path) != expected_hashes[name]:
            raise ValueError(f"{mod}: STOP_NEUTRAL_IDENTITY_FILE_DIGEST_{name}")
    return entry


def load_modality(root, mod, receipt, identity_cert):
    verify_identity_cert(root, mod, root / "NEUTRAL_EXPORT_RECEIPT_V1.json", identity_cert)
    r = receipt.get("exports", {}).get(mod, {})
    if r.get("source_rds_sha256_after_export") != EXPECTED_RDS[mod]:
        raise ValueError(f"{mod}: SOURCE_RDS_DIGEST_NOT_AUTHENTICATED")
    bp = root / f"{mod}_counts_int32.bin"
    if sha256(bp) != r.get("counts_bin_sha256"):
        raise ValueError(f"{mod}: NEUTRAL_COUNT_EXPORT_DIGEST_MISMATCH")
    shape = [int(s.strip()) for s in (root / f"{mod}_shape.txt").read_text().splitlines() if s.strip()]
    if len(shape) != 2 or shape[0] <= 0 or shape[1] <= 0:
        raise ValueError(f"{mod}: INVALID_SHAPE")
    if bp.stat().st_size != 4 * shape[0] * shape[1] or list(r.get("dim", [])) != shape:
        raise ValueError(f"{mod}: COUNT_BYTES_DIMENSION_MISMATCH")
    feats = (root / f"{mod}_features.txt").read_text().splitlines()
    with open(root / f"{mod}_gd_meta.csv", newline="", encoding="utf-8-sig") as f:
        meta = list(csv.DictReader(f))
    if len(feats) != shape[0] or len(set(feats)) != len(feats) or len(meta) != shape[1]:
        raise ValueError(f"{mod}: IDENTITY_OR_SHAPE_MISMATCH")
    if len({m["guide_donor"] for m in meta}) != len(meta):
        raise ValueError(f"{mod}: DUPLICATE_GUIDE_DONOR")
    if set(m["donor"] for m in meta) != set(DONORS):
        raise ValueError(f"{mod}: EXPECTED_TWO_DONORS")
    if set(m["crispr"] for m in meta) != {"Perturbed", "NT"}:
        raise ValueError(f"{mod}: UNEXPECTED_GROUP_TYPE")
    n_cells = np.array([int(m["n_cells"]) for m in meta], dtype=np.int64)
    if (n_cells < 0).any() or any(not m["Gene_Targeted"] for m in meta if m["crispr"] == "Perturbed"):
        raise ValueError(f"{mod}: INVALID_GROUP_METADATA")
    counts = np.memmap(bp, dtype="<i4", mode="r", shape=tuple(shape), order="F")
    if np.any(counts < 0):
        raise ValueError(f"{mod}: NEGATIVE_COUNTS")
    return counts, feats, meta, n_cells


def audit_modality(root, mod, receipt, draws, max_cell_ratio, rng, identity_cert):
    counts, feats, meta, cell = load_modality(root, mod, receipt, identity_cert)
    index = {gene: i for i, gene in enumerate(feats) if gene in SENTINELS}
    donor = np.array([m["donor"] for m in meta])
    role = np.array([m["crispr"] for m in meta])
    targeted = np.array([m["Gene_Targeted"] for m in meta])
    targets = sorted(set(targeted[role == "Perturbed"]))
    report = {"source_rds_sha256": EXPECTED_RDS[mod],
              "counts_bin_sha256": sha256(root / f"{mod}_counts_int32.bin"),
              "gd_meta_sha256": sha256(root / f"{mod}_gd_meta.csv"),
              "features_sha256": sha256(root / f"{mod}_features.txt"),
              "assayed_gene_count": len(feats), "targets": len(targets),
              "missing_sentinel_genes": sorted(set(SENTINELS) - set(index)),
              "donors": {}}
    for d in DONORS:
        nt = np.flatnonzero((role == "NT") & (donor == d))
        if len(nt) < 3 or int(cell[nt].sum()) <= 0:
            raise ValueError(f"{mod}/{d}: NO_USABLE_NT_REFERENCE")
        nt_total = counts[:, nt].sum(axis=1, dtype=np.int64)
        if int(nt_total.sum()) <= 0:
            raise ValueError(f"{mod}/{d}: ZERO_NT_DEPTH")
        target_rows = {}
        for target in targets:
            ti = np.flatnonzero((role == "Perturbed") & (donor == d) & (targeted == target))
            n_cells = int(cell[ti].sum())
            if n_cells < MIN_CELLS:
                target_rows[target] = {"status": "NOT_ESTIMABLE_TARGET_CELL_SUPPORT",
                                       "cells": n_cells, "guides": len(ti)}
                continue
            raw = counts[:, ti].sum(axis=1, dtype=np.int64)
            if int(raw.sum()) <= 0:
                target_rows[target] = {"status": "NOT_ESTIMABLE_TARGET_ZERO_DEPTH",
                                       "cells": n_cells, "guides": len(ti)}
                continue
            observed = effects(raw, nt_total)
            obs_median, shared = median_ratio_sensitivity(raw, nt_total)
            obs_top = top_extremes(observed, index)
            null_values = {gene: [] for gene in index}
            null_top = {gene: {"down": 0, "up": 0} for gene in index}
            depth_values = {gene: [] for gene in index}
            depth_top = {gene: {"down": 0, "up": 0} for gene in index}
            subset_signatures = set()
            matched_cells, null_absmax, depth_absmax, depth_totals = [], [], [], []
            for _ in range(draws):
                selection, selected_cells = matched_subset(
                    nt, cell[nt], len(ti), n_cells, rng,
                    max_cell_ratio=max_cell_ratio)
                if selection is None:
                    break
                # Do not count the same set repeatedly as additional support.
                sig = tuple(selection.tolist())
                if sig in subset_signatures:
                    continue
                subset_signatures.add(sig)
                pseudo = counts[:, selection].sum(axis=1, dtype=np.int64)
                reference = nt_total - pseudo
                if int(reference.sum()) <= 0 or int(pseudo.sum()) <= 0:
                    continue
                null = effects(pseudo, reference)
                extrema = top_extremes(null, index)
                matched_cells.append(selected_cells)
                null_absmax.append(float(np.max(np.abs(null))))
                for gene, ix in index.items():
                    null_values[gene].append(float(null[ix]))
                    null_top[gene]["down"] += int(extrema[gene]["down"])
                    null_top[gene]["up"] += int(extrema[gene]["up"])
            # Independent diagnostic arm: same pooled NT composition, binomially
            # thinned in read space to the actual target unit's raw depth.
            for _ in range(draws):
                thin = depth_only_null(nt_total, int(raw.sum()), rng)
                if thin is None:
                    break
                de = effects(thin, nt_total)
                extrema = top_extremes(de, index)
                depth_totals.append(int(thin.sum()))
                depth_absmax.append(float(np.max(np.abs(de))))
                for gene, ix in index.items():
                    depth_values[gene].append(float(de[ix]))
                    depth_top[gene]["down"] += int(extrema[gene]["down"])
                    depth_top[gene]["up"] += int(extrema[gene]["up"])

            n = len(matched_cells)
            dn = len(depth_totals)
            if n < draws // 2:
                target_rows[target] = {"status": "NOT_ESTIMABLE_INSUFFICIENT_MATCHED_NT_NULL",
                                       "cells": n_cells, "guides": len(ti),
                                       "matched_null_draws": n}
                continue
            if dn < draws // 2:
                target_rows[target] = {"status": "NOT_ESTIMABLE_INSUFFICIENT_DEPTH_ONLY_NULL",
                                       "cells": n_cells, "guides": len(ti),
                                       "depth_null_draws": dn}
                continue
            details = {}
            for gene, ix in index.items():
                null = np.asarray(null_values[gene], dtype=float)
                dnull = np.asarray(depth_values[gene], dtype=float)
                obs = float(observed[ix])
                details[gene] = {
                    "observed_log2cpm_fc": obs,
                    "null_median": float(np.median(null)),
                    "null_q025_q975": [float(x) for x in np.quantile(null, [0.025, 0.975])],
                    "null_exceedance_fraction_abs": float(np.mean(np.abs(null) >= abs(obs))),
                    "observed_top25_down": bool(obs_top[gene]["down"]),
                    "observed_top25_up": bool(obs_top[gene]["up"]),
                    "null_top25_down_fraction": null_top[gene]["down"] / n,
                    "null_top25_up_fraction": null_top[gene]["up"] / n,
                    "depth_only_null_median": float(np.median(dnull)),
                    "depth_only_null_q025_q975": [float(x) for x in np.quantile(dnull, [0.025, 0.975])],
                    "depth_only_null_exceedance_fraction_abs": float(np.mean(np.abs(dnull) >= abs(obs))),
                    "depth_only_top25_down_fraction": depth_top[gene]["down"] / dn,
                    "depth_only_top25_up_fraction": depth_top[gene]["up"] / dn,
                    "median_centred_log_ratio_sensitivity": (
                        float(obs_median[ix]) if np.isfinite(obs_median[ix]) else None),
                }
            target_rows[target] = {
                "status": "MATCHED_DESCRIPTIVE_NULL_ONLY",
                "cells": n_cells, "guides": len(ti), "unit_raw_depth": int(raw.sum()),
                "full_nt_cells": int(cell[nt].sum()), "full_nt_depth": int(nt_total.sum()),
                "nt_depth_to_unit_depth": float(nt_total.sum() / raw.sum()),
                "median_ratio_shared_positive_genes": shared,
                "matched_null_draws": n, "matched_null_cells_min_max": [
                    int(min(matched_cells)), int(max(matched_cells))],
                "null_max_abs_fc_median": float(np.median(null_absmax)),
                "depth_only_null_draws": dn,
                "depth_only_raw_total_min_max": [int(min(depth_totals)), int(max(depth_totals))],
                "depth_only_expected_raw_total": int(raw.sum()),
                "depth_only_max_abs_fc_median": float(np.median(depth_absmax)),
                "sentinel_genes": details,
            }
        report["donors"][d] = {
            "nt_guides": int(len(nt)), "nt_cells": int(cell[nt].sum()),
            "nt_total_raw_depth": int(nt_total.sum()), "targets": target_rows}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neutral-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--identity-cert", required=True, type=Path,
                        help="V2 certification rederived from original authenticated RDS by certify_gse301119_neutral_identity_v2.R")
    parser.add_argument("--draws", type=int, default=64)
    parser.add_argument("--max-cell-ratio", type=float, default=1.5)
    args = parser.parse_args(argv)
    if args.draws < 16 or not np.isfinite(args.max_cell_ratio) or args.max_cell_ratio < 1:
        parser.error("draws must be >=16 and max-cell-ratio >=1")
    if args.out_dir.exists():  # never overwrite any previous receipt
        raise SystemExit("STOP_OUTPUT_EXISTS__USE_NEW_VERSIONED_DIRECTORY")
    receipt_path = args.neutral_dir / "NEUTRAL_EXPORT_RECEIPT_V1.json"
    if not receipt_path.is_file():
        raise SystemExit("STOP_MISSING_NEUTRAL_EXPORT_RECEIPT")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if receipt.get("schema") != "GSE301119_NEUTRAL_ARRAY_EXPORT_V1":
        raise SystemExit("STOP_UNEXPECTED_NEUTRAL_EXPORT_SCHEMA")
    if not args.identity_cert.is_file():
        raise SystemExit("STOP_MISSING_RDS_BACKED_NEUTRAL_IDENTITY_CERT_V2")
    cert = json.loads(args.identity_cert.read_text(encoding="utf-8-sig"))
    report = {
        "schema": "GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1",
        "status": "DEVELOPMENT_ONLY_NO_SCIENTIFIC_QUALIFICATION",
        "predeclared": {"draws": args.draws, "max_cell_ratio": args.max_cell_ratio,
                        "matching_variables": ["donor", "guide_count_exact", "cell_count_ratio"],
                        "selection_does_not_use_RNA_or_depth": True,
                        "depth_only_arm": "binomial thinning of full donor NT pooled counts to target raw-depth expectation",
                        "seed": SEED, "pseudocount": PSEUDOCOUNT,
                        "top_k_each_tail": TOP_K, "sentinels": SENTINELS},
        "neutral_export_receipt_sha256": sha256(receipt_path),
        "neutral_identity_certification_v2_sha256": sha256(args.identity_cert),
        "script_sha256": sha256(Path(__file__)),
        "modalities": {},
        "limitations": [
            "NT guide resamples overlap; they are not independent biological replicates or p-values",
            "Matching on guide/cell counts does not balance cell-state composition",
            "Depth-only binomial draws preserve aggregate NT composition only in expectation and share the full NT source",
            "Pseudo-target NT excludes its guides from its own donor NT comparator",
            "Median-centred log ratio is exploratory only; zeros are missing, not true zero effects",
            "No claim of real intervention causality or transport to adult brain",
        ],
        "training_authorized": False, "protected_outcome_opened": False,
        "therapeutic_ranking": False,
    }
    rng = np.random.default_rng(SEED)
    for mod in MODALITIES:
        report["modalities"][mod] = audit_modality(
            args.neutral_dir, mod, receipt, args.draws, args.max_cell_ratio, rng, cert)
    args.out_dir.mkdir(parents=True, exist_ok=False)
    out = args.out_dir / "GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1.json"
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"DEVELOPMENT DESCRIPTIVE NULL COMPLETE: {out}")


if __name__ == "__main__":
    main()
