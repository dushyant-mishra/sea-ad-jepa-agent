#!/usr/bin/env python3
"""Prospective E0-E3 broad-cell-class propagation tournament.

The runner is deliberately fail-closed on the corrected S174 evaluation-universe bytes. It may
be imported and structurally tested without those bytes, but a scientific run requires the exact
hash-bound 14,417-address NPZ recorded by the corrected S174 replay. No substitute universe is
accepted. Corrected real values are descriptive references while S159 remains unresolved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "v64"))

import build_v77_class_composition_authority as CA  # noqa: E402
import build_v77_class_aware_truth as CAT  # noqa: E402
import build_v77_class_aware_fullscale_rna_observer as CFO  # noqa: E402
import build_v77_extended_truth as EXT  # noqa: E402
import v77_matched_scoring as MS  # noqa: E402
import v73_full104_population_geometry as G  # noqa: E402

ARMS = ("E0", "E1", "E2", "E3")
REAL_REFERENCE_STATUS = "DESCRIPTIVE_ONLY__S159_NOT_BINARY_AUTHORITY"
CORRECTED_UNIVERSE_SHA256 = "e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763"
CORRECTED_UNIVERSE_NAME = "TRAIN_PREVALENCE05_19569"  # legacy name; corrected universe has 14,417 addresses
CORRECTED_UNIVERSE_N = 14417
DEFAULT_SEED = 7302
DEFAULT_CELLS = 2500
BASE_ENABLED_COMPONENTS = tuple(EXT.WORLD_PRESETS["B"])
FULLSCALE_OUT_NAME = "FULLSCALE_CLASS_PROPAGATION_sharded"

REQUIRED_PANEL_FIELDS = (
    "expression.median_abs_corr",
    "expression.frac_abs_gt_0p3",
    "expression.var_top10_pc",
    "detection.median_abs_corr",
    "detection.frac_abs_gt_0p3",
    "detection.mean_degree",
    "detection.transitivity",
    "detection.largest_community_frac",
    "t5.within_over_pooled",
    "abundance.abundance_max_over_median_nonzero",
    "abundance.top1pct_count_share",
    "median_detected_per_cell",
)

EXECUTOR_FILES = (
    "scripts/v77/run_v77_class_propagation_tournament.py",
    "scripts/v77/build_v77_class_composition_authority.py",
    "scripts/v77/build_v77_class_aware_truth.py",
    "scripts/v77/build_v77_class_aware_fullscale_rna_observer.py",
    "scripts/v77/build_v77_fullscale_rna_observer_v2.py",
    "scripts/v77/v77_matched_scoring.py",
    "scripts/v64/v73_full104_population_geometry.py",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate_arm(arm: str) -> str:
    arm = str(arm)
    if arm == "E4":
        raise PermissionError("E4 donor×class interaction remains unauthorized")
    if arm not in ARMS:
        raise ValueError(f"unknown class-propagation arm: {arm}")
    return arm


def operator_support_2k(seed: int = DEFAULT_SEED) -> dict:
    authority, triplets, quotas = G.quotas_for_n(2000)
    counts = np.bincount(
        triplets[:, 1], weights=quotas, minlength=int(authority["n_operators"])
    ).astype(np.int64)
    return {
        "n_cells": 2000,
        "seed": int(seed),
        "n_operators": int(authority["n_operators"]),
        "operators_present": int(np.count_nonzero(counts)),
        "minimum_operator_count": int(counts.min()),
        "operator_counts": counts.tolist(),
    }


def load_universe(path: Path, expected_sha: str = CORRECTED_UNIVERSE_SHA256,
                  expected_name: str = CORRECTED_UNIVERSE_NAME) -> np.ndarray:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"corrected S174 evaluation universe is unavailable: {path}; expected sha256={expected_sha}"
        )
    actual = sha256_file(path)
    if actual != expected_sha:
        raise RuntimeError(f"evaluation universe sha256 mismatch: expected {expected_sha}, got {actual}")
    with np.load(path, allow_pickle=False) as z:
        if "evaluation_universe" not in z.files:
            raise RuntimeError("evaluation universe NPZ lacks evaluation_universe")
        if "name" in z.files and str(z["name"]) != expected_name:
            raise RuntimeError(f"evaluation universe name mismatch: {z['name']!s} != {expected_name}")
        universe = np.asarray(z["evaluation_universe"], dtype=np.int64)
    if expected_sha == CORRECTED_UNIVERSE_SHA256 and len(universe) != CORRECTED_UNIVERSE_N:
        raise RuntimeError(
            f"corrected universe must contain {CORRECTED_UNIVERSE_N} addresses, got {len(universe)}"
        )
    if len(universe) == 0 or np.any(universe < 0) or np.any(universe >= CFO.N_ADDRESSES):
        raise RuntimeError("evaluation universe contains invalid canonical address indices")
    return universe


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def executor_digests() -> dict[str, str]:
    out = {}
    for rel in EXECUTOR_FILES:
        p = ROOT / rel
        if not p.exists():
            raise FileNotFoundError(f"missing tournament executor: {rel}")
        if not _git("ls-files", "--", rel):
            raise RuntimeError(f"untracked tournament executor: {rel}")
        out[rel] = sha256_file(p)
    return out


def require_clean_executor_state(allow_dirty: bool = False) -> str:
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    if dirty and not allow_dirty:
        raise RuntimeError("refusing scientific tournament from dirty tracked state:\n" + dirty)
    head = _git("rev-parse", "HEAD")
    if not head:
        raise RuntimeError("cannot resolve git HEAD")
    return head


def _load_truth_classes(root: Path, n_cells: int, authority: dict, seed: int,
                        external_for_e0: bool = False) -> np.ndarray:
    truth = Path(root) / "hidden_truth"
    tm = json.loads((truth / "TRUTH_MANIFEST.json").read_text())
    classes = np.empty(int(n_cells), dtype=np.int16)
    for s in tm["shards"]:
        with np.load(truth / s["file"], allow_pickle=False) as z:
            ids = np.asarray(z["global_cell_index"], dtype=np.int64)
            if external_for_e0:
                cls = CA.allocate_classes(authority, int(n_cells), int(seed), ids)
            else:
                cls = np.asarray(z["broad_class_index"], dtype=np.int16)
            classes[ids] = cls
    return classes


def load_fullscale_counts(root: Path, out_name: str = FULLSCALE_OUT_NAME) -> np.ndarray:
    obs = Path(root) / "observable_raw" / out_name
    manifest = json.loads((obs / "FULLSCALE_V2_MANIFEST.json").read_text())
    n_cells = int(manifest["n_cells"])
    n_addresses = int(manifest["n_addresses"])
    if n_addresses != CFO.N_ADDRESSES:
        raise RuntimeError(f"fullscale observer returned {n_addresses} addresses, expected {CFO.N_ADDRESSES}")
    counts = np.zeros((n_cells, n_addresses), dtype=np.int32)
    seen = np.zeros(n_cells, dtype=bool)
    for shard in manifest["shards"]:
        p = obs / shard["file"]
        if sha256_file(p) != shard["sha256"]:
            raise RuntimeError("observable shard digest mismatch: " + shard["file"])
        with np.load(p, allow_pickle=False) as z:
            ids = np.asarray(z["global_cell_index"], dtype=np.int64)
            mat = sparse.csr_matrix(
                (z["data"], z["indices"], z["indptr"]),
                shape=(len(ids), n_addresses),
            )
            counts[ids] = mat.toarray().astype(np.int32, copy=False)
            seen[ids] = True
    if not seen.all():
        raise RuntimeError(f"observable output missing {int((~seen).sum())} cell rows")
    return counts


def _panel_has_required_fields(score: dict) -> None:
    actual = {
        "expression.median_abs_corr": score["expression"]["median_abs_corr"],
        "expression.frac_abs_gt_0p3": score["expression"]["frac_abs_gt_0p3"],
        "expression.var_top10_pc": score["expression"]["var_top10_pc"],
        "detection.median_abs_corr": score["detection"]["median_abs_corr"],
        "detection.frac_abs_gt_0p3": score["detection"]["frac_abs_gt_0p3"],
        "detection.mean_degree": score["detection"]["mean_degree"],
        "detection.transitivity": score["detection"]["transitivity"],
        "detection.largest_community_frac": score["detection"]["largest_community_frac"],
        "t5.within_over_pooled": score["t5"]["within_over_pooled"],
        "abundance.abundance_max_over_median_nonzero": score["abundance"]["abundance_max_over_median_nonzero"],
        "abundance.top1pct_count_share": score["abundance"]["top1pct_count_share"],
        "median_detected_per_cell": score["median_detected_per_cell"],
    }
    if set(actual) != set(REQUIRED_PANEL_FIELDS):
        raise RuntimeError("scoring panel field mismatch")


def make_receipt(authority_sha: str, universe_sha: str, universe_name: str, seed: int,
                 cells: int, results: dict, operator_support: dict,
                 executor_digests: dict) -> dict:
    return {
        "schema": "V77_CLASS_PROPAGATION_TOURNAMENT_V1",
        "claim_class": "DESCRIPTIVE_SYNTHETIC_MECHANISM_EXPERIMENT",
        "arms": list(ARMS),
        "base_enabled_components": list(BASE_ENABLED_COMPONENTS),
        "fullscale_background": CFO.DEFAULT_BACKGROUND,
        "seed": int(seed),
        "cells": int(cells),
        "class_authority_sha256": authority_sha,
        "evaluation_universe": {"name": universe_name, "sha256": universe_sha},
        "real_reference_status": REAL_REFERENCE_STATUS,
        "statistical_ruling": {
            "real_point_estimates": "descriptive references",
            "donor_resampled_distributions": "uncertainty diagnostics",
            "s159_binary_gate": False,
            "recentring": False,
        },
        "no_post_outcome_retuning": True,
        "e4_authorized": False,
        "operator_support_2k": operator_support,
        "executor_digests": executor_digests,
        "scoring_rule": MS.RULE,
        "required_panel_fields": list(REQUIRED_PANEL_FIELDS),
        "results": results,
    }


def _build_and_observe_arm(arm: str, work: Path, authority_path: Path, authority: dict,
                           cells: int, seed: int, measurement_seed: int) -> tuple[dict, np.ndarray, np.ndarray]:
    validate_arm(arm)
    root = work / arm
    if arm == "E0":
        truth_manifest = EXT.build(root, cells, min(cells, 500), seed, list(BASE_ENABLED_COMPONENTS))
        obs_manifest = CFO.observe(root, seed, measurement_seed, background=CFO.DEFAULT_BACKGROUND)
        classes = _load_truth_classes(root, cells, authority, seed, external_for_e0=True)
    else:
        truth_manifest = CAT.build(
            root, cells, min(cells, 500), seed, arm, authority_path,
            enabled=list(BASE_ENABLED_COMPONENTS),
        )
        obs_manifest = CFO.observe(root, seed, measurement_seed, background=CFO.DEFAULT_BACKGROUND)
        classes = _load_truth_classes(root, cells, authority, seed, external_for_e0=False)
    counts = load_fullscale_counts(root)
    return {"truth": truth_manifest, "observer": obs_manifest}, counts, classes


def run_tournament(universe_path: Path, authority_path: Path, work: Path, cells: int,
                   seed: int, measurement_seed: int) -> dict:
    universe = load_universe(universe_path, CORRECTED_UNIVERSE_SHA256, CORRECTED_UNIVERSE_NAME)
    authority_path = Path(authority_path)
    authority_sha = sha256_file(authority_path)
    authority = json.loads(authority_path.read_text())
    if authority.get("schema") != CA.SCHEMA:
        raise RuntimeError("class authority schema mismatch")
    results = {}
    for arm in ARMS:
        manifests, counts, classes = _build_and_observe_arm(
            arm, Path(work), authority_path, authority, int(cells), int(seed), int(measurement_seed)
        )
        score = MS.score_matched(counts, universe, classes)
        _panel_has_required_fields(score)
        results[arm] = {
            "score": score,
            "truth_manifest_schema": manifests["truth"]["schema"],
            "observer_manifest_schema": manifests["observer"]["schema"],
            "class_scoring_source": (
                "EXTERNAL_FROZEN_CLASS_ALLOCATION_FOR_UNMODIFIED_E0"
                if arm == "E0" else "HIDDEN_TRUTH_BROAD_CLASS_INDEX"
            ),
        }
    # E1 is a label-only arm; scientific interpretation requires its observable score to equal E0.
    if results["E0"]["score"] != results["E1"]["score"]:
        raise RuntimeError("E1 label-only arm changed matched observable scores relative to E0")
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--authority", default="results/v77/V77_CLASS_COMPOSITION_AUTHORITY_V1.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--cells", type=int, default=DEFAULT_CELLS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--measurement-seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()

    head = require_clean_executor_state(args.allow_dirty)
    digests = executor_digests()
    universe = Path(args.universe)
    # Authenticate before any large synthetic world is materialized.
    load_universe(universe, CORRECTED_UNIVERSE_SHA256, CORRECTED_UNIVERSE_NAME)
    authority_path = Path(args.authority)
    if not authority_path.is_absolute():
        authority_path = ROOT / authority_path
    if not authority_path.exists():
        raise FileNotFoundError(f"class authority artifact unavailable: {authority_path}")
    results = run_tournament(
        universe, authority_path, Path(args.work), args.cells, args.seed, args.measurement_seed
    )
    receipt = make_receipt(
        authority_sha=sha256_file(authority_path),
        universe_sha=sha256_file(universe),
        universe_name=CORRECTED_UNIVERSE_NAME,
        seed=args.seed,
        cells=args.cells,
        results=results,
        operator_support=operator_support_2k(args.seed),
        executor_digests=digests,
    )
    receipt["git_head"] = head
    receipt["provenance_status"] = (
        "DEVELOPMENT_ALLOW_DIRTY" if args.allow_dirty else "CLEAN_COMMITTED_HEAD"
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "status": "RECORDED",
        "arms": list(ARMS),
        "cells": args.cells,
        "universe_sha256": CORRECTED_UNIVERSE_SHA256,
        "s159_binary_gate": False,
    }, indent=2))


if __name__ == "__main__":
    main()
