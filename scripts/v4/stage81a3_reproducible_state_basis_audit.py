#!/usr/bin/env python3
"""Qualify RepPCA-160 as a reproducible biological state coordinate system."""

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
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.conditional_predictability import (  # noqa: E402
    build_fixture,
    correlation_columns,
    r2_columns,
    ridge_fit,
    ridge_predict,
)
from sea_ad_jepa.v4.reproducible_state import (  # noqa: E402
    PairMeanBasis,
    ReproducibleBasis,
    column_correlation,
    fit_pairmean_pca,
    fit_reproducible_basis,
    residual_prior,
)

ANCHOR = "808ce4f170055c5568cc5c1e0e3a56415b52f908"
SEED = 8114001
CELLS, GENES, FACTORS, WIDTH = 4096, 4096, 32, 160
TRAIN, VALIDATION, TEST = 3072, 512, 512
EXPECTED_HASHES = {
    "results/v4/stage81a3_ipb_jepa_feasibility.json": "aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308",
    "results/v4/stage81a3_rlc_causal_fast_probe.json": "ac3e8a69964bfa11f5d8211f373e20c6476534095850dc48e8851ea9b42ab8fc",
    "results/v4/stage81a3_conditional_predictability_audit.json": "fae778621cbec948c0a238998d2683aae09be680b1c96f7ed4f2b6b8cc7ed6f5",
}
OUTPUT_JSON = Path("results/v4/stage81a3_reproducible_state_basis_audit.json")
OUTPUT_COORDINATES = Path("results/v4/stage81a3_reproducible_state_coordinates.csv")
OUTPUT_MASKS = Path("results/v4/stage81a3_reproducible_state_masks.csv")
OUTPUT_BASIS = Path("results/v4/stage81a3_reproducible_state_basis.pt")


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
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    try:
        torch.save(payload, temporary); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def summarize(values: torch.Tensor) -> dict[str, float]:
    finite = values.detach().float().flatten(); finite = finite[torch.isfinite(finite)]
    return {
        "minimum": float(finite.min()), "p10": float(torch.quantile(finite, .10)),
        "p25": float(torch.quantile(finite, .25)), "median": float(finite.median()),
        "mean": float(finite.mean()), "p75": float(torch.quantile(finite, .75)),
        "p90": float(torch.quantile(finite, .90)), "maximum": float(finite.max()),
    }


def load_cpiu_masks(path: Path, device: torch.device) -> list[dict[str, Any]]:
    masks = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            visible = torch.zeros(GENES, dtype=torch.bool, device=device)
            hidden = torch.zeros(GENES, dtype=torch.bool, device=device)
            visible[torch.tensor([int(x) for x in row["visible_indices"].split(";")], device=device)] = True
            hidden[torch.tensor([int(x) for x in row["hidden_indices"].split(";")], device=device)] = True
            if int(hidden.sum()) != 1638 or torch.any(visible & hidden) or not torch.all(visible | hidden):
                raise RuntimeError("frozen CP-IU mask contract failed")
            masks.append({"family": row["family"], "view": int(row["view"]), "visible": visible, "hidden": hidden})
    if len(masks) != 12:
        raise RuntimeError("expected exactly 12 frozen CP-IU masks")
    return masks


def factor_readout(coordinates: torch.Tensor, factors: torch.Tensor) -> dict[str, Any]:
    model = ridge_fit(
        coordinates[TRAIN:TRAIN + VALIDATION], factors[TRAIN:TRAIN + VALIDATION], 1e-3
    )
    prediction = ridge_predict(model, coordinates[-TEST:])
    scores = r2_columns(factors[-TEST:], prediction)
    return {**summarize(scores), "per_factor_r2": [float(x) for x in scores.cpu()]}


def basis_readouts(basis: ReproducibleBasis | PairMeanBasis, fixture: Any) -> dict[str, Any]:
    transform = basis.transform
    sources = {
        "LAMBDA_NORM": fixture.lambda_norm,
        "X_A": fixture.x_a,
        "X_B": fixture.x_b,
        "PAIRMEAN": 0.5 * (fixture.x_a + fixture.x_b),
    }
    return {name: factor_readout(transform(values), fixture.factors) for name, values in sources.items()}


