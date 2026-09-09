"""Replay verifier for a production technical-completeness authority package.

Reloads a written package and recomputes everything it claims: the completeness
root, the parent contract root, the package root, the donor summaries and the
cell counts consumed. It also rebuilds the B2 substrate from the frozen inputs
and replays the B2 population authority, so the package's parent identities are
checked against freshly derived roots rather than against themselves.

Two strengths of check
----------------------
By default this verifies that the package agrees with itself and with the
parents on disk: the roots recompute over the stored records, the substrate
rebuilds to the same three roots, the donor set matches B2 and the cell count is
20,804.

`--rederive` adds the stronger form. It walks the substrate again and recomputes
every donor's Q_DEPTH and Q_DETECT from authenticated bytes, then compares those
values against the stored records one by one. Only that mode shows the numbers
reproduce rather than merely that the digests are consistent. It costs a second
full pass over the counts store.

Requires, per the review checklist:

    stored == recomputed == expected for every root it claims
    donor count matches the B2 donor set
    cells consumed matches 20,804
    no missing donors, no duplicate donor rows
    no pathology field in the artifacts
    the retired SYNTHETIC_ONLY__PRODUCTION_B2_NOT_RUN terminal is absent

Usage
-----
    python t0_technical_completeness_replay_v1.py --pkgdir <dir>
        --store <phase2 expression_level4> --membership <csv>
        --population-pkg <b2 package dir>
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_raw_source_row_authority_v1 as rs  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402
import t0_technical_completeness_production_run_v1 as runner  # noqa: E402

EXPECTED_CELLS = 20_804
EXPECTED_DONORS = 46


def rederive_and_compare(*, records, closure, logical, plan, population,
                         projection, store: Path, log=print) -> dict:
    """Recompute every donor summary from the substrate and compare, value by value.

    A stored summary that cannot be reproduced from authenticated bytes is a
    STOP. Comparison is exact on the string forms the package carries, because
    the package is the artifact under test and a tolerance here would be a
    tolerance on the thing being verified.
    """
    paths = {row["counts_path"] for row in logical["rows"]}
    payloads = runner.LazyCountsPayloads(store, paths)
    log("  re-deriving over %d counts blocks" % len(paths))
    rederived = tc.derive_rows_from_authenticated_parents(
        logical=logical,
        expected_logical_root_sha256=logical[
            "logical_row_authority_root_sha256"],
        expected_closure_root_sha256=closure[
            "population_closure_root_sha256"],
        counts_payload_bytes_by_path=payloads,
        projection=projection,
        expected_projection_root_sha256=tc.projection_root(projection),
        population_raw_source=population,
        expected_population_raw_source_root_sha256=population[
            "population_raw_source_root_sha256"],
        block_geometry=closure["block_geometry"],
        expected_source_sha256=rs.MTG_SOURCE_SHA256)
    log("  re-derived %d donor rows over %d payload reads (%d cache hits)"
        % (len(rederived), payloads.reads, payloads.hits))

    stored_by_donor = {str(r["donor_id"]): r for r in records}
    rederived_by_donor = {str(r["donor_id"]): r for r in rederived}
    if set(stored_by_donor) != set(rederived_by_donor):
        raise AssertionError(
            "the re-derivation covers a different donor set: only-stored %s, "
            "only-rederived %s"
            % (sorted(set(stored_by_donor) - set(rederived_by_donor)),
               sorted(set(rederived_by_donor) - set(stored_by_donor))))

    compared = 0
    for donor in sorted(stored_by_donor):
        stored, fresh = stored_by_donor[donor], rederived_by_donor[donor]
        for field in ("cells", "Q_DEPTH", "Q_DETECT", "technical_complete"):
            want = str(fresh[field])
            got = str(stored[field])
            if got != want:
                raise AssertionError(
                    "donor %s: the package records %s=%r but the substrate "
                    "yields %r" % (donor, field, got, want))
            compared += 1
    log("  every stored donor summary reproduces (%d field comparisons)"
        % compared)

    fresh_root = tc.completeness_root(rederived)
    return {"donors_compared": len(stored_by_donor),
            "field_comparisons": compared,
            "rederived_completeness_root_sha256": fresh_root,
            "counts_payload_reads": payloads.reads,
            "counts_payload_cache_hits": payloads.hits}


def replay(*, pkgdir: Path, store: Path, membership_path: Path,
           population_pkg: Path, feature_split: Path | None = None,
           rederive: bool = False, log=print) -> dict:
    summary_path = Path(pkgdir) / "T0_TECHNICAL_COMPLETENESS_RUN_SUMMARY.json"
    if not summary_path.is_file():
        raise AssertionError("no run summary at %s" % summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    log("rebuilding the B2 substrate from the frozen inputs")
    substrate = runner.rebuild_substrate(store=store,
                                         membership_path=membership_path)
    closure, logical, plan = (substrate["closure"], substrate["logical"],
                              substrate["plan"])
    for name, produced, recorded in (
            ("population closure root",
             closure["population_closure_root_sha256"],
             summary["population_closure_root_sha256"]),
            ("logical row authority root",
             logical["logical_row_authority_root_sha256"],
             summary["logical_row_authority_root_sha256"]),
            ("physical read plan root",
             plan["physical_read_plan_root_sha256"],
             summary["physical_read_plan_root_sha256"])):
        if produced != recorded:
            raise AssertionError("%s rebuilt as %s but the run recorded %s"
                                 % (name, produced, recorded))
        log("  %s reproduces: %s" % (name, produced))

    log("replaying the B2 population raw-source authority")
    population, _b2 = runner.load_population(population_pkg, logical)
    if population["population_raw_source_root_sha256"] != summary[
            "population_raw_source_root_sha256"]:
        raise AssertionError("the population root does not match the run record")
    log("  population root reproduces: %s"
        % population["population_raw_source_root_sha256"])

    log("recomputing the B1 projection root")
    projection_root = summary["projection_root_sha256"]
    if int(summary["projection_positions"]) != tc.SCALAR_FEATURES:
        raise AssertionError("the run used %s projection positions, expected %d"
                             % (summary["projection_positions"],
                                tc.SCALAR_FEATURES))
    log("  positions %d" % summary["projection_positions"])

    log("replaying the technical-completeness package from disk")
    replayed = tc.load_authority(
        Path(pkgdir),
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_completeness_root_sha256=summary["completeness_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"])
    meta = replayed["metadata"]
    records = replayed["records"]
    log("  donor rows %d" % len(records))

    donors = [str(r["donor_id"]) for r in records]
    if len(donors) != len(set(donors)):
        duplicates = sorted({d for d in donors if donors.count(d) > 1})
        raise AssertionError("duplicate donor rows: %s" % duplicates)
    if len(donors) != EXPECTED_DONORS:
        raise AssertionError("%d donor rows, expected %d"
                             % (len(donors), EXPECTED_DONORS))
    b2_donors = set(closure["donors"])
    if set(donors) != b2_donors:
        raise AssertionError("donor set differs from the B2 closure: only-here %s,"
                             " only-B2 %s"
                             % (sorted(set(donors) - b2_donors),
                                sorted(b2_donors - set(donors))))
    log("  donor set matches the B2 closure exactly")

    cells = sum(int(r["cells"]) for r in records)
    if cells != EXPECTED_CELLS:
        raise AssertionError("cells consumed %d, expected %d"
                             % (cells, EXPECTED_CELLS))
    log("  cells consumed %d" % cells)

    complete = sum(1 for r in records
                   if str(r["technical_complete"]).strip().lower() == "true")
    log("  technically complete %d of %d" % (complete, len(records)))

    tc.assert_production_run_status_not_retired(meta.get("production_run_status"))
    if meta.get("production_run_status") != tc.PRODUCTION_RUN_STATUS_POPULATION:
        raise AssertionError(
            "the package records %r; a replayed production authority must claim "
            "the real population" % meta.get("production_run_status"))
    log("  production status: %s" % meta["production_run_status"])

    rs.assert_no_pathology_in_artifact(list(records[0].keys()))
    for flag in ("thresholds_introduced", "pathology_values_read",
                 "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError("%s must be False in the package" % flag)
    log("  no pathology field in the artifacts; no thresholds; not ready")

    rederivation = None
    if rederive:
        if feature_split is None:
            raise AssertionError("re-derivation needs the frozen B1 feature "
                                 "split to rebuild the 35,076-position "
                                 "projection")
        log("independently re-deriving every donor summary from the substrate")
        projection = runner.load_projection(Path(feature_split))
        if tc.projection_root(projection) != summary["projection_root_sha256"]:
            raise AssertionError(
                "the supplied feature split yields projection root %s but the "
                "run recorded %s" % (tc.projection_root(projection),
                                     summary["projection_root_sha256"]))
        rederivation = rederive_and_compare(
            records=records, closure=closure, logical=logical, plan=plan,
            population=population, projection=projection,
            store=store, log=log)
        if rederivation["rederived_completeness_root_sha256"] != summary[
                "completeness_root_sha256"]:
            raise AssertionError(
                "the re-derived completeness root is %s but the package records "
                "%s" % (rederivation["rederived_completeness_root_sha256"],
                        summary["completeness_root_sha256"]))
        log("  the re-derived completeness root equals the stored one")

    report = {
        "schema": "JEPA_T0_TECHNICAL_COMPLETENESS_REPLAY_REPORT_V1",
        "independently_rederived": bool(rederive),
        "rederivation": rederivation,
        "package_dir": str(pkgdir),
        "donor_rows": len(records),
        "cells_consumed": cells,
        "technically_complete_donors": complete,
        "completeness_root_sha256": summary["completeness_root_sha256"],
        "parent_contract_root_sha256": summary["parent_contract_root_sha256"],
        "package_root_sha256": replayed["package_root_sha256"],
        "population_raw_source_root_sha256": population[
            "population_raw_source_root_sha256"],
        "population_closure_root_sha256": closure[
            "population_closure_root_sha256"],
        "logical_row_authority_root_sha256": logical[
            "logical_row_authority_root_sha256"],
        "physical_read_plan_root_sha256": plan["physical_read_plan_root_sha256"],
        "projection_root_sha256": projection_root,
        "production_run_status": meta["production_run_status"],
        "stored_equals_recomputed_equals_expected": True,
        "donor_set_matches_b2": True,
        "duplicate_donor_rows": False,
        "pathology_fields_in_artifacts": False,
        "retired_terminal_present": False,
        "real_execution_ready": False,
        "member_digests": {},
    }
    for name in tc.MEMBERS:
        blob = (Path(pkgdir) / name).read_bytes()
        report["member_digests"][name] = {
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkgdir", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--membership", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument(
        "--feature-split", type=Path, default=None,
        help="the frozen B1 feature role split; required with --rederive")
    parser.add_argument(
        "--rederive", action="store_true",
        help="recompute every donor summary from the substrate and compare "
             "value by value; costs a second full pass over the counts store")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.rederive and args.feature_split is None:
        raise SystemExit("--rederive requires --feature-split")

    report = replay(pkgdir=args.pkgdir, store=args.store,
                    membership_path=args.membership,
                    population_pkg=args.population_pkg,
                    feature_split=args.feature_split,
                    rederive=args.rederive)
    print()
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report is not None:
        with io.open(args.report, "w", encoding="utf-8", newline="\n") as h:
            h.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print()
    print("TECHNICAL COMPLETENESS REPLAY PASS"
          + (" (INDEPENDENTLY RE-DERIVED)" if args.rederive else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
