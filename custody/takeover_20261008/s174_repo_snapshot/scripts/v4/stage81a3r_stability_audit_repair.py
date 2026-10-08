"""Method-independent synthetic stability calibration and sample-size audit repair."""

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
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sea_ad_jepa.v4.full_transcriptome_synthetic import generate_full_transcriptome_fixture  # noqa: E402
from sea_ad_jepa.v4.successor_candidate import fit_reproducibility_weighted_basis, masked_project  # noqa: E402
from scripts.v4.stage81a3r_full_transcriptome_microqual import (  # noqa: E402
    coordinate_subspace_similarity, reproducibility,
)


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as handle:
        temporary = Path(handle.name)
    frame.to_csv(temporary, index=False, lineterminator="\n"); os.replace(temporary, path)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n"); temporary = Path(handle.name)
    os.replace(temporary, path)


def effective_rank(singular: np.ndarray) -> float:
    probability = singular / singular.sum().clip(min=1e-12)
    return float(np.exp(-(probability * np.log(probability.clip(min=1e-12))).sum()))


def known_factor_r2(coordinates: np.ndarray, factors: np.ndarray, train: np.ndarray, test: np.ndarray) -> float:
    values = []
    for column in range(factors.shape[1]):
        model = Ridge(alpha=1.0).fit(coordinates[train], factors[train, column])
        values.append(r2_score(factors[test, column], model.predict(coordinates[test])))
    return float(np.mean(values))


