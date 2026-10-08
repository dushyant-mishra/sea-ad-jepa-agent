#!/usr/bin/env python3
"""Qualify out-of-fold conditional covariance without neural training."""

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

from sea_ad_jepa.v4.belief_geometry import (  # noqa: E402
    correlation_matrix,
    covariance,
    diagonal_gaussian_nll,
    eigenspectrum_summary,
    full_gaussian_nll,
    mahalanobis_diagonal,
    mahalanobis_full,
    marginal_shape,
    offdiag_energy_fraction,
)
from sea_ad_jepa.v4.conditional_predictability import build_fixture, ridge_fit, ridge_predict  # noqa: E402
from sea_ad_jepa.v4.oof_covariance import (  # noqa: E402
    construct_lrd,
    deterministic_fold_ids,
    fold_indices,
    lrd_gaussian_nll,
    lrd_mahalanobis,
    positive_correlated_spectrum,
    select_correlated_rank,
    shared_architecture_rank,
)
from sea_ad_jepa.v4.reproducible_state import ReproducibleBasis  # noqa: E402

ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
SEED = 8114001
TRAIN, VALIDATION, SEALED = 3072, 512, 512
GENES, WIDTH = 4096, 160
FOLDS, ALPHA = 8, 1.0e-3
BASIS_HASH = "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c"
EXPECTED_HASHES = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_conditional_predictability_audit.json": "fae778621cbec948c0a238998d2683aae09be680b1c96f7ed4f2b6b8cc7ed6f5",
    "results/v4/stage81a3_rbb_belief_geometry_audit.json": "9e3986ec12767e8d04acdb9ac921c88a4f288ca20b3c4da4abf24fcdbe444b59",
}
OUTPUT_JSON = Path("results/v4/stage81a3_rbb_oof_covariance_audit.json")
OUTPUT_MASKS = Path("results/v4/stage81a3_rbb_oof_covariance_masks.csv")
OUTPUT_SPECTRUM = Path("results/v4/stage81a3_rbb_oof_covariance_spectrum.csv")


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


def summarize(values: torch.Tensor) -> dict[str, float]:
    finite = values.detach().double().flatten()
    finite = finite[torch.isfinite(finite)]
    return {
        "minimum": float(finite.min()), "p10": float(torch.quantile(finite, .10)),
        "p25": float(torch.quantile(finite, .25)), "median": float(torch.quantile(finite, .50)),
        "mean": float(finite.mean()), "p75": float(torch.quantile(finite, .75)),
        "p90": float(torch.quantile(finite, .90)), "p95": float(torch.quantile(finite, .95)),
        "p99": float(torch.quantile(finite, .99)), "maximum": float(finite.max()),
    }


def load_basis(device: torch.device) -> ReproducibleBasis:
    path = Path("results/v4/stage81a3_reproducible_state_basis.pt")
    if file_hash(path) != BASIS_HASH:
        raise RuntimeError("qualified RepPCA basis hash changed")
    state = torch.load(path, map_location=device, weights_only=True)
    return ReproducibleBasis(state["mean"], state["vectors"], state["eigenvalues"], float(state["epsilon"]))


