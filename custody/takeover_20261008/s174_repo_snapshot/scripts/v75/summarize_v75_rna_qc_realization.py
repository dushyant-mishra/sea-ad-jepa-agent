#!/usr/bin/env python3
"""Re-read every FULL104-like RNA shard and prove technical QC targets were realized."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def summarize(root: Path) -> dict:
    base = Path(root) / "observable_raw" / "FULL104_like_sharded"
    manifest_path = base / "FULL104_SHARDED_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())

    n_cells = 0
    depth_mismatch = 0
    support_mismatch = 0
    unavailable_nonzero = 0
    shard_rows = []

    for shard in manifest["shards"]:
        path = base / shard["rna_file"]
        z = np.load(path, allow_pickle=False)
        counts = z["counts"]
        availability = z["availability"]
        target_depth = z["empirical_projected_panel_count_target_int"]
        target_support = z["empirical_projected_detected_feature_target_int"]

        actual_depth = counts.sum(axis=0)
        actual_support = ((counts > 0) & (availability > 0)).sum(axis=0)
        dmis = int(np.count_nonzero(actual_depth != target_depth))
        smis = int(np.count_nonzero(actual_support != target_support))
        unz = int(np.count_nonzero(counts[availability == 0]))
        cells = int(counts.shape[1])

        depth_mismatch += dmis
        support_mismatch += smis
        unavailable_nonzero += unz
        n_cells += cells
        shard_rows.append({
            "file": shard["rna_file"],
            "cells": cells,
            "panel_depth_mismatch_cells": dmis,
            "detected_support_mismatch_cells": smis,
            "unavailable_features_nonzero_count": unz,
        })

    expected = int(manifest["n_cells"])
    cell_reconciliation = n_cells == expected
    depth_ok = depth_mismatch == 0
    support_ok = support_mismatch == 0
    unavailable_ok = unavailable_nonzero == 0
    passed = cell_reconciliation and depth_ok and support_ok and unavailable_ok

    return {
        "schema": "V75_RNA_QC_REALIZATION_SUMMARY_V1",
        "status": "PASS__RNA_QC_TARGETS_REALIZED" if passed else "FAIL__RNA_QC_TARGETS_NOT_REALIZED",
        "n_cells_checked": n_cells,
        "manifest_n_cells": expected,
        "cell_count_reconciles": cell_reconciliation,
        "panel_depth_matches_target": depth_ok,
        "panel_depth_mismatch_cells": depth_mismatch,
        "detected_support_matches_target": support_ok,
        "detected_support_mismatch_cells": support_mismatch,
        "unavailable_features_nonzero_count": unavailable_nonzero,
        "all_unavailable_features_zero": unavailable_ok,
        "shards_checked": len(shard_rows),
        "per_shard": shard_rows,
        "claim_scope": "technical measurement-realization verification only; no learned-state or biological qualification",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    result = summarize(Path(a.root))
    text = json.dumps(result, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
