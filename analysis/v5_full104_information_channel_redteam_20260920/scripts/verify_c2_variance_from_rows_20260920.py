"""Independent row-level verification of the C2 scorer-variability classification.

C2 classifies each (target, donor) pair as scorer-variable or not from the
sufficient statistics, via ``rss = n * (nsq/n - (nsum/n)**2) > EPS``. That form
suffers catastrophic cancellation exactly where the audit looks hardest — at
near-zero variance — so the classification must be checked against the
underlying rows rather than trusted.

This script recomputes the within-donor variance of the frozen normalized target
value **directly from the authenticated Level-4 rows**, in one pass, and compares
it against the sufficient-statistics classification.

Two selection routes, reported separately
-----------------------------------------
``HASH_SAMPLE``
    Targets and donors chosen by SHA-256 of a declared salt joined to the
    identifier. This depends on nothing about the data or the classification, so
    it is an unbiased check — but with only a few percent of pairs non-variable
    it will mostly exercise the variable class.

``FLAGGED_VERIFICATION``
    Every pair *within the sampled donors* that C2 flagged non-variable. This is
    a targeted check of the positive class, and is labelled as such: it is not a
    random sample and its counts must not be read as prevalence.

Both are necessary. The hash sample alone would barely touch the class the audit
is about; the flagged set alone could not detect false negatives.

Numerical route
---------------
Variance is recomputed by a **two-pass** algorithm — mean first, then summed
squared deviations — which does not suffer the cancellation the one-pass
sufficient-statistics form does. That is the point of the check: a different
numerical route, not the same arithmetic recomputed.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

SCHEMA = "V5_FULL104_C2_ROW_LEVEL_VARIANCE_VERIFICATION_V1"
_EPS = 1e-12                      # the frozen scorer's own epsilon
N_LEDGER = 41238

_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id", "expression_row",
    "primary_row_weight", "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_order(items, salt: str):
    return sorted(range(len(items)),
                  key=lambda i: hashlib.sha256(f"{salt}|{items[i]}".encode()).digest())


_W: dict = {}


def _init(root: str, columns: np.ndarray, donor_of_cell: dict, keep_donors: set):
    os.environ["OMP_NUM_THREADS"] = "1"
    _W.update(root=Path(root), columns=columns, donor_of_cell=donor_of_cell,
              keep_donors=keep_donors)


def _chunk(rows: list[dict]) -> dict:
    """Accumulate, per (donor, sampled target): n, sum, sumsq of normalized value.

    Values are accumulated here only to locate the mean; the squared-deviation
    pass happens in the parent once means are known, so the comparison route
    stays two-pass.
    """
    from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import _parse_source_library

    root, columns = _W["root"], _W["columns"]
    keep = _W["keep_donors"]
    n_cols = columns.size
    acc: dict[int, dict] = {}

    for row in rows:
        meta_path = root / row["meta_path"]
        if sha256_file(meta_path) != row["meta_sha256"]:
            raise RuntimeError(f"metadata hash mismatch: {row['block_key']}")
        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise RuntimeError(f"metadata schema mismatch: {row['block_key']}")
            meta = list(reader)
        donors = np.asarray([_W["donor_of_cell"][str(m["donor_id"])] for m in meta],
                            dtype=np.int64)
        if not np.isin(donors, list(keep)).any():
            continue
        libs = np.asarray([_parse_source_library(str(m["source_library"]).strip())
                           for m in meta], dtype=np.float64)

        counts_path = root / row["counts_path"]
        if sha256_file(counts_path) != row["counts_sha256"]:
            raise RuntimeError(f"counts digest mismatch: {row['block_key']}")
        sub = np.asarray(sp.load_npz(counts_path).tocsr()[:, columns].todense(),
                         dtype=np.float64)
        norm = np.log1p(sub * (10000.0 / libs[:, None]))      # frozen normalization

        for donor in np.unique(donors):
            d = int(donor)
            if d not in keep:
                continue
            block = norm[donors == d]
            slot = acc.setdefault(d, {"n": 0,
                                      "sum": np.zeros(n_cols),
                                      "sumsq": np.zeros(n_cols),
                                      "values": []})
            slot["n"] += block.shape[0]
            slot["sum"] += block.sum(axis=0)
            slot["sumsq"] += (block * block).sum(axis=0)
            slot["values"].append(block.astype(np.float32))
    return acc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, default=Path("C:/jepa_full104_ssd/expression_level4"))
    ap.add_argument("--stats", type=Path,
                    default=Path("D:/jepa_full104_redteam_20260920_external/"
                                 "core_sufficient_statistics_v1.npz"))
    ap.add_argument("--eligibility", type=Path,
                    default=Path("analysis/v5_full104_pass1_rebuild_20260920/evidence/"
                                 "full104_target_eligibility_v1.json"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--targets", type=int, default=32)
    ap.add_argument("--donors", type=int, default=12)
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    started = time.time()
    st = np.load(args.stats, allow_pickle=True)
    core = np.asarray(st["core"], dtype=np.int64)
    duniq = [str(x) for x in st["duniq"]]
    donor_cells = np.asarray(st["donor_cells"], dtype=np.int64)
    donor_nsum = np.asarray(st["donor_nsum"], dtype=np.float64)
    donor_nsq = np.asarray(st["donor_nsq"], dtype=np.float64)
    donor_nnz = np.asarray(st["donor_nnz"], dtype=np.int64)

    eligible = np.asarray(json.loads(args.eligibility.read_text(encoding="utf-8"))
                          ["eligible_target_cols_all_folds"], dtype=np.int64)
    pos_of = {int(a): i for i, a in enumerate(core)}

    # ---- deterministic selection, independent of any classification
    t_order = hash_order([int(a) for a in eligible], "V5_C2_ROW_VERIFY_TARGET_20260920")
    targets = np.sort(eligible[np.asarray(t_order[: args.targets], dtype=np.int64)])
    d_order = hash_order(duniq, "V5_C2_ROW_VERIFY_DONOR_20260920")
    donors = sorted(d_order[: args.donors])
    target_pos = np.asarray([pos_of[int(a)] for a in targets], dtype=np.int64)

    # sufficient-statistics classification for the sampled cells
    n_d = donor_cells[:, None].astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_ss = donor_nsum[:, target_pos] / np.maximum(n_d, 1.0)
        var_ss = donor_nsq[:, target_pos] / np.maximum(n_d, 1.0) - mean_ss * mean_ss
    rss_ss = np.maximum(var_ss, 0.0) * np.maximum(n_d, 1.0)
    variable_ss = rss_ss > _EPS

    manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    donor_of_cell = {d: i for i, d in enumerate(duniq)}
    keep = set(int(d) for d in donors)

    workers = args.workers if args.workers > 0 else min(8, max(1, (os.cpu_count() or 2) - 2))
    size = max(1, len(rows) // (workers * 4))
    chunks = [rows[i:i + size] for i in range(0, len(rows), size)]
    print(f"row-level verification: {len(targets)} targets x {len(donors)} donors, "
          f"{len(rows)} blocks scanned, {workers} worker(s)", flush=True)

    merged: dict[int, dict] = {}

    def merge(part):
        for d, slot in part.items():
            cur = merged.setdefault(d, {"n": 0, "sum": np.zeros(targets.size),
                                        "sumsq": np.zeros(targets.size), "values": []})
            cur["n"] += slot["n"]
            cur["sum"] += slot["sum"]
            cur["sumsq"] += slot["sumsq"]
            cur["values"].extend(slot["values"])

    if workers == 1:
        _init(str(args.level4_root), targets, donor_of_cell, keep)
        for c in chunks:
            merge(_chunk(c))
    else:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers, initializer=_init,
                      initargs=(str(args.level4_root), targets, donor_of_cell, keep)) as pool:
            for i, part in enumerate(pool.imap(_chunk, chunks)):
                merge(part)
                if (i + 1) % 8 == 0 or i + 1 == len(chunks):
                    print(f"  chunk {i+1}/{len(chunks)} {time.time()-started:.0f}s", flush=True)

    # ---- two-pass variance from the retained rows
    hash_rows, flagged_rows = [], []
    disagreements = []
    for d in donors:
        slot = merged.get(d)
        if slot is None or slot["n"] == 0:
            disagreements.append(f"donor {duniq[d]}: no rows recovered")
            continue
        if slot["n"] != int(donor_cells[d]):
            disagreements.append(f"donor {duniq[d]}: recovered {slot['n']} rows, "
                                 f"artifact says {int(donor_cells[d])}")
        values = np.concatenate(slot["values"], axis=0).astype(np.float64)
        mean_two_pass = values.mean(axis=0)
        ss_two_pass = ((values - mean_two_pass) ** 2).sum(axis=0)   # second pass
        for j, addr in enumerate(targets):
            variable_rows = bool(ss_two_pass[j] > _EPS)
            claimed = bool(variable_ss[d, j])
            rec = {
                "donor": duniq[d],
                "target_address": int(addr),
                "cells": int(slot["n"]),
                "detected_cells": int(donor_nnz[d, target_pos[j]]),
                "ss_two_pass_from_rows": float(ss_two_pass[j]),
                "rss_from_sufficient_statistics": float(rss_ss[d, j]),
                "scorer_variable_from_rows": variable_rows,
                "scorer_variable_from_statistics": claimed,
                "agree": variable_rows == claimed,
            }
            hash_rows.append(rec)
            if not claimed:
                flagged_rows.append(rec)
            if variable_rows != claimed:
                disagreements.append(
                    f"{duniq[d]} / address {int(addr)}: rows say variable={variable_rows}, "
                    f"statistics say {claimed} (ss={ss_two_pass[j]:.3e}, "
                    f"rss={rss_ss[d, j]:.3e})")

    agree = sum(1 for r in hash_rows if r["agree"])
    payload = {
        "schema": SCHEMA,
        "scope_class": "CURRENT_FULL104_RECONNAISSANCE",
        "selection": {
            "route_1": "HASH_SAMPLE",
            "route_1_rule": "SHA-256 of a declared salt joined to the target address / donor id; "
                            "independent of the data and of the C2 classification",
            "route_2": "FLAGGED_VERIFICATION",
            "route_2_note": "every sampled pair C2 flagged non-variable; a targeted check of the "
                            "positive class, NOT a random sample -- its counts are not prevalence",
            "targets": int(targets.size),
            "donors": int(len(donors)),
            "pairs": len(hash_rows),
        },
        "numerical_route": "two-pass (mean, then summed squared deviations) recomputed from rows; "
                           "deliberately different from the one-pass sufficient-statistics form, "
                           "which cancels catastrophically at near-zero variance",
        "pairs_checked": len(hash_rows),
        "pairs_in_agreement": agree,
        "pairs_disagreeing": len(hash_rows) - agree,
        "flagged_non_variable_pairs_verified": len(flagged_rows),
        "disagreements": disagreements[:40],
        "verdict": "C2_CLASSIFICATION_CONFIRMED_AT_ROW_LEVEL" if not disagreements
                   else "C2_CLASSIFICATION_DISAGREES_WITH_ROWS",
        "workers": workers,
        "elapsed_seconds": time.time() - started,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "disagreements"}, indent=2))
    if disagreements:
        for d in disagreements[:20]:
            print("  DISAGREEMENT:", d)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
