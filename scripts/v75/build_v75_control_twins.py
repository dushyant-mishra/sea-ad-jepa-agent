#!/usr/bin/env python3
"""Materialize prospective V75 synthetic control worlds.

This is a measurement-architecture control generator, not a learned-JEPA evaluator.
It creates:
  * measurement_null_a: reference biology, measurement seed 8501
  * measurement_null_b: identical biology/operator mapping, measurement seed 8502
  * biology_positive: same population and measurement seed as A, with the prospectively
    frozen +1.0 displacement on z_global[:, 0] for global_cell_index % 4 == 0.

No real data, pathology, correspondence, protected TEST, or training is opened here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

V64 = Path(__file__).resolve().parents[1] / "v64"
sys.path.insert(0, str(V64))
import build_v73_sharded_master_truth as T
import build_v73_full104_sharded_observer as R
import build_v73_paired_multiome_sharded_observer as M

TRUTH_SEED = 7302
MEASUREMENT_SEED_A = 8501
MEASUREMENT_SEED_B = 8502
TARGET_MODULO = 4
TARGET_REMAINDER = 0
DELTA_Z_GLOBAL_0 = np.float32(1.0)


def _mutate_biology_positive(root: Path) -> int:
    truth = root / "hidden_truth"
    manifest_path = truth / "TRUTH_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    targeted_total = 0
    for shard in manifest["shards"]:
        path = truth / shard["file"]
        z = np.load(path, allow_pickle=False)
        payload = {k: z[k] for k in z.files}
        ids = payload["global_cell_index"].astype(np.int64)
        targeted = (ids % TARGET_MODULO) == TARGET_REMAINDER
        zg = payload["z_global"].copy()
        zg[targeted, 0] = zg[targeted, 0] + DELTA_Z_GLOBAL_0
        payload["z_global"] = zg
        targeted_total += int(targeted.sum())
        np.savez(path, **payload)
        shard["sha256"] = T.sha256_file(path)
    manifest["control_intervention"] = {
        "status": "PROSPECTIVE_SYNTHETIC_BIOLOGY_POSITIVE",
        "target_rule": "global_cell_index % 4 == 0",
        "target_modulo": TARGET_MODULO,
        "target_remainder": TARGET_REMAINDER,
        "latent_block": "z_global",
        "latent_dimension": 0,
        "delta_z_global_0": float(DELTA_Z_GLOBAL_0),
        "n_targeted_cells": targeted_total,
        "population_assignment_changed": False,
        "technical_latents_changed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return targeted_total


def _build_world(root: Path, n_cells: int, shard_size: int, measurement_seed: int, positive: bool = False) -> dict:
    T.build(root, n_cells=n_cells, shard_size=shard_size, seed=TRUTH_SEED)
    targeted = _mutate_biology_positive(root) if positive else 0
    rna = R.observe(root, seed=TRUTH_SEED, measurement_seed=measurement_seed)
    multi = M.observe(root, seed=TRUTH_SEED, measurement_seed=measurement_seed)
    return {
        "root": str(root.resolve()),
        "truth_manifest": str((root / "hidden_truth/TRUTH_MANIFEST.json").resolve()),
        "truth_manifest_sha256": T.sha256_file(root / "hidden_truth/TRUTH_MANIFEST.json"),
        "rna_manifest": str((root / "observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json").resolve()),
        "rna_manifest_sha256": R.sha256_file(root / "observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json"),
        "multiome_manifest": str((root / "observable_raw/PAIRED_MULTIOME_like_sharded/PAIRED_MULTIOME_SHARDED_MANIFEST.json").resolve()),
        "multiome_manifest_sha256": M.sha256_file(root / "observable_raw/PAIRED_MULTIOME_like_sharded/PAIRED_MULTIOME_SHARDED_MANIFEST.json"),
        "truth_seed": TRUTH_SEED,
        "measurement_seed": measurement_seed,
        "n_cells": n_cells,
        "source_counts": rna["source_counts"],
        "paired_same_cell_identity": multi["paired_same_cell_identity"],
        "n_targeted_cells": targeted,
    }


def build_controls(root: Path, n_cells: int = 2000, shard_size: int = 333) -> dict:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    a_root = root / "measurement_null_a"
    b_root = root / "measurement_null_b"
    p_root = root / "biology_positive"

    a = _build_world(a_root, n_cells, shard_size, MEASUREMENT_SEED_A, positive=False)
    b = _build_world(b_root, n_cells, shard_size, MEASUREMENT_SEED_B, positive=False)
    p = _build_world(p_root, n_cells, shard_size, MEASUREMENT_SEED_A, positive=True)

    receipt = {
        "schema": "V75_CONTROL_TWINS_RECEIPT_V1",
        "status": "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION",
        "truth_seed": TRUTH_SEED,
        "n_cells_per_world": int(n_cells),
        "shard_size": int(shard_size),
        "worlds": {
            "measurement_null_a": a,
            "measurement_null_b": b,
            "biology_positive": p,
        },
        "measurement_null": {
            "world_a_measurement_seed": MEASUREMENT_SEED_A,
            "world_b_measurement_seed": MEASUREMENT_SEED_B,
            "biology_identical": True,
            "population_identical": True,
            "observation_operator_mapping_identical": True,
        },
        "biology_positive": {
            "reference_world": "measurement_null_a",
            "measurement_seed": MEASUREMENT_SEED_A,
            "target_rule": "global_cell_index % 4 == 0",
            "target_modulo": TARGET_MODULO,
            "target_remainder": TARGET_REMAINDER,
            "delta_z_global_0": float(DELTA_Z_GLOBAL_0),
            "n_targeted_cells": int(p["n_targeted_cells"]),
            "measurement_conditions_matched_to_reference": True,
        },
        "claim_boundary": {
            "learned_160d_jepa_evaluated": False,
            "biological_claim_qualified": False,
            "purpose": "materialize identifiable measurement-null and biology-positive controls for later learned-state qualification",
        },
        "governance": {
            "training": "OFF",
            "multimodal_training": "OFF",
            "stage4": "NOT_AUTHORIZED",
            "real_correspondence": "UNOPENED",
            "Morabito": "PROTECTED",
            "recoverability_TEST": "SEALED",
            "pathology_used": False,
        },
    }
    (root / "V75_CONTROL_TWINS_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cells", type=int, default=2000)
    ap.add_argument("--shard-size", type=int, default=333)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    receipt = build_controls(Path(args.root), n_cells=args.cells, shard_size=args.shard_size)
    text = json.dumps(receipt, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
