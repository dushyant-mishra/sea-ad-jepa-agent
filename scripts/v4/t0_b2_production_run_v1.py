"""Production B2 runner: substrate authorities plus population raw-source closure.

Why this is a committed script rather than a scratchpad one
-----------------------------------------------------------
An earlier attempt at this run was driven from a temporary script with a local
edit to the raw-source module that was never pushed. The numbers it produced were
real, but they were not reproducible from committed code, so they could not be
claimed. An external review said so and was right. This runner and its replay
counterpart are committed before use, so anyone can reproduce the run from the
branch.

Scope
-----
Pathology-blind throughout. It reads the accepted immune membership, the complete
Phase2 block manifest, the operator-31 block metadata, and the raw MTG H5AD
`layers/UMIs` counts plus exactly two `obs` identity fields. No pathology column
is opened, no donor role is computed, no eligible-donor set is derived, and
`real_execution_ready` is never set.

What it establishes
-------------------
    population closure root      exhaustive scan of all operator-31 blocks
    logical row authority root   the accepted rows in frozen membership order
    physical read plan root      an I/O ordering that restores the logical set
    population raw-source root   every accepted row proven byte-to-row from the
                                 authenticated H5AD

The last one is the point. A three-row spot check establishes mechanics; only a
proof over every accepted row closes the population.

Usage
-----
    python t0_b2_production_run_v1.py --outdir <dir> [--store <dir>]
        [--membership <csv>] [--source <h5ad>] [--limit N]

`--limit` exists for a smoke run over the first N rows. A limited run is marked
`partial` in its metadata and must never be presented as closure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402

MEMBERSHIP_SHA = "d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529"
MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
SOURCE_SHA = "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"
FEATURE_ROOT = "538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8"

OPERATOR = 31
MATRIX = "sea_ad_mtg_rna_final_2026"
EXPECTED_TOTAL_BLOCKS = 8_915
EXPECTED_OPERATORS = 42
EXPECTED_OP31_BLOCKS = 1_247
EXPECTED_METADATA_ROWS = 638_150
EXPECTED_LOGICAL_ROWS = 20_804
EXPECTED_DONORS = 46

MANIFEST_NAME = "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"


def code_sha256(name: str) -> str:
    """Git blob content digest of a module: LF bytes, not worktree bytes.

    A platform line-ending transform changes the worktree bytes, so a disk
    digest would not be reproducible from the branch.
    """
    path = Path(__file__).resolve().parent / name
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def run(*, store: Path, membership_path: Path, source: Path, outdir: Path,
        limit: int | None = None, log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%8.1fs] %s" % (time.time() - started, message))

    stamp("authenticating inputs before anything is parsed")
    membership = membership_path.read_bytes()
    manifest = (store / MANIFEST_NAME).read_bytes()
    membership_sha = hashlib.sha256(membership).hexdigest()
    manifest_sha = hashlib.sha256(manifest).hexdigest()
    if membership_sha != MEMBERSHIP_SHA:
        raise AssertionError("membership is %s, expected %s"
                             % (membership_sha, MEMBERSHIP_SHA))
    if manifest_sha != MANIFEST_SHA:
        raise AssertionError("complete manifest is %s, expected %s"
                             % (manifest_sha, MANIFEST_SHA))
    source_bytes = source.stat().st_size
    stamp("  membership %s" % membership_sha)
    stamp("  manifest   %s" % manifest_sha)
    stamp("  source     %s bytes at %s" % (source_bytes, source))

    op31 = [row for row in csv.DictReader(manifest.decode("utf-8").splitlines())
            if int(row["operator_index"]) == OPERATOR]
    meta_bytes = {row["meta_path"]: (store / row["meta_path"]).read_bytes()
                  for row in op31}
    stamp("loaded %d operator-31 metadata members (%.1f MB)"
          % (len(meta_bytes), sum(len(b) for b in meta_bytes.values()) / 1e6))

    stamp("STEP 1  population closure")
    closure = rc.build_population_closure(
        membership_bytes=membership,
        expected_membership_sha256=MEMBERSHIP_SHA,
        block_manifest_bytes=manifest,
        expected_block_manifest_sha256=MANIFEST_SHA,
        meta_bytes_by_path=meta_bytes,
        operator_index=OPERATOR, matrix_id=MATRIX,
        expected_total_blocks=EXPECTED_TOTAL_BLOCKS,
        expected_operators=EXPECTED_OPERATORS,
        expected_op31_block_count=EXPECTED_OP31_BLOCKS)
    if closure["metadata_rows_scanned"] != EXPECTED_METADATA_ROWS:
        raise AssertionError("scanned %d metadata rows, expected %d"
                             % (closure["metadata_rows_scanned"],
                                EXPECTED_METADATA_ROWS))
    if closure["target_cells"] != EXPECTED_LOGICAL_ROWS:
        raise AssertionError("closed %d target cells, expected %d"
                             % (closure["target_cells"], EXPECTED_LOGICAL_ROWS))
    if len(closure["donors"]) != EXPECTED_DONORS:
        raise AssertionError("closed %d donors, expected %d"
                             % (len(closure["donors"]), EXPECTED_DONORS))
    stamp("  blocks %d  metadata rows %d  target cells %d  donors %d"
          % (closure["blocks_scanned"], closure["metadata_rows_scanned"],
             closure["target_cells"], len(closure["donors"])))
    stamp("  closure root       %s" % closure["population_closure_root_sha256"])

    stamp("STEP 2  logical row authority")
    logical = rc.build_logical_row_authority(
        closure=closure, membership_bytes=membership,
        feature_authority_root_sha256=FEATURE_ROOT)
    stamp("  rows %d" % logical["row_count"])
    stamp("  logical root       %s"
          % logical["logical_row_authority_root_sha256"])

    stamp("STEP 3  physical read plan")
    plan = rc.build_physical_read_plan(logical=logical)
    stamp("  entries %d" % plan["entries"])
    stamp("  physical plan root %s" % plan["physical_read_plan_root_sha256"])

    stamp("STEP 4  external verification of all three substrate roots")
    rc.assert_closure_lawful(
        closure=closure,
        expected_closure_root_sha256=closure["population_closure_root_sha256"],
        expected_membership_sha256=MEMBERSHIP_SHA,
        expected_block_manifest_sha256=MANIFEST_SHA)
    rc.assert_row_authority_lawful(
        logical=logical,
        expected_logical_row_authority_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_feature_authority_root_sha256=FEATURE_ROOT,
        expected_population_closure_root_sha256=closure[
            "population_closure_root_sha256"])
    rc.assert_physical_plan_lawful(
        plan=plan,
        expected_physical_root_sha256=plan["physical_read_plan_root_sha256"],
        expected_logical_root_sha256=logical["logical_row_authority_root_sha256"],
        logical=logical)
    stamp("  stored == recomputed == expected for all three")

    proving = logical
    partial = False
    if limit is not None and limit < logical["row_count"]:
        partial = True
        trimmed = [dict(row, logical_index=index)
                   for index, row in enumerate(logical["rows"][:limit])]
        proving = dict(logical)
        proving["rows"] = trimmed
        proving["row_count"] = len(trimmed)
        proving["logical_row_authority_root_sha256"] = rc._logical_root(
            trimmed, logical["feature_authority_root_sha256"],
            closure["population_closure_root_sha256"])
        stamp("SMOKE RUN over %d rows; this is NOT population closure" % limit)

    stamp("STEP 5  population raw-source proof over every row of the set")
    stamp("  digesting the source asset before opening it")
    marks = {"last": time.time(), "at": 0}

    def progress(done: int, total: int) -> None:
        if done % 2000 == 0 or done == total:
            span = max(time.time() - marks["last"], 1e-9)
            rate = (done - marks["at"]) / span
            marks["last"], marks["at"] = time.time(), done
            stamp("  proven %6d / %d  (%.0f rows/s)" % (done, total, rate))

    population = rs.prove_population_from_source_path(
        source_path=source, logical=proving,
        expected_logical_root_sha256=proving[
            "logical_row_authority_root_sha256"],
        expected_source_sha256=SOURCE_SHA,
        expected_row_count=proving["row_count"],
        progress=progress)
    stamp("  rows proven %d  digest bytes %d"
          % (population["rows_proven"], population["digest_bytes_read"]))
    stamp("  population root    %s"
          % population["population_raw_source_root_sha256"])

    stamp("STEP 6  coverage verification against the logical authority")
    rs.assert_population_authority_covers_logical(
        population=population, logical=proving,
        expected_population_root_sha256=population[
            "population_raw_source_root_sha256"],
        expected_logical_root_sha256=proving[
            "logical_row_authority_root_sha256"],
        expected_source_sha256=SOURCE_SHA)
    stamp("  covered %d of %d rows"
          % (population["rows_proven"], proving["row_count"]))

    stamp("STEP 7  writing the immutable authority package")
    written = rs.build_population_authority_package(
        outdir,
        population=population,
        closure_root_sha256=closure["population_closure_root_sha256"],
        feature_authority_root_sha256=FEATURE_ROOT,
        physical_read_plan_root_sha256=plan["physical_read_plan_root_sha256"],
        membership_sha256=MEMBERSHIP_SHA,
        complete_manifest_sha256=MANIFEST_SHA,
        source_bytes=source_bytes,
        derivation_code_sha256=code_sha256(
            "t0_raw_source_row_authority_v1.py"),
        expected_row_count=proving["row_count"])
    stamp("  package root       %s" % written["package_root_sha256"])

    summary = {
        "schema": "JEPA_T0_B2_PRODUCTION_RUN_SUMMARY_V1",
        "partial": partial,
        "closure_is_population": not partial,
        "pathology_blind": True,
        "runner_code_sha256": code_sha256("t0_b2_production_run_v1.py"),
        "raw_source_code_sha256": code_sha256(
            "t0_raw_source_row_authority_v1.py"),
        "row_count_code_sha256": code_sha256(
            "t0_v20_row_count_authority_v1.py"),
        "membership_sha256": MEMBERSHIP_SHA,
        "complete_manifest_sha256": MANIFEST_SHA,
        "source_sha256": SOURCE_SHA,
        "source_bytes": source_bytes,
        "feature_authority_root_sha256": FEATURE_ROOT,
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "physical_read_plan_root_sha256": plan["physical_read_plan_root_sha256"],
        "proved_logical_root_sha256": proving[
            "logical_row_authority_root_sha256"],
        "population_raw_source_root_sha256": population[
            "population_raw_source_root_sha256"],
        "package_root_sha256": written["package_root_sha256"],
        "blocks_scanned": closure["blocks_scanned"],
        "metadata_rows_scanned": closure["metadata_rows_scanned"],
        "target_cells": closure["target_cells"],
        "donors": len(closure["donors"]),
        "logical_rows": logical["row_count"],
        "rows_proven": population["rows_proven"],
        "digest_bytes_read": population["digest_bytes_read"],
        "elapsed_seconds": round(time.time() - started, 1),
        "numeric_confirmation_at8_accessed": False,
        "donor_roles_computed": False,
        "eligible_donors_computed": False,
        "real_execution_ready": False,
    }
    with io.open(Path(outdir) / "T0_B2_PRODUCTION_RUN_SUMMARY.json", "w",
                 encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    stamp("wrote the run summary")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    summary = run(store=args.store, membership_path=args.membership,
                  source=args.source, outdir=args.outdir, limit=args.limit)
    print()
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["partial"]:
        print()
        print("PARTIAL RUN: this is a smoke run and is NOT population closure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
