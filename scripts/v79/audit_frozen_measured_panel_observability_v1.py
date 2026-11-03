"""Read-only, NON-AUTHORIZING measurement-support diagnostic on PR328's frozen world.

Not a target generator, encoder, teacher, learner, biological scoring law or
replacement for V79 Q00-Q11 / PR318 / PR438. It reuses the EXACT existing
PR328 default world/fit seeds and receipt, and reports only aggregate support.
The 8-other-gene panel is a source-blind synthetic illustration of R5's
*measured* q-other-8 construction, NOT R5's biological 8-gene panel.

A structural-unmeasured gene is never treated as a measured zero. The queried
scalar is excluded from the measured-panel denominator. No controller truth
or source-human outcome is read. Do not import from any fit/teacher executor.
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Mapping

import numpy as np

from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology
from scripts.v79.unified_synthetic_fit_view_v1 import (
    UnifiedObservationConfig, fit_view_sha256, observe_unified_world, serialize_fit_view,
)

SCHEMA = "JEPA_SYNTHETIC_FROZEN_Q_OTHER_8_OBSERVABILITY_V1"
SOURCE_PR328_HEAD = "25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec"
RECEIPT = "results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json"
WORLD_SEED = 20261013
OBSERVATION_SEED = 20261014
QUERY_INDEX = 0
OTHER_GENE_PANEL = (1, 2, 3, 4, 5, 6, 7, 8)
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
AUTHORITY_FIELDS = (
    "target_selection_authorized",
    "representation_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
    "real_data_authorized",
    "synthetic_training_authorized",
)
_FORBIDDEN_FIT_KEYS = frozenset({
    "rare_activity", "rare_eligible", "rare_program_activity",
    "rare_donor_prevalence", "expected_molecular_state", "perturbation_state",
    "controller_truth", "controller_truth_sha256", "candidate_mapping",
    "counterfactual_truth", "latent_abundance", "pseudo_rare",
})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("SYNTHETIC_PANEL_MEASUREMENT_REFUSED: " + message)


def measured_panel_target(counts: np.ndarray, support: np.ndarray, *,
                          query_index: int = QUERY_INDEX,
                          panel: tuple[int, ...] = OTHER_GENE_PANEL) -> tuple[np.ndarray, np.ndarray]:
    """Private diagnostic, not a learner/teacher production interface.

    Returns eligible measurement-row mask and a q-excluded log1p(10k) panel.
    Ineligible targets are NaN and must NOT be scored as zeros.
    """
    _require(type(query_index) is int and query_index >= 0, "exact query index")
    _require(type(panel) is tuple and len(panel) == 8
             and all(type(g) is int and g >= 0 for g in panel)
             and len(set(panel)) == 8 and query_index not in panel, "exact other-gene panel")
    _require(type(counts) is np.ndarray and counts.ndim == 2
             and counts.dtype.kind in "iu", "raw integer count matrix")
    _require(type(support) is np.ndarray and support.dtype == np.dtype("bool")
             and support.shape == counts.shape, "exact Boolean support matrix")
    _require(max((query_index, *panel)) < counts.shape[1], "index outside frozen panel")
    _require(bool(np.all(counts >= 0)), "negative count")
    _require(bool(np.all(counts[~support] == 0)), "unmeasured entries cannot carry count")

    p = np.asarray(panel, dtype=np.int64)
    # Convert to Python integers to avoid NumPy integer-sum overflow.
    denominators = [sum(int(k) for k in row) for row in counts[:, p]]
    measured = support[:, query_index] & support[:, p].all(axis=1)
    positive = np.asarray([d > 0 for d in denominators], dtype=bool)
    eligible = measured & positive
    target = np.full((counts.shape[0], len(panel)), np.nan, dtype=np.float64)
    for i in np.flatnonzero(eligible):
        denom = denominators[int(i)]
        target[i, :] = np.log1p(10000.0 * counts[i, p].astype(np.float64) / denom)
    return eligible, target


def analyze_frozen_fixture(repo_root: Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    receipt_path = root / RECEIPT
    _require(receipt_path.is_file() and not receipt_path.is_symlink(), "frozen receipt unavailable")
    receipt: Mapping[str, object] = json.loads(receipt_path.read_text(encoding="utf-8"))
    _require(receipt.get("schema") == "UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2", "frozen schema")
    authority = receipt.get("authority")
    _require(type(authority) is dict and set(authority) == set(AUTHORITY_FIELDS)
             and all(authority[k] is False for k in AUTHORITY_FIELDS), "frozen authority-off")
    _require(receipt.get("controller_in_fit_package") is False, "controller separation")
    calib = receipt.get("calibration")
    _require(isinstance(calib, dict)
             and calib.get("rare_frequency_source") == "SYNTHETIC_STRESS_PRESETS_NOT_EMPIRICAL_CALIBRATION"
             and calib.get("pseudo_rarity_source") == "SYNTHETIC_STRESS_PRESET_NOT_EMPIRICAL_CALIBRATION"
             and calib.get("stat1_50k_physical_row_status") == "QUARANTINED_NOT_HARD_AUTHORITY",
             "synthetic/nonempirical calibration scope")

    # Reconstruct the existing PR328 receipt world with its ORIGINAL fixed seeds.
    # Never run a fresh scientific tournament or generate a tuned new world.
    world = build_unified_biology(UnifiedBiologyConfig(), seed=WORLD_SEED)
    fit = observe_unified_world(world, UnifiedObservationConfig(), seed=OBSERVATION_SEED)
    _require(world.world_hash == receipt.get("world_sha256"), "frozen world SHA mismatch")
    observed_fit_sha = fit_view_sha256(fit)
    _require(observed_fit_sha == receipt.get("fit_view_sha256"), "frozen fit SHA mismatch")
    payload = serialize_fit_view(fit)
    _require(not (_FORBIDDEN_FIT_KEYS & set(payload)), "controller truth exposed in fit")
    _require(payload["schema"] == "UNIFIED_SYNTHETIC_FIT_VIEW_V1", "fit schema")

    values, support = fit.values, fit.support
    eligible, target = measured_panel_target(values, support)
    # A legal q-other-8 measurement is invariant to the q scalar itself.
    altered = np.asarray(values).copy()
    altered[:, QUERY_INDEX] += 10000
    changed_eligible, changed_target = measured_panel_target(altered, support)
    _require(bool(np.array_equal(eligible, changed_eligible))
             and bool(np.array_equal(target, changed_target, equal_nan=True)),
             "query scalar leaks into other-gene target")

    p = np.asarray(OTHER_GENE_PANEL, dtype=np.int64)
    per_source = {}
    for source in SOURCE_NAMES:
        rows = np.flatnonzero(fit.source == source)
        _require(bool(len(rows)), f"expected fixture source absent: {source}")
        subset = support[rows]
        donor_count = len(np.unique(fit.donor_id[rows]))
        missing = [int(g) for g in p if not bool(subset[:, int(g)].all())]
        support_rows = int((subset[:, QUERY_INDEX] & subset[:, p].all(axis=1)).sum())
        positive_rows = int(eligible[rows].sum())
        per_source[source] = {
            "cells": int(len(rows)),
            "donors": int(donor_count),
            "panel_missing_addresses": missing,
            "fully_measured_8_gene_rows": support_rows,
            "positive_denominator_rows": positive_rows,
            "not_estimable_rows": int(len(rows) - positive_rows),
        }

    return {
        "schema": SCHEMA,
        "generator_head": SOURCE_PR328_HEAD,
        "world_sha256": receipt["world_sha256"],
        "fit_view_sha256": observed_fit_sha,
        "world_seed": WORLD_SEED,
        "observation_seed": OBSERVATION_SEED,
        "query_address_index": QUERY_INDEX,
        "other_gene_panel_address_indices": list(OTHER_GENE_PANEL),
        "construction": "MEASURED_Q_OTHER_8__Q_EXCLUDED_LOG1P10K__STRICT_SUPPORT",
        "q_scalar_invariance": True,
        "n_cells": int(len(fit.source)),
        "per_synthetic_source": per_source,
        "controller_truth_used": False,
        "human_query_rights_authenticated": False,
        "source_labels_are_synthetic": True,
        "fitted_any_model": False,
        "selected_any_target": False,
        "result_scope": "FIXTURE_MEASUREMENT_AVAILABILITY_ONLY__NOT_BIOLOGY_OR_TEACHER_QUALIFICATION",
        "authority": dict(authority),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", default=".")
    opts = parser.parse_args()
    print("FROZEN_PANEL_DIAGNOSTIC_BEGIN")
    print(json.dumps(analyze_frozen_fixture(Path(opts.repo_root)), sort_keys=True, indent=2))
    print("FROZEN_PANEL_DIAGNOSTIC_END")
