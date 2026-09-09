"""Replay verifier for the T0 eligible-donor authority package.

Reloads the written package and re-derives everything it claims, then rebuilds
the eligibility decision from the parent authorities themselves so the package is
checked against freshly derived inputs rather than against its own record.

Requires:

    stored == recomputed == expected for the eligible-donor root, the donor-role
      root, the parent contract root and the package root
    the candidate universe is exactly the 46 proven B2 donors
    no missing donors, no duplicate donor rows
    the predicate holds on every row, and roles follow the frozen rule
    the eligible count carries 18 CONFIRMATION and at least 18 DISCOVERY
    no pathology field and no covariate value in any artifact
    real_execution_ready is False

It also re-derives the decision independently: the parents are loaded again,
projected again, and run through the frozen predicate and split again, and the
resulting roots must equal the stored ones. A package that only agrees with
itself has not been replayed.

Usage
-----
    python t0_eligible_donor_replay_v1.py --pkgdir <dir>
        --at8-pkg <dir> --tc-pkg <dir> --age-sex-pkg <dir>
        --population-pkg <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as runner  # noqa: E402

EXPECTED_CANDIDATE_DONORS = 46
EXPECTED_POPULATION_ROWS = 20_804

# No artifact this authority writes may contain a donor covariate value. The
# registry is booleans, identifiers and hex digests, and this is checked by
# reading the bytes rather than by trusting the writer.
#
# Note the sex labels only: a substring test for "age" would match the
# `age_present` field name, which is exactly the boolean the design does want.
# Age is caught structurally instead, by requiring every non-identifier cell to
# be one of the two boolean spellings.
FORBIDDEN_IN_ARTIFACT = ("Female", "Male", "female", "male", "F,", "M,")
BOOLEAN_CELLS = ("True", "False")


def replay(*, pkgdir: Path, at8_pkg: Path, tc_pkg: Path, age_sex_pkg: Path,
           population_pkg: Path, log=print) -> dict:
    summary_path = Path(pkgdir) / "T0_ELIGIBLE_DONOR_RUN_SUMMARY.json"
    if not summary_path.is_file():
        raise AssertionError("no run summary at %s" % summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    log("re-deriving the eligibility decision from the parent authorities")
    universe = runner.load_candidate_universe(Path(population_pkg))
    at8 = runner.load_at8_availability(Path(at8_pkg))
    complete = runner.load_technical_completeness(Path(tc_pkg))
    presence = runner.load_age_sex_presence(Path(age_sex_pkg))
    donors = universe["donors"]
    if len(donors) != EXPECTED_CANDIDATE_DONORS:
        raise AssertionError("%d candidate donors, expected %d"
                             % (len(donors), EXPECTED_CANDIDATE_DONORS))
    if complete["cells_consumed"] != EXPECTED_POPULATION_ROWS:
        raise AssertionError("technical completeness consumed %d cells, "
                             "expected %d" % (complete["cells_consumed"],
                                              EXPECTED_POPULATION_ROWS))
    log("  %d candidate donors over %d proven rows; %d cells complete"
        % (len(donors), universe["rows_proven"], complete["cells_consumed"]))

    projected = {
        name: runner._project(mapping, donors, name=name)
        for name, mapping in (
            ("at8_available", at8["flags"]),
            ("technical_complete", complete["flags"]),
            ("age_present", presence["age_present"]),
            ("sex_present", presence["sex_present"]))}
    rederived = eld.derive_eligible_donors(candidate_donors=donors,
                                           **projected)
    rederived_root = eld.eligible_donor_root(rederived)
    rederived_role_root = eld.donor_role_root(rederived)
    log("  re-derived eligible donor root %s" % rederived_root)
    log("  re-derived donor role root     %s" % rederived_role_root)

    log("replaying the package from disk")
    replayed = eld.load_authority(
        Path(pkgdir),
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_eligible_donor_root_sha256=summary[
            "eligible_donor_root_sha256"],
        expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"],
        expected_candidate_donors=donors)
    rows = replayed["rows"]
    meta = replayed["metadata"]

    # stored == recomputed == expected, in all three positions.
    for name, stored, recomputed, expected in (
            ("eligible donor root", meta["eligible_donor_root_sha256"],
             replayed["eligible_donor_root_sha256"], rederived_root),
            ("donor role root", meta["donor_role_root_sha256"],
             replayed["donor_role_root_sha256"], rederived_role_root)):
        if not (stored == recomputed == expected):
            raise AssertionError(
                "%s: stored %s, recomputed %s, re-derived from parents %s"
                % (name, stored, recomputed, expected))
        log("  %s: stored == recomputed == re-derived (%s)" % (name, stored))

    recomputed_parents = eld.parent_contract_root(meta["parents"])
    if recomputed_parents != summary["parent_contract_root_sha256"]:
        raise AssertionError("parent contract root %s, summary %s"
                             % (recomputed_parents,
                                summary["parent_contract_root_sha256"]))
    # And the parent identities are the ones actually on disk right now.
    for field, produced in (
            ("at8_availability_package_root_sha256",
             at8["package_root_sha256"]),
            # Added in R6: the two parent identities the runner now verifies
            # against frozen external expectations must also be bound into the
            # package and re-checked here, or the strengthening would not be
            # observable from the artifact.
            ("at8_availability_root_sha256", at8["availability_root_sha256"]),
            ("age_sex_root_sha256", presence["age_sex_root_sha256"]),
            ("technical_completeness_root_sha256",
             complete["completeness_root_sha256"]),
            ("technical_completeness_package_root_sha256",
             complete["package_root_sha256"]),
            ("age_sex_package_root_sha256", presence["package_root_sha256"]),
            ("population_raw_source_root_sha256",
             universe["population_raw_source_root_sha256"]),
            ("b2_authority_package_root_sha256",
             universe["package_root_sha256"])):
        if str(meta["parents"].get(field)) != str(produced):
            raise AssertionError(
                "%s: the package records %r but the parent on disk is %r"
                % (eld.STOP_PARENT_IDENTITY, meta["parents"].get(field),
                   produced))
    for name, parent in (("AT8 availability", at8), ("age/sex", presence)):
        if not parent.get("independently_verified"):
            raise AssertionError(
                "%s: the %s parent was not independently verified"
                % (eld.STOP_PARENT_IDENTITY, name))
        if not parent.get("expected_roots_supplied_externally"):
            raise AssertionError(
                "%s: the %s parent's expected roots did not come from outside "
                "its own directory" % (eld.STOP_PARENT_IDENTITY, name))
    if presence.get("covariate_values_emitted") is not False:
        raise AssertionError("%s: the age/sex parent emitted covariate values"
                             % eld.STOP_FIELD_SCHEMA)
    log("  every parent identity matches the authority on disk")
    log("  both replayed parents verified against frozen external roots")

    donor_ids = [r["donor_id"] for r in rows]
    if len(donor_ids) != len(set(donor_ids)):
        duplicates = sorted({d for d in donor_ids if donor_ids.count(d) > 1})
        raise AssertionError("duplicate donor rows: %s" % duplicates)
    if set(donor_ids) != set(donors):
        raise AssertionError(
            "donor set differs from the proven B2 population: only-here %s, "
            "only-B2 %s" % (sorted(set(donor_ids) - set(donors)),
                            sorted(set(donors) - set(donor_ids))))
    log("  %d donor rows, no duplicates, set matches the B2 population"
        % len(rows))

    eld.assert_predicate_holds_on_every_row(rows)
    eld.assert_roles_agree_with_frozen_rule(rows)
    eligible = [r for r in rows if r["eligible"]]
    confirmation = [r for r in rows if r["donor_role"] == "CONFIRMATION"]
    discovery = [r for r in rows if r["donor_role"] == "DISCOVERY"]
    if len(confirmation) != eld.CONFIRMATION_DONORS:
        raise AssertionError("%d CONFIRMATION donors, frozen design needs %d"
                             % (len(confirmation), eld.CONFIRMATION_DONORS))
    if len(discovery) < eld.MINIMUM_DISCOVERY_DONORS:
        raise AssertionError("%d DISCOVERY donors, frozen minimum %d"
                             % (len(discovery), eld.MINIMUM_DISCOVERY_DONORS))
    log("  eligible %d; CONFIRMATION %d; DISCOVERY %d; INELIGIBLE %d"
        % (len(eligible), len(confirmation), len(discovery),
           len(rows) - len(eligible)))

    # No covariate value, and no pathology field, anywhere in the bytes.
    for name in eld.MEMBERS:
        blob = (Path(pkgdir) / name).read_bytes()
        text = blob.decode("utf-8")
        for needle in FORBIDDEN_IN_ARTIFACT:
            if needle in text:
                raise AssertionError(
                    "%s: %s contains %r, and no donor covariate value may "
                    "appear in this authority"
                    % (eld.STOP_FIELD_SCHEMA, name, needle))
    # Age is excluded structurally: every registry cell other than the donor id,
    # the split hash and the role must be a boolean spelling, so no number can
    # be carried at all.
    registry_text = (Path(pkgdir) / eld.REGISTRY).read_text(encoding="utf-8")
    header = registry_text.splitlines()[0].split(",")
    if header != list(eld.REGISTRY_FIELDS):
        raise AssertionError("%s: registry header is %r, expected %r"
                             % (eld.STOP_FIELD_SCHEMA, header,
                                list(eld.REGISTRY_FIELDS)))
    for line in registry_text.splitlines()[1:]:
        cells = line.split(",")
        for position, cell in enumerate(cells):
            if header[position] in ("donor_id", "split_hash", "donor_role"):
                continue
            if cell not in BOOLEAN_CELLS:
                raise AssertionError(
                    "%s: %s carries %r for %s, and only %r are permitted"
                    % (eld.STOP_FIELD_SCHEMA, line.split(",")[0], cell,
                       header[position], list(BOOLEAN_CELLS)))
    eld.assert_no_pathology_in_artifact(eld.REGISTRY_FIELDS)
    for flag in ("numeric_at8_value_read", "numeric_at8_value_emitted",
                 "numeric_covariate_values_emitted",
                 "pathology_fields_in_artifact", "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError("%s must be False in the package" % flag)
    log("  no covariate value, no pathology field, real_execution_ready False")

    divergence = eld.split_rule_divergence(donors,
                                           [r["donor_id"] for r in eligible])
    log("  the two frozen role paths agree: %s" % divergence["paths_agree"])

    report = {
        "schema": "JEPA_T0_ELIGIBLE_DONOR_REPLAY_REPORT_V1",
        "package_dir": str(pkgdir),
        "candidate_donors": len(rows),
        "eligible_donors": len(eligible),
        "confirmation_donors": len(confirmation),
        "discovery_donors": len(discovery),
        "ineligible_donors": sorted(r["donor_id"] for r in rows
                                    if not r["eligible"]),
        "eligible_donor_root_sha256": replayed["eligible_donor_root_sha256"],
        "donor_role_root_sha256": replayed["donor_role_root_sha256"],
        "parent_contract_root_sha256": recomputed_parents,
        "package_root_sha256": replayed["package_root_sha256"],
        "rederived_from_parents": True,
        "parents_independently_replayed": {
            "at8_availability": {
                "package_root_sha256": at8["package_root_sha256"],
                "availability_root_sha256": at8["availability_root_sha256"],
                "verified_against": at8["verified_against"],
            },
            "age_sex": {
                "package_root_sha256": presence["package_root_sha256"],
                "age_sex_root_sha256": presence["age_sex_root_sha256"],
                "verified_against": presence["verified_against"],
                "presence_proven_upstream": presence[
                    "presence_is_proven_upstream_by_exact_age_and_exact_sex"],
            },
        },
        "stored_equals_recomputed_equals_rederived": True,
        "donor_set_matches_b2_population": True,
        "duplicate_donor_rows": False,
        "predicate_holds_on_every_row": True,
        "roles_follow_the_frozen_rule": True,
        "pathology_fields_in_artifacts": False,
        "covariate_values_in_artifacts": False,
        "real_execution_ready": False,
        "frozen_role_path_agreement": divergence,
        "population_rows_proven": universe["rows_proven"],
        "technical_completeness_cells_consumed": complete["cells_consumed"],
        "member_digests": {},
    }
    for name in eld.MEMBERS:
        blob = (Path(pkgdir) / name).read_bytes()
        report["member_digests"][name] = {
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkgdir", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--tc-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    report = replay(pkgdir=args.pkgdir, at8_pkg=args.at8_pkg,
                    tc_pkg=args.tc_pkg, age_sex_pkg=args.age_sex_pkg,
                    population_pkg=args.population_pkg)
    print()
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report is not None:
        with io.open(args.report, "w", encoding="utf-8", newline="\n") as h:
            h.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print()
    print("ELIGIBLE DONOR AUTHORITY REPLAY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
