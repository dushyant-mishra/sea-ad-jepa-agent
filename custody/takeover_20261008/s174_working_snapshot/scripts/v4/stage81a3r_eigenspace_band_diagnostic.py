"""Diagnose hard-fixture flat-eigenspectrum and contiguous-band identifiability."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT)); sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sea_ad_jepa.v4.full_transcriptome_synthetic import generate_full_transcriptome_fixture  # noqa: E402
from sea_ad_jepa.v4.successor_candidate import fit_reproducibility_weighted_basis, masked_project  # noqa: E402
from scripts.v4.stage81a3r_full_transcriptome_microqual import reproducibility  # noqa: E402


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as handle: temporary = Path(handle.name)
    frame.to_csv(temporary, index=False, lineterminator="\n"); os.replace(temporary, path)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n"); temporary = Path(handle.name)
    os.replace(temporary, path)


def factor_r2(coordinates: np.ndarray, factors: np.ndarray, train: np.ndarray, test: np.ndarray) -> float:
    scores = []
    for index in range(factors.shape[1]):
        model = Ridge(alpha=1.0).fit(coordinates[train], factors[train, index])
        scores.append(r2_score(factors[test, index], model.predict(coordinates[test])))
    return float(np.mean(scores))


def donor_covariance_fraction(coordinates: np.ndarray, donors: np.ndarray) -> tuple[float, float]:
    centered = coordinates - coordinates.mean(0, keepdims=True)
    total = float(np.mean(centered ** 2))
    donor_means = {donor: coordinates[donors == donor].mean(0) for donor in sorted(set(donors))}
    between = float(np.mean(np.stack([donor_means[value] for value in donors]) ** 2))
    fraction = min(1.0, max(0.0, between / max(total, 1e-12)))
    return fraction, 1.0 - fraction


def evaluate(fixture, config: dict) -> tuple[list[dict], list[dict], dict]:
    cells = len(fixture.factors); train = np.arange(int(cells * 2 / 3)); test = np.arange(int(cells * 2 / 3), cells)
    donors = sorted(set(fixture.donor_ids[train])); midpoint = len(donors) // 2
    subsets = (set(donors[:midpoint]), set(donors[midpoint:]))
    maximum = int(config["max_dimension"]); fits_by_type = {"ordinary_pca": [], "reproducibility_weighted": []}
    for subset in subsets:
        rows = np.asarray([value in subset for value in fixture.donor_ids[train]])
        both = fixture.support_view1[train][rows] & fixture.support_view2[train][rows]
        local_repro = reproducibility(fixture.normalized_view1[train][rows], fixture.normalized_view2[train][rows], both)
        fits_by_type["ordinary_pca"].append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], np.ones_like(local_repro), fixture.donor_ids[train][rows], maximum))
        fits_by_type["reproducibility_weighted"].append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], local_repro, fixture.donor_ids[train][rows], maximum))
    both = fixture.support_view1[train] & fixture.support_view2[train]
    full_repro = reproducibility(fixture.normalized_view1[train], fixture.normalized_view2[train], both)
    full_fits = {
        "ordinary_pca": fit_reproducibility_weighted_basis(fixture.normalized_view1[train], fixture.support_view1[train], np.ones_like(full_repro), fixture.donor_ids[train], maximum),
        "reproducibility_weighted": fit_reproducibility_weighted_basis(fixture.normalized_view1[train], fixture.support_view1[train], full_repro, fixture.donor_ids[train], maximum),
    }
    spectrum_rows = []
    for basis_type, basis in full_fits.items():
        eigenvalues = basis.singular_values ** 2
        total = eigenvalues.sum()
        for index, value in enumerate(eigenvalues, start=1):
            next_value = eigenvalues[index] if index < len(eigenvalues) else np.nan
            spectrum_rows.append({"fixture": fixture.name, "basis_type": basis_type, "dimension": index, "eigenvalue": value, "explained_fraction_within_audited_96": value / total, "cumulative_fraction_within_audited_96": eigenvalues[:index].sum() / total, "relative_eigengap_to_next": (value - next_value) / value if np.isfinite(next_value) else np.nan})

    band_rows = []; all_bands = [("local", *band) for band in config["local_bands"]] + [("cumulative", *band) for band in config["cumulative_bands"]]
    for basis_type, fits in fits_by_type.items():
        full = full_fits[basis_type]
        all_coordinates = masked_project(fixture.normalized_view1, fixture.support_view1, full, maximum)
        view2_coordinates = masked_project(fixture.normalized_view2, fixture.support_view2, full, maximum)
        paired_covariance = np.maximum(np.diag(np.cov(all_coordinates[train].T, view2_coordinates[train].T)[:maximum, maximum:]), 0.0)
        reproducible_total = paired_covariance.sum().clip(min=1e-12)
        for band_type, start, end in all_bands:
            left = fits[0].components[:, start - 1:end]; right = fits[1].components[:, start - 1:end]
            singular = np.linalg.svd(left.T @ right, compute_uv=False)
            coordinates = all_coordinates[:, start - 1:end]
            donor_fraction, shared_fraction = donor_covariance_fraction(coordinates[train], fixture.donor_ids[train])
            band_rows.append({
                "fixture": fixture.name, "basis_type": basis_type, "band_type": band_type,
                "band_start": start, "band_end": end, "band_width": end - start + 1,
                "median_canonical_correlation": float(np.median(singular)),
                "minimum_canonical_correlation": float(np.min(singular)),
                "maximum_principal_angle_degrees": float(np.degrees(np.arccos(np.clip(np.min(singular), -1, 1)))),
                "reproducible_variance_fraction_within_audited_96": float(paired_covariance[start - 1:end].sum() / reproducible_total),
                "cumulative_reproducible_variance_fraction": float(paired_covariance[:end].sum() / reproducible_total) if start == 1 else np.nan,
                "donor_covariance_fraction": donor_fraction, "shared_within_donor_covariance_fraction": shared_fraction,
                "hidden_factor_mean_r2": factor_r2(coordinates, fixture.factors, train, test),
                "stable": bool(np.median(singular) >= config["stability_threshold"]),
            })
    raw_features = np.stack([fixture.normalized_view1[:, mask].mean(1) for mask in fixture.factor_gene_mask], axis=1)
    raw_recovery = factor_r2(raw_features, fixture.factors, train, test)
    weighted_cumulative = [row for row in band_rows if row["basis_type"] == "reproducibility_weighted" and row["band_type"] == "cumulative"]
    stable_wider = [row for row in weighted_cumulative if row["stable"] and row["band_end"] > config["cumulative_bands"][0][1]]
    if stable_wider:
        classification = "BOUNDARY / EIGENSPACE IDENTIFIABILITY LIMITATION"
    elif raw_recovery >= config["raw_recoverability_r2_threshold"]:
        classification = "DONOR-HETEROGENEITY / COMMON-SUBSPACE UNRESOLVED"
    else:
        classification = "GLOBAL REPRESENTATION CONCERN"
    summary = {"fixture": fixture.name, "cells": cells, "genes": fixture.counts_view1.shape[1], "raw_informative_mean_factor_r2": raw_recovery, "stable_wider_weighted_band": bool(stable_wider), "stable_wider_weighted_band_end": min((row["band_end"] for row in stable_wider), default=None), "classification": classification, "dimension_or_band_promoted": False}
    return spectrum_rows, band_rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--project-dir", type=Path, default=Path(".")); parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_a3r_microqual.yaml")); args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle: root = yaml.safe_load(handle)
    config = root["eigenspace_band_diagnostic"]
    gene_count = len(pd.read_csv(project / root["outputs"]["exact_registry"], usecols=["successor_gene_index"]))
    spectrum = []; bands = []; summaries = []
    for item in root["synthetic"]["fixtures"]:
        fixture = generate_full_transcriptome_fixture(gene_count, cells=int(config["cells"]), seed=int(item["seed"]), name=item["name"])
        local_spectrum, local_bands, summary = evaluate(fixture, config); spectrum.extend(local_spectrum); bands.extend(local_bands); summaries.append(summary)
    atomic_csv(project / root["outputs"]["eigenspectrum"], pd.DataFrame(spectrum)); atomic_csv(project / root["outputs"]["eigenspace_bands"], pd.DataFrame(bands))
    report = {"stage": "stage81a3r_hard_fixture_eigenspace_diagnostic_candidate", "status": "PROVISIONAL_NOT_FROZEN", "hard_fixtures_only": True, "generator_changed": False, "weighting_changed": False, "architecture_changed": False, "thresholds_changed": False, "sample_size_changed": False, "summaries": summaries, "global_resolution_decision": "UNADJUDICATED", "dimension_or_band_promoted": False, "dev_rna_accessed": False, "sealed_rna_accessed": False, "pathology_accessed": False, "neural_optimizer_updates": 0, "stage81b_started": False, "stage81c_started": False}
    atomic_json(project / root["outputs"]["eigenspace_report"], report); print(json.dumps(report, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
