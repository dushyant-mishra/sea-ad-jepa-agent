"""Replay verifier for a production B2 population raw-source authority package.

An authority that cannot be reloaded from disk and re-verified is not an
authority; it is a console transcript. This script reloads a written package,
recomputes the population root from the reloaded registry, and requires
stored == recomputed == externally expected. It also rebuilds the substrate
authorities from the frozen inputs so the package's parent identities are checked
against freshly derived roots rather than against themselves.

It reads no pathology column and asserts that none appears in the emitted
artifacts.

Usage
-----
    python t0_b2_production_replay_v1.py --pkgdir <dir> --store <dir>
        --membership <csv> [--rebuild-substrate]

Without `--rebuild-substrate` the replay verifies the package against the roots
recorded in its own summary. With it, the substrate is rebuilt from the frozen
membership and manifest and the package must agree with the rebuilt roots, which
is the stronger check.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
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
MANIFEST_NAME = "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"


def rebuild_substrate(*, store: Path, membership_path: Path) -> dict:
    """Rebuild closure, logical authority and plan from the frozen inputs."""
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


def replay(*, pkgdir: Path, store: Path | None = None,
           membership_path: Path | None = None, log=print) -> dict:
    summary_path = Path(pkgdir) / "T0_B2_PRODUCTION_RUN_SUMMARY.json"
    if not summary_path.is_file():
        raise AssertionError("no run summary at %s" % summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    log("run summary: partial=%s rows_proven=%s"
        % (summary["partial"], summary["rows_proven"]))

    logical = None
    if store is not None and membership_path is not None:
        log("rebuilding the substrate from the frozen inputs")
        rebuilt = rebuild_substrate(store=store, membership_path=membership_path)
        logical = rebuilt["logical"]
        for name, produced, recorded in (
                ("population closure root",
                 rebuilt["closure"]["population_closure_root_sha256"],
                 summary["population_closure_root_sha256"]),
                ("logical row authority root",
                 rebuilt["logical"]["logical_row_authority_root_sha256"],
                 summary["logical_row_authority_root_sha256"]),
                ("physical read plan root",
                 rebuilt["plan"]["physical_read_plan_root_sha256"],
                 summary["physical_read_plan_root_sha256"])):
            if produced != recorded:
                raise AssertionError(
                    "%s rebuilt as %s but the run recorded %s"
                    % (name, produced, recorded))
            log("  %s reproduces: %s" % (name, produced))
        if summary["partial"]:
            # A smoke run proved a trimmed set, so coverage cannot be checked
            # against the full logical authority.
            logical = None
            log("  partial run: skipping full-population coverage comparison")

    log("replaying the population authority package from disk")
    replayed = rs.load_population_authority_package(
        Path(pkgdir),
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_population_root_sha256=summary[
            "population_raw_source_root_sha256"],
        expected_logical_root_sha256=summary["proved_logical_root_sha256"],
        expected_source_sha256=SOURCE_SHA,
        expected_row_count=summary["rows_proven"],
        logical=logical)
    log("  rows replayed %d" % replayed["rows_replayed"])
    log("  package root  %s" % replayed["package_root_sha256"])
    log("  population root recomputed from the reloaded registry: %s"
        % replayed["population_raw_source_root_sha256"])

    meta = replayed["metadata"]
    for flag in ("caller_supplied_values", "caller_supplied_handle",
                 "pathology_fields_read",
                 "numeric_confirmation_at8_accessed",
                 "donor_roles_computed", "eligible_donors_computed",
                 "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError("%s must be False in the package" % flag)
    rs.assert_no_pathology_in_artifact(meta["registry_fields"])
    log("  no pathology field appears in the emitted schema")

    report = {
        "schema": "JEPA_T0_B2_PRODUCTION_REPLAY_REPORT_V1",
        "package_dir": str(pkgdir),
        "partial": summary["partial"],
        "closure_is_population": summary["closure_is_population"],
        "rows_replayed": replayed["rows_replayed"],
        "package_root_sha256": replayed["package_root_sha256"],
        "population_raw_source_root_sha256": replayed[
            "population_raw_source_root_sha256"],
        "stored_equals_recomputed_equals_expected": True,
        "substrate_rebuilt": logical is not None or (
            store is not None and membership_path is not None),
        "pathology_fields_in_artifacts": False,
        "member_digests": {},
        "real_execution_ready": False,
    }
    for name in rs.PKG_MEMBERS:
        blob = (Path(pkgdir) / name).read_bytes()
        report["member_digests"][name] = {
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkgdir", required=True, type=Path)
    parser.add_argument("--store", type=Path, default=None)
    parser.add_argument("--membership", type=Path, default=None)
    parser.add_argument("--rebuild-substrate", action="store_true")
    args = parser.parse_args(argv)

    store = args.store if args.rebuild_substrate else None
    membership = args.membership if args.rebuild_substrate else None
    report = replay(pkgdir=args.pkgdir, store=store, membership_path=membership)
    print()
    print(json.dumps(report, indent=2, sort_keys=True))
    print()
    print("REPLAY PASS" if not report["partial"]
          else "REPLAY PASS (PARTIAL RUN, NOT POPULATION CLOSURE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
