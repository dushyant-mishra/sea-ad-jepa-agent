#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from build_v72_coupled_multidataset_synthetic_fixture import build

TARGETS = {
    "SMALL_CI_10K": 10000,
    "MEDIUM_STRESS_100K": 100000,
    "MEDIUM_STRESS_500K": 500000,
    "FULL104_SCALE": 4553407,
}


def directory_bytes(root: Path):
    total = 0
    by_family = defaultdict(int)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        n = p.stat().st_size
        total += n
        rel = p.relative_to(root)
        family = rel.parts[0] if rel.parts else "_root"
        by_family[family] += n
    return total, dict(sorted(by_family.items()))


def measure(challenge_root: Path):
    obs = challenge_root / "observable_raw"
    total, by_family = directory_bytes(obs)
    full = json.loads((obs / "FULL104_LIKE/contract.json").read_text())
    # The current CI generator has 240 FULL104-like cells. Read it from metadata rather than
    # hard-coding, so the resource receipt follows the emitted fixture.
    with open(obs / "FULL104_LIKE/metadata.csv", encoding="utf-8") as fh:
        n_cells = sum(1 for _ in fh) - 1
    return {
        "observable_bytes": total,
        "bytes_by_family": by_family,
        "full104_like_cells_measured": n_cells,
        "full104_structural_missingness_semantics": full["structural_missingness_is_not_zero"],
    }


def make_receipt(challenge_root: Path):
    m = measure(challenge_root)
    n = m["full104_like_cells_measured"]
    full_bytes = m["bytes_by_family"]["FULL104_LIKE"]
    bytes_per_full104_ci_cell = full_bytes / n

    projections = {}
    for name, cells in TARGETS.items():
        projections[name] = {
            "cells": cells,
            "FULL104_like_linear_projection_bytes": int(round(bytes_per_full104_ci_cell * cells)),
            "FULL104_like_linear_projection_gib": round(
                bytes_per_full104_ci_cell * cells / (1024 ** 3), 3
            ),
            "status": "PLANNING_ESTIMATE_ONLY",
        }

    return {
        "schema": "V72_SYNTHETIC_RESOURCE_ESTIMATE_V1",
        "status": "MEASURED_SMALL_CI_BYTES__PROJECTIONS_ARE_PLANNING_ONLY",
        "measured": m,
        "projection_basis": {
            "what_is_linearized": "FULL104_LIKE emitted bytes per CI cell only",
            "what_is_not_linearized": [
                "SCENIC+ fragments and peak-calling temporary expansion",
                "cisTarget motif databases",
                "MACS/pycisTopic intermediates",
                "checkpoint size",
                "sparse nonzero scaling",
                "compression-ratio changes with scale",
                "filesystem/container overhead",
            ],
            "rule": "A projection is not a resource qualification. MEDIUM_STRESS must be measured before FULL104_SCALE.",
        },
        "projections": projections,
        "promotion": {
            "MEDIUM_STRESS": "requires an executed 100k then 500k resource receipt",
            "FULL104_SCALE": "forbidden until medium-stress resource/streaming gates pass",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge-root")
    ap.add_argument("--build-temp", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if bool(a.challenge_root) == bool(a.build_temp):
        raise SystemExit("choose exactly one of --challenge-root or --build-temp")

    if a.build_temp:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "challenge"
            build(root)
            receipt = make_receipt(root)
    else:
        receipt = make_receipt(Path(a.challenge_root))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
