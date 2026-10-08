#!/usr/bin/env python3
"""Final validation-calibrated covariance qualification before RBB-JEPA."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

from sea_ad_jepa.v4.belief_geometry import (  # noqa: E402
    covariance,
    diagonal_gaussian_nll,
    eigenspectrum_summary,
    mahalanobis_diagonal,
    offdiag_energy_fraction,
)
from sea_ad_jepa.v4.conditional_predictability import build_fixture  # noqa: E402
from sea_ad_jepa.v4.oof_covariance import (  # noqa: E402
    construct_lrd,
    deterministic_fold_ids,
    lrd_gaussian_nll,
    lrd_mahalanobis,
)
from sea_ad_jepa.v4.validation_covariance import dense_gaussian_terms, oas_covariance  # noqa: E402
from stage81a3_rbb_oof_covariance_audit import (  # noqa: E402
    correlation_summary,
    gaussianity,
    load_basis,
    load_masks,
    marginal_calibration,
    oof_prediction,
    summarize,
    symmetric_prediction,
)

ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
SEED = 8114001
TRAIN, VALIDATION, SEALED = 3072, 512, 512
WIDTH = 160
ARCHITECTURE_RANK = 9
BASIS_HASH = "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c"
EXPECTED_HASHES = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_conditional_predictability_audit.json": "fae778621cbec948c0a238998d2683aae09be680b1c96f7ed4f2b6b8cc7ed6f5",
    "results/v4/stage81a3_rbb_belief_geometry_audit.json": "9e3986ec12767e8d04acdb9ac921c88a4f288ca20b3c4da4abf24fcdbe444b59",
    "results/v4/stage81a3_rbb_oof_covariance_audit.json": "7a5042125860f2c598a28038f41fa3211074bf21d9e204dc6386b5246982a87f",
}
OUTPUT_JSON = Path("results/v4/stage81a3_rbb_validation_covariance_audit.json")
OUTPUT_MASKS = Path("results/v4/stage81a3_rbb_validation_covariance_masks.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path: Path, payload: Any) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def score_family(
    residuals: torch.Tensor,
    sigma_val: torch.Tensor,
    lrd: dict[str, Any],
    sigma_oas: torch.Tensor,
) -> dict[str, Any]:
    diagonal = torch.diag(sigma_val)
    diagonal_nll = diagonal_gaussian_nll(residuals, diagonal) / WIDTH
    lrd_nll = lrd_gaussian_nll(residuals, lrd["diagonal"], lrd["u"]) / WIDTH
    oas_nll, oas_mahal, _ = dense_gaussian_terms(residuals, sigma_oas)
    oas_nll = oas_nll / WIDTH
    diagonal_mahal = mahalanobis_diagonal(residuals, diagonal)
    lrd_mahal = lrd_mahalanobis(residuals, lrd["diagonal"], lrd["u"])
    return {
        "diagonal_nll_per_dimension": float(diagonal_nll.mean()),
        "lrd_nll_per_dimension": float(lrd_nll.mean()),
        "oas_nll_per_dimension": float(oas_nll.mean()),
        "diagonal_minus_lrd_nll": float((diagonal_nll - lrd_nll).mean()),
        "diagonal_minus_oas_nll": float((diagonal_nll - oas_nll).mean()),
        "lrd_minus_oas_nll": float((lrd_nll - oas_nll).mean()),
        "diagonal_mahalanobis": summarize(diagonal_mahal),
        "lrd_mahalanobis": summarize(lrd_mahal),
        "oas_mahalanobis": summarize(oas_mahal),
        "diagonal_whitened_squared_norm": summarize(diagonal_mahal),
        "lrd_whitened_squared_norm": summarize(lrd_mahal),
        "oas_whitened_squared_norm": summarize(oas_mahal),
        "diagonal_marginal_calibration": marginal_calibration(residuals, diagonal),
        "lrd_marginal_calibration": marginal_calibration(residuals, torch.diag(lrd["matrix"])),
        "oas_marginal_calibration": marginal_calibration(residuals, torch.diag(sigma_oas)),
    }


def main() -> int:
    args = parse_args()
    os.chdir(args.project_dir.resolve())
    if not torch.cuda.is_available():
        raise RuntimeError("locked CUDA runtime required")
    if any(path.exists() for path in (OUTPUT_JSON, OUTPUT_MASKS)) and not args.overwrite:
        raise RuntimeError("validation covariance output exists; use --overwrite deliberately")
    actual_hashes = {path: file_hash(Path(path)) for path in EXPECTED_HASHES}
    if actual_hashes != EXPECTED_HASHES:
        raise RuntimeError("prior evidence hash changed")

    device = torch.device("cuda")
    torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    basis = load_basis(device)
    masks = load_masks(device)
    fixture = build_fixture(device)
    fold_ids = deterministic_fold_ids(TRAIN, 8, device=device)
    all_train = torch.arange(TRAIN, device=device)
    all_cells = torch.arange(TRAIN + VALIDATION + SEALED, device=device)

    reports: list[dict[str, Any]] = []
    mask_rows: list[dict[str, Any]] = []
    for mask in masks:
        family, view, visible, hidden = mask["family"], mask["view"], mask["visible"], mask["hidden"]
        print(f"{family} view={view}: full-TRAIN mean, VALIDATION covariance, SEALED score", flush=True)
        r_a = basis.contribution(fixture.x_a, hidden)
        r_b = basis.contribution(fixture.x_b, hidden)
        r_pair = 0.5 * (r_a + r_b)
        full_prediction = symmetric_prediction(
            fixture.x_a, fixture.x_b, r_pair, visible,
            fitting=all_train, predicting=all_cells,
        )
        oof, _ = oof_prediction(fixture.x_a, fixture.x_b, r_pair, visible, fold_ids)
        in_sample_residual = r_pair[:TRAIN] - full_prediction[:TRAIN]
        validation_residual = r_pair[TRAIN:TRAIN + VALIDATION] - full_prediction[TRAIN:TRAIN + VALIDATION]
        validation_mean = validation_residual.double().mean(0)
        oof_residual = r_pair[:TRAIN] - oof

        sigma_in = covariance(in_sample_residual)
        sigma_oof = covariance(oof_residual)
        sigma_val = covariance(validation_residual)
        val_to_in = torch.diag(sigma_val) / torch.diag(sigma_in).clamp_min(1e-30)
        val_to_oof = torch.diag(sigma_val) / torch.diag(sigma_oof).clamp_min(1e-30)
        lrd = construct_lrd(sigma_val, ARCHITECTURE_RANK)
        sigma_oas, oas_shrinkage, oas_mu = oas_covariance(validation_residual)
        sealed_residual = r_pair[-SEALED:].double() - full_prediction[-SEALED:].double() - validation_mean
        scores = score_family(sealed_residual, sigma_val, lrd, sigma_oas)
        sealed_shape = gaussianity(sealed_residual)

        woodbury = lrd_gaussian_nll(sealed_residual[:128], lrd["diagonal"], lrd["u"])
        dense = dense_gaussian_terms(sealed_residual[:128], lrd["matrix"])[0]
        woodbury_parity = float((woodbury - dense).abs().max())
        if woodbury_parity > 1e-7:
            raise RuntimeError(f"Woodbury parity failed: {woodbury_parity}")
        relative_diagonal_error = (
            (torch.diag(lrd["matrix"]) - torch.diag(sigma_val)).abs()
            / torch.diag(sigma_val).abs().clamp_min(1e-30)
        )
        geometry = {
            "offdiag_energy_fraction": offdiag_energy_fraction(sigma_val),
            "absolute_correlation": correlation_summary(sigma_val),
            "eigenspectrum": eigenspectrum_summary(sigma_val),
        }
        report = {
            "family": family, "view": view,
            "mean_predictor_fit_cells": TRAIN,
            "mean_predictor_validation_cells": 0,
            "mean_predictor_sealed_cells": 0,
            "covariance_calibration_cells": VALIDATION,
            "scale_comparison": {
                "in_sample_variance": summarize(torch.diag(sigma_in)),
                "validation_variance": summarize(torch.diag(sigma_val)),
                "oof_variance": summarize(torch.diag(sigma_oof)),
                "validation_to_in_sample_ratio": summarize(val_to_in),
                "validation_to_oof_ratio": summarize(val_to_oof),
            },
            "validation_geometry": geometry,
            "lrd": {
                "rank": ARCHITECTURE_RANK,
                "diagonal_floor": lrd["floor"], "floor_count": lrd["floor_count"],
                "diagonal_relative_error": summarize(relative_diagonal_error),
                "offdiagonal_energy_ratio": lrd["offdiagonal_energy_ratio"],
                "offdiagonal_reconstruction_explained_fraction": lrd["offdiagonal_reconstruction_explained_fraction"],
                "woodbury_dense_maximum_nll_difference": woodbury_parity,
            },
            "oas": {"analytic_shrinkage": oas_shrinkage, "isotropic_target_variance": oas_mu},
            "sealed_scores": scores,
            "sealed_gaussianity": sealed_shape,
        }
        reports.append(report)
        mask_rows.append({
            "family": family, "view": view, "rank": ARCHITECTURE_RANK,
            "median_validation_to_in_sample_variance_ratio": report["scale_comparison"]["validation_to_in_sample_ratio"]["median"],
            "median_validation_to_oof_variance_ratio": report["scale_comparison"]["validation_to_oof_ratio"]["median"],
            "validation_offdiag_energy_fraction": geometry["offdiag_energy_fraction"],
            "oas_analytic_shrinkage": oas_shrinkage,
            "diagonal_nll_per_dimension": scores["diagonal_nll_per_dimension"],
            "lrd_nll_per_dimension": scores["lrd_nll_per_dimension"],
            "oas_nll_per_dimension": scores["oas_nll_per_dimension"],
            "diagonal_minus_lrd_nll": scores["diagonal_minus_lrd_nll"],
            "diagonal_minus_oas_nll": scores["diagonal_minus_oas_nll"],
            "lrd_minus_oas_nll": scores["lrd_minus_oas_nll"],
            "diagonal_joint_scale_ratio": scores["diagonal_mahalanobis"]["mean"] / WIDTH,
            "lrd_joint_scale_ratio": scores["lrd_mahalanobis"]["mean"] / WIDTH,
            "oas_joint_scale_ratio": scores["oas_mahalanobis"]["mean"] / WIDTH,
            "diagonal_standardized_variance": scores["diagonal_marginal_calibration"]["standardized_variance"]["median"],
            "lrd_standardized_variance": scores["lrd_marginal_calibration"]["standardized_variance"]["median"],
            "oas_standardized_variance": scores["oas_marginal_calibration"]["standardized_variance"]["median"],
            "diagonal_one_sigma_coverage": scores["diagonal_marginal_calibration"]["fraction_within_one_sigma"],
            "lrd_one_sigma_coverage": scores["lrd_marginal_calibration"]["fraction_within_one_sigma"],
            "oas_one_sigma_coverage": scores["oas_marginal_calibration"]["fraction_within_one_sigma"],
            "diagonal_one_96_sigma_coverage": scores["diagonal_marginal_calibration"]["fraction_within_1_96_sigma"],
            "lrd_one_96_sigma_coverage": scores["lrd_marginal_calibration"]["fraction_within_1_96_sigma"],
            "oas_one_96_sigma_coverage": scores["oas_marginal_calibration"]["fraction_within_1_96_sigma"],
            "severe_non_gaussian_fraction": sealed_shape["severe_fraction"],
            "woodbury_dense_maximum_nll_difference": woodbury_parity,
        })

    med = lambda key: float(np.median([row[key] for row in mask_rows]))
    families = ("RANDOM_40", "COEXPRESSION_BLOCK_40")
    family_med = lambda family, key: float(np.median([
        row[key] for row in mask_rows if row["family"] == family
    ]))
    joint = {name: med(f"{name}_joint_scale_ratio") for name in ("diagonal", "lrd", "oas")}
    marginal = {name: med(f"{name}_standardized_variance") for name in ("diagonal", "lrd", "oas")}
    calibrated = {
        name: 0.80 <= joint[name] <= 1.25 and 0.80 <= marginal[name] <= 1.25
        for name in joint
    }
    diag_lrd = med("diagonal_minus_lrd_nll")
    diag_oas = med("diagonal_minus_oas_nll")
    lrd_oas = med("lrd_minus_oas_nll")
    comparable_joint = abs(joint["lrd"] - joint["oas"]) <= 0.10
    severe = max(row["severe_non_gaussian_fraction"] for row in mask_rows)
    family_evidence = {}
    for family in families:
        family_joint = {
            name: family_med(family, f"{name}_joint_scale_ratio")
            for name in ("diagonal", "lrd", "oas")
        }
        family_marginal = {
            name: family_med(family, f"{name}_standardized_variance")
            for name in ("diagonal", "lrd", "oas")
        }
        family_calibrated = {
            name: 0.80 <= family_joint[name] <= 1.25 and 0.80 <= family_marginal[name] <= 1.25
            for name in family_joint
        }
        family_evidence[family] = {
            "joint_scale_ratio": family_joint,
            "standardized_variance": family_marginal,
            "calibrated": family_calibrated,
            "diagonal_minus_lrd_nll": family_med(family, "diagonal_minus_lrd_nll"),
            "diagonal_minus_oas_nll": family_med(family, "diagonal_minus_oas_nll"),
            "lrd_minus_oas_nll": family_med(family, "lrd_minus_oas_nll"),
            "lrd_oas_joint_scale_comparable": abs(family_joint["lrd"] - family_joint["oas"]) <= 0.10,
        }
    rank9_family_adequate = {
        family: (
            evidence["calibrated"]["lrd"]
            and evidence["diagonal_minus_lrd_nll"] >= -0.02
            and evidence["lrd_minus_oas_nll"] <= 0.02
            and evidence["lrd_oas_joint_scale_comparable"]
        )
        for family, evidence in family_evidence.items()
    }
    oas_exposes_underexpression = {
        family: (
            evidence["calibrated"]["oas"]
            and evidence["diagonal_minus_oas_nll"] > 0.02
            and evidence["lrd_minus_oas_nll"] > 0.02
        )
        for family, evidence in family_evidence.items()
    }
    finite = all(math.isfinite(value) for row in mask_rows for value in row.values() if isinstance(value, float))
    if not finite:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    elif severe >= 0.25:
        classification = "NON-GAUSSIAN / MULTI-HYPOTHESIS BELIEF MAY BE REQUIRED"
    elif all(rank9_family_adequate.values()) and any(
        evidence["diagonal_minus_lrd_nll"] > 0.02 for evidence in family_evidence.values()
    ):
        classification = "RANK-9 LOW-RANK + DIAGONAL GAUSSIAN QUALIFIED FOR RBB-JEPA"
    elif any(oas_exposes_underexpression.values()):
        classification = "CORRELATED GAUSSIAN SUPPORTED, BUT RANK-9 LRD UNDEREXPRESSIVE"
    elif all(
        evidence["calibrated"]["diagonal"]
        and evidence["diagonal_minus_lrd_nll"] <= 0.02
        and evidence["diagonal_minus_oas_nll"] <= 0.02
        for evidence in family_evidence.values()
    ):
        classification = "DIAGONAL GAUSSIAN SUFFICIENT AFTER VALIDATION CALIBRATION"
    elif not any(calibrated.values()):
        classification = "GAUSSIAN BELIEF STILL NOT CALIBRATED"
    else:
        classification = "GAUSSIAN BELIEF STILL NOT CALIBRATED"

    family_summaries = {
        family: {
            key: float(np.median([row[key] for row in mask_rows if row["family"] == family]))
            for key in mask_rows[0] if isinstance(mask_rows[0][key], (int, float)) and key not in {"view"}
        }
        for family in families
    }
    payload = {
        "stage": "Stage81A3_RBB_VAL_COV", "anchor": ANCHOR,
        "prior_evidence_hashes": actual_hashes, "basis_sha256": BASIS_HASH,
        "fixture": {"seed": SEED, "train": TRAIN, "validation": VALIDATION, "sealed": SEALED},
        "conditional_mean": {
            "estimator": "symmetric fixed ridge", "alpha": 1.0e-3,
            "fit_cells": TRAIN, "validation_fit_cells": 0, "sealed_fit_cells": 0,
        },
        "covariance_calibration": {
            "split": "validation_only", "cells": VALIDATION,
            "rank": ARCHITECTURE_RANK, "rank_predeclared": True,
            "oas": "analytic Oracle Approximating Shrinkage",
        },
        "mask_reports": reports, "family_summaries": family_summaries,
        "classification_statistics": {
            "median_joint_scale_ratio": joint,
            "median_standardized_variance": marginal,
            "calibrated": calibrated,
            "median_diagonal_minus_lrd_nll_per_dimension": diag_lrd,
            "median_diagonal_minus_oas_nll_per_dimension": diag_oas,
            "median_lrd_minus_oas_nll_per_dimension": lrd_oas,
            "lrd_oas_joint_scale_comparable": comparable_joint,
            "maximum_severe_non_gaussian_fraction": severe,
            "aggregation": "family median, then conservative qualification across mask families",
            "family_evidence": family_evidence,
            "rank9_family_adequate": rank9_family_adequate,
            "oas_exposes_rank9_underexpression": oas_exposes_underexpression,
        },
        "classification": classification,
        "classification_rationale": (
            "The classification uses family-median calibration and proper-score rules, then "
            "requires conservative qualification across mask families. "
            "OAS is an analytic statistical control and is not a neural covariance-head design."
        ),
        "performance": {
            "runtime_seconds": time.perf_counter() - started,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        },
        "governance": {
            "stage81a3_complete": False, "ready_for_stage81b": False,
            "rbb_jepa_trained": False, "rbb_jepa_optimizer_updates": 0,
            "real_rna_accessed": False, "pathology_opened": False,
            "validation_used_for_covariance_calibration": True,
            "sealed_used_for_fitting": False, "sealed_used_for_rank_selection": False,
            "rank_9_predeclared_before_audit": True,
            "factor_labels_used_for_fitting": False, "hyperparameter_sweep": False,
        },
    }
    atomic_csv(OUTPUT_MASKS, mask_rows)
    atomic_json(OUTPUT_JSON, payload)
    append_documentation(payload)
    print(json.dumps({"classification": classification, **payload["classification_statistics"]}, indent=2), flush=True)
    return 0


def append_documentation(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    heading = "## RBB-JEPA VALIDATION-CALIBRATED BELIEF COVARIANCE AUDIT"
    existing = path.read_text(encoding="utf-8")
    if heading in existing:
        existing = existing[:existing.index(heading)].rstrip() + "\n"
    stats = payload["classification_statistics"]
    section = f"""