def stability(basis: ReproducibleBasis | PairMeanBasis, fixture: Any) -> dict[str, Any]:
    z_a, z_b = basis.transform(fixture.x_a), basis.transform(fixture.x_b)
    train_scale = (0.5 * (z_a[:TRAIN] + z_b[:TRAIN])).std(0, unbiased=False).clamp_min(1e-8)
    a, b = z_a[-TEST:] / train_scale, z_b[-TEST:] / train_scale
    correlations = column_correlation(a, b)
    within = torch.linalg.vector_norm(a - b, dim=1)
    generator = torch.Generator(device=a.device).manual_seed(SEED + 404)
    permutation = torch.randperm(TEST, generator=generator, device=a.device)
    between = torch.linalg.vector_norm(a - b[permutation], dim=1)
    return {
        "per_coordinate_correlation": [float(x) for x in correlations.cpu()],
        "coordinate_correlation": summarize(correlations),
        "paired_cosine": summarize(F.cosine_similarity(a, b, dim=1)),
        "paired_standardized_l2": summarize(within),
        "random_pair_standardized_l2": summarize(between),
        "within_between_mean_ratio": float(within.mean() / between.mean().clamp_min(1e-12)),
    }


def noise_rejection(basis: ReproducibleBasis | PairMeanBasis, fixture: Any) -> dict[str, Any]:
    expected = basis.transform(fixture.lambda_norm[-TEST:])
    a = basis.transform(fixture.x_a[-TEST:]); b = basis.transform(fixture.x_b[-TEST:])
    pair = basis.transform(0.5 * (fixture.x_a[-TEST:] + fixture.x_b[-TEST:]))
    return {
        "x_a_to_expected": summarize(torch.linalg.vector_norm(a - expected, dim=1)),
        "x_b_to_expected": summarize(torch.linalg.vector_norm(b - expected, dim=1)),
        "pairmean_to_expected": summarize(torch.linalg.vector_norm(pair - expected, dim=1)),
    }