def load_masks(device: torch.device) -> list[dict[str, Any]]:
    masks = []
    with Path("results/v4/stage81a3_predictability_masks.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["family"] not in {"RANDOM_40", "COEXPRESSION_BLOCK_40"}:
                continue
            visible = torch.tensor([int(x) for x in row["visible_indices"].split(";")], device=device)
            hidden = torch.zeros(GENES, dtype=torch.bool, device=device)
            hidden[torch.tensor([int(x) for x in row["hidden_indices"].split(";")], device=device)] = True
            masks.append({"family": row["family"], "view": int(row["view"]), "visible": visible, "hidden": hidden})
    if len(masks) != 8:
        raise RuntimeError("expected eight realistic mask views")
    return masks


def symmetric_prediction(
    x_a: torch.Tensor,
    x_b: torch.Tensor,
    target: torch.Tensor,
    visible: torch.Tensor,
    fitting: torch.Tensor,
    predicting: torch.Tensor,
) -> torch.Tensor:
    model_a = ridge_fit(x_a[fitting][:, visible], target[fitting], ALPHA)
    model_b = ridge_fit(x_b[fitting][:, visible], target[fitting], ALPHA)
    prediction = 0.5 * (
        ridge_predict(model_a, x_a[predicting][:, visible])
        + ridge_predict(model_b, x_b[predicting][:, visible])
    )
    return prediction.to(target.dtype)


def oof_prediction(
    x_a: torch.Tensor,
    x_b: torch.Tensor,
    target: torch.Tensor,
    visible: torch.Tensor,
    fold_ids: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    prediction = torch.empty_like(target[:TRAIN])
    assignments = torch.zeros(TRAIN, dtype=torch.int16, device=target.device)
    for fold in range(FOLDS):
        fitting, held_out = fold_indices(fold_ids, fold)
        prediction[held_out] = symmetric_prediction(x_a, x_b, target, visible, fitting, held_out)
        assignments[held_out] += 1
    if not torch.all(assignments == 1):
        raise RuntimeError("every TRAIN cell must receive exactly one OOF prediction")
    return prediction, assignments


def correlation_summary(matrix: torch.Tensor) -> dict[str, float]:
    correlation = correlation_matrix(matrix).abs()
    values = correlation[~torch.eye(len(matrix), dtype=torch.bool, device=matrix.device)]
    report = summarize(values)
    for threshold in (.1, .2, .3, .5):
        report[f"fraction_above_{threshold}"] = float((values > threshold).double().mean())
    return report


def covariance_geometry(matrix: torch.Tensor) -> dict[str, Any]:
    return {
        "offdiag_energy_fraction": offdiag_energy_fraction(matrix),
        "absolute_correlation": correlation_summary(matrix),
        "eigenspectrum": eigenspectrum_summary(matrix),
    }


def gaussianity(values: torch.Tensor) -> dict[str, Any]:
    skew, kurtosis = marginal_shape(values)
    severe = (skew.abs() > 1.0) | (kurtosis > 3.0)
    return {
        "skewness": summarize(skew), "excess_kurtosis": summarize(kurtosis),
        "severe_coordinates": int(severe.sum()),
        "severe_fraction": float(severe.double().mean()),
    }


def marginal_calibration(values: torch.Tensor, diagonal: torch.Tensor) -> dict[str, Any]:
    standardized = values.double() / torch.sqrt(diagonal.double().clamp_min(1e-30))
    coordinate_mse_ratio = values.double().square().mean(0) / diagonal.double().clamp_min(1e-30)
    return {
        "standardized_mean": summarize(standardized.mean(0)),
        "standardized_variance": summarize(standardized.var(0, unbiased=False)),
        "fraction_within_one_sigma": float((standardized.abs() <= 1.0).double().mean()),
        "fraction_within_1_96_sigma": float((standardized.abs() <= 1.96).double().mean()),
        "mse_over_predicted_variance": summarize(coordinate_mse_ratio),
    }


def score_covariances(values: torch.Tensor, covariance_oof: torch.Tensor, lrd: dict[str, Any]) -> dict[str, Any]:
    diagonal = torch.diag(covariance_oof)
    diagonal_nll = diagonal_gaussian_nll(values, diagonal) / WIDTH
    lrd_nll = lrd_gaussian_nll(values, lrd["diagonal"], lrd["u"]) / WIDTH
    full_nll, full_ridge = full_gaussian_nll(values, covariance_oof)
    full_nll = full_nll / WIDTH
    diagonal_mahal = mahalanobis_diagonal(values, diagonal)
    lrd_mahal = lrd_mahalanobis(values, lrd["diagonal"], lrd["u"])
    full_mahal = mahalanobis_full(values, covariance_oof)
    return {
        "diagonal_nll_per_dimension": float(diagonal_nll.mean()),
        "lrd_nll_per_dimension": float(lrd_nll.mean()),
        "full_nll_per_dimension": float(full_nll.mean()),
        "diagonal_minus_lrd_nll": float((diagonal_nll - lrd_nll).mean()),
        "lrd_minus_full_nll": float((lrd_nll - full_nll).mean()),
        "full_stabilizer": full_ridge,
        "diagonal_mahalanobis": summarize(diagonal_mahal),
        "lrd_mahalanobis": summarize(lrd_mahal),
        "full_mahalanobis": summarize(full_mahal),
        "diagonal_whitened_squared_norm": summarize(diagonal_mahal),
        "lrd_whitened_squared_norm": summarize(lrd_mahal),
        "full_whitened_squared_norm": summarize(full_mahal),
        "diagonal_marginal_calibration": marginal_calibration(values, diagonal),
        "lrd_marginal_calibration": marginal_calibration(values, torch.diag(lrd["matrix"])),
        "full_marginal_calibration": marginal_calibration(
            values, diagonal + full_ridge
        ),
    }


def dense_lrd_nll(values: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    cholesky = torch.linalg.cholesky(matrix.double())
    solution = torch.cholesky_solve(values.double().T, cholesky).T
    quadratic = (values.double() * solution).sum(1)
    logdet = 2.0 * torch.log(torch.diag(cholesky)).sum()
    return 0.5 * (WIDTH * math.log(2 * math.pi) + logdet + quadratic)


def main() -> int:
    args = parse_args()
    project = args.project_dir.resolve()
    os.chdir(project)
    if not torch.cuda.is_available():
        raise RuntimeError("locked CUDA runtime required")
    if any(path.exists() for path in (OUTPUT_JSON, OUTPUT_MASKS, OUTPUT_SPECTRUM)) and not args.overwrite:
        raise RuntimeError("OOF covariance output exists; use --overwrite deliberately")
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
    fold_ids = deterministic_fold_ids(TRAIN, FOLDS, device=device)
    if not torch.all(torch.bincount(fold_ids, minlength=FOLDS) == TRAIN // FOLDS):
        raise RuntimeError("OOF folds are not balanced")

    states: list[dict[str, Any]] = []
    spectrum_rows: list[dict[str, Any]] = []
    for mask in masks:
        family, view, visible, hidden = mask["family"], mask["view"], mask["visible"], mask["hidden"]
        print(f"{family} view={view}: building eight-fold OOF prediction", flush=True)
        r_a = basis.contribution(fixture.x_a, hidden)
        r_b = basis.contribution(fixture.x_b, hidden)
        r_pair = 0.5 * (r_a + r_b)
        oof, assignments = oof_prediction(fixture.x_a, fixture.x_b, r_pair, visible, fold_ids)
        all_train = torch.arange(TRAIN, device=device)
        all_cells = torch.arange(TRAIN + VALIDATION + SEALED, device=device)
        full_prediction = symmetric_prediction(
            fixture.x_a, fixture.x_b, r_pair, visible, all_train, all_cells
        )
        in_sample_residual = r_pair[:TRAIN] - full_prediction[:TRAIN]
        oof_residual = r_pair[:TRAIN] - oof
        oof_mean = oof_residual.double().mean(0)
        sealed_residual = r_pair[-SEALED:].double() - full_prediction[-SEALED:].double() - oof_mean
        sigma_in = covariance(in_sample_residual)
        sigma_oof = covariance(oof_residual)
        ratio = torch.diag(sigma_oof) / torch.diag(sigma_in).clamp_min(1e-30)
        positive_values, _, _ = positive_correlated_spectrum(sigma_oof)
        rank_star, captured, target_reached = select_correlated_rank(positive_values)
        lrd_star = construct_lrd(sigma_oof, rank_star)
        relative_diagonal_error = (
            (torch.diag(lrd_star["matrix"]) - torch.diag(sigma_oof)).abs()
            / torch.diag(sigma_oof).abs().clamp_min(1e-30)
        )
        for index, value in enumerate(positive_values):
            cumulative = float(positive_values[:index + 1].square().sum() / positive_values.square().sum())
            spectrum_rows.append({
                "family": family, "view": view, "positive_index": index + 1,
                "eigenvalue": float(value), "cumulative_positive_correlated_energy": cumulative,
                "selected_by_r_star": index < rank_star,
            })
        states.append({
            "family": family, "view": view, "sigma_oof": sigma_oof,
            "sealed_residual": sealed_residual, "rank_star": rank_star,
            "positive_count": len(positive_values), "rank_target_reached": target_reached,
            "rank_star_energy": captured, "variance_ratio": summarize(ratio),
            "in_sample_diagonal": summarize(torch.diag(sigma_in)),
            "oof_diagonal": summarize(torch.diag(sigma_oof)),
            "oof_geometry": covariance_geometry(sigma_oof),
            "oof_gaussianity": gaussianity(oof_residual - oof_mean),
            "sealed_gaussianity": gaussianity(sealed_residual),
            "oof_assignments_valid": bool(torch.all(assignments == 1)),
            "rank_star_reconstruction": {
                "diagonal_relative_error": summarize(relative_diagonal_error),
                "offdiagonal_energy_ratio": lrd_star["offdiagonal_energy_ratio"],
                "offdiagonal_reconstruction_explained_fraction": lrd_star["offdiagonal_reconstruction_explained_fraction"],
                "diagonal_floor": lrd_star["floor"], "floor_count": lrd_star["floor_count"],
            },
        })

    ranks_by_family = {
        family: [state["rank_star"] for state in states if state["family"] == family]
        for family in ("RANDOM_40", "COEXPRESSION_BLOCK_40")
    }
    architecture_rank = shared_architecture_rank(ranks_by_family)
    for row in spectrum_rows:
        row["selected_by_architecture_rank"] = row["positive_index"] <= architecture_rank
    mask_rows: list[dict[str, Any]] = []
    woodbury_benchmark = []
    for state in states:
        lrd = construct_lrd(state["sigma_oof"], architecture_rank)
        shared_relative_diagonal_error = (
            (torch.diag(lrd["matrix"]) - torch.diag(state["sigma_oof"])).abs()
            / torch.diag(state["sigma_oof"]).abs().clamp_min(1e-30)
        )
        scores = score_covariances(state["sealed_residual"], state["sigma_oof"], lrd)
        bench_values = state["sealed_residual"][:128]
        torch.cuda.synchronize()
        woodbury_start = time.perf_counter()
        woodbury_nll = lrd_gaussian_nll(bench_values, lrd["diagonal"], lrd["u"])
        torch.cuda.synchronize()
        woodbury_seconds = time.perf_counter() - woodbury_start
        dense_start = time.perf_counter()
        dense_nll = dense_lrd_nll(bench_values, lrd["matrix"])
        torch.cuda.synchronize()
        dense_seconds = time.perf_counter() - dense_start
        parity = float((woodbury_nll - dense_nll).abs().max())
        if parity > 1e-7:
            raise RuntimeError(f"Woodbury/dense NLL parity failed: {parity}")
        woodbury_benchmark.append({
            "family": state["family"], "view": state["view"],
            "woodbury_seconds": woodbury_seconds, "dense_seconds": dense_seconds,
            "maximum_absolute_nll_difference": parity,
        })
        state["shared_rank"] = architecture_rank
        state["shared_rank_lrd"] = {
            "diagonal_floor": lrd["floor"], "floor_count": lrd["floor_count"],
            "diagonal_relative_error": summarize(shared_relative_diagonal_error),
            "offdiagonal_energy_ratio": lrd["offdiagonal_energy_ratio"],
            "offdiagonal_reconstruction_explained_fraction": lrd["offdiagonal_reconstruction_explained_fraction"],
        }
        state["sealed_scores"] = scores
        mask_rows.append({
            "family": state["family"], "view": state["view"],
            "rank_star": state["rank_star"], "architecture_rank": architecture_rank,
            "positive_correlated_eigenvalues": state["positive_count"],
            "rank_target_reached": state["rank_target_reached"],
            "rank_star_energy": state["rank_star_energy"],
            "median_oof_to_in_sample_variance_ratio": state["variance_ratio"]["median"],
            "oof_offdiag_energy_fraction": state["oof_geometry"]["offdiag_energy_fraction"],
            "diagonal_nll_per_dimension": scores["diagonal_nll_per_dimension"],
            "lrd_nll_per_dimension": scores["lrd_nll_per_dimension"],
            "full_nll_per_dimension": scores["full_nll_per_dimension"],
            "diagonal_minus_lrd_nll": scores["diagonal_minus_lrd_nll"],
            "diagonal_mahalanobis_mean": scores["diagonal_mahalanobis"]["mean"],
            "lrd_mahalanobis_mean": scores["lrd_mahalanobis"]["mean"],
            "full_mahalanobis_mean": scores["full_mahalanobis"]["mean"],
            "standardized_variance_median": scores["diagonal_marginal_calibration"]["standardized_variance"]["median"],
            "one_sigma_coverage": scores["diagonal_marginal_calibration"]["fraction_within_one_sigma"],
            "one_96_sigma_coverage": scores["diagonal_marginal_calibration"]["fraction_within_1_96_sigma"],
            "maximum_severe_non_gaussian_fraction": max(
                state["oof_gaussianity"]["severe_fraction"], state["sealed_gaussianity"]["severe_fraction"]
            ),
        })

    med = lambda key: float(np.median([row[key] for row in mask_rows]))
    material_variance_correction = med("median_oof_to_in_sample_variance_ratio") >= 1.25
    standardized_variance = med("standardized_variance_median")
    diagonal_mahal_ratio = med("diagonal_mahalanobis_mean") / WIDTH
    lrd_mahal_ratio = med("lrd_mahalanobis_mean") / WIDTH
    diagonal_calibrated = 0.80 <= standardized_variance <= 1.25 and 0.80 <= diagonal_mahal_ratio <= 1.25
    lrd_calibrated = 0.80 <= standardized_variance <= 1.25 and 0.80 <= lrd_mahal_ratio <= 1.25
    diagonal_error = abs(diagonal_mahal_ratio - 1.0)
    lrd_error = abs(lrd_mahal_ratio - 1.0)
    mahal_improvement = (diagonal_error - lrd_error) / max(diagonal_error, 1e-30)
    lrd_nll_improvement = med("diagonal_minus_lrd_nll")
    lrd_no_worse = lrd_nll_improvement >= -0.02
    lrd_advantage = lrd_nll_improvement > 0 or mahal_improvement >= 0.05
    full_not_required = float(np.median([
        state["sealed_scores"]["lrd_minus_full_nll"] for state in states
    ])) <= 0.02
    severe_fraction = max(row["maximum_severe_non_gaussian_fraction"] for row in mask_rows)
    finite = all(math.isfinite(value) for row in mask_rows for value in row.values() if isinstance(value, float))
    if not finite:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    elif severe_fraction >= 0.25:
        classification = "NON-GAUSSIAN / MULTI-HYPOTHESIS BELIEF MAY BE REQUIRED"
    elif (
        (material_variance_correction or diagonal_calibrated) and architecture_rank <= 32
        and lrd_no_worse and lrd_advantage and full_not_required and lrd_calibrated
    ):
        classification = "LOW-RANK + DIAGONAL GAUSSIAN QUALIFIED FOR RBB-JEPA"
    elif diagonal_calibrated and not lrd_advantage:
        classification = "DIAGONAL OOF GAUSSIAN SUFFICIENT AFTER CALIBRATION CORRECTION"
    else:
        classification = "GAUSSIAN BELIEF FAMILY NOT YET QUALIFIED"

    family_summary_keys = {
        "oof_to_in_sample_variance_ratio": "median_oof_to_in_sample_variance_ratio",
        "oof_offdiag_energy_fraction": "oof_offdiag_energy_fraction",
        "diagonal_nll_per_dimension": "diagonal_nll_per_dimension",
        "lrd_nll_per_dimension": "lrd_nll_per_dimension",
        "full_nll_per_dimension": "full_nll_per_dimension",
        "diagonal_minus_lrd_nll": "diagonal_minus_lrd_nll",
        "diagonal_mahalanobis_mean": "diagonal_mahalanobis_mean",
        "lrd_mahalanobis_mean": "lrd_mahalanobis_mean",
        "full_mahalanobis_mean": "full_mahalanobis_mean",
        "standardized_variance": "standardized_variance_median",
        "one_sigma_coverage": "one_sigma_coverage",
        "one_96_sigma_coverage": "one_96_sigma_coverage",
    }
    family_summaries = {
        family: {
            "median_rank_star": float(np.median(ranks_by_family[family])),
            **{
                f"median_{label}": float(np.median([
                    row[source] for row in mask_rows if row["family"] == family
                ]))
                for label, source in family_summary_keys.items()
            },
        }
        for family in ranks_by_family
    }
    runtime = time.perf_counter() - started
    serializable_states = [{k: v for k, v in state.items() if k not in {"sigma_oof", "sealed_residual"}} for state in states]
    payload = {
        "stage": "Stage81A3_RBB_OOF_COV", "anchor": ANCHOR,
        "prior_evidence_hashes": actual_hashes, "basis_sha256": BASIS_HASH,
        "fixture": {
            "cells": 4096, "genes": 4096, "factors": 32, "seed": SEED,
            "train": TRAIN, "validation": VALIDATION, "sealed": SEALED,
            "global_rng_bound_before_generation": True,
            "provenance_limitation": (
                "Prior artifacts did not preserve the original Poisson RNG state; this is the "
                "deterministic declared-seed recreation used by the preceding geometry audit."
            ),
        },
        "oof": {
            "folds": FOLDS, "assignment_rule": "TRAIN cell index modulo 8",
            "fold_ids": [int(value) for value in fold_ids.cpu()],
            "cells_per_fold": [int(value) for value in torch.bincount(fold_ids).cpu()],
            "predictor_training_cells_per_fold": TRAIN - TRAIN // FOLDS,
            "each_cell_predicted_once": all(state["oof_assignments_valid"] for state in states),
            "ridge_alpha": ALPHA, "factor_labels_used": False, "sealed_used": False,
        },
        "mask_reports": serializable_states,
        "ranks_by_family": ranks_by_family, "family_summaries": family_summaries,
        "architecture_rank": architecture_rank,
        "woodbury_benchmark": woodbury_benchmark,
        "classification_statistics": {
            "median_oof_to_in_sample_variance_ratio": med("median_oof_to_in_sample_variance_ratio"),
            "median_standardized_variance": standardized_variance,
            "median_diagonal_mahalanobis_mean": med("diagonal_mahalanobis_mean"),
            "median_lrd_mahalanobis_mean": med("lrd_mahalanobis_mean"),
            "median_diagonal_minus_lrd_nll_per_dimension": lrd_nll_improvement,
            "median_lrd_minus_full_nll_per_dimension": float(np.median([
                state["sealed_scores"]["lrd_minus_full_nll"] for state in states
            ])),
            "maximum_severe_non_gaussian_fraction": severe_fraction,
            "material_variance_correction": material_variance_correction,
            "diagonal_calibrated": diagonal_calibrated, "lrd_calibrated": lrd_calibrated,
            "mahalanobis_relative_error_improvement": mahal_improvement,
            "lrd_no_worse_than_diagonal": lrd_no_worse,
            "lrd_advantage": lrd_advantage, "full_unrestricted_not_required": full_not_required,
        },
        "classification": classification,
        "classification_rationale": (
            "OOF residual fitting materially corrected the previous in-sample covariance "
            "underestimate but produced over-dispersed SEALED uncertainty. Shared-rank LRD "
            "improved NLL modestly without acceptable joint calibration, and unrestricted full "
            "covariance retained a material proper-score advantage. Marginal non-Gaussianity was "
            "not severe, so neither a Gaussian RBB head nor a mixture model is qualified."
        ),
        "performance": {
            "runtime_seconds": runtime,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        },
        "governance": {
            "stage81a3_complete": False, "ready_for_stage81b": False,
            "rbb_jepa_trained": False, "rbb_jepa_optimizer_updates": 0,
            "real_rna_accessed": False, "pathology_opened": False,
            "sealed_used_to_choose_covariance_rank": False,
            "factor_labels_used_for_fitting": False, "hyperparameter_sweep": False,
        },
    }
    atomic_csv(OUTPUT_MASKS, mask_rows)
    atomic_csv(OUTPUT_SPECTRUM, spectrum_rows)
    atomic_json(OUTPUT_JSON, payload)
    append_documentation(payload)
    print(json.dumps({
        "classification": classification, "architecture_rank": architecture_rank,
        **payload["classification_statistics"],
    }, indent=2), flush=True)
    return 0


def append_documentation(payload: dict[str, Any]) -> None:
    path = Path("docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md")
    heading = "## RBB-JEPA OUT-OF-FOLD CONDITIONAL UNCERTAINTY AUDIT"
    existing = path.read_text(encoding="utf-8")
    if heading in existing:
        existing = existing[:existing.index(heading)].rstrip() + "\n"
    stats = payload["classification_statistics"]
    section = f"""

{heading}

The preceding geometry audit correctly detected correlated conditional residual structure, but
its covariance scale came from residuals of a ridge predictor evaluated on the same cells used
to fit it. This audit therefore assigned every TRAIN cell to exactly one of eight deterministic
held-out folds, fitted the fixed symmetric ridge on the other seven folds, and estimated
conditional covariance only from concatenated out-of-fold errors. Factor labels, expected-state
values, SEALED cells, real RNA, and pathology did not enter fitting or rank selection.

Median OOF-to-in-sample coordinate variance ratio was
`{stats['median_oof_to_in_sample_variance_ratio']:.6f}`. The shared architecture rank selected
from TRAIN-only positive correlated energy was `{payload['architecture_rank']}`. On SEALED cells,
median standardized variance was `{stats['median_standardized_variance']:.6f}`; median diagonal
and LRD Mahalanobis means were `{stats['median_diagonal_mahalanobis_mean']:.6f}` and
`{stats['median_lrd_mahalanobis_mean']:.6f}` for a 160-dimensional target. Median diagonal-minus-LRD
NLL was `{stats['median_diagonal_minus_lrd_nll_per_dimension']:.6f}` nats per dimension.

Primary classification: **{payload['classification']}**. This is uncertainty-family qualification
only. It does not train or authorize RBB-JEPA, identify pathways, open pathology, or complete
Stage81A3.
"""
    atomic_text(path, existing + section)


if __name__ == "__main__":
    raise SystemExit(main())
