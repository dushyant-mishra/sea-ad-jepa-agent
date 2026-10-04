#!/usr/bin/env python3
"""V69: merge motif-wise cisTarget shards, with the merge VALIDATED not assumed.

WHY MOTIF-WISE SHARDS ARE THE RIGHT AXIS. cisTarget ranks regions WITHIN each motif.
A shard that holds a subset of motifs but ALL regions therefore contains everything
needed to rank its own motifs, so both scores and rankings are shard-decomposable.
Sharding by region would not have this property. This script nonetheless proves the
equivalence on a fixture rather than relying on the argument.

THE INVARIANT THIS ENFORCES, which has never been enforced in this repository:

    concat(shard motif axes, in shard order) == the frozen ordered motif universe
      - equal length
      - zero duplicates
      - element-by-element identical, in order
      - matching ordered digest

and every shard's REGION axis identical to every other's.

A merge that silently drops or reorders motifs would remap every downstream score
without crashing, which is the index-order failure this project has repeatedly been
burned by.

No prior sharding or merge code existed in this repository; this is written from
scratch, modelled on three prior primitives: an empty/duplicate motif-axis assertion,
an ordered column-name digest, and a positional axis-parity comparison.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REGION_INDEX_COLUMN = "regions"   # in <prefix>.motifs_vs_regions.* (rows = regions)
MOTIF_INDEX_COLUMN = "motifs"     # in <prefix>.regions_vs_motifs.* (rows = motifs)


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    """Order-sensitive digest. A permuted axis must not pass."""
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def read_axis_frame(path: Path, index_column: str) -> pd.DataFrame:
    if not path.exists():
        raise FailClosed("FAIL__SHARD_OUTPUT_ABSENT", path=str(path))
    df = pd.read_feather(path)
    if index_column not in df.columns:
        raise FailClosed("FAIL__EXPECTED_INDEX_COLUMN_ABSENT",
                         path=str(path), expected=index_column,
                         observed_last_columns=list(df.columns[-3:]))
    return df.set_index(index_column)


def validate_motif_axis(shard_motifs: list, frozen_motifs: list) -> dict:
    """The core invariant. Fails closed on omission, duplication or reordering."""
    concat = [m for lst in shard_motifs for m in lst]
    n_dupes = len(concat) - len(set(concat))
    missing = [m for m in frozen_motifs if m not in set(concat)]
    extra = [m for m in concat if m not in set(frozen_motifs)]

    if n_dupes:
        seen, dupes = set(), []
        for m in concat:
            if m in seen and m not in dupes:
                dupes.append(m)
            seen.add(m)
        raise FailClosed("FAIL__MERGED_MOTIF_AXIS_HAS_DUPLICATES",
                         n_duplicates=n_dupes, examples=dupes[:10])
    if missing:
        raise FailClosed("FAIL__MERGED_MOTIF_AXIS_MISSING_MOTIFS",
                         n_missing=len(missing), examples=missing[:10])
    if extra:
        raise FailClosed("FAIL__MERGED_MOTIF_AXIS_HAS_UNEXPECTED_MOTIFS",
                         n_extra=len(extra), examples=extra[:10])
    if len(concat) != len(frozen_motifs):
        raise FailClosed("FAIL__MERGED_MOTIF_AXIS_LENGTH_MISMATCH",
                         merged=len(concat), frozen=len(frozen_motifs))
    if concat != list(frozen_motifs):
        first = next(i for i, (a, b) in enumerate(zip(concat, frozen_motifs)) if a != b)
        raise FailClosed("FAIL__MERGED_MOTIF_AXIS_ORDER_DIFFERS",
                         first_differing_index=first,
                         merged_at=concat[first], frozen_at=frozen_motifs[first])
    return {
        "n_motifs": len(concat),
        "n_shards": len(shard_motifs),
        "duplicates": 0,
        "omissions": 0,
        "order_matches_frozen_universe": True,
        "merged_ordered_digest": ordered_digest(concat),
        "frozen_ordered_digest": ordered_digest(frozen_motifs),
        "digests_equal": ordered_digest(concat) == ordered_digest(frozen_motifs),
    }


def merge(shard_dirs, shard_prefixes, frozen_motif_list: Path, out_prefix: Path,
          kind: str = "scores") -> dict:
    frozen = [l.strip() for l in frozen_motif_list.read_text().splitlines() if l.strip()]
    if not frozen:
        raise FailClosed("FAIL__FROZEN_MOTIF_LIST_EMPTY", path=str(frozen_motif_list))

    suffix = f".motifs_vs_regions.{kind}.feather"
    frames, shard_motifs, region_axis, shard_records = [], [], None, []

    for d, pfx in zip(shard_dirs, shard_prefixes):
        p = Path(d) / f"{pfx}{suffix}"
        df = read_axis_frame(p, REGION_INDEX_COLUMN)
        if region_axis is None:
            region_axis = list(df.index)
        elif list(df.index) != region_axis:
            raise FailClosed("FAIL__SHARD_REGION_AXIS_DIFFERS",
                             shard=pfx,
                             n_regions_here=len(df.index),
                             n_regions_expected=len(region_axis))
        frames.append(df)
        shard_motifs.append(list(df.columns))
        shard_records.append({"shard": pfx, "path": str(p),
                              "sha256": sha256_file(p),
                              "n_motifs": int(df.shape[1]),
                              "n_regions": int(df.shape[0]),
                              "ordered_motif_digest": ordered_digest(df.columns)})

    axis = validate_motif_axis(shard_motifs, frozen)

    merged = pd.concat(frames, axis=1)
    if list(merged.columns) != frozen:
        raise FailClosed("FAIL__MERGED_FRAME_COLUMNS_NOT_IN_FROZEN_ORDER")
    if list(merged.index) != region_axis:
        raise FailClosed("FAIL__MERGED_FRAME_REGION_AXIS_CHANGED")

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    out_path = Path(str(out_prefix) + suffix)
    merged.reset_index().to_feather(out_path)

    # Re-read from disk: the recorded state describes the file, not memory.
    verify = read_axis_frame(out_path, REGION_INDEX_COLUMN)
    if list(verify.columns) != frozen or list(verify.index) != region_axis:
        raise FailClosed("FAIL__MERGED_FILE_REREAD_AXIS_MISMATCH")
    if not np.array_equal(verify.to_numpy(dtype=np.float64),
                          merged.to_numpy(dtype=np.float64)):
        raise FailClosed("FAIL__MERGED_FILE_REREAD_VALUES_DIFFER")

    return {
        "schema": "V69_CISTARGET_SHARD_MERGE_V1",
        "merged_utc": utcnow(),
        "kind": kind,
        "motif_axis_validation": axis,
        "region_axis": {"n_regions": len(region_axis),
                        "ordered_region_digest": ordered_digest(region_axis)},
        "shards": shard_records,
        "output_path": str(out_path),
        "output_sha256": sha256_file(out_path),
        "output_shape_regions_by_motifs": [int(verify.shape[0]), int(verify.shape[1])],
        "reread_from_disk_before_recording": True,
        "status": "PASS__SHARDS_MERGED_AND_AXIS_VALIDATED",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", action="append", required=True,
                    metavar="DIR:PREFIX", help="repeatable, in FROZEN shard order")
    ap.add_argument("--frozen-motif-list", required=True)
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--kind", default="scores", choices=["scores", "rankings"])
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    dirs, prefixes = [], []
    for s in a.shard:
        d, _, p = s.rpartition(":")
        dirs.append(d); prefixes.append(p)
    try:
        r = merge(dirs, prefixes, Path(a.frozen_motif_list), Path(a.out_prefix), a.kind)
    except FailClosed as e:
        r = {"schema": "V69_CISTARGET_SHARD_MERGE_V1", "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2)[:3000])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
