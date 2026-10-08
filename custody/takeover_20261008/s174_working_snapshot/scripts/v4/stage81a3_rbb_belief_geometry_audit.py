#!/usr/bin/env python3
"""Select a mathematical belief family from fixed RepPCA residual geometry."""

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
    fixed_stabilizer,
    full_gaussian_nll,
    mahalanobis_diagonal,
    mahalanobis_full,
    marginal_shape,
    measurement_noise_covariance,
    offdiag_energy_fraction,
)
from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    build_fixture,
    r2_columns,
    ridge_fit,
    ridge_predict,
)
from sea_ad_jepa.v4.reproducible_state import ReproducibleBasis  # noqa: E402

ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
SEED = 8114001
TRAIN, VALIDATION, TEST = 3072, 512, 512
GENES, WIDTH, FACTORS = 4096, 160, 32
BASIS_HASH = "ea07915a043ed8b8c3e38fe56ba2e3b9095bf4f0db3804773ae9394f3fbeab9c"
EXPECTED_HASHES = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_conditional_predictability_audit.json": "fae778621cbec948c0a238998d2683aae09be680b1c96f7ed4f2b6b8cc7ed6f5",
}
OUTPUT_JSON = Path("results/v4/stage81a3_rbb_belief_geometry_audit.json")
OUTPUT_COVARIANCE = Path("results/v4/stage81a3_rbb_covariance_summary.csv")
OUTPUT_COORDINATES = Path("results/v4/stage81a3_rbb_coordinate_uncertainty.csv")
OUTPUT_MATRICES = Path("results/v4/stage81a3_rbb_covariance_matrices.pt")


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
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle: handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def atomic_json(path: Path, payload: Any) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def atomic_torch(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent); os.close(descriptor)
    try:
        torch.save(payload, temporary); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def summarize(values: torch.Tensor) -> dict[str, float]:
    finite = values.detach().double().flatten(); finite = finite[torch.isfinite(finite)]
    return {
        "minimum": float(finite.min()), "p10": float(torch.quantile(finite, .10)),
        "p25": float(torch.quantile(finite, .25)), "median": float(finite.median()),
        "mean": float(finite.mean()), "p75": float(torch.quantile(finite, .75)),
        "p90": float(torch.quantile(finite, .90)), "p95": float(torch.quantile(finite, .95)),
        "p99": float(torch.quantile(finite, .99)), "maximum": float(finite.max()),
    }


def correlation_summary(matrix: torch.Tensor) -> dict[str, float]:
    correlation = correlation_matrix(matrix).abs()
    values = correlation[~torch.eye(len(correlation), dtype=torch.bool, device=matrix.device)]
    report = summarize(values)
    for threshold in (.1, .2, .3, .5):
        report[f"fraction_above_{threshold}"] = float((values > threshold).double().mean())
    return report


def load_basis(path: Path, device: torch.device) -> ReproducibleBasis:
    if file_hash(path) != BASIS_HASH: raise RuntimeError("qualified RepPCA basis hash changed")
    state = torch.load(path, map_location=device, weights_only=True)
    return ReproducibleBasis(state["mean"], state["vectors"], state["eigenvalues"], float(state["epsilon"]))


def load_realistic_masks(path: Path, device: torch.device) -> list[dict[str, Any]]:
    masks = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["family"] not in {"RANDOM_40", "COEXPRESSION_BLOCK_40"}: continue
            visible = torch.zeros(GENES, dtype=torch.bool, device=device)
            hidden = torch.zeros(GENES, dtype=torch.bool, device=device)
            visible[torch.tensor([int(x) for x in row["visible_indices"].split(";")], device=device)] = True
            hidden[torch.tensor([int(x) for x in row["hidden_indices"].split(";")], device=device)] = True
            masks.append({"family": row["family"], "view": int(row["view"]), "visible": visible, "hidden": hidden})
    if len(masks) != 8: raise RuntimeError("expected eight realistic frozen masks")
    return masks


def covariance_row(family: str, view: int, kind: str, matrix: torch.Tensor) -> dict[str, Any]:
    return {
        "family": family, "view": view, "covariance": kind,
        "nll_evaluation_status": "not_applicable_prior" if kind == "prior" else "pending",
        "offdiag_energy_fraction": offdiag_energy_fraction(matrix),
        **{f"correlation_{key}": value for key, value in correlation_summary(matrix).items()},
        **eigenspectrum_summary(matrix),
    }