{heading}

In-sample covariance underestimated predictive uncertainty because the residuals came from the
same cells used to fit the ridge mean. Eight-fold OOF covariance then overestimated deployment
uncertainty because each mean predictor used 2,688 rather than all 3,072 TRAIN cells. This final
audit fit the unchanged mean predictor on all TRAIN cells, estimated covariance exclusively from
512 untouched VALIDATION residuals, and evaluated all fixed covariance families once on SEALED.

Rank nine was frozen before this audit. The correlated controls were rank-9 LRD and analytic OAS;
OAS is a statistical upper-bound/control, not a proposed neural output head. Median SEALED joint
scale ratios were diagonal `{stats['median_joint_scale_ratio']['diagonal']:.6f}`, LRD
`{stats['median_joint_scale_ratio']['lrd']:.6f}`, and OAS
`{stats['median_joint_scale_ratio']['oas']:.6f}`. Median diagonal-minus-LRD and
diagonal-minus-OAS NLL improvements were
`{stats['median_diagonal_minus_lrd_nll_per_dimension']:.6f}` and
`{stats['median_diagonal_minus_oas_nll_per_dimension']:.6f}` nats per dimension.

Primary classification: **{payload['classification']}**. This remains a bounded uncertainty
qualification result. It does not train or authorize RBB-JEPA, alter rank, open real RNA or
pathology, or complete Stage81A3.
"""
    atomic_text(path, existing + section)


if __name__ == "__main__":
    raise SystemExit(main())
