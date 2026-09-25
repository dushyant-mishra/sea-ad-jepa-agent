#!/usr/bin/env python3
"""Development-only GSE301119 depth-only NT null: same donor, same NT cells.

Binomially thin pooled raw NT gene counts to the expected total RNA depth of
each genuine donor x target unit. This is a *coupled reference* diagnostic:
the thinned pseudo-target and full NT denominator come from the SAME source
molecules; it is not an independent NT replicate or a formal null p-value.
Unlike the separate matched-NT guide resampling, this deliberately holds the
source cell composition fixed. It isolates read-sampling / detection effects
under an idealized uniform thinning model. No protected outcome is read.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from gse301119_matched_nt_null_v1 import (
    EXPECTED_RDS, SENTINELS, DONORS, MODALITIES, MIN_CELLS, SEED,
    effects, top_extremes, sha256, load_modality
)


def depth_only_draw(raw_nt, target_depth, rng):
    """One read-level thinning at probability target_depth / full NT depth."""
    nt = np.asarray(raw_nt, dtype=np.int64)
    if nt.ndim != 1 or np.any(nt < 0):
        raise ValueError("NEGATIVE_OR_NONVECTOR_NT")
    total = int(nt.sum())
    if total <= 0 or target_depth <= 0 or target_depth > total:
        raise ValueError("TARGET_DEPTH_OUT_OF_RANGE_FOR_THINNING")
    p = float(target_depth / total)
    # Gene-wise binomial counts sum to a Binomial(full NT depth, p) draw.
    return rng.binomial(nt, p).astype(np.int64), p


def stable_rng(mod, donor, target, seed=SEED):
    token = f"{seed}|{mod}|{donor}|{target}|DEPTH_ONLY_V1"
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def audit_modality(root, mod, receipt, draws=64):
    counts, feats, meta, cells = load_modality(root, mod, receipt)
    donor = np.array([m["donor"] for m in meta])
    role = np.array([m["crispr"] for m in meta])
    targeted = np.array([m["Gene_Targeted"] for m in meta])
    targets = sorted(set(targeted[role == "Perturbed"]))
    sent = {s: i for i, s in enumerate(feats) if s in SENTINELS}
    out = {
        "source_rds_sha256": EXPECTED_RDS[mod],
        "counts_bin_sha256": sha256(root / f"{mod}_counts_int32.bin"),
        "gd_meta_sha256": sha256(root / f"{mod}_gd_meta.csv"),
        "features_sha256": sha256(root / f"{mod}_features.txt"),
        "assayed_gene_count": len(feats),
        "missing_sentinel_genes": sorted(set(SENTINELS) - set(sent)),
        "donors": {},
    }
    for d in DONORS:
        nt_idx = np.flatnonzero((donor == d) & (role == "NT"))
        if not len(nt_idx):
            raise ValueError(f"{mod}/{d}: NO_DONOR_NT")
        nt = counts[:, nt_idx].sum(axis=1, dtype=np.int64)
        nt_depth = int(nt.sum())
        if nt_depth <= 0:
            raise ValueError(f"{mod}/{d}: ZERO_NT_DEPTH")
        rows = {}
        for target in targets:
            ti = np.flatnonzero((donor == d) & (role == "Perturbed")
                                & (targeted == target))
            n_cells = int(cells[ti].sum())
            if n_cells < MIN_CELLS:
                rows[target] = {"status": "NOT_ESTIMABLE_TARGET_CELL_SUPPORT",
                                "cells": n_cells, "guides": int(len(ti))}
                continue
            target_raw = counts[:, ti].sum(axis=1, dtype=np.int64)
            target_depth = int(target_raw.sum())
            if target_depth <= 0:
                rows[target] = {"status": "NOT_ESTIMABLE_TARGET_ZERO_DEPTH",
                                "cells": n_cells, "guides": int(len(ti))}
                continue
            if target_depth > nt_depth:
                rows[target] = {"status": "NOT_ESTIMABLE_TARGET_DEEPER_THAN_NT",
                                "cells": n_cells, "guides": int(len(ti)),
                                "target_depth": target_depth, "nt_depth": nt_depth}
                continue
            p = target_depth / nt_depth
            observed = effects(target_raw, nt)
            obs_top = top_extremes(observed, sent)
            values = {s: [] for s in sent}
            hit = {s: {"down": 0, "up": 0} for s in sent}
            maxima, depths = [], []
            rng = stable_rng(mod, d, target)
            for _ in range(draws):
                thin, _ = depth_only_draw(nt, target_depth, rng)
                depth = int(thin.sum())
                if depth <= 0:
                    # A rare zero-depth draw should not be represented as
                    # meaningful zero effect. Insufficient valid draws STOP.
                    continue
                null = effects(thin, nt)
                top = top_extremes(null, sent)
                depths.append(depth)
                maxima.append(float(np.max(np.abs(null))))
                for s, ix in sent.items():
                    values[s].append(float(null[ix]))
                    hit[s]["down"] += int(top[s]["down"])
                    hit[s]["up"] += int(top[s]["up"])
            n = len(depths)
            if n < draws:
                rows[target] = {"status": "NOT_ESTIMABLE_DEPTH_ONLY_ZERO_DRAW",
                                "valid_draws": n, "requested_draws": draws}
                continue
            genes = {}
            for s, ix in sent.items():
                arr = np.asarray(values[s], dtype=float)
                observed_value = float(observed[ix])
                genes[s] = {
                    "observed_log2cpm_fc": observed_value,
                    "depth_null_median": float(np.median(arr)),
                    "depth_null_q025_q975": [float(q) for q in np.quantile(arr, [0.025, 0.975])],
                    "depth_null_exceedance_abs_fraction":
                        float(np.mean(np.abs(arr) >= abs(observed_value))),
                    "observed_top25_down": bool(obs_top[s]["down"]),
                    "observed_top25_up": bool(obs_top[s]["up"]),
                    "depth_null_top25_down_fraction": hit[s]["down"] / n,
                    "depth_null_top25_up_fraction": hit[s]["up"] / n,
                }
            rows[target] = {
                "status": "COUPLED_DEPTH_ONLY_DESCRIPTIVE_DIAGNOSTIC",
                "cells": n_cells, "guides": int(len(ti)),
                "target_raw_depth": target_depth, "full_nt_raw_depth": nt_depth,
                "thin_probability": p, "requested_draws": draws,
                "valid_draws": n,
                "observed_thinned_depth_min_max": [int(min(depths)), int(max(depths))],
                "depth_null_max_abs_fc_median": float(np.median(maxima)),
                "sentinel_genes": genes,
            }
        out["donors"][d] = {
            "nt_guide_groups": int(len(nt_idx)),
            "nt_cells": int(cells[nt_idx].sum()),
            "nt_raw_depth": nt_depth,
            "targets": rows,
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--neutral-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--draws", default=64, type=int)
    args = ap.parse_args(argv)
    if args.draws < 16:
        ap.error("draws must be at least 16")
    if args.out_dir.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS__USE_NEW_VERSIONED_DIRECTORY")
    receipt_file = args.neutral_dir / "NEUTRAL_EXPORT_RECEIPT_V1.json"
    if not receipt_file.exists():
        raise SystemExit("STOP_NEUTRAL_EXPORT_RECEIPT_MISSING")
    receipt = json.loads(receipt_file.read_text(encoding="utf-8-sig"))
    if receipt.get("schema") != "GSE301119_NEUTRAL_ARRAY_EXPORT_V1":
        raise SystemExit("STOP_NEUTRAL_EXPORT_SCHEMA_MISMATCH")
    report = {
        "schema": "GSE301119_NT_DEPTH_ONLY_DESCRIPTIVE_DIAGNOSTIC_V1",
        "scope": "DEVELOPMENT_ONLY_NOT_BIOLOGICAL_REPLICATION",
        "predeclared": {
            "seed": SEED, "draws_per_target_donor": args.draws,
            "thinning": "independent gene-wise binomial at p=target_depth/full_donor_NT_depth",
            "comparator": "the original same-donor full NT pool: coupled reference",
            "feature_space": "each modality separately, no imputation",
            "sentinels": list(SENTINELS), "top_k_each_tail": 25,
            "pseudocount": 1.0,
        },
        "neutral_export_receipt_sha256": sha256(receipt_file),
        "script_sha256": sha256(Path(__file__)),
        "modalities": {},
        "limitations": [
            "Pooled NT raw counts cannot recover single-cell identity or cell-state sampling.",
            "Thinned pseudo-target shares original source molecules with the comparator.",
            "This is not independent biological replication or a formal p-value.",
            "Uniform thinning assumes exchangeable reads; it does not model gene-specific capture.",
            "Null separates idealized depth from guide/cell sampling, not biological causality.",
        ],
        "protected_outcomes_opened": False,
        "training_authorized": False,
        "therapeutic_ranking": False,
    }
    for mod in MODALITIES:
        report["modalities"][mod] = audit_modality(
            args.neutral_dir, mod, receipt, draws=args.draws)
    args.out_dir.mkdir(parents=True, exist_ok=False)
    out = args.out_dir / "GSE301119_NT_DEPTH_ONLY_DIAGNOSTIC_V1.json"
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n",
                   encoding="utf-8")
    print(f"DEVELOPMENT DEPTH-ONLY DIAGNOSTIC COMPLETE: {out}")


if __name__ == "__main__":
    main()