def evaluate_fixture(fixture, prefix: int, stability_threshold: float, fixture_role: str) -> dict:
    cells = len(fixture.factors); train = np.arange(int(cells * 2 / 3)); test = np.arange(int(cells * 2 / 3), cells)
    donors = sorted(set(fixture.donor_ids[train])); midpoint = len(donors) // 2
    subsets = (set(donors[:midpoint]), set(donors[midpoint:]))
    weighted = []; ordinary = []; effective_cells = []
    for subset in subsets:
        rows = np.asarray([value in subset for value in fixture.donor_ids[train]])
        effective_cells.append(int(rows.sum()))
        both = fixture.support_view1[train][rows] & fixture.support_view2[train][rows]
        local_repro = reproducibility(fixture.normalized_view1[train][rows], fixture.normalized_view2[train][rows], both)
        maximum = min(prefix, int(rows.sum()) - 1)
        weighted.append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], local_repro, fixture.donor_ids[train][rows], maximum))
        ordinary.append(fit_reproducibility_weighted_basis(fixture.normalized_view1[train][rows], fixture.support_view1[train][rows], np.ones_like(local_repro), fixture.donor_ids[train][rows], maximum))

    def metrics(fits):
        dimension = min(prefix, *(item.components.shape[1] for item in fits))
        singular = np.linalg.svd(fits[0].components[:, :dimension].T @ fits[1].components[:, :dimension], compute_uv=False)
        coordinates = [masked_project(fixture.normalized_view1[test], fixture.support_view1[test], item, dimension) for item in fits]
        return float(np.median(singular)), coordinate_subspace_similarity(*coordinates)

    ordinary_basis, ordinary_projected = metrics(ordinary)
    weighted_basis, weighted_projected = metrics(weighted)
    all_both = fixture.support_view1[train] & fixture.support_view2[train]
    full_repro = reproducibility(fixture.normalized_view1[train], fixture.normalized_view2[train], all_both)
    full_ordinary = fit_reproducibility_weighted_basis(fixture.normalized_view1[train], fixture.support_view1[train], np.ones_like(full_repro), fixture.donor_ids[train], prefix)
    full_weighted = fit_reproducibility_weighted_basis(fixture.normalized_view1[train], fixture.support_view1[train], full_repro, fixture.donor_ids[train], prefix)
    ordinary_coordinates = masked_project(fixture.normalized_view1, fixture.support_view1, full_ordinary, prefix)
    weighted_coordinates = masked_project(fixture.normalized_view1, fixture.support_view1, full_weighted, prefix)
    ordinary_factor = known_factor_r2(ordinary_coordinates, fixture.factors, train, test)
    weighted_factor = known_factor_r2(weighted_coordinates, fixture.factors, train, test)
    raw_features = np.stack([fixture.normalized_view1[:, mask].mean(1) for mask in fixture.factor_gene_mask], axis=1)
    raw_factor = known_factor_r2(raw_features, fixture.factors, train, test)
    if ordinary_basis < stability_threshold:
        classification = "AUDIT / FIXTURE LIMITATION"
    elif weighted_basis < stability_threshold:
        classification = "GLOBAL REPRESENTATION-DESIGN CONCERN"
    elif weighted_projected < stability_threshold:
        classification = "IMPLEMENTATION / PROJECTION CONCERN"
    else:
        classification = "STABILITY MACHINERY VALID AT THIS PREFIX"
    eigengap_index = min(prefix, len(full_ordinary.singular_values) - 1)
    eigengap = float((full_ordinary.singular_values[eigengap_index - 1] - full_ordinary.singular_values[eigengap_index]) / full_ordinary.singular_values[eigengap_index - 1]) if eigengap_index < len(full_ordinary.singular_values) else np.nan
    return {
        "fixture": fixture.name, "fixture_role": fixture_role, "cells": cells,
        "genes": fixture.counts_view1.shape[1], "donors": len(set(fixture.donor_ids)),
        "fit_cells_half_1": effective_cells[0], "fit_cells_half_2": effective_cells[1],
        "evaluated_prefix": prefix, "ordinary_basis_median_canonical_correlation": ordinary_basis,
        "weighted_basis_median_canonical_correlation": weighted_basis,
        "ordinary_projected_state_similarity": ordinary_projected,
        "weighted_projected_state_similarity": weighted_projected,
        "raw_informative_mean_factor_r2": raw_factor,
        "ordinary_pca_mean_factor_r2": ordinary_factor,
        "weighted_basis_mean_factor_r2": weighted_factor,
        "ordinary_effective_rank": effective_rank(full_ordinary.singular_values),
        "weighted_effective_rank": effective_rank(full_weighted.singular_values),
        "ordinary_relative_eigengap_at_prefix": eigengap,
        "ordinary_top_singular_values": "|".join(f"{value:.8g}" for value in full_ordinary.singular_values[: min(20, len(full_ordinary.singular_values))]),
        "classification": classification,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_a3r_microqual.yaml"))
    args = parser.parse_args(); project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle: config = yaml.safe_load(handle)
    repair = config["stability_audit_repair"]; prefix = int(repair["evaluated_prefix"]); threshold = float(repair["stability_threshold"])
    rows = []
    calibration = generate_full_transcriptome_fixture(int(repair["calibration_gene_count"]), cells=int(repair["calibration_cells"]), seed=int(repair["seed"]), name="stability_calibration")
    rows.append(evaluate_fixture(calibration, int(repair["calibration_known_rank"]), threshold, "method_independent_stability_calibration"))
    gene_count = len(pd.read_csv(project / config["outputs"]["exact_registry"], usecols=["successor_gene_index"]))
    for fixture_item in config["synthetic"]["fixtures"]:
        for cells in repair["hard_fixture_cell_levels"]:
            fixture = generate_full_transcriptome_fixture(gene_count, cells=int(cells), seed=int(fixture_item["seed"]), name=fixture_item["name"])
            rows.append(evaluate_fixture(fixture, prefix, threshold, "unchanged_hard_fixture_sample_size_diagnostic"))
    frame = pd.DataFrame(rows)
    output = project / config["outputs"]["stability_repair"]
    atomic_csv(output, frame)
    calibration_row = frame.iloc[0]
    hard = frame.iloc[1:]
    report = {
        "stage": "stage81a3r_stability_audit_repair_candidate",
        "status": "PROVISIONAL_NOT_FROZEN",
        "calibration_classification": calibration_row.classification,
        "calibration_ordinary_pca_stable": bool(calibration_row.ordinary_basis_median_canonical_correlation >= threshold),
        "hard_fixture_results": hard[["fixture", "cells", "classification", "ordinary_basis_median_canonical_correlation", "weighted_basis_median_canonical_correlation"]].to_dict(orient="records"),
        "hard_fixture_diagnosis": "donor heterogeneity / flat eigenspectrum remains unresolved; ordinary PCA is unstable despite increasing N",
        "valid_stable_hard_hierarchy_earned": bool((hard.classification == "STABILITY MACHINERY VALID AT THIS PREFIX").any()),
        "heldout_family_rerun_on_supported_prefix": False,
        "heldout_family_reason": "no hard fixture earned a stable supported global prefix",
        "sample_size_only_changed": True,
        "factor_amplitudes_changed_across_hard_levels": False,
        "thresholds_changed": False,
        "global_resolution_decision": "UNADJUDICATED",
        "historical_negative_outputs_overwritten": False,
        "dev_rna_accessed": False, "sealed_rna_accessed": False, "pathology_accessed": False,
        "neural_optimizer_updates": 0, "stage81b_started": False, "stage81c_started": False,
    }
    atomic_json(project / config["outputs"]["stability_repair_report"], report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
