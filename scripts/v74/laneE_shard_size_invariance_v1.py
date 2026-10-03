#!/usr/bin/env python3
"""V74 LANE E: does SHARD SIZE change the numbers?

The project has proven that cisTarget outputs are invariant to worker count and to
storage location. It has NOT proven they are invariant to how many motifs are scored in
one invocation. That matters more than either, because the production database is
assembled from shards and a shard-size dependence would make the merged database a
function of an operational choice rather than of the data.

The test is available for free: the 128-motif bench list is the first 128 entries of the
frozen universe, and the 512-motif pilot slice is the first 512. The first 128 columns of
the pilot's motif axis are therefore the SAME 128 motifs over the SAME 150,561 regions.
They must agree.

SCORES and RANKINGS are checked separately and for different reasons.

  SCORES are expected to be independent of batch size: Cluster-Buster scores each
  (motif, region) pair on its own.

  RANKINGS are the one to worry about. They are produced with a pinned tie-break seed
  (20261001). If that seed drives a single RNG stream consumed across the whole batch,
  then the number of motifs in the batch changes the draws each motif receives, and two
  shards of different sizes would disagree. This script answers that empirically rather
  than by reading the tool's source.

A POSITIVE CONTROL is mandatory: the comparison machinery is pointed at two axes that
are genuinely different and must be shown to report a difference. A check that cannot
fail would make an equality result worthless.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def ordered_digest(items) -> str:
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode())
        h.update(b"\x1f")
        h.update(str(s).encode())
        h.update(b"\x1e")
    return h.hexdigest()


def compare(small: Path, big: Path, index_col: str, axis: str):
    """axis='columns' -> motifs are columns (motifs_vs_regions)
       axis='rows'    -> motifs are rows    (regions_vs_motifs)"""
    a = pd.read_feather(small)
    b = pd.read_feather(big)

    if axis == "columns":
        keys = [c for c in a.columns if c != index_col]
        missing = [k for k in keys if k not in b.columns]
        if missing:
            return {"status": "FAIL__MOTIFS_ABSENT_FROM_THE_LARGER_SHARD",
                    "n_missing": len(missing), "first_missing": missing[:5]}
        # align the index axis by NAME, never by position
        a = a.set_index(index_col).sort_index()
        b = b.set_index(index_col).sort_index()
        if list(a.index) != list(b.index):
            return {"status": "FAIL__INDEX_AXIS_DIFFERS"}
        A = a[keys].to_numpy()
        B = b[keys].to_numpy()
    else:
        a = a.set_index(index_col)
        b = b.set_index(index_col)
        keys = list(a.index)
        missing = [k for k in keys if k not in b.index]
        if missing:
            return {"status": "FAIL__MOTIFS_ABSENT_FROM_THE_LARGER_SHARD",
                    "n_missing": len(missing), "first_missing": missing[:5]}
        if list(a.columns) != list(b.columns):
            return {"status": "FAIL__REGION_AXIS_DIFFERS",
                    "n_small": len(a.columns), "n_big": len(b.columns)}
        A = a.loc[keys].to_numpy()
        B = b.loc[keys].to_numpy()

    diff = A != B
    n_diff = int(diff.sum())
    try:
        max_abs = float(np.nanmax(np.abs(A.astype(float) - B.astype(float)))) if n_diff else 0.0
    except (TypeError, ValueError):
        max_abs = "NON_NUMERIC"
    return {
        "status": "PASS__IDENTICAL" if n_diff == 0 else "DIFFERS",
        "n_motifs_compared": len(keys),
        "n_cells_compared": int(A.size),
        "n_cells_differing": n_diff,
        "max_abs_difference": max_abs,
        "small_matrix_digest": hashlib.sha256(np.ascontiguousarray(A)).hexdigest(),
        "big_subset_matrix_digest": hashlib.sha256(np.ascontiguousarray(B)).hexdigest(),
        "ordered_motif_digest_small": ordered_digest(keys),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--small-prefix", required=True,
                    help="path prefix of the 128-motif run outputs")
    ap.add_argument("--big-prefix", required=True,
                    help="path prefix of the 512-motif pilot outputs")
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)

    sp, bp = Path(a.small_prefix), Path(a.big_prefix)
    results = {}

    results["motifs_vs_regions.scores"] = compare(
        Path(str(sp) + ".motifs_vs_regions.scores.feather"),
        Path(str(bp) + ".motifs_vs_regions.scores.feather"),
        "regions", "columns")

    results["regions_vs_motifs.scores"] = compare(
        Path(str(sp) + ".regions_vs_motifs.scores.feather"),
        Path(str(bp) + ".regions_vs_motifs.scores.feather"),
        "motifs", "rows")

    results["regions_vs_motifs.rankings"] = compare(
        Path(str(sp) + ".regions_vs_motifs.rankings.feather"),
        Path(str(bp) + ".regions_vs_motifs.rankings.feather"),
        "motifs", "rows")

    # ---- POSITIVE CONTROL -----------------------------------------------------
    # Point the same machinery at two objects that genuinely differ -- the scores and
    # the rankings of the SAME run -- and require it to report a difference. If this
    # reports PASS__IDENTICAL the comparator is broken and every equality above is
    # meaningless.
    control = compare(
        Path(str(bp) + ".regions_vs_motifs.scores.feather"),
        Path(str(bp) + ".regions_vs_motifs.rankings.feather"),
        "motifs", "rows")
    control_fires = control.get("status") == "DIFFERS"

    equalities = {k: v.get("status") == "PASS__IDENTICAL" for k, v in results.items()}
    if not control_fires:
        status = "VOID__POSITIVE_CONTROL_DID_NOT_FIRE__RESULTS_NOT_INTERPRETABLE"
    elif all(equalities.values()):
        status = "PASS__OUTPUTS_ARE_INVARIANT_TO_SHARD_SIZE"
    else:
        status = "FAIL__OUTPUTS_DEPEND_ON_SHARD_SIZE"

    rec = {
        "schema": "V74_LANEE_SHARD_SIZE_INVARIANCE_V1",
        "status": status,
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": ("Do cisTarget scores and rankings depend on how many motifs are "
                     "scored in one invocation?"),
        "why_it_matters": ("The production database is assembled from shards. A "
                           "shard-size dependence would make the merged database a "
                           "function of an operational choice, and shards of different "
                           "sizes -- including the ragged 9-motif tail -- would be "
                           "mutually inconsistent."),
        "design": ("The 128-motif bench list is the first 128 entries of the frozen "
                   "universe and the 512-motif pilot slice is the first 512, over the "
                   "identical region FASTA, cbust, parameters and seed 20261001. The "
                   "first 128 motifs are therefore directly comparable, aligned by NAME "
                   "on both axes rather than by position."),
        "small_prefix": str(sp),
        "big_prefix": str(bp),
        "comparisons": results,
        "equalities": equalities,
        "POSITIVE_CONTROL": {
            "what": ("The same comparator applied to the 512-motif run's own scores vs "
                     "its own rankings, which must differ."),
            "fired": control_fires,
            "result": control,
            "why_required": ("An equality result from a comparator that could never "
                             "report a difference would be worthless."),
        },
    }

    out = Path(a.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    persisted = json.loads(out.read_text(encoding="utf-8"))
    print(json.dumps({"status": persisted["status"],
                      "equalities": persisted["equalities"],
                      "positive_control_fired": persisted["POSITIVE_CONTROL"]["fired"],
                      "comparisons": persisted["comparisons"]}, indent=2))
    return 0 if persisted["status"].startswith("PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
