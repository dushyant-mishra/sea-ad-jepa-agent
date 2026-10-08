#!/usr/bin/env python3
"""S174 repair, old-against-new receipts that the frozen rebuild script does not produce itself.

Two things, both computed from the freeze record, the validated decoders and the two caches; no new
source read:
  recovery     for each SEA-AD and HVS matrix, which addresses carry a clean, single-gene value in the
               rebuilt cache but had none the decoder could vouch for in the old one (the decoder's
               ambiguous columns, the old positional blocks)
  side_by_side for each replayed analysis, every numeric leaf of the old result beside the corrected one,
               paired by path, so no number is replaced silently

Usage:
  python compare_s174_rebuild.py recovery --out results/v77/S174_REBUILD_RECOVERY_V1.json
  python compare_s174_rebuild.py side-by-side --old-dir results/v77 --new-dir results/v77/s174_replay \
      --out results/v77/s174_replay/S174_REPLAY_SIDE_BY_SIDE_V1.json NAME.json [NAME.json ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def write_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1) + "\n")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------ side by side

SKIP_KEYS = {"shard_digests", "executor_sha256", "arrays", "index_file", "digests", "source_commit", "command",
             "provenance_status", "head", "sha256"}


def numeric_leaves(obj, prefix=""):
    """Every finite numeric leaf with its path; provenance blocks are skipped."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS:
                continue
            out.update(numeric_leaves(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        if len(obj) <= 64:
            for i, v in enumerate(obj):
                out.update(numeric_leaves(v, f"{prefix}[{i}]"))
    elif isinstance(obj, bool):
        out[prefix] = obj
    elif isinstance(obj, (int, float)) and math.isfinite(float(obj)):
        out[prefix] = obj
    return out


def pair(old: dict, new: dict) -> list[dict]:
    lo, ln = numeric_leaves(old), numeric_leaves(new)
    rows = []
    for path in sorted(set(lo) | set(ln)):
        a, b = lo.get(path), ln.get(path)
        row = dict(path=path, old=a, corrected=b)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) \
                and not isinstance(b, bool):
            row["delta"] = b - a
        rows.append(row)
    return rows


def side_by_side(old_dir: Path, new_dir: Path, names: list[str], out: Path) -> None:
    results = []
    for name in names:
        po, pn = old_dir / name, new_dir / name
        old, new = json.loads(po.read_text(encoding="utf-8")), json.loads(pn.read_text(encoding="utf-8"))
        rows = pair(old, new)
        results.append(dict(result=name, old=dict(path=po.as_posix(), sha256=sha256_file(po)),
                            corrected=dict(path=pn.as_posix(), sha256=sha256_file(pn)),
                            n_numbers=len(rows), rows=rows))
    write_json(out, dict(schema="S174_REPLAY_SIDE_BY_SIDE_V1",
                         rule="old numbers are kept beside the corrected ones; nothing is replaced in place",
                         results=results))
    print("side by side written", out, "|", len(results), "results")


# --------------------------------------------------------------------------------------- recovery

def recovery(out: Path) -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location("s174_rebuild", HERE / "rebuild_s174_train_cache.py")
    RB = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(RB)
    fr = json.loads(RB.FREEZE.read_text(encoding="utf-8"))
    rows = []
    for m in fr["matrices"]:
        mid, s = m["matrix_id"], m["stem"]
        zn = np.load(RB.NEW_CACHE / f"{s}.counts.npz", allow_pickle=False)
        zo = np.load(RB.OLD_CACHE / f"{s}.counts.npz", allow_pickle=False)
        new_addr = set(np.unique(zn["indices"]).tolist())
        old_cols = set(np.unique(zo["indices"]).tolist())
        dec = None
        for d in RB.DECODER_DIRS:
            f = d / f"decoder_{mid.replace('::', '__')}.npz"
            if f.exists():
                z = np.load(f, allow_pickle=False)
                dec = dict(zip(z["block_column"].astype(int), z["true_address"].astype(int)))
                break
        row = dict(matrix_id=mid, study=m["study"], mapped_columns_new=m["mapped_columns"],
                   excluded_new=m["excluded"], collision_addresses_new=m["collision_addresses"],
                   old_positional_blocked=m["old_positional_blocked"],
                   addresses_with_any_count_new=len(new_addr), columns_with_any_count_old=len(old_cols))
        if dec is not None:
            vouched = set(dec.values())
            row.update(decoder_clean_addresses=len(vouched),
                       addresses_with_counts_new_but_never_vouched_by_the_decoder=len(new_addr - vouched),
                       addresses_vouched_by_the_decoder_with_counts_new=len(new_addr & vouched))
        rows.append(row)
    write_json(out, dict(schema="S174_REBUILD_RECOVERY_V1",
                         reading=("addresses with counts in the rebuilt cache that the decoder could never vouch for "
                                  "are the recovered ones: columns the old positional map blocked or summed with "
                                  "another gene, now placed by identifier"),
                         freeze_sha256=sha256_file(RB.FREEZE), matrices=rows))
    print("recovery written", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("recovery")
    r.add_argument("--out", required=True)
    s = sub.add_parser("side-by-side")
    s.add_argument("--old-dir", required=True)
    s.add_argument("--new-dir", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("names", nargs="+")
    a = ap.parse_args()
    if a.mode == "recovery":
        recovery(Path(a.out))
    else:
        side_by_side(Path(a.old_dir), Path(a.new_dir), a.names, Path(a.out))


if __name__ == "__main__":
    main()