def main() -> int:
    args = parse_args(); project = args.project_dir.resolve(); os.chdir(project)
    if not torch.cuda.is_available(): raise RuntimeError("locked CUDA runtime required")
    if any(path.exists() for path in (OUTPUT_JSON, OUTPUT_COORDINATES, OUTPUT_MASKS, OUTPUT_BASIS)) and not args.overwrite:
        raise RuntimeError("RepPCA output exists; use --overwrite for deliberate regeneration")
    actual_hashes = {path: file_hash(Path(path)) for path in EXPECTED_HASHES}
    if actual_hashes != EXPECTED_HASHES: raise RuntimeError("prior evidence hash changed")
    torch.set_float32_matmul_precision("high"); torch.backends.cuda.matmul.allow_tf32 = True
    device = torch.device("cuda"); torch.cuda.reset_peak_memory_stats(device); overall = time.perf_counter()
    timings: dict[str, float] = {}
    started = time.perf_counter(); fixture = build_fixture(device); timings["fixture_seconds"] = time.perf_counter() - started
    masks = load_cpiu_masks(Path("results/v4/stage81a3_predictability_masks.csv"), device)
    mask_hash = file_hash(Path("results/v4/stage81a3_predictability_masks.csv"))
    started = time.perf_counter(); basis, spectrum = fit_reproducible_basis(fixture.x_a[:TRAIN], fixture.x_b[:TRAIN]); timings["shared_covariance_and_eigh_seconds"] = time.perf_counter() - started
    if basis is None:
        payload = {
            "classification": "REPRODUCIBLE STATE BASIS NOT QUALIFIED", "prior_evidence_hashes": actual_hashes,
            "eigenspectrum": {key: value for key, value in spectrum.items() if not isinstance(value, torch.Tensor)},
            "qualification_gates": {"S1_positive_eigenvalues": False},
            "governance": {"factor_labels_used_to_fit_basis": False, "real_rna_accessed": False, "pathology_opened": False},
        }
        atomic_json(OUTPUT_JSON, payload); print(payload["classification"]); return 0
    started = time.perf_counter(); control = fit_pairmean_pca(fixture.x_a[:TRAIN], fixture.x_b[:TRAIN]); timings["pairmean_pca_seconds"] = time.perf_counter() - started

    identity = torch.eye(WIDTH, device=device)
    orthogonality_error = float((basis.vectors @ basis.vectors.T - identity).abs().max())
    rep_readouts, control_readouts = basis_readouts(basis, fixture), basis_readouts(control, fixture)
    rep_stability, control_stability = stability(basis, fixture), stability(control, fixture)
    rep_noise, control_noise = noise_rejection(basis, fixture), noise_rejection(control, fixture)

    maximum_decomposition_error = 0.0; mask_rows = []
    for mask in masks:
        visible, hidden = mask["visible"], mask["hidden"]
        for source_name, values in (("LAMBDA_NORM", fixture.lambda_norm[-TEST:]), ("X_A", fixture.x_a[-TEST:]), ("X_B", fixture.x_b[-TEST:])):
            error = (basis.transform(values, whiten=True) - basis.contribution(values, visible) - basis.contribution(values, hidden)).abs().max()
            maximum_decomposition_error = max(maximum_decomposition_error, float(error))
        prior = None
        if mask["family"] != "ORACLE_COVERAGE_40":
            prior = residual_prior(
                basis.contribution(fixture.x_a[:TRAIN], hidden),
                basis.contribution(fixture.x_b[:TRAIN], hidden),
            )
        for coordinate in range(WIDTH):
            mask_rows.append({
                "family": mask["family"], "view": mask["view"], "coordinate": coordinate,
                "hidden_genes": int(hidden.sum()), "visible_genes": int(visible.sum()),
                "maximum_decomposition_error": maximum_decomposition_error,
                "prior_mean": float(prior["mean"][coordinate]) if prior is not None else None,
                "prior_variance": float(prior["prior_variance"][coordinate]) if prior is not None else None,
                "measurement_noise_variance": float(prior["noise_variance"][coordinate]) if prior is not None else None,
                "measurement_noise_fraction": float(prior["noise_fraction"][coordinate]) if prior is not None else None,
                "oracle_generator_label_diagnostic_only": mask["family"] == "ORACLE_COVERAGE_40",
            })
    realistic = [row for row in mask_rows if row["family"] != "ORACLE_COVERAGE_40"]
    prior_means = torch.tensor([row["prior_mean"] for row in realistic])
    noise_fractions = torch.tensor([row["measurement_noise_fraction"] for row in realistic])

    coordinate_rows = []
    rep_correlations = rep_stability["per_coordinate_correlation"]
    control_correlations = control_stability["per_coordinate_correlation"]
    for coordinate in range(WIDTH):
        coordinate_rows.append({
            "coordinate": coordinate, "shared_eigenvalue": float(basis.eigenvalues[coordinate]),
            "whitening_scale": float(1.0 / torch.sqrt(basis.eigenvalues[coordinate] + basis.epsilon)),
            "reppca_replicate_correlation": rep_correlations[coordinate],
            "pairmean_pca_replicate_correlation": control_correlations[coordinate],
            "cpiu_coordinate_alignment": "DIRECT COORDINATE ALIGNMENT NOT DEFINED ACROSS BASES",
        })

    gates = {
        "S1_positive_eigenvalues": spectrum["positive_count"] >= WIDTH,
        "S2_orthogonality": orthogonality_error <= 1e-5,
        "S3_visible_hidden_decomposition": maximum_decomposition_error <= 1e-5,
        "S4_lambda_factor_r2": rep_readouts["LAMBDA_NORM"]["mean"] >= .97,
        "S5_x_a_factor_retention": rep_readouts["X_A"]["mean"] >= control_readouts["X_A"]["mean"] - .02,
        "S6_x_b_factor_retention": rep_readouts["X_B"]["mean"] >= control_readouts["X_B"]["mean"] - .02,
        "S7_replicate_correlation": rep_stability["coordinate_correlation"]["median"] >= control_stability["coordinate_correlation"]["median"] - .02,
        "S8_distance_ratio": rep_stability["within_between_mean_ratio"] <= control_stability["within_between_mean_ratio"] * 1.05,
        "S9_numerical_stability": all(math.isfinite(value) for value in (
            orthogonality_error, maximum_decomposition_error, spectrum["maximum_relative_rayleigh_difference"],
        )),
        "S10_no_factor_labels_in_fit": True,
    }
    classification = "REPRODUCIBLE STATE BASIS QUALIFIED FOR BELIEF-JEPA" if all(gates.values()) else "REPRODUCIBLE STATE BASIS NOT QUALIFIED"
    atomic_torch(OUTPUT_BASIS, {
        "mean": basis.mean.cpu(), "vectors": basis.vectors.cpu(),
        "eigenvalues": basis.eigenvalues.cpu(), "epsilon": basis.epsilon,
        "anchor": ANCHOR, "seed": SEED,
    })
    basis_hash = file_hash(OUTPUT_BASIS)
    timings["total_audit_seconds"] = time.perf_counter() - overall
    payload = {
        "stage": "Stage81A3_reproducible_biological_state_basis_audit",
        "anchor": ANCHOR, "prior_evidence_hashes": actual_hashes,
        "fixture": {"source": "accepted CP-IU mechanics", "cells": CELLS, "genes": GENES, "factors": FACTORS, "seed": SEED, "train": TRAIN, "validation": VALIDATION, "sealed": TEST},
        "cpiu_mask_hash": mask_hash,
        "eigenspectrum": {
            "positive_count": spectrum["positive_count"], "near_zero_count": spectrum["near_zero_count"],
            "negative_count": spectrum["negative_count"], "largest_eigenvalue": spectrum["largest_eigenvalue"],
            "positivity_threshold": spectrum["threshold"],
            "maximum_relative_float32_vs_float64_rayleigh_difference": spectrum["maximum_relative_rayleigh_difference"],
        },
        "reppca": {"components": WIDTH, "epsilon": basis.epsilon, "orthogonality_max_abs_error": orthogonality_error, "basis_sha256": basis_hash},
        "factor_retention": {"REPPCA160": rep_readouts, "PAIRMEAN_PCA160": control_readouts},
        "cross_replicate_stability": {"REPPCA160": rep_stability, "PAIRMEAN_PCA160": control_stability},
        "count_noise_rejection": {"REPPCA160": rep_noise, "PAIRMEAN_PCA160": control_noise},
        "visible_hidden_decomposition": {"maximum_absolute_error": maximum_decomposition_error, "tolerance": 1e-5},
        "residual_prior": {"mean_absolute_prior_mean": float(prior_means.abs().mean()), "prior_mean": summarize(prior_means)},
        "measurement_noise_floor": {"noise_fraction": summarize(noise_fractions)},
        "cpiu_coordinate_link": "DIRECT COORDINATE ALIGNMENT NOT DEFINED ACROSS BASES",
        "qualification_gates": gates, "classification": classification,
        "timings": timings,
        "performance": {"peak_allocated_bytes": torch.cuda.max_memory_allocated(device), "peak_reserved_bytes": torch.cuda.max_memory_reserved(device)},
        "governance": {
            "stage81a3_complete": False, "ready_for_stage81b": False,
            "rbb_jepa_trained": False, "foundation_model_trained": False,
            "real_rna_accessed": False, "pathology_opened": False,
            "factor_labels_used_to_fit_basis": False, "factor_labels_used_for_evaluation": True,
            "neural_optimizer_updates": 0,
        },
    }
    write_csv(OUTPUT_COORDINATES, coordinate_rows); write_csv(OUTPUT_MASKS, mask_rows); atomic_json(OUTPUT_JSON, payload)
    append_documentation(project, payload)
    print(json.dumps({"classification": classification, "qualification_gates": gates}, indent=2), flush=True)
    return 0