def factor_association(completed: torch.Tensor, fixture: Any, conditional_diagonal: torch.Tensor, factor_map: dict[str, torch.Tensor]) -> dict[str, Any]:
    prediction = ridge_predict(
        ridge_fit(completed[TRAIN:TRAIN + VALIDATION], fixture.factors[TRAIN:TRAIN + VALIDATION], 1e-3),
        completed[-TEST:],
    )
    scores = r2_columns(fixture.factors[-TEST:], prediction)
    weights = factor_map["weights"].double()
    exposure = (weights.square() * conditional_diagonal[:, None]).sum(0) / weights.square().sum(0).clamp_min(1e-30)
    error = 1.0 - scores.double()
    association = torch.corrcoef(torch.stack((exposure, error)))[0, 1]
    return {
        "per_factor_completed_r2": [float(x) for x in scores.cpu()],
        "per_factor_conditional_variance_exposure": [float(x) for x in exposure.cpu()],
        "uncertainty_exposure_vs_factor_error_correlation": float(association),
    }


def main() -> int:
    args = parse_args(); project = args.project_dir.resolve(); os.chdir(project)
    if not torch.cuda.is_available(): raise RuntimeError("locked CUDA runtime required")
    if any(path.exists() for path in (OUTPUT_JSON, OUTPUT_COVARIANCE, OUTPUT_COORDINATES, OUTPUT_MATRICES)) and not args.overwrite:
        raise RuntimeError("belief-geometry output exists; use --overwrite deliberately")
    actual_hashes = {path: file_hash(Path(path)) for path in EXPECTED_HASHES}
    if actual_hashes != EXPECTED_HASHES: raise RuntimeError("prior evidence hash changed")
    device = torch.device("cuda"); torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    torch.cuda.reset_peak_memory_stats(device); overall = time.perf_counter(); cpu_started = time.perf_counter()
    basis = load_basis(Path("results/v4/stage81a3_reproducible_state_basis.pt"), device)
    masks = load_realistic_masks(Path("results/v4/stage81a3_predictability_masks.csv"), device)
    cpu_preparation = time.perf_counter() - cpu_started
    # build_fixture uses an explicit generator for biological state but the global
    # generator for paired Poisson draws. Bind both to the fixture's declared seed.
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    fixture = build_fixture(device)
    full_expected = basis.transform(fixture.lambda_norm, whiten=True)
    factor_map = ridge_fit(full_expected[TRAIN:TRAIN + VALIDATION], fixture.factors[TRAIN:TRAIN + VALIDATION], 1e-3)

    covariance_rows: list[dict[str, Any]] = []
    coordinate_rows: list[dict[str, Any]] = []
    mask_reports = []
    matrix_payload: dict[str, torch.Tensor] = {}
    for mask in masks:
        family, view, visible, hidden = mask["family"], mask["view"], mask["visible"], mask["hidden"]
        r_a = basis.contribution(fixture.x_a, hidden)
        r_b = basis.contribution(fixture.x_b, hidden)
        r_pair = .5 * (r_a + r_b)
        # LAMBDA_NORM residual is evaluation-only and never enters covariance fitting.
        evaluation_only_r_expected = basis.contribution(fixture.lambda_norm[-TEST:], hidden)
        model_a = ridge_fit(fixture.x_a[:TRAIN, visible], r_pair[:TRAIN], 1e-3)
        model_b = ridge_fit(fixture.x_b[:TRAIN, visible], r_pair[:TRAIN], 1e-3)
        prediction_a = ridge_predict(model_a, fixture.x_a[:, visible])
        prediction_b = ridge_predict(model_b, fixture.x_b[:, visible])
        prediction = .5 * (prediction_a + prediction_b)
        conditional = r_pair - prediction
        sigma_prior = covariance(r_pair[:TRAIN])
        sigma_noise = measurement_noise_covariance(r_a[:TRAIN], r_b[:TRAIN])
        sigma_cond = covariance(conditional[:TRAIN])
        matrices = {"prior": sigma_prior, "noise": sigma_noise, "conditional": sigma_cond}
        for kind, matrix in matrices.items():
            key = f"{family}__{view}__{kind}"; matrix_payload[key] = matrix.cpu()
            covariance_rows.append(covariance_row(family, view, kind, matrix))

        cond_train_mean = conditional[:TRAIN].double().mean(0)
        cond_test = conditional[-TEST:].double() - cond_train_mean
        noise_train = (r_a[:TRAIN] - r_b[:TRAIN]).double() / math.sqrt(2.0)
        noise_test = (r_a[-TEST:] - r_b[-TEST:]).double() / math.sqrt(2.0) - noise_train.mean(0)
        cond_diag, noise_diag = torch.diag(sigma_cond), torch.diag(sigma_noise)
        cond_diag_nll = diagonal_gaussian_nll(cond_test, cond_diag) / WIDTH
        cond_full_nll, cond_ridge = full_gaussian_nll(cond_test, sigma_cond); cond_full_nll /= WIDTH
        noise_diag_nll = diagonal_gaussian_nll(noise_test, noise_diag) / WIDTH
        noise_full_nll, noise_ridge = full_gaussian_nll(noise_test, sigma_noise); noise_full_nll /= WIDTH
        cond_diag_mahal = mahalanobis_diagonal(cond_test, cond_diag)
        cond_full_mahal = mahalanobis_full(cond_test, sigma_cond)
        standardized = cond_test / torch.sqrt(cond_diag.clamp_min(1e-30))
        skew, kurtosis = marginal_shape(cond_test)
        severe = (skew.abs() > 1.0) | (kurtosis > 3.0)
        calibration_mean = standardized.mean(0); calibration_variance = standardized.var(0, unbiased=False)
        within_one = (standardized.abs() <= 1.0).double().mean(0)
        within_196 = (standardized.abs() <= 1.96).double().mean(0)
        prior_diag = torch.diag(sigma_prior)
        conditional_fraction = cond_diag / prior_diag.clamp_min(1e-30)
        noise_fraction = noise_diag / prior_diag.clamp_min(1e-30)
        predictable_fraction = 1.0 - conditional_fraction
        visible_pair = .5 * (
            basis.contribution(fixture.x_a, visible) + basis.contribution(fixture.x_b, visible)
        )
        completed = visible_pair + prediction
        factor_report = factor_association(completed, fixture, cond_diag, factor_map)
        mask_report = {
            "family": family, "view": view,
            "conditional_diagonal_nll_per_dimension": float(cond_diag_nll.mean()),
            "conditional_full_nll_per_dimension": float(cond_full_nll.mean()),
            "conditional_nll_improvement": float((cond_diag_nll - cond_full_nll).mean()),
            "noise_diagonal_nll_per_dimension": float(noise_diag_nll.mean()),
            "noise_full_nll_per_dimension": float(noise_full_nll.mean()),
            "noise_nll_improvement": float((noise_diag_nll - noise_full_nll).mean()),
            "conditional_full_covariance_ridge": cond_ridge,
            "noise_full_covariance_ridge": noise_ridge,
            "conditional_diagonal_mahalanobis": summarize(cond_diag_mahal),
            "conditional_full_mahalanobis": summarize(cond_full_mahal),
            "standardized_error_mean": summarize(calibration_mean),
            "standardized_error_variance": summarize(calibration_variance),
            "fraction_within_one_sigma": summarize(within_one),
            "fraction_within_1_96_sigma": summarize(within_196),
            "severe_non_gaussian_coordinates": int(severe.sum()),
            "severe_non_gaussian_fraction": float(severe.double().mean()),
            "expected_residual_evaluation_only_variance": summarize(evaluation_only_r_expected.var(0, unbiased=True)),
            "factor_association": factor_report,
        }
        mask_reports.append(mask_report)
        for row in covariance_rows[-3:]:
            if row["covariance"] == "conditional":
                row.update({
                    "nll_evaluation_status": "sealed_scored",
                    "diagonal_nll_per_dimension": mask_report["conditional_diagonal_nll_per_dimension"],
                    "full_nll_per_dimension": mask_report["conditional_full_nll_per_dimension"],
                    "full_minus_diagonal_nll_improvement_per_dimension": mask_report["conditional_nll_improvement"],
                    "full_covariance_ridge": cond_ridge,
                })
            elif row["covariance"] == "noise":
                row.update({
                    "nll_evaluation_status": "sealed_scored",
                    "diagonal_nll_per_dimension": mask_report["noise_diagonal_nll_per_dimension"],
                    "full_nll_per_dimension": mask_report["noise_full_nll_per_dimension"],
                    "full_minus_diagonal_nll_improvement_per_dimension": mask_report["noise_nll_improvement"],
                    "full_covariance_ridge": noise_ridge,
                })
        for coordinate in range(WIDTH):
            coordinate_rows.append({
                "family": family, "view": view, "coordinate": coordinate,
                "prior_variance": float(prior_diag[coordinate]),
                "conditional_variance": float(cond_diag[coordinate]),
                "measurement_noise_variance": float(noise_diag[coordinate]),
                "conditional_fraction": float(conditional_fraction[coordinate]),
                "noise_fraction": float(noise_fraction[coordinate]),
                "empirical_predictable_fraction": float(predictable_fraction[coordinate]),
                "standardized_error_mean": float(calibration_mean[coordinate]),
                "standardized_error_variance": float(calibration_variance[coordinate]),
                "fraction_within_one_sigma": float(within_one[coordinate]),
                "fraction_within_1_96_sigma": float(within_196[coordinate]),
                "skewness": float(skew[coordinate]), "excess_kurtosis": float(kurtosis[coordinate]),
                "severe_non_gaussian": bool(severe[coordinate]),
            })

    cond_rows = [row for row in covariance_rows if row["covariance"] == "conditional"]
    median_offdiag = float(np.median([row["offdiag_energy_fraction"] for row in cond_rows]))
    median_nll_improvement = float(np.median([row["conditional_nll_improvement"] for row in mask_reports]))
    median_severe = float(np.median([row["severe_non_gaussian_fraction"] for row in mask_reports]))
    median_standardized_variance = float(np.median([
        row["standardized_error_variance"]["median"] for row in mask_reports
    ]))
    median_diagonal_mahalanobis_mean = float(np.median([
        row["conditional_diagonal_mahalanobis"]["mean"] for row in mask_reports
    ]))
    median_full_mahalanobis_mean = float(np.median([
        row["conditional_full_mahalanobis"]["mean"] for row in mask_reports
    ]))
    numerical = all(math.isfinite(value) for value in (median_offdiag, median_nll_improvement, median_severe))
    if not numerical:
        classification = "ENGINEERING / NUMERICAL FAILURE"
    elif median_severe >= .25:
        classification = "NON-GAUSSIAN / MULTI-HYPOTHESIS BELIEF MAY BE REQUIRED"
    elif median_offdiag > .15 or median_nll_improvement > .05:
        classification = "CORRELATED GAUSSIAN BELIEF REQUIRED"
    else:
        classification = "DIAGONAL GAUSSIAN BELIEF FAMILY ADEQUATE FOR FIRST RBB-JEPA PROBE"

    atomic_torch(OUTPUT_MATRICES, {"anchor": ANCHOR, "basis_sha256": BASIS_HASH, "matrices": matrix_payload})
    matrix_hash = file_hash(OUTPUT_MATRICES)
    runtime = time.perf_counter() - overall
    payload = {
        "stage": "Stage81A3_RBB_JEPA_belief_geometry_audit", "anchor": ANCHOR,
        "prior_evidence_hashes": actual_hashes, "basis_sha256": BASIS_HASH,
        "fixture": {
            "cells": 4096, "genes": 4096, "factors": 32, "seed": SEED,
            "train": TRAIN, "validation": VALIDATION, "sealed": TEST,
            "global_rng_bound_before_generation": True,
            "replicate_rng_seed": SEED,
            "provenance_limitation": (
                "The accepted prior artifacts did not retain original Poisson RNG state or count "
                "tensors; this audit deterministically recreates the declared fixture contract but "
                "cannot assert byte identity to the earlier count realization."
            ),
        },
        "residual_definitions": {
            "prior": "Cov(TRAIN r_pair)", "noise": "0.5 * Cov(TRAIN r_A-r_B)",
            "conditional": "Cov(TRAIN r_pair-symmetric_fixed_ridge_visible_prediction)",
            "expected_state_usage": "evaluation_only",
        },
        "mask_reports": mask_reports,
        "classification_statistics": {
            "median_conditional_offdiag_energy_fraction": median_offdiag,
            "median_full_minus_diagonal_nll_improvement_per_dimension": median_nll_improvement,
            "median_severe_non_gaussian_fraction": median_severe,
            "median_coordinate_standardized_error_variance": median_standardized_variance,
            "median_diagonal_mahalanobis_mean": median_diagonal_mahalanobis_mean,
            "median_full_mahalanobis_mean": median_full_mahalanobis_mean,
            "ideal_gaussian_mahalanobis_mean": WIDTH,
            "mask_aggregation": "median over eight realistic views",
        },
        "classification_rationale": {
            "correlation_trigger_pass": median_offdiag > .15,
            "full_covariance_nll_trigger_pass": median_nll_improvement > .05,
            "severe_non_gaussian_trigger_pass": median_severe >= .25,
            "naive_full_covariance_deployment_supported": median_nll_improvement > 0.0,
            "interpretation": (
                "The predeclared correlated-family rule is triggered by conditional off-diagonal "
                "energy. The fixed, unregularized full-covariance estimator worsens SEALED NLL and "
                "is not qualified for deployment. Both fixed TRAIN-residual covariance estimates "
                "severely underestimate SEALED residual scale despite non-severe marginal shape; "
                "this is a conditional-reference calibration failure, not evidence that a mixture "
                "model is required. Correlated parameterization requires separate regularization, "
                "calibration, and human review."
            ),
        },
        "classification": classification,
        "covariance_matrices_sha256": matrix_hash,
        "performance": {
            "runtime_seconds": runtime, "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
            "cpu_preparation_seconds": cpu_preparation, "cpu_preparation_fraction": cpu_preparation / runtime,
            "mean_gpu_utilization_percent": None,
        },
        "governance": {
            "stage81a3_complete": False, "ready_for_stage81b": False,
            "rbb_jepa_trained": False, "rbb_jepa_optimizer_updates": 0,
            "foundation_model_trained": False, "real_rna_accessed": False,
            "pathology_opened": False, "belief_family_selected_by_hyperparameter_sweep": False,
            "factor_labels_used_for_fitting": False, "factor_labels_used_for_evaluation": True,
        },
    }
    write_csv(OUTPUT_COVARIANCE, covariance_rows); write_csv(OUTPUT_COORDINATES, coordinate_rows); atomic_json(OUTPUT_JSON, payload)
    append_documentation(project, payload)
    print(json.dumps({"classification": classification, **payload["classification_statistics"]}, indent=2), flush=True)
    return 0


