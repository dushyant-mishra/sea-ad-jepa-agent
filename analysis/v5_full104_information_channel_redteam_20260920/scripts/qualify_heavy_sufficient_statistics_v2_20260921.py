"""Independent aggregate qualification of the heavy B/C/E sufficient statistics.

Parser equivalence establishes that the legacy ``int(float(token))`` coercion
used to build the 242 MB artifact returns the same integer as the production
parser for every authenticated FULL104 metadata row. That is necessary but not
sufficient for reuse: it says the artifact's *inputs* were parsed identically, not
that the artifact's *contents* are consistent with the authenticated substrate.

This script closes that gap by recomputing aggregate invariants **from source
metadata by a second route** and comparing them against the artifact. It reads
block metadata only; it never touches expression matrices, terminal outcomes, or
protected data.

Checks, each fail-closed
------------------------
1. artifact SHA-256 equals the bound value (content addressing);
2. total cell count;
3. donor count and donor registry ordering;
4. per-source cell counts;
5. strict-core address dimension and per-donor matrix geometry;
6. a deterministic sample of per-donor cell totals, recomputed from metadata;
7. the **total source-library sum**, recomputed from metadata with the production
   parser and compared against the artifact's ``libraries`` vector;
8. cross-reference against Audit A's independently produced total, which came
   from a different script in a different run.

Check 7 is the substantive one. It is an exact integer equality over
4,553,407 rows accumulated by a route that shares no code with the artifact's
producer, so agreement is corroboration rather than tautology.

Parallelism
-----------
Metadata parsing dominates, and blocks are independent, so the sweep runs across
processes with an ordered reduction. All accumulators are exact integers, so the
result is independent of reduction order by construction.

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

SCHEMA = "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2"

EXPECTED_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_CORE = 17_186
BOUND_ARTIFACT_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"

#: Audit A's independently produced total, from a different script and run.
AUDIT_A_TOTAL_SOURCE_LIBRARY = 122_517_308_792

#: Per-source cell counts established by the authenticated census.
EXPECTED_SOURCE_CELLS = {"HVS": 198_718, "NPH52": 236_476, "SEA_AD": 4_118_213}

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


_W: dict = {}


def _init(level4_root: str, donor_index: dict, n_donors: int):
    os.environ["OMP_NUM_THREADS"] = "1"
    _W.update(root=Path(level4_root), donor_index=donor_index, n_donors=n_donors)


def _chunk(rows: list[dict]) -> dict:
    """Recompute metadata aggregates for a chunk of blocks, including donor-source identity."""
    from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import _parse_source_library

    root = _W["root"]
    donor_index = _W["donor_index"]
    donor_cells = np.zeros(_W["n_donors"], dtype=np.int64)
    donor_library = np.zeros(_W["n_donors"], dtype=object)   # python ints, no overflow
    donor_library[:] = 0
    source_cells: dict[str, int] = {}
    donor_source = np.full(_W["n_donors"], None, dtype=object)
    total_library = 0
    total_rows = 0
    selection_min = None
    selection_max = None

    for row in rows:
        meta = root / row["meta_path"]
        if sha256_file(meta) != row["meta_sha256"]:
            raise RuntimeError(f"metadata hash mismatch: {row['block_key']}")
        with meta.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise RuntimeError(f"metadata schema mismatch: {row['block_key']}")
            for record in reader:
                donor = donor_index[str(record["donor_id"])]
                source = str(row["source"])
                previous_source = donor_source[donor]
                if previous_source is None:
                    donor_source[donor] = source
                elif str(previous_source) != source:
                    raise RuntimeError(
                        f"donor {record['donor_id']!r} appears under multiple sources: "
                        f"{previous_source!r} and {source!r}"
                    )
                lib = _parse_source_library(str(record["source_library"]).strip())
                sel = int(record["selection_row"])
                donor_cells[donor] += 1
                donor_library[donor] += lib
                total_library += lib
                total_rows += 1
                selection_min = sel if selection_min is None else min(selection_min, sel)
                selection_max = sel if selection_max is None else max(selection_max, sel)
        source_cells[row["source"]] = source_cells.get(row["source"], 0) + int(row["rows"])

    return {
        "donor_cells": donor_cells,
        "donor_library": donor_library,
        "source_cells": source_cells,
        "donor_source": donor_source,
        "total_library": total_library,
        "total_rows": total_rows,
        "selection_min": selection_min,
        "selection_max": selection_max,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level4-root", type=Path, default=Path("C:/jepa_full104_ssd/expression_level4"))
    ap.add_argument("--artifact", type=Path,
                    default=Path("D:/jepa_full104_redteam_20260920_external/"
                                 "core_sufficient_statistics_v1.npz"))
    ap.add_argument("--pass1", type=Path,
                    default=Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
                                 "full104_pass1_v2_selection_row_keyed.npz"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--donor-sample", type=int, default=12)
    ap.add_argument("--workers", type=int, default=0)
    # Expectation overrides exist ONLY so the instrument can be exercised against
    # a synthetic fixture whose answer is known. The real FULL104 run must always
    # use the defaults, which are hard-bound to the authenticated census.
    ap.add_argument("--expect-cells", type=int, default=EXPECTED_CELLS)
    ap.add_argument("--expect-donors", type=int, default=EXPECTED_DONORS)
    ap.add_argument("--expect-core", type=int, default=EXPECTED_CORE)
    ap.add_argument("--expect-manifest-sha256", default=EXPECTED_MANIFEST_SHA256)
    ap.add_argument("--bound-artifact-sha256", default=BOUND_ARTIFACT_SHA256)
    ap.add_argument("--expect-source-cells", default=None,
                    help="JSON object of source -> cell count; defaults to the census values")
    ap.add_argument("--audit-a-total", type=int, default=AUDIT_A_TOTAL_SOURCE_LIBRARY)
    args = ap.parse_args()

    expected_cells = args.expect_cells
    expected_donors = args.expect_donors
    expected_core = args.expect_core
    expected_manifest = args.expect_manifest_sha256
    bound_artifact = args.bound_artifact_sha256
    expected_source_cells = (json.loads(args.expect_source_cells)
                             if args.expect_source_cells else EXPECTED_SOURCE_CELLS)
    audit_a_total = args.audit_a_total

    started = time.time()
    failures: list[str] = []

    # ---- 1. content addressing
    if not args.artifact.is_file():
        raise SystemExit(f"heavy artifact absent: {args.artifact}")
    artifact_sha = sha256_file(args.artifact)
    if artifact_sha != bound_artifact:
        failures.append(f"artifact SHA-256 {artifact_sha} != bound {bound_artifact}")

    st = np.load(args.artifact, allow_pickle=True)
    duniq = [str(x) for x in st["duniq"]]
    donor_index = {d: i for i, d in enumerate(duniq)}
    art_donor_cells = np.asarray(st["donor_cells"], dtype=np.int64)
    art_libraries = np.asarray(st["libraries"], dtype=np.int64)
    art_core = np.asarray(st["core"], dtype=np.int64)
    art_donor_nnz = np.asarray(st["donor_nnz"], dtype=np.int64)
    art_src_of_cell = np.asarray(st["src_of_cell"], dtype=np.int64)
    art_source_names = [str(x) for x in st["source_names"]]

    # ---- 2/3/5. shape invariants
    if art_libraries.size != expected_cells:
        failures.append(f"artifact libraries vector has {art_libraries.size} entries, "
                        f"expected {expected_cells}")
    if len(duniq) != expected_donors:
        failures.append(f"artifact donor registry has {len(duniq)}, expected {expected_donors}")
    if duniq != sorted(set(duniq)):
        failures.append("artifact donor registry is not a sorted unique list")
    if art_core.size != expected_core:
        failures.append(f"artifact core has {art_core.size} addresses, expected {expected_core}")
    if art_donor_nnz.shape != (expected_donors, expected_core):
        failures.append(f"donor_nnz geometry {art_donor_nnz.shape} != "
                        f"({expected_donors}, {expected_core})")

    # ---- second-route recomputation from metadata
    manifest_path = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest_path) != expected_manifest:
        raise SystemExit("block manifest hash mismatch")
    manifest_rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8")))

    workers = args.workers if args.workers > 0 else min(8, max(1, (os.cpu_count() or 2) - 2))
    size = max(1, len(manifest_rows) // (workers * 4))
    chunks = [manifest_rows[i:i + size] for i in range(0, len(manifest_rows), size)]
    print(f"recomputing metadata aggregates: {len(manifest_rows)} blocks, "
          f"{workers} worker(s), {len(chunks)} chunks", flush=True)

    donor_cells = np.zeros(expected_donors, dtype=np.int64)
    donor_library = [0] * expected_donors
    source_cells: dict[str, int] = {}
    donor_source: list[str | None] = [None] * expected_donors
    total_library = 0
    total_rows = 0
    sel_min: int | None = None
    sel_max: int | None = None

    def merge(part: dict) -> None:
        nonlocal total_library, total_rows, sel_min, sel_max
        donor_cells[:] += part["donor_cells"]
        for i, v in enumerate(part["donor_library"]):
            donor_library[i] += int(v)
        for k, v in part["source_cells"].items():
            source_cells[k] = source_cells.get(k, 0) + v
        for i, value in enumerate(part["donor_source"]):
            if value is None:
                continue
            if donor_source[i] is None:
                donor_source[i] = str(value)
            elif donor_source[i] != str(value):
                raise RuntimeError(
                    f"donor {duniq[i]!r} appears under multiple sources across chunks: "
                    f"{donor_source[i]!r} and {value!r}"
                )
        total_library += part["total_library"]
        total_rows += part["total_rows"]
        if part["selection_min"] is not None:
            sel_min = part["selection_min"] if sel_min is None else min(sel_min, part["selection_min"])
            sel_max = part["selection_max"] if sel_max is None else max(sel_max, part["selection_max"])

    if workers == 1:
        _init(str(args.level4_root), donor_index, expected_donors)
        for i, c in enumerate(chunks):
            merge(_chunk(c))
    else:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers, initializer=_init,
                      initargs=(str(args.level4_root), donor_index, expected_donors)) as pool:
            for i, part in enumerate(pool.imap(_chunk, chunks)):
                merge(part)
                if (i + 1) % 8 == 0 or i + 1 == len(chunks):
                    print(f"  chunk {i+1}/{len(chunks)} {time.time()-started:.0f}s", flush=True)

    # ---- comparisons
    if total_rows != expected_cells:
        failures.append(f"metadata sweep saw {total_rows} rows, expected {expected_cells}")
    if sel_min != 0 or sel_max != expected_cells - 1:
        failures.append(f"selection_row range [{sel_min}, {sel_max}] is not "
                        f"[0, {expected_cells - 1}]")
    for name, expected in expected_source_cells.items():
        got = source_cells.get(name)
        if got != expected:
            failures.append(f"source {name}: manifest rows {got} != expected {expected}")
    if not np.array_equal(donor_cells, art_donor_cells):
        bad = int((donor_cells != art_donor_cells).sum())
        failures.append(f"per-donor cell totals disagree with the artifact for {bad} donors")

    recomputed_total = int(total_library)
    artifact_total = int(art_libraries.sum(dtype=np.int64))
    if recomputed_total != artifact_total:
        failures.append(f"total source library: metadata {recomputed_total} != "
                        f"artifact {artifact_total}")
    if recomputed_total != audit_a_total:
        failures.append(f"total source library: metadata {recomputed_total} != Audit A "
                        f"{audit_a_total}")

    # per-donor library totals, deterministic sample chosen without using any result
    order = sorted(range(expected_donors),
                   key=lambda i: hashlib.sha256(
                       f"V5_HEAVY_QUALIFICATION_DONOR_SAMPLE_20260920|{duniq[i]}".encode()).digest())
    sample = order[: args.donor_sample]
    donor_rows = []
    for d in sample:
        recomputed = donor_library[d]
        donor_rows.append({
            "donor": duniq[d],
            "cells_metadata": int(donor_cells[d]),
            "cells_artifact": int(art_donor_cells[d]),
            "source_library_sum_metadata": recomputed,
        })

    # Cross-check ALL donor library totals and the full per-cell source vector
    # against the artifact, using pass1's authenticated cell->donor map.
    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    all_donor_library_agreement = False
    per_cell_source_vector_agreement = False
    if cell_donor.size != expected_cells:
        failures.append("pass1 cell_donor length mismatch")
    elif cell_donor.min(initial=0) < 0 or cell_donor.max(initial=-1) >= expected_donors:
        failures.append("pass1 cell_donor contains an out-of-range donor code")
    else:
        artifact_donor_library = np.zeros(expected_donors, dtype=np.int64)
        np.add.at(artifact_donor_library, cell_donor, art_libraries)
        recomputed_donor_library = np.asarray(
            [int(x) for x in donor_library], dtype=np.int64
        )
        mismatch = np.flatnonzero(artifact_donor_library != recomputed_donor_library)
        all_donor_library_agreement = mismatch.size == 0
        if mismatch.size:
            failures.append(
                f"per-donor source-library totals disagree with the artifact for "
                f"{int(mismatch.size)} donors")

        for row, d in zip(donor_rows, sample):
            row["source_library_sum_artifact"] = int(artifact_donor_library[d])

        if any(x is None for x in donor_source):
            failures.append("metadata sweep did not recover a source for every donor")
        elif len(art_source_names) != len(set(art_source_names)):
            failures.append("artifact source_names contains duplicates")
        else:
            source_to_code = {name: i for i, name in enumerate(art_source_names)}
            missing_sources = sorted({str(x) for x in donor_source} - set(source_to_code))
            if missing_sources:
                failures.append(
                    f"artifact source_names omits metadata sources: {missing_sources}")
            elif art_src_of_cell.shape != (expected_cells,):
                failures.append(
                    f"artifact src_of_cell shape {art_src_of_cell.shape} != "
                    f"({expected_cells},)")
            else:
                donor_source_code = np.asarray(
                    [source_to_code[str(x)] for x in donor_source], dtype=np.int64
                )
                expected_src_of_cell = donor_source_code[cell_donor]
                bad_source = np.flatnonzero(art_src_of_cell != expected_src_of_cell)
                per_cell_source_vector_agreement = bad_source.size == 0
                if bad_source.size:
                    failures.append(
                        f"per-cell source vector disagrees with authenticated donor/source "
                        f"identity for {int(bad_source.size)} cells")

    verdict = "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE" if not failures else "HEAVY_ARTIFACT_NOT_QUALIFIED"
    payload = {
        "schema": SCHEMA,
        "scope_class": "CURRENT_FULL104_RECONNAISSANCE",
        "artifact": str(args.artifact),
        "artifact_sha256": artifact_sha,
        "bound_artifact_sha256": bound_artifact,
        "artifact_sha_matches_bound": artifact_sha == bound_artifact,
        "block_manifest_sha256": expected_manifest,
        "rows_traversed": total_rows,
        "donors": len(duniq),
        "core_addresses": int(art_core.size),
        "selection_row_range": [sel_min, sel_max],
        "source_cells_from_manifest": source_cells,
        "expected_source_cells": expected_source_cells,
        "total_source_library_recomputed_from_metadata": recomputed_total,
        "total_source_library_in_artifact": artifact_total,
        "total_source_library_audit_a_independent": audit_a_total,
        "three_route_total_agreement": (recomputed_total == artifact_total
                                        == audit_a_total),
        "all_104_donor_library_totals_agree": all_donor_library_agreement,
        "per_cell_source_vector_agrees": per_cell_source_vector_agreement,
        "donor_sample_rule": "SHA-256 of a fixed salt joined to the donor id; independent of any result",
        "donor_sample": donor_rows,
        "failures": failures,
        "verdict": verdict,
        "workers": workers,
        "elapsed_seconds": time.time() - started,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "donor_sample"}, indent=2))
    if failures:
        for f in failures:
            print("  FAILURE:", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
