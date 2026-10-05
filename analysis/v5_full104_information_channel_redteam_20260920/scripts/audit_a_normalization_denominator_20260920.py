"""Audit A -- hidden normalization-denominator information.

The question
-----------
Both authenticated materializers compute ``source_library`` from the RAW source
expression, BEFORE mapping and filtering to the 41,238-address ledger.

Python/H5 materializer (SHA 575d02a4...), verbatim::

    libraries.append(int(np.rint(values).sum()))      # ALL raw source counts
    in_range = indices < len(source_to_address)
    targets  = np.full(len(indices), -1, dtype=np.int32)
    targets[in_range] = source_to_address[indices[in_range]]
    keep = targets >= 0                               # only mapped addresses
    value_parts.append(np.rint(values[keep]).astype(np.int32))

NPH52 R materializer (SHA ca595536...), verbatim::

    mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
    libraries <- as.numeric(Matrix::colSums(counts[,columns,drop=FALSE]))   # FULL
    local <- t(counts[mapping$source_feature_index+1L, columns[take], drop=FALSE])

(R stores genes x cells, so ``colSums`` is the per-cell total over all genes.)

Therefore ``source_library`` is NOT necessarily the sum of model-visible ledger
counts, and RNA that never enters the ledger -- unmapped features,
collision-blocked features, out-of-range source indices -- influences EVERY
visible normalized feature through ``log1p(raw * 10000 / source_library)``.

This script quantifies that channel. It reads only; it alters no artifact.

Per-cell quantities
-------------------
``L_total``   = ``source_library`` from the authenticated block metadata
``L_ledger``  = sum of raw counts across the stored 41,238 ledger addresses
``L_core``    = sum of raw counts across the strict 17,186 common core
``L_outside_ledger``      = ``L_total - L_ledger``
``fraction_outside_ledger``, ``fraction_inside_ledger``, ``fraction_core``

Fail-closed arithmetic invariants
---------------------------------
Any of these aborts the run:
  * ``L_total <= 0``
  * ``L_ledger > L_total``           (ledger mass exceeds source library)
  * ``L_outside_ledger < 0``         (negative outside-ledger mass)
  * any non-finite fraction
  * ``L_core > L_ledger``            (core is a subset of the ledger)

Independent corroboration
-------------------------
Two headline totals are accumulated by genuinely different routes, not by
calling the same helper twice:

  * ``L_ledger`` via ``csr.sum(axis=1)`` AND via ``np.add.reduceat`` over the
    raw ``data``/``indptr`` arrays;
  * the observed per-cell core nonzero count is compared against
    ``cell_nnz_core`` in the authenticated pass1 NPZ, which was produced by a
    different script in a different session.

Scope
-----
This is supporting-only shortcut reconnaissance. It makes no biological claim.

`outside-ledger denominator influence` and `direct hidden-target leakage` are
DIFFERENT channels and are labelled separately throughout. This script measures
only the first.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

SCHEMA = "V5_FULL104_NORMALIZATION_DENOMINATOR_AUDIT_V1"

#: Exact positive-integral grammar for the authenticated source_library field.
#: Mirrors the frozen production parser: no underscores, no hex, no NaN/Inf.
_LIBRARY_TOKEN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")

_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id",
    "expression_row", "primary_row_weight", "source_library",
)

QUANTILES = (0.0, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1.0)
QUANTILE_NAMES = ("min", "p01", "p05", "p25", "median", "p75", "p95", "p99", "max")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_library(raw: object) -> int:
    """Parse an exact positive integral source_library, or raise."""
    if raw is None:
        raise ValueError("source_library is absent")
    text = str(raw).strip()
    if not _LIBRARY_TOKEN.match(text):
        raise ValueError(f"source_library failed the exact grammar: {text!r}")
    from decimal import Decimal, InvalidOperation
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"source_library is not an exact decimal: {text!r}") from exc
    if value != value.to_integral_value():
        raise ValueError(f"source_library is not integral: {text!r}")
    out = int(value)
    if out <= 0:
        raise ValueError(f"source_library must be positive: {out}")
    return out


def describe(values: np.ndarray) -> dict:
    """Unconditional summary over every attempted unit. No filtering."""
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return {"n": 0}
    qs = np.quantile(values, QUANTILES)
    out = {"n": int(values.size), "mean": float(values.mean())}
    out.update({name: float(q) for name, q in zip(QUANTILE_NAMES, qs)})
    return out


def stream_blocks(level4_root: Path, core: np.ndarray, *, verify_hashes: bool,
                  limit_blocks: int | None = None):
    """Yield per-block arrays. Verifies block digests against the manifest."""
    manifest_path = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))
    if limit_blocks is not None:
        rows = rows[:limit_blocks]

    is_core = np.zeros(41238, dtype=bool)
    is_core[core] = True

    for index, row in enumerate(rows):
        counts_path = level4_root / row["counts_path"]
        meta_path = level4_root / row["meta_path"]
        if verify_hashes:
            if sha256_file(counts_path) != row["counts_sha256"]:
                raise SystemExit(f"counts digest mismatch: {row['block_key']}")
            if sha256_file(meta_path) != row["meta_sha256"]:
                raise SystemExit(f"meta digest mismatch: {row['block_key']}")

        with meta_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise SystemExit(f"block metadata schema mismatch: {row['block_key']}")
            meta = list(reader)
        selection = np.asarray([int(m["selection_row"]) for m in meta], dtype=np.int64)
        libraries = np.asarray([parse_library(m["source_library"]) for m in meta], dtype=np.int64)
        donor_ids = [str(m["donor_id"]) for m in meta]

        matrix = sp.load_npz(counts_path).tocsr()
        if matrix.shape[0] != len(meta) or matrix.shape[1] != 41238:
            raise SystemExit(f"block geometry mismatch: {row['block_key']}")
        if np.any(matrix.data < 0):
            raise SystemExit(f"negative raw counts: {row['block_key']}")

        # int64 BEFORE any reduction. int32 row sums silently overflow on this
        # substrate; that defect previously produced 0.009717 in place of
        # 0.832983 and must never recur.
        data64 = matrix.data.astype(np.int64)
        m64 = sp.csr_matrix((data64, matrix.indices, matrix.indptr), shape=matrix.shape)

        # Route 1: scipy sparse reduction.
        ledger_a = np.asarray(m64.sum(axis=1)).ravel().astype(np.int64)
        # Route 2: independent accumulation straight off indptr. Not the same
        # code path, so agreement is corroboration rather than a tautology.
        ledger_b = np.add.reduceat(
            np.concatenate([data64, np.zeros(1, np.int64)]), matrix.indptr[:-1]
        ).astype(np.int64)
        empty = np.diff(matrix.indptr) == 0
        ledger_b[empty] = 0
        if not np.array_equal(ledger_a, ledger_b):
            raise SystemExit(f"independent ledger-sum routes disagree: {row['block_key']}")

        core_mask = is_core[matrix.indices]
        row_of_entry = np.repeat(np.arange(matrix.shape[0], dtype=np.int64),
                                 np.diff(matrix.indptr))
        core_sum = np.bincount(row_of_entry[core_mask],
                               weights=data64[core_mask].astype(np.float64),
                               minlength=matrix.shape[0])
        if not np.all(core_sum == np.rint(core_sum)):
            raise SystemExit(f"core sum lost integrality: {row['block_key']}")
        core_sum = core_sum.astype(np.int64)
        core_nnz = np.bincount(row_of_entry[core_mask & (data64 > 0)],
                               minlength=matrix.shape[0]).astype(np.int64)

        yield {
            "block_key": row["block_key"],
            "source": row["source"],
            "operator_index": int(row["operator_index"]),
            "selection": selection,
            "donor_ids": donor_ids,
            "L_total": libraries,
            "L_ledger": ledger_a,
            "L_core": core_sum,
            "core_nnz": core_nnz,
            "index": index,
            "total_blocks": len(rows),
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, default=Path("C:/jepa_full104_ssd/expression_level4"))
    ap.add_argument("--pass1", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "full104_pass1_v2_selection_row_keyed.npz"))
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--cell-level-out", type=Path, default=None,
                    help="optional external NPZ of per-cell quantities (NOT for GitHub)")
    ap.add_argument("--limit-blocks", type=int, default=None)
    ap.add_argument("--no-verify-hashes", action="store_true")
    ap.add_argument("--expect-core-size", type=int, default=17186,
                    help="fail closed unless the pass1 core has exactly this many addresses; "
                         "the real FULL104 run must always use the default")
    args = ap.parse_args()

    started = time.time()
    pass1 = np.load(args.pass1, allow_pickle=True)
    core = np.asarray(pass1["core"], dtype=np.int64)
    if core.size != args.expect_core_size:
        raise SystemExit(
            f"expected a {args.expect_core_size:,}-address strict core, got {core.size}")
    cell_donor = np.asarray(pass1["cell_donor"], dtype=np.int64)
    cell_nnz_core_pass1 = np.asarray(pass1["cell_nnz_core"], dtype=np.int64)
    duniq = [str(x) for x in pass1["duniq"]]
    donor_src = np.asarray(pass1["donor_src"], dtype=np.int64)
    n_cells = cell_donor.size

    L_total = np.zeros(n_cells, np.int64)
    L_ledger = np.zeros(n_cells, np.int64)
    L_core = np.zeros(n_cells, np.int64)
    core_nnz_obs = np.zeros(n_cells, np.int64)
    src_of_cell = np.full(n_cells, -1, np.int64)
    op_of_cell = np.full(n_cells, -1, np.int64)
    seen = np.zeros(n_cells, bool)
    source_names: dict[str, int] = {}

    for block in stream_blocks(args.level4_root, core,
                               verify_hashes=not args.no_verify_hashes,
                               limit_blocks=args.limit_blocks):
        sel = block["selection"]
        if sel.min() < 0 or sel.max() >= n_cells:
            raise SystemExit(f"selection_row out of range in {block['block_key']}")
        if np.any(seen[sel]):
            raise SystemExit(f"duplicate selection_row in {block['block_key']}")
        seen[sel] = True
        L_total[sel] = block["L_total"]
        L_ledger[sel] = block["L_ledger"]
        L_core[sel] = block["L_core"]
        core_nnz_obs[sel] = block["core_nnz"]
        code = source_names.setdefault(block["source"], len(source_names))
        src_of_cell[sel] = code
        op_of_cell[sel] = block["operator_index"]
        if block["index"] % 500 == 0:
            done = block["index"] + 1
            print(f"  block {done}/{block['total_blocks']} "
                  f"({100.0*done/block['total_blocks']:.1f}%) "
                  f"{time.time()-started:.0f}s", flush=True)

    partial = args.limit_blocks is not None
    if not partial and not seen.all():
        raise SystemExit(f"{int((~seen).sum())} cells were never written; identity space not closed")

    mask = seen
    n_seen = int(mask.sum())

    # ---------------------------------------------------------------- invariants
    failures = []
    if np.any(L_total[mask] <= 0):
        failures.append(f"{int((L_total[mask] <= 0).sum())} cells with source_library <= 0")
    over = L_ledger[mask] > L_total[mask]
    if np.any(over):
        failures.append(f"{int(over.sum())} cells where ledger mass exceeds source library")
    outside = L_total - L_ledger
    if np.any(outside[mask] < 0):
        failures.append(f"{int((outside[mask] < 0).sum())} cells with negative outside-ledger mass")
    if np.any(L_core[mask] > L_ledger[mask]):
        failures.append(f"{int((L_core[mask] > L_ledger[mask]).sum())} cells where core mass exceeds ledger mass")

    with np.errstate(divide="ignore", invalid="ignore"):
        frac_outside = np.where(L_total > 0, outside / np.maximum(L_total, 1), np.nan)
        frac_inside = np.where(L_total > 0, L_ledger / np.maximum(L_total, 1), np.nan)
        frac_core = np.where(L_total > 0, L_core / np.maximum(L_total, 1), np.nan)
    for name, arr in (("fraction_outside_ledger", frac_outside),
                      ("fraction_inside_ledger", frac_inside),
                      ("fraction_core", frac_core)):
        if not np.all(np.isfinite(arr[mask])):
            failures.append(f"{name} is non-finite for {int((~np.isfinite(arr[mask])).sum())} cells")

    # Independent corroboration against a different producer.
    nnz_agree = bool(np.array_equal(core_nnz_obs[mask], cell_nnz_core_pass1[mask]))
    if not nnz_agree:
        bad = int((core_nnz_obs[mask] != cell_nnz_core_pass1[mask]).sum())
        failures.append(f"core nonzero count disagrees with authenticated pass1 for {bad} cells")

    if failures:
        for f in failures:
            print("  INVARIANT FAILURE:", f, file=sys.stderr)
        raise SystemExit("Audit A aborted on arithmetic/corroboration invariants")

    # ------------------------------------------------------------------ strata
    code_to_source = {v: k for k, v in source_names.items()}
    donor_of_cell = cell_donor
    src_by_donor_code = {i: int(donor_src[i]) for i in range(len(duniq))}

    def decile(values: np.ndarray) -> np.ndarray:
        edges = np.quantile(values[mask], np.linspace(0, 1, 11))
        edges = np.unique(edges)
        return np.clip(np.digitize(values, edges[1:-1], right=True), 0, len(edges) - 2)

    depth_decile = decile(L_total)
    corenz_decile = decile(cell_nnz_core_pass1)

    metrics = {
        "L_total": L_total, "L_ledger": L_ledger, "L_core": L_core,
        "L_outside_ledger": outside,
        "fraction_outside_ledger": frac_outside,
        "fraction_inside_ledger": frac_inside,
        "fraction_core": frac_core,
    }

    def grouped(keys: np.ndarray, label_of) -> list[dict]:
        rows = []
        for key in sorted(set(keys[mask].tolist())):
            sel = mask & (keys == key)
            row = {"group": label_of(key), "n": int(sel.sum())}
            for name, arr in metrics.items():
                d = describe(arr[sel])
                for stat, value in d.items():
                    if stat == "n":
                        continue
                    row[f"{name}__{stat}"] = value
            rows.append(row)
        return rows

    by_source = grouped(src_of_cell, lambda k: code_to_source[k])
    by_operator = grouped(op_of_cell, lambda k: f"op{int(k):02d}")
    by_donor = grouped(donor_of_cell, lambda k: duniq[int(k)])
    by_depth = grouped(depth_decile, lambda k: f"depth_decile_{int(k)}")
    by_corenz = grouped(corenz_decile, lambda k: f"core_nnz_decile_{int(k)}")

    src_op = src_of_cell.astype(np.int64) * 1000 + op_of_cell.astype(np.int64)
    by_source_operator = grouped(
        src_op, lambda k: f"{code_to_source[int(k)//1000]}|op{int(k)%1000:02d}")

    # ------------------------------------------------- denominator predictiveness
    # Donor-honest: predict a donor-level label from the DONOR MEAN of the
    # denominator fractions, so no cell of a donor informs that donor's own
    # prediction. Nearest-centroid on held-out donors; unconditional accuracy.
    donors_observed = np.zeros(len(duniq), bool)
    donor_feat = np.zeros((len(duniq), 3), np.float64)
    for d in range(len(duniq)):
        sel = mask & (donor_of_cell == d)
        if not sel.any():
            continue
        donors_observed[d] = True
        donor_feat[d] = [frac_outside[sel].mean(), frac_inside[sel].mean(), frac_core[sel].mean()]

    # Donor-level predictiveness is only defined when every donor is present.
    # In a partial run it is reported NOT_MEASURABLE rather than computed over a
    # silently truncated donor set -- missing evidence is never a result.
    all_donors_present = bool(donors_observed.all())

    def donor_honest_nearest_centroid(labels: np.ndarray) -> dict:
        n = len(duniq)
        correct = 0
        attempted = 0
        for held in np.flatnonzero(donors_observed):
            train = (np.arange(n) != held) & donors_observed
            classes = sorted(set(labels[train].tolist()))
            if len(classes) < 2:
                attempted += 1        # counted, never silently dropped
                continue
            cents = np.stack([donor_feat[train][labels[train] == c].mean(axis=0) for c in classes])
            d2 = ((cents - donor_feat[held]) ** 2).sum(axis=1)
            pred = classes[int(np.argmin(d2))]
            attempted += 1
            correct += int(pred == labels[held])
        counts = np.bincount(labels, minlength=int(labels.max()) + 1)
        majority = float(counts.max() / counts.sum())
        return {
            "n_donors_attempted": attempted,
            "accuracy_unconditional": correct / attempted if attempted else float("nan"),
            "majority_class_rate": majority,
            "n_classes": int(len(set(labels.tolist()))),
        }

    source_label = np.asarray([src_by_donor_code[d] for d in range(len(duniq))], np.int64)
    op_first = np.zeros(len(duniq), np.int64)
    for d in range(len(duniq)):
        sel = mask & (donor_of_cell == d)
        if not sel.any():
            continue
        vals, cnts = np.unique(op_of_cell[sel], return_counts=True)
        op_first[d] = int(vals[int(np.argmax(cnts))])
    _, op_label = np.unique(op_first, return_inverse=True)

    if not all_donors_present:
        predictiveness = {
            "state": "NOT_MEASURABLE",
            "reason": f"only {int(donors_observed.sum())} of {len(duniq)} donors present; "
                      "donor-level predictiveness is undefined on a truncated donor set",
            "partial_run": True,
        }
        summary_predictiveness_only_partial = True
    else:
        summary_predictiveness_only_partial = False
    predictiveness_full = {
        "method": "donor-honest leave-one-donor-out nearest centroid on the DONOR-MEAN "
                  "denominator fractions (outside, inside, core). Unconditional over all "
                  "104 donors; donors with a degenerate training label set are counted as "
                  "attempted and not silently dropped.",
        "features": ["mean fraction_outside_ledger", "mean fraction_inside_ledger",
                     "mean fraction_core"],
        "source": donor_honest_nearest_centroid(source_label),
        "operator": donor_honest_nearest_centroid(op_label),
        "donor_identity_note": "donor identity is not predicted from donor-mean features: "
                               "leave-one-donor-out makes the held-out donor's own class absent "
                               "from training, so the task is undefined by construction. Reported "
                               "instead as a CELL-level separability diagnostic below.",
    }

    # Cell-level donor separability: what share of a donor's cells fall nearer
    # their own donor's mean denominator vector than any other donor's.
    cell_feat = np.stack([frac_outside, frac_inside, frac_core], axis=1)
    hit = 0
    for d in np.flatnonzero(donors_observed):
        sel = mask & (donor_of_cell == d)
        if not sel.any():
            continue
        d2 = ((donor_feat[None, :, :] - cell_feat[sel][:, None, :]) ** 2).sum(axis=2)
        hit += int((np.argmin(d2, axis=1) == d).sum())
    predictiveness_full["donor_cell_level_nearest_donor_mean"] = {
        "accuracy_unconditional": hit / n_seen,
        "chance_rate": 1.0 / len(duniq),
        "note": "SUPPORTING diagnostic only. Cells of a donor contribute to that donor's own "
                "centroid, so this is a separability measure, not an out-of-donor claim.",
    }
    if all_donors_present:
        predictiveness = predictiveness_full

    # ------------------------------------------------------------------- output
    args.out_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(path: Path, rows: list[dict]) -> None:
        if not rows:
            return
        fields = list(rows[0].keys())
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_SOURCE.csv", by_source)
    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_OPERATOR.csv", by_operator)
    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_DONOR.csv", by_donor)
    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_SOURCE_OPERATOR.csv", by_source_operator)
    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_DEPTH_DECILE.csv", by_depth)
    write_csv(args.out_dir / "NORMALIZATION_DENOMINATOR_BY_CORE_NNZ_DECILE.csv", by_corenz)

    summary = {
        "schema": SCHEMA,
        "partial_run": partial,
        "blocks_limited_to": args.limit_blocks,
        "cells_measured": n_seen,
        "cells_expected": int(n_cells),
        "identity_space_closed": bool(partial or seen.all()),
        "global": {name: describe(arr[mask]) for name, arr in metrics.items()},
        "invariants": {
            "source_library_positive": True,
            "ledger_mass_never_exceeds_source_library": True,
            "outside_ledger_mass_never_negative": True,
            "core_mass_never_exceeds_ledger_mass": True,
            "all_fractions_finite": True,
            "core_nonzero_count_matches_authenticated_pass1": nnz_agree,
            "independent_ledger_sum_routes_agree": True,
        },
        "aggregate_mass": {
            "total_source_library": int(L_total[mask].sum()),
            "total_ledger_mass": int(L_ledger[mask].sum()),
            "total_core_mass": int(L_core[mask].sum()),
            "total_outside_ledger_mass": int(outside[mask].sum()),
            "pooled_fraction_outside_ledger": float(outside[mask].sum() / L_total[mask].sum()),
            "pooled_fraction_core": float(L_core[mask].sum() / L_total[mask].sum()),
        },
        "cells_with_any_outside_ledger_mass": int((outside[mask] > 0).sum()),
        "fraction_of_cells_with_any_outside_ledger_mass": float((outside[mask] > 0).mean()),
        "denominator_predictiveness": predictiveness,
        "all_donors_present": all_donors_present,
        "labels": {
            "channel": "OUTSIDE_LEDGER_DENOMINATOR_INFLUENCE",
            "not_the_same_as": "DIRECT_HIDDEN_TARGET_LEAKAGE",
            "evidence_class": "SUPPORTING_SHORTCUT_RECONNAISSANCE",
            "biological_claim": "NONE",
        },
        "elapsed_seconds": time.time() - started,
        "training_authorized": False,
    }
    (args.out_dir / "NORMALIZATION_DENOMINATOR_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if args.cell_level_out is not None:
        args.cell_level_out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            args.cell_level_out,
            L_total=L_total, L_ledger=L_ledger, L_core=L_core,
            cell_donor=cell_donor, source_code=src_of_cell, operator_index=op_of_cell,
            source_names=np.array([code_to_source[i] for i in range(len(source_names))], dtype=object),
            schema=np.array(SCHEMA),
        )
        print("  external cell-level artifact:", args.cell_level_out)

    print(json.dumps(summary["global"]["fraction_outside_ledger"], indent=2))
    print("pooled fraction outside ledger:",
          summary["aggregate_mass"]["pooled_fraction_outside_ledger"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
