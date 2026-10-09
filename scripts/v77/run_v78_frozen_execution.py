#!/usr/bin/env python3
"""Frozen V78 F0→F1→F2→F3 scientific execution driver.

This module executes only the prospectively frozen V78 arm definitions after an
explicit READY preexecution-gate receipt. It reuses the proven V77 E2 truth and
observer mechanics, monkeypatching only the surfaces prospectively authorized by
V78: BackgroundV2 for F1, signed detection selection for F2/F3, and F3 compact
abundance/depth marginals. No post-outcome tuning surface is exposed.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_v77_class_aware_fullscale_rna_observer as CLASS_OBSERVER  # noqa: E402
import build_v77_class_aware_truth as CLASS_TRUTH  # noqa: E402
import build_v77_extended_truth as EXT  # noqa: E402
import build_v77_fullscale_rna_observer_v2 as BASE  # noqa: E402
import build_v78_fullscale_rna_observer as V78OBS  # noqa: E402
import build_v78_marginal_authority as MARGINAL  # noqa: E402
import run_v77_class_propagation_tournament as V77  # noqa: E402
import run_v78_signed_detection_marginal_tournament as CONTRACT  # noqa: E402
import v77_background_v2 as BG2  # noqa: E402
import v78_signed_detection as SIGNED  # noqa: E402
import v78_signed_scoring as SCORE  # noqa: E402

ARMS = ("F0", "F1", "F2", "F3")
DEFAULT_SEED = 7302
DEFAULT_MEASUREMENT_SEED = 7302
DEFAULT_CELLS = 2500
NO_POST_OUTCOME_RETUNING = True
BASE_ENABLED_COMPONENTS = tuple(EXT.WORLD_PRESETS["B"])


def require_ready_gate(gate_receipt: dict) -> None:
    if gate_receipt.get("status") != "READY" or gate_receipt.get("blockers"):
        raise PermissionError(
            "V78 frozen execution requires READY gate with no blockers: "
            + ", ".join(map(str, gate_receipt.get("blockers", [])))
        )
    if gate_receipt.get("training_authorized") is not False:
        raise PermissionError("V78 gate must preserve training_authorized=false")
    if gate_receipt.get("post_outcome_retuning_authorized") is not False:
        raise PermissionError("V78 gate must preserve post_outcome_retuning_authorized=false")


def _truth_classes(root: Path, n_cells: int) -> np.ndarray:
    truth = Path(root) / "hidden_truth"
    tm = json.loads((truth / "TRUTH_MANIFEST.json").read_text())
    classes = np.empty(int(n_cells), dtype=np.int16)
    for shard in tm["shards"]:
        with np.load(truth / shard["file"], allow_pickle=False) as z:
            ids = np.asarray(z["global_cell_index"], dtype=np.int64)
            classes[ids] = np.asarray(z["broad_class_index"], dtype=np.int16)
    return classes


def _cache_background_v2_loadings_exactly():
    """Avoid rebuilding the identical immutable loading matrix once per truth shard."""
    original = BG2.BackgroundV2.loading_matrix

    def cached(self):
        if not hasattr(self, "_v78_exact_loading_cache"):
            self._v78_exact_loading_cache = original(self)
        return self._v78_exact_loading_cache

    BG2.BackgroundV2.loading_matrix = cached
    return original


def observe_frozen_arm(root: Path, arm: str, marginal_authority: dict | None,
                       seed: int = DEFAULT_SEED,
                       measurement_seed: int = DEFAULT_MEASUREMENT_SEED) -> dict:
    arm = CONTRACT.validate_arm(arm)
    root = Path(root)
    tm = json.loads((root / "hidden_truth" / "TRUTH_MANIFEST.json").read_text())
    if tm.get("arm") != "E2":
        raise RuntimeError("V78 scientific arms require frozen E2 truth")
    n_classes = len(tm.get("class_labels", []))
    if n_classes <= 0:
        raise RuntimeError("E2 truth lacks broad-class labels")

    if arm == "F0":
        return CLASS_OBSERVER.observe(
            root, int(seed), int(measurement_seed), background="v1"
        )

    original_eta = BASE.build_eta
    original_sparse = BASE.sparse_counts
    original_depth = BASE.depth_targets
    original_bg2_loading = None

    def eta_with_e2_class(z, enabled, eta_seed, uni, alloc, bg, n,
                          suppress=frozenset(), bg2=None):
        eta = original_eta(
            z, enabled, eta_seed, uni, alloc, bg, n,
            suppress=suppress, bg2=bg2,
        )
        eta = eta + CLASS_OBSERVER.class_program_contribution(z, eta_seed, n_classes)
        return eta.astype(np.float32, copy=False)

    BASE.build_eta = eta_with_e2_class
    out_name = f"V78_{arm}_sharded"

    if arm == "F1":
        original_bg2_loading = _cache_background_v2_loadings_exactly()
        background = "v2"
    else:
        background = "v1"

    if arm in {"F2", "F3"}:
        def sparse_with_signed(rel, sup, ids, lib, det, mseed):
            field = SIGNED.field(int(seed), np.asarray(ids, dtype=np.int64), rel.shape[1])
            weight_rel = None
            if arm == "F3":
                if marginal_authority is None:
                    raise RuntimeError("F3 requires marginal authority")
                assigned = MARGINAL.assign_rank_scrubbed_abundance(
                    marginal_authority["rank_scrubbed_abundance"], int(seed), rel.shape[1]
                )
                original_baseline = np.exp(
                    BASE.AU.AddressUniverse(int(seed)).log_abundance.astype(np.float64)
                )
                weight_rel = V78OBS.f3_positive_count_weights(
                    rel, original_baseline, assigned
                )
            return V78OBS.sparse_counts_separated(
                rel, sup, ids, lib, det, mseed,
                signed_field=field, weight_rel=weight_rel,
            )
        BASE.sparse_counts = sparse_with_signed

    if arm == "F3":
        if marginal_authority is None:
            raise RuntimeError("F3 requires marginal authority")
        MARGINAL.validate_runtime_authority(marginal_authority)
        depth_authority = marginal_authority["depth_marginals"]
        operator_sources = np.asarray(tm["operator_sources"]).astype(str)

        def depth_from_repaired_authority(ids, op, sup, qc, operator_ids, qprobs, mseed):
            source_labels = operator_sources[np.asarray(op, dtype=np.int64)]
            lib, det, _used = V78OBS.depth_targets_from_authority(
                ids, op, source_labels, sup, depth_authority, mseed
            )
            return lib, det

        BASE.depth_targets = depth_from_repaired_authority

    try:
        return BASE.observe(
            root, int(seed), int(measurement_seed), out_name=out_name,
            suppress=None, background=background,
        )
    finally:
        BASE.build_eta = original_eta
        BASE.sparse_counts = original_sparse
        BASE.depth_targets = original_depth
        if original_bg2_loading is not None:
            BG2.BackgroundV2.loading_matrix = original_bg2_loading


def run_frozen_tournament(*, work: Path, e2_reference_path: Path,
                          class_authority_path: Path, marginal_authority_path: Path,
                          universe_path: Path, gate_receipt: dict,
                          cells: int = DEFAULT_CELLS,
                          seed: int = DEFAULT_SEED,
                          measurement_seed: int = DEFAULT_MEASUREMENT_SEED) -> dict:
    require_ready_gate(gate_receipt)
    if int(cells) != DEFAULT_CELLS or int(seed) != DEFAULT_SEED or int(measurement_seed) != DEFAULT_MEASUREMENT_SEED:
        raise PermissionError("first V78 scientific tournament is frozen to 2500 cells and seed 7302")

    reference = CONTRACT.load_e2_reference(Path(e2_reference_path))
    universe = V77.load_universe(
        Path(universe_path), CONTRACT.EXPECTED_EVALUATION_UNIVERSE_SHA256,
        V77.CORRECTED_UNIVERSE_NAME,
    )
    authority_path = Path(class_authority_path)
    if V77.sha256_file(authority_path) != CONTRACT.EXPECTED_CLASS_AUTHORITY_SHA256:
        raise RuntimeError("class authority digest mismatch")
    marginal_path = Path(marginal_authority_path)
    marginal = json.loads(marginal_path.read_text())
    MARGINAL.validate_runtime_authority(marginal)

    results = {}
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        root = work / arm
        if root.exists():
            shutil.rmtree(root)
        CLASS_TRUTH.build(
            root, int(cells), min(int(cells), 500), int(seed), "E2",
            authority_path, enabled=list(BASE_ENABLED_COMPONENTS),
        )
        observer = observe_frozen_arm(
            root, arm, marginal, int(seed), int(measurement_seed)
        )
        out_name = (
            V77.FULLSCALE_OUT_NAME if arm == "F0" else f"V78_{arm}_sharded"
        )
        counts = V77.load_fullscale_counts(root, out_name=out_name)
        classes = _truth_classes(root, int(cells))
        score = SCORE.score_v78(counts, universe, classes)
        if arm == "F0":
            CONTRACT.assert_f0_score_matches_reference(score["legacy"], reference)
        results[arm] = {
            "score": score,
            "truth_arm": "E2",
            "observer_manifest_schema": observer["schema"],
            "config": CONTRACT.arm_config(arm),
        }

    return {
        "schema": "V78_SIGNED_DETECTION_MARGINAL_TOURNAMENT_V1",
        "claim_class": "DESCRIPTIVE_SYNTHETIC_MECHANISM_EXPERIMENT",
        "arms": list(ARMS),
        "cells": int(cells),
        "seed": int(seed),
        "measurement_seed": int(measurement_seed),
        "evaluation_universe_sha256": CONTRACT.EXPECTED_EVALUATION_UNIVERSE_SHA256,
        "class_authority_sha256": CONTRACT.EXPECTED_CLASS_AUTHORITY_SHA256,
        "marginal_authority_sha256": V77.sha256_file(marginal_path),
        "f0_exact_e2_reproduction": True,
        "real_reference_status": "DESCRIPTIVE_ONLY__S159_NOT_BINARY_AUTHORITY",
        "no_post_outcome_retuning": NO_POST_OUTCOME_RETUNING,
        "training_authorized": False,
        "e4_authorized": False,
        "results": results,
    }