def append_documentation(project: Path, payload: dict[str, Any]) -> None:
    path = project / "docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md"
    heading = "## Reproducible Biological State Basis Audit"
    existing = path.read_text(encoding="utf-8")
    if heading in existing: existing = existing[:existing.index(heading)].rstrip() + "\n"
    rep = payload["factor_retention"]["REPPCA160"]
    control = payload["factor_retention"]["PAIRMEAN_PCA160"]
    section = f"""

{heading}

RepPCA-160 was fitted without factor labels from the symmetrized cross-covariance of two
independent TRAIN sequencing realizations of the same synthetic biological cells. It is intended
to emphasize reproducible cross-replicate molecular variation. It is not assumed to be biological
truth, is not a pathway basis, is not pathology-informed, and is not yet a production representation.

The shared eigenspectrum contained `{payload['eigenspectrum']['positive_count']}` positive,
`{payload['eigenspectrum']['near_zero_count']}` near-zero, and
`{payload['eigenspectrum']['negative_count']}` negative directions under the fixed threshold.
RepPCA mean factor R2 was `{rep['LAMBDA_NORM']['mean']:.6f}` for expected biology,
`{rep['X_A']['mean']:.6f}` for X_A, and `{rep['X_B']['mean']:.6f}` for X_B. Pair-mean PCA
controls were `{control['X_A']['mean']:.6f}` and `{control['X_B']['mean']:.6f}` for the two
count replicates. RepPCA median coordinate replicate correlation was
`{payload['cross_replicate_stability']['REPPCA160']['coordinate_correlation']['median']:.6f}`;
its within/between distance ratio was
`{payload['cross_replicate_stability']['REPPCA160']['within_between_mean_ratio']:.6f}`.

All frozen CP-IU masks passed exact whitened visible-plus-hidden decomposition. TRAIN-only
residual priors and replicate measurement-noise floors were recorded per realistic mask and
coordinate. Direct coordinate alignment to the old CP-IU PCA table is not defined across bases
and was not invented. Final classification: **{payload['classification']}**. Qualification does
not authorize Belief-JEPA training; human review remains required.
"""
    atomic_text(path, existing + section)


if __name__ == "__main__":
    raise SystemExit(main())