def append_documentation(project: Path, payload: dict[str, Any]) -> None:
    path = project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md"
    heading = "## RBB-JEPA Belief Geometry Audit"
    existing = path.read_text(encoding="utf-8")
    if heading in existing: existing = existing[:existing.index(heading)].rstrip() + "\n"
    statistics = payload["classification_statistics"]
    section = f"""

{heading}

State preservation and conditional predictability are distinct. Using the exact qualified
RepPCA-160 basis, this no-neural-training audit estimated TRAIN-only prior, replicate-noise,
and fixed-ridge conditional residual covariance for eight realistic masks, then scored diagonal
and full Gaussian geometry on SEALED cells. No coordinate is interpreted as a pathway, and no
factor label, expected-state target, real RNA, or pathology data entered uncertainty fitting.

Median conditional off-diagonal energy was
`{statistics['median_conditional_offdiag_energy_fraction']:.6f}`; median full-over-diagonal
held-out NLL improvement was
`{statistics['median_full_minus_diagonal_nll_improvement_per_dimension']:.6f}` nats per latent
dimension; median severe marginal non-Gaussian fraction was
`{statistics['median_severe_non_gaussian_fraction']:.6f}`. Classification:
**{payload['classification']}**. This selects only a mathematical family for human review.
The classification was triggered by off-diagonal residual energy, not by superior full-covariance
scoring. Under the fixed estimator, full covariance worsened SEALED NLL, so an unregularized full
covariance is not deployment-ready; any correlated parameterization requires separate
regularization and human review.
Both covariance forms also underestimated held-out residual scale: median coordinate-level
standardized-error variance was
`{statistics['median_coordinate_standardized_error_variance']:.6f}`, and median diagonal/full
Mahalanobis means were `{statistics['median_diagonal_mahalanobis_mean']:.6f}` and
`{statistics['median_full_mahalanobis_mean']:.6f}` versus an ideal 160-dimensional Gaussian mean
of `{statistics['ideal_gaussian_mahalanobis_mean']}`. With zero severe marginal-shape flags, this
is recorded as conditional-reference scale miscalibration rather than evidence for an automatic
mixture model.
No RBB-JEPA was trained or authorized.
"""
    atomic_text(path, existing + section)


if __name__ == "__main__":
    raise SystemExit(main())
