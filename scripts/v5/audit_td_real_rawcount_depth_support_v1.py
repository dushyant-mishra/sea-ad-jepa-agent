"""Outcome-blind raw-count depth-support census over the FULL104 Level-4 store.

Scope: OUTCOME_BLIND_CALIBRATION__SUPPORT_MAPPING.  Reads only reader_fit raw
integer count blocks that are hash-bound to the frozen block manifest.  No
candidate representation, outcome, pathology, validation/oracle or DEV/SEALED
object is read.  No random thinning is drawn: depth effects are exact
binomial-thinning expectations, so no RNG namespace is consumed.

Per (donor, operator) it reports the raw-count objects available, the exact
expected detection retained at p in {0.25, 0.50, 0.75}, the expected number
of cells whose stored counts all thin to zero, and the relation between the
stored-address count sum and the full-source library used for normalization.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import scipy.sparse as sp

MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CONTRACT_SHA256 = "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17"
STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_BLOCKS, EXPECTED_CELLS, EXPECTED_DONORS, ADDRESSES = 8915, 4_553_407, 104, 41_238
DEPTHS = (0.25, 0.50, 0.75)
LOG2_BINS = 25  # histogram of floor(log2(stored_sum + 1))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _library(text: str) -> tuple[int, bool]:
    """Parse a per-cell library size; accept only integer-valued text, flag float formatting."""
    if text.isdigit():
        return int(text), False
    head, dot, tail = text.partition(".")
    if dot and head.isdigit() and tail and set(tail) == {"0"}:
        return int(head), True
    raise RuntimeError(f"non-integer source_library value: {text!r}")


def _block(task):
    root, row, scalar_mask = task
    counts_path, meta_path = root / row["counts_path"], root / row["meta_path"]
    if sha256(counts_path) != row["counts_sha256"] or sha256(meta_path) != row["meta_sha256"]:
        raise RuntimeError(f"block hash mismatch: {row['block_key']}")
    m = sp.load_npz(counts_path).tocsr()
    if m.shape != (int(row["rows"]), ADDRESSES) or m.nnz != int(row["nnz"]):
        raise RuntimeError(f"block shape/nnz mismatch: {row['block_key']}")
    if m.data.dtype.kind not in "iu":
        raise RuntimeError("non-integer count dtype")
    with meta_path.open(encoding="utf-8") as f:
        meta = list(csv.DictReader(f))
    if len(meta) != m.shape[0]:
        raise RuntimeError("meta/count row mismatch")
    data = m.data.astype(np.int64)
    out = {"block_key": row["block_key"], "negative_entries": int((data < 0).sum()),
           "explicit_zero_entries": int((data == 0).sum()),
           "entries_outside_measured_scalar": int((~scalar_mask[m.indices]).sum()),
           "selection_rows": [int(r["selection_row"]) for r in meta], "groups": {}}
    S = np.asarray(m.sum(axis=1)).ravel().astype(np.int64)
    nnz = np.diff(m.indptr)
    parsed = [_library(r["source_library"]) for r in meta]
    L = np.array([v for v, _ in parsed], dtype=np.int64)
    out["library_float_formatted_rows"] = sum(1 for _, f in parsed if f)
    row_of_entry = np.repeat(np.arange(m.shape[0]), nnz)
    miss = {p: np.bincount(row_of_entry, weights=np.power(1.0 - p, data), minlength=m.shape[0]) for p in DEPTHS}
    donors = np.array([r["donor_id"] for r in meta])
    for d in np.unique(donors):
        idx = np.flatnonzero(donors == d)
        g = {"cells": int(idx.size), "stored_sum": int(S[idx].sum()), "library_sum": int(L[idx].sum()),
             "nnz": int(nnz[idx].sum()), "cells_stored_sum_zero": int((S[idx] == 0).sum()),
             "cells_library_lt_stored": int((L[idx] < S[idx]).sum()),
             "stored_over_library_min": float((S[idx] / np.maximum(L[idx], 1)).min()),
             "stored_over_library_max": float((S[idx] / np.maximum(L[idx], 1)).max()),
             "log2_stored_hist": np.bincount(np.minimum(np.floor(np.log2(S[idx] + 1)).astype(int), LOG2_BINS - 1),
                                             minlength=LOG2_BINS).tolist()}
        for p in DEPTHS:
            g[f"exp_detected_retained_p{p}"] = float(nnz[idx].sum() - miss[p][idx].sum())
            g[f"exp_cells_all_stored_zero_p{p}"] = float(np.power(1.0 - p, S[idx].astype(float)).sum())
        out["groups"][d] = g
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level4", required=True)
    ap.add_argument("--state-npz", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--smoke-blocks", type=int, default=0, help="process N blocks, print, write nothing")
    args = ap.parse_args()
    root, out = Path(args.level4), Path(args.out)
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256(manifest) != MANIFEST_SHA256 or sha256(root / "MATERIALIZATION_CONTRACT.json") != CONTRACT_SHA256:
        raise SystemExit("Level-4 manifest/contract identity mismatch")
    if sha256(Path(args.state_npz)) != STATE_SHA256:
        raise SystemExit("observation-state identity mismatch")
    contract = json.loads((root / "MATERIALIZATION_CONTRACT.json").read_text(encoding="utf-8"))
    if contract.get("no_validation_oracle_dev_sealed_pathology") is not True:
        raise SystemExit("Level-4 store is not certified free of validation/oracle/DEV/SEALED/pathology")
    z = np.load(args.state_npz, allow_pickle=False)
    states, mids = z["states"], [str(x) for x in z["matrix_id"]]
    with manifest.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != EXPECTED_BLOCKS:
        raise SystemExit("block count drift")
    tasks = []
    for r in rows:
        op = int(r["operator_index"])
        if mids[op] != r["matrix_id"]:
            raise SystemExit("operator/matrix identity mismatch")
        tasks.append((root, r, states[op] == 1))
    if args.smoke_blocks:
        res = [_block(t) for t in tasks[:args.smoke_blocks]]
        print(json.dumps([{k: v for k, v in x.items() if k != "selection_rows"} for x in res])[:3000])
        return
    agg = defaultdict(lambda: defaultdict(float))
    hist = defaultdict(lambda: np.zeros(LOG2_BINS, dtype=np.int64))
    ratio = defaultdict(lambda: [np.inf, -np.inf])
    meta_of = {}
    checks = defaultdict(int)
    seen = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for res, r in zip(pool.map(_block, tasks, chunksize=4), rows):
            for k in ("negative_entries", "explicit_zero_entries", "entries_outside_measured_scalar"):
                checks[k] += res[k]
            checks[f"library_float_formatted_rows__source={r['source']}"] += res["library_float_formatted_rows"]
            seen.extend(res["selection_rows"])
            for d, g in res["groups"].items():
                key = (d, int(r["operator_index"]))
                meta_of[key] = (r["source"], r["matrix_id"])
                for k, v in g.items():
                    if k == "log2_stored_hist":
                        hist[key] += np.asarray(v, dtype=np.int64)
                    elif k == "stored_over_library_min":
                        ratio[key][0] = min(ratio[key][0], v)
                    elif k == "stored_over_library_max":
                        ratio[key][1] = max(ratio[key][1], v)
                    else:
                        agg[key][k] += v
    seen_arr = np.asarray(seen, dtype=np.int64)
    identity = {
        "cells_total": int(seen_arr.size),
        "selection_rows_unique": int(np.unique(seen_arr).size),
        "donors": len({d for d, _ in agg}),
        "donor_operator_strata": len(agg),
    }
    if identity["cells_total"] != EXPECTED_CELLS or identity["selection_rows_unique"] != EXPECTED_CELLS \
            or identity["donors"] != EXPECTED_DONORS:
        raise SystemExit(f"identity drift: {identity}")
    (out / "support").mkdir(parents=True, exist_ok=True)
    cols = ["cells", "stored_sum", "library_sum", "nnz", "cells_stored_sum_zero", "cells_library_lt_stored"]
    for p in DEPTHS:
        cols += [f"exp_detected_retained_p{p}", f"exp_cells_all_stored_zero_p{p}"]
    with (out / "support/RAWCOUNT_DONOR_X_OPERATOR_DEPTH_SUPPORT.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["donor_id", "source", "operator_index", "matrix_id", *cols,
                    "stored_over_library_min", "stored_over_library_max",
                    *[f"log2_stored_bin{b}" for b in range(LOG2_BINS)]])
        for key in sorted(agg):
            g = agg[key]
            w.writerow([key[0], meta_of[key][0], key[1], meta_of[key][1],
                        *[int(g[c]) if not c.startswith("exp_") else round(g[c], 3) for c in cols],
                        round(ratio[key][0], 6), round(ratio[key][1], 6), *hist[key].tolist()])
    receipt = {
        "schema": "JEPA_TD_REAL_RAWCOUNT_DEPTH_SUPPORT_CENSUS_V1",
        "scope": "OUTCOME_BLIND_CALIBRATION__SUPPORT_MAPPING__READER_FIT_RAW_COUNTS_ONLY",
        "level4_block_manifest_sha256": MANIFEST_SHA256,
        "level4_materialization_contract_sha256": CONTRACT_SHA256,
        "observation_state_sha256": STATE_SHA256,
        "blocks_hash_verified": EXPECTED_BLOCKS,
        "identity": identity,
        "integrity_checks": dict(checks),
        "depths": list(DEPTHS),
        "depth_method": "exact binomial-thinning expectations; no RNG draw; no seed namespace consumed",
        "candidate_representation_computed": False,
        "candidate_outcomes_opened": False,
        "validation_oracle_dev_sealed_opened": False,
        "pathology_opened": False,
        "authority": "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
    }
    (out / "RAWCOUNT_DEPTH_SUPPORT_CENSUS_RECEIPT_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
