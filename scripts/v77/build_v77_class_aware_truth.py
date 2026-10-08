#!/usr/bin/env python3
"""Successor V77 hidden truth for preregistered broad-cell-class propagation arms.

E0 remains the existing V77 truth. E1 adds only broad-class hidden metadata; it must not change
any pre-existing truth array or any observable output. E2/E3 are enabled in later RED->GREEN
steps. E4 is explicitly unauthorized here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v77_class_composition_authority as CA  # noqa: E402
import build_v77_extended_truth as V77  # noqa: E402

ALLOWED_NOW = {"E0", "E1"}
FUTURE_ARMS = {"E2", "E3"}
FORBIDDEN_ARMS = {"E4"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _load_authority(path: Path) -> tuple[dict, str]:
    path = Path(path)
    authority = json.loads(path.read_text())
    if authority.get("schema") != CA.SCHEMA:
        raise ValueError("wrong class authority schema")
    if not authority.get("pathology_blind") or not authority.get("train_only") or not authority.get("read_only"):
        raise PermissionError("class authority must be pathology-blind TRAIN-only read-only")
    return authority, sha256_file(path)


def build(root: Path, n_cells: int, shard_size: int, seed: int, arm: str,
          class_authority_path: Path | None, enabled: list[str] | None = None) -> dict:
    arm = str(arm)
    if arm in FORBIDDEN_ARMS:
        raise PermissionError("E4 donor×class interaction is not authorized in this implementation")
    if arm in FUTURE_ARMS:
        raise NotImplementedError(f"{arm} is preregistered but not implemented in the E1 step")
    if arm not in ALLOWED_NOW:
        raise ValueError(f"unknown class-propagation arm: {arm}")
    enabled = list(enabled or [])
    root = Path(root)

    base = V77.build(root, int(n_cells), int(shard_size), int(seed), enabled)
    if arm == "E0":
        return base
    if class_authority_path is None:
        raise ValueError("E1 requires class_authority_path")
    authority, authority_sha = _load_authority(Path(class_authority_path))

    truth = root / "hidden_truth"
    for shard in base["shards"]:
        path = truth / shard["file"]
        with np.load(path, allow_pickle=False) as zf:
            payload = {k: zf[k] for k in zf.files}
        ids = payload["global_cell_index"].astype(np.int64)
        payload["broad_class_index"] = CA.allocate_classes(
            authority, int(n_cells), int(seed), ids)
        np.savez(path, **payload)
        shard["sha256"] = sha256_file(path)

    quotas = CA.largest_remainder_quotas(
        np.asarray(authority["class_counts"], dtype=np.int64), int(n_cells))
    manifest = dict(base)
    manifest.update(
        schema="V77_CLASS_AWARE_MASTER_TRUTH_MANIFEST_V1",
        arm=arm,
        class_authority_sha256=authority_sha,
        class_authority_calibration_sha256=authority["calibration_sha256"],
        class_labels=list(authority["class_labels"]),
        class_quotas=[int(x) for x in quotas],
        class_assignment_stream=int(authority["class_assignment_stream"]),
        class_assignment_inputs=["global_cell_index", "seed", "class_authority"],
        class_conditioned_expression=False,
        class_program_content="NONE_E1_LABEL_ONLY",
        class_assignment_independent_of=["donor", "source", "operator", "expression", "query"],
    )
    (truth / "TRUTH_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--shard-size", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--arm", choices=["E0", "E1", "E2", "E3", "E4"], required=True)
    ap.add_argument("--class-authority", default=None)
    ap.add_argument("--components", default="")
    args = ap.parse_args()
    enabled = [x.strip() for x in args.components.split(",") if x.strip()]
    manifest = build(
        Path(args.root), args.cells, args.shard_size, args.seed, args.arm,
        (Path(args.class_authority) if args.class_authority else None), enabled=enabled)
    print(json.dumps({
        "status": "PASS",
        "arm": args.arm,
        "n_cells": manifest["n_cells"],
        "n_shards": len(manifest["shards"]),
        "class_authority_sha256": manifest.get("class_authority_sha256"),
    }, indent=2))


if __name__ == "__main__":
    main()
