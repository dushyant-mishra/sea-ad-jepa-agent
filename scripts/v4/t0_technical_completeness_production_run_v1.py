"""Production technical-completeness runner, consuming the B2 population authority.

Scope
-----
Pathology-blind. It consumes the authenticated B2 closure, logical row authority
and physical read plan, the population raw-source authority produced by the B2
run, the B1 projection, and the operator-31 counts payloads. No pathology column
is opened, no donor role is computed, no eligible-donor set is derived, and
`real_execution_ready` is never set.

Why the payloads are read lazily
--------------------------------
The 1,246 counts payloads the accepted rows reference total 7.89 GB, so holding
them all as bytes is not possible on this machine. The largest single payload is
7.7 MB, so a mapping that reads a payload on demand and keeps a small number of
recently used ones is enough. `derive_rows_from_authenticated_parents` only ever
asks a payload mapping for `path in mapping` and `mapping[path]`, so a lazy
mapping satisfies it without changing the reviewed derivation code at all.

Every payload is still authenticated against the digest its own logical row
binds, inside the derivation, exactly as an in-memory mapping would be. Laziness
changes when bytes are read, not whether they are checked.

Usage
-----
    python t0_technical_completeness_production_run_v1.py --outdir <dir>
        --store <phase2 expression_level4> --membership <csv>
        --population-pkg <b2 package dir> --feature-split <split csv>
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_v20_row_count_authority_v1 as rc  # noqa: E402

MEMBERSHIP_SHA = "d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529"
MANIFEST_SHA = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
SOURCE_SHA = "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"
FEATURE_ROOT = "538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8"

OPERATOR = 31
MATRIX = "sea_ad_mtg_rna_final_2026"
MANIFEST_NAME = "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
EXPECTED_LOGICAL_ROWS = 20_804
EXPECTED_DONORS = 46
EXPECTED_PROJECTION = 35_076


class LazyCountsPayloads(Mapping):
    """A payload mapping that reads from disk on demand, keeping a few cached.

    Presented as a Mapping because that is exactly the contract the derivation
    uses: membership testing and item access. Nothing about authentication moves
    here; the derivation still checks every payload against the digest its
    logical row binds.
    """

    def __init__(self, store: Path, paths, *, cache: int = 48) -> None:
        self._store = Path(store)
        self._paths = set(paths)
        self._cache: collections.OrderedDict[str, bytes] = collections.OrderedDict()
        self._limit = int(cache)
        self.reads = 0
        self.hits = 0

    def __contains__(self, key: object) -> bool:
        return str(key) in self._paths

    def __getitem__(self, key: str) -> bytes:
        name = str(key)
        if name not in self._paths:
            raise KeyError(name)
        if name in self._cache:
            self.hits += 1
            self._cache.move_to_end(name)
            return self._cache[name]
        blob = (self._store / name).read_bytes()
        self.reads += 1
        self._cache[name] = blob
        while len(self._cache) > self._limit:
            self._cache.popitem(last=False)
        return blob

    def __iter__(self):
        return iter(self._paths)

    def __len__(self) -> int:
        return len(self._paths)


def code_sha256(name: str) -> str:
    path = Path(__file__).resolve().parent / name
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def load_projection(split_csv: Path) -> dict:
    """The B1 projection: the 35,076 measured addresses, from the frozen split."""
    rows = list(csv.DictReader(Path(split_csv).open(encoding="utf-8", newline="")))
    positions = sorted({int(r["molecular_address_index"]) for r in rows})
    if len(positions) != EXPECTED_PROJECTION:
        raise AssertionError("the split yields %d distinct addresses, expected %d"
                             % (len(positions), EXPECTED_PROJECTION))
    return {"positions": positions,
            "feature_authority_root_sha256": FEATURE_ROOT}


def rebuild_substrate(*, store: Path, membership_path: Path) -> dict:
    membership = membership_path.read_bytes()
    manifest = (store / MANIFEST_NAME).read_bytes()
    op31 = [row for row in csv.DictReader(manifest.decode("utf-8").splitlines())
            if int(row["operator_index"]) == OPERATOR]
    meta_bytes = {row["meta_path"]: (store / row["meta_path"]).read_bytes()
                  for row in op31}
    closure = rc.build_population_closure(
        membership_bytes=membership,
        expected_membership_sha256=MEMBERSHIP_SHA,
        block_manifest_bytes=manifest,
        expected_block_manifest_sha256=MANIFEST_SHA,
        meta_bytes_by_path=meta_bytes,
        operator_index=OPERATOR, matrix_id=MATRIX,
        expected_total_blocks=8_915, expected_operators=42,
        expected_op31_block_count=1_247)
    logical = rc.build_logical_row_authority(
        closure=closure, membership_bytes=membership,
        feature_authority_root_sha256=FEATURE_ROOT)
    plan = rc.build_physical_read_plan(logical=logical)
    return {"closure": closure, "logical": logical, "plan": plan}


def load_population(pkgdir: Path, logical) -> dict:
    """Replay the B2 population authority and shape it for the consumer."""
    summary = json.loads(
        (Path(pkgdir) / "T0_B2_PRODUCTION_RUN_SUMMARY.json").read_text(
            encoding="utf-8"))
    if summary["partial"]:
        raise AssertionError(
            "the supplied population package is a partial smoke run and does "
            "not close the population")
    replayed = rs.load_population_authority_package(
        Path(pkgdir),
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_population_root_sha256=summary[
            "population_raw_source_root_sha256"],
        expected_logical_root_sha256=summary["proved_logical_root_sha256"],
        expected_source_sha256=SOURCE_SHA,
        expected_row_count=summary["rows_proven"],
        logical=logical)
    return {
        "proofs": replayed["proofs"],
        "population_raw_source_root_sha256": replayed[
            "population_raw_source_root_sha256"],
        "logical_row_authority_root_sha256": replayed["metadata"][
            "logical_row_authority_root_sha256"],
        "source_sha256": replayed["metadata"]["source_sha256"],
    }, summary


def run(*, store: Path, membership_path: Path, population_pkg: Path,
        feature_split: Path, outdir: Path, log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%8.1fs] %s" % (time.time() - started, message))

    stamp("rebuilding the authenticated B2 substrate from the frozen inputs")
    substrate = rebuild_substrate(store=store, membership_path=membership_path)
    closure, logical, plan = (substrate["closure"], substrate["logical"],
                              substrate["plan"])
    if logical["row_count"] != EXPECTED_LOGICAL_ROWS:
        raise AssertionError("logical rows %d, expected %d"
                             % (logical["row_count"], EXPECTED_LOGICAL_ROWS))
    stamp("  closure root  %s" % closure["population_closure_root_sha256"])
    stamp("  logical root  %s" % logical["logical_row_authority_root_sha256"])
    stamp("  plan root     %s" % plan["physical_read_plan_root_sha256"])

    stamp("replaying the B2 population raw-source authority")
    population, b2_summary = load_population(population_pkg, logical)
    stamp("  population root %s"
          % population["population_raw_source_root_sha256"])
    stamp("  rows covered    %d" % len(population["proofs"]))

    stamp("loading the B1 projection")
    projection = load_projection(feature_split)
    projection_root = tc.projection_root(projection)
    stamp("  positions %d   projection root %s"
          % (len(projection["positions"]), projection_root))

    donors = sorted(closure["donors"])
    if len(donors) != EXPECTED_DONORS:
        raise AssertionError("closed %d donors, expected %d"
                             % (len(donors), EXPECTED_DONORS))

    paths = {row["counts_path"] for row in logical["rows"]}
    payloads = LazyCountsPayloads(store, paths)
    stamp("lazy payload mapping over %d counts blocks" % len(paths))

    stamp("deriving technical completeness over every accepted row")
    summary = tc.build_production_authority(
        outdir,
        closure=closure,
        expected_closure_root_sha256=closure["population_closure_root_sha256"],
        expected_membership_sha256=MEMBERSHIP_SHA,
        expected_block_manifest_sha256=MANIFEST_SHA,
        logical=logical,
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        physical_plan=plan,
        expected_physical_plan_root_sha256=plan[
            "physical_read_plan_root_sha256"],
        counts_payload_bytes_by_path=payloads,
        projection=projection,
        expected_projection_root_sha256=projection_root,
        population_raw_source=population,
        expected_population_raw_source_root_sha256=population[
            "population_raw_source_root_sha256"],
        expected_source_sha256=SOURCE_SHA,
        derivation_code_sha256=code_sha256(
            "t0_technical_completeness_authority_v1.py"),
        candidate_donors=donors)
    stamp("  donors %d   cells consumed %d"
          % (summary["donor_count"], summary["cells_consumed"]))
    stamp("  technically complete %d" % summary["technically_complete_donors"])
    stamp("  completeness root %s" % summary["completeness_root_sha256"])
    stamp("  package root      %s" % summary["package_root_sha256"])
    stamp("  payload reads %d, cache hits %d" % (payloads.reads, payloads.hits))

    record = {
        "schema": "JEPA_T0_TECHNICAL_COMPLETENESS_PRODUCTION_RUN_SUMMARY_V1",
        "pathology_blind": True,
        "runner_code_sha256": code_sha256(
            "t0_technical_completeness_production_run_v1.py"),
        "authority_code_sha256": code_sha256(
            "t0_technical_completeness_authority_v1.py"),
        "membership_sha256": MEMBERSHIP_SHA,
        "complete_manifest_sha256": MANIFEST_SHA,
        "source_sha256": SOURCE_SHA,
        "feature_authority_root_sha256": FEATURE_ROOT,
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "physical_read_plan_root_sha256": plan["physical_read_plan_root_sha256"],
        "population_raw_source_root_sha256": population[
            "population_raw_source_root_sha256"],
        "b2_package_root_sha256": b2_summary["package_root_sha256"],
        "projection_root_sha256": projection_root,
        "projection_positions": len(projection["positions"]),
        "completeness_root_sha256": summary["completeness_root_sha256"],
        "parent_contract_root_sha256": summary["parent_contract_root_sha256"],
        "package_root_sha256": summary["package_root_sha256"],
        "donor_count": summary["donor_count"],
        "technically_complete_donors": summary["technically_complete_donors"],
        "cells_consumed": summary["cells_consumed"],
        "counts_payload_reads": payloads.reads,
        "counts_payload_cache_hits": payloads.hits,
        "elapsed_seconds": round(time.time() - started, 1),
        "numeric_confirmation_at8_accessed": False,
        "donor_roles_computed": False,
        "eligible_donors_computed": False,
        "real_execution_ready": False,
    }
    with io.open(Path(outdir) / "T0_TECHNICAL_COMPLETENESS_RUN_SUMMARY.json",
                 "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    stamp("wrote the run summary")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--membership", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument("--feature-split", required=True, type=Path)
    args = parser.parse_args(argv)

    record = run(store=args.store, membership_path=args.membership,
                 population_pkg=args.population_pkg,
                 feature_split=args.feature_split, outdir=args.outdir)
    print()
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
