#!/usr/bin/env python3
"""Replace the invalid fixed-axis stability gate with the refitted null audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def leading_supported_dimensions(common: pd.Series, rank: int) -> list[int]:
    """Return only the jointly supported contiguous prefix starting at D=1."""
    ordered = sorted(int(d) for d in common.index if int(d) <= rank)
    expected = list(range(1, rank + 1))
    if ordered != expected:
        raise RuntimeError("joint-support dimensions must be exactly 1..validation_rank")
    supported: list[int] = []
    for dimension in expected:
        if not bool(common.loc[dimension]):
            break
        supported.append(dimension)
    return supported


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analytic", required=True)
    parser.add_argument("--empirical", required=True)
    parser.add_argument("--refit-null", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    analytic, empirical, refit = map(lambda p: Path(p).resolve(), [args.analytic, args.empirical, args.refit_null])
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    old = json.loads((empirical / "SHARED_DIMENSION_SELECTION_LEVEL.json").read_text())
    audit = json.loads((refit / "SHARED_REFIT_EMPIRICAL_NULL_VALIDATION.json").read_text())
    level = int(old["sample_level"])
    if int(audit["sample_level"]) != level or int(audit["replicates"]) != 256:
        raise RuntimeError("refit-null audit does not match empirical level")
    base = pd.read_csv(empirical / "TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL.csv")
    corrected = pd.read_csv(refit / "SHARED_REFIT_EMPIRICAL_NULL_CALIBRATION.csv")
    merged = base.merge(corrected, on=["sketch", "dimension"], how="left", validate="one_to_one")
    rank = int(audit["validation_rank"])
    merged["empirical_null_stability_supported_original_invalid"] = merged["empirical_null_stability_supported"]
    merged["empirical_null_stability_supported"] = merged["refit_stability_supported"].fillna(False)
    merged["empirical_null_predictability_supported"] = merged["refit_heldout_supported"].fillna(False)
    merged["empirical_null_signal_supported_original_invalid"] = merged["empirical_null_signal_supported"]
    merged["empirical_null_signal_supported"] = merged["refit_signal_supported"].fillna(False)
    merged["jointly_supported"] = merged["empirical_null_signal_supported"] & merged["empirical_null_stability_supported"] & merged["empirical_null_predictability_supported"]
    merged["stability_null_statistic"] = "REFITTED_GENERALIZED_EIGENSYSTEM_PRINCIPAL_SUBSPACE"
    corrected_path = out / "TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL_REFIT_CORRECTED.csv"
    merged.to_csv(corrected_path, index=False, lineterminator="\n")

    held = pd.read_csv(analytic / "SHARED_DONOR_HELDOUT_PREDICTABILITY.csv")
    paired = held.pivot_table(index=["donor_index", "dimension"], columns="sketch", values="heldout_predictability").reset_index()
    paired["paired_predictability"] = paired[["A", "B"]].mean(axis=1)
    curve = paired.groupby("dimension").paired_predictability.agg(["mean", "std", "count"])
    curve["se"] = curve["std"] / curve["count"].pow(0.5)
    best_any = int(curve["mean"].idxmax())
    if best_any > rank or float(curve.loc[rank + 1 :, "mean"].max()) >= float(curve.loc[best_any, "mean"] - curve.loc[best_any, "se"]):
        raise RuntimeError("rank-32 refit envelope cannot eliminate higher dimensions under the frozen one-SE rule")
    common = merged.groupby("dimension").jointly_supported.all()
    supported = leading_supported_dimensions(common, rank)
    candidate = None
    interval = []
    if supported:
        valid = curve.loc[supported]
        best = int(valid["mean"].idxmax())
        threshold = float(valid.loc[best, "mean"] - valid.loc[best, "se"])
        interval = [int(x) for x in valid[valid["mean"] >= threshold].index]
        candidate = min(interval)
    result = {
        "schema": "full104-shared-empirical-level-selection-refit-corrected-v1",
        "status": "ADVANCE_LADDER",
        "reason": "NO_REFIT_NULL_SUPPORTED_PREFIX" if candidate is None else "REFIT_NULL_CANDIDATE_REQUIRES_SUCCESSIVE_LEVEL_STABILITY",
        "sample_level": level,
        "cells": int(old["cells"]), "donors": 104, "operators": 42,
        "candidate_D_shared": candidate,
        "one_se_dimension_interval": [min(interval), max(interval)] if interval else None,
        "refitted_null_validation_rank": rank,
        "higher_dimensions_mathematically_eliminated_by_frozen_predictability_curve": True,
        "global_predictability_best_dimension": best_any,
        "search_boundary_supported": candidate == rank,
        "next_ladder_level_required": True,
        "terminal_scientific_decision_permitted": False,
        "analytic_null_role": "DIAGNOSTIC_ONLY",
        "empirical_null_role": "SELECTING_WITH_LIKE_FOR_LIKE_REFIT_REPAIR",
        "empirical_null_replicates": 256,
        "input_hashes": {
            "analytic_manifest": sha(analytic / f"SHARED_LEVEL{level}_ANALYTIC_DIAGNOSTIC_MANIFEST.csv"),
            "empirical_manifest": sha(empirical / f"SHARED_LEVEL{level}_EMPIRICAL_PACKAGE_MANIFEST.csv"),
            "refit_manifest": sha(refit / "SHARED_REFIT_EMPIRICAL_NULL_MANIFEST.csv"),
            "code": sha(Path(__file__)),
        },
        "corrected_calibration_sha256": sha(corrected_path),
        "no_private_or_protected_or_training_work": True,
    }
    result_path = out / "SHARED_DIMENSION_SELECTION_LEVEL_REFIT_CORRECTED.json"
    atomic_json(result_path, result)
    manifest = out / "SHARED_SELECTION_REFIT_CORRECTION_MANIFEST.csv"
    files = [corrected_path, result_path, Path(__file__)]
    pd.DataFrame([{"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (out / "SHARED_SELECTION_REFIT_CORRECTION_ROOT_SHA256.txt").write_text(sha(manifest) + "\n", encoding="ascii")
    print(json.dumps({**result, "manifest_sha256": sha(manifest)}, indent=2))


if __name__ == "__main__":
    main()
