"""Build the T0 eligible-donor authority over the real 46-donor universe.

Consumes four authenticated pathology-blind parents and nothing else:

    B2 population closure          the candidate donor universe
    AT8 availability authority     the boolean AT8_available, never a magnitude
    technical completeness         the boolean technical_complete
    age/sex authority              age and sex, read for definedness only

Two things about how the parents are consumed are worth stating plainly.

The AT8 availability authority covers a broader cohort than the T0 candidate
universe, so it is *projected* onto the universe here rather than in the
authority module. The projection is explicit and recorded: the metadata carries
each parent's full donor count beside the count actually used, so a reader can
see that a 46-donor decision was taken from an 84-donor parent. The authority
module still refuses an unprojected mapping, which is the last line of defence
against a parent keyed on the wrong cohort.

The age/sex authority carries values, and definedness cannot be decided without
reading them. So this runner reads age and sex and emits only whether each was
present. No age, no sex and no pathology value reaches the artifact. The frozen
predicate is matched exactly: `isfinite(age)` and `sex` non-null and non-empty.

Nothing here sets execution readiness, opens numeric AT8, or touches DEV or
SEALED.

Usage
-----
    python t0_eligible_donor_production_run_v1.py
        --outdir outputs/t0_eligible_donor_20260909
        --at8-pkg outputs/t0_at8_availability_20260908
        --tc-pkg outputs/t0_technical_completeness_20260909
        --age-sex-pkg outputs/t0_age_sex_20260908
        --population-pkg outputs/t0_b2_production_20260909
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_age_sex_authority_v1 as ages  # noqa: E402
import t0_at8_availability_authority_v1 as at8  # noqa: E402
import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402

EXPECTED_CANDIDATE_DONORS = 46
EXPECTED_POPULATION_ROWS = 20_804

# ---------------------------------------------------------------------------
# Expected parent identities, supplied from OUTSIDE the package directories.
#
# This is the R6 repair for the external reviewer's findings 1 and 2. Reading a
# package's own *_PACKAGE_ROOT_SHA256.txt and passing it back as the expected
# root lets the package attest to itself: a substituted package whose manifest
# and root file are rewritten to agree with its own altered bytes then passes.
# The committed red case demonstrates that the previous loaders accepted exactly
# that.
#
# Freezing the roots here puts them on the branch, where a reviewer reads them
# independently of any directory. A substituted parent is refused by identity.
# ---------------------------------------------------------------------------
AT8_EXPECTED_PACKAGE_ROOT = (
    "3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a")
AT8_EXPECTED_AVAILABILITY_ROOT = (
    "e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b")
AGE_SEX_EXPECTED_PACKAGE_ROOT = (
    "8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b")
AGE_SEX_EXPECTED_ROOT = (
    "95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff")
AGE_SEX_EXPECTED_SOURCE_SHA256 = (
    "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a")
AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET = (
    "59769cfda71860570eddc005ab7ee844e74d2dda8146245ddb930ade88af6345")

AT8_REGISTRY = "T0_AT8_AVAILABILITY_REGISTRY.csv"
AT8_ROOT_FILE = "T0_AT8_AVAILABILITY_PACKAGE_ROOT_SHA256.txt"
AGE_SEX_REGISTRY = "T0_AGE_SEX_REGISTRY.csv"
AGE_SEX_ROOT_FILE = "T0_AGE_SEX_PACKAGE_ROOT_SHA256.txt"

# The availability lane must not carry a magnitude. If the AT8 registry ever
# grows a numeric column, that is a specification failure to elevate, not a
# column to ignore.
AT8_PERMITTED_FIELDS = ("donor_id", "AT8_available")


def code_sha256(filename: str) -> str:
    """SHA-256 over the LF-normalized file content.

    This is the convention the rest of the lane uses, and the normalization is
    what makes it reproducible: the repository checks out CRLF on this platform,
    so hashing the worktree bytes would give a different digest than hashing the
    same content elsewhere. An earlier version of this function shelled out to
    `git hash-object`, which returns a 40-character SHA-1 in a SHA-1 repository
    and would have recorded that under a field named `_sha256`. The width is
    asserted so a wrong algorithm cannot be mislabelled again.
    """
    path = Path(__file__).resolve().parent / filename
    digest = hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()
    if len(digest) != 64:
        raise AssertionError("%s: %s yielded a %d-character digest, not SHA-256"
                             % (eld.STOP_PARENT_IDENTITY, filename,
                                len(digest)))
    return digest


def _read_registry(path: Path) -> list[dict[str, str]]:
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _root_of(pkgdir: Path, root_file: str) -> str:
    return (pkgdir / root_file).read_text(encoding="utf-8").strip()


def load_at8_availability(
        pkgdir: Path,
        *,
        expected_package_root_sha256: str = AT8_EXPECTED_PACKAGE_ROOT,
        expected_availability_root_sha256: str = AT8_EXPECTED_AVAILABILITY_ROOT,
) -> dict:
    """Replay the AT8 availability authority as a verified parent.

    The package is put through its own loader, which enumerates the directory,
    refuses a symlink or an unexpected member, captures every member's bytes
    exactly once, and checks both roots against values supplied from outside the
    directory. Nothing here re-reads a member after authentication.

    The verification outcome is *returned*, not asserted by the caller. The
    previous version of this runner set the availability authority's
    independent-verification flag to a hardcoded true, which the external
    reviewer correctly refused: a flag a caller sets is not evidence. A guard
    test now fails if that literal reappears anywhere in this module, prose
    included, so this docstring names the flag without spelling the assignment.
    """
    replayed = at8.load_availability_authority(
        Path(pkgdir),
        expected_package_root_sha256=str(expected_package_root_sha256),
        expected_availability_root_sha256=str(
            expected_availability_root_sha256))

    records = replayed["registry"]
    fields = tuple(records[0].keys()) if records else ()
    if fields != AT8_PERMITTED_FIELDS:
        raise AssertionError(
            "STOP_T0_AT8_AVAILABILITY_LANE_CARRIES_MORE_THAN_A_BOOLEAN: the "
            "registry fields are %r but the availability lane permits exactly "
            "%r" % (list(fields), list(AT8_PERMITTED_FIELDS)))
    eld.assert_no_pathology_in_artifact(fields)

    meta = replayed["metadata"]
    # The availability lane must still be a lane that never parsed a magnitude.
    for flag in ("numeric_at8_value_parsed", "numeric_at8_value_retained",
                 "numeric_at8_value_emitted", "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError(
                "STOP_T0_AT8_AVAILABILITY_LANE_CLAIMS_A_NUMERIC_VALUE: %s is %r"
                % (flag, meta.get(flag)))

    flags = {}
    for record in records:
        value = str(record["AT8_available"]).strip()
        if value not in ("True", "False"):
            raise AssertionError(
                "%s: AT8_available for %s is %r, and the availability lane "
                "carries booleans only"
                % (eld.STOP_NOT_BOOLEAN, record["donor_id"], value))
        flags[str(record["donor_id"])] = (value == "True")

    return {"flags": flags,
            "package_root_sha256": replayed["package_root_sha256"],
            "availability_root_sha256": replayed["availability_root_sha256"],
            "donors_covered": len(flags),
            "independently_verified": True,
            "expected_roots_supplied_externally": True,
            "verified_against": {
                "package_root_sha256": str(expected_package_root_sha256),
                "availability_root_sha256": str(
                    expected_availability_root_sha256)},
            "numeric_at8_value_parsed": False,
            "membership_donor_set_sha256": meta.get(
                "membership_donor_set_sha256"),
            # The endpoint identity, surfaced from the verified parent so a
            # consumer need not hand-write it. The availability authority
            # recorded which column it tested for missingness without ever
            # parsing a magnitude from it.
            "at8_endpoint_identity": meta.get("at8_field"),
            "donor_id_field": meta.get("donor_id_field"),
            "metadata": meta}


def load_technical_completeness(pkgdir: Path) -> dict:
    """The technical-completeness authority, replayed rather than read."""
    summary = json.loads(
        (pkgdir / "T0_TECHNICAL_COMPLETENESS_RUN_SUMMARY.json").read_text(
            encoding="utf-8"))
    replayed = tc.load_authority(
        pkgdir,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_completeness_root_sha256=summary["completeness_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"])
    meta = replayed["metadata"]
    tc.assert_production_run_status_not_retired(meta.get("production_run_status"))
    if meta.get("production_run_status") != tc.PRODUCTION_RUN_STATUS_POPULATION:
        raise AssertionError(
            "STOP_T0_ELIGIBLE_DONOR_TECHNICAL_COMPLETENESS_NOT_OVER_THE_"
            "POPULATION: the package records %r"
            % meta.get("production_run_status"))
    flags = {}
    cells = 0
    for record in replayed["records"]:
        value = str(record["technical_complete"]).strip()
        if value not in ("True", "False"):
            raise AssertionError(
                "%s: technical_complete for %s is %r"
                % (eld.STOP_NOT_BOOLEAN, record["donor_id"], value))
        flags[str(record["donor_id"])] = (value == "True")
        cells += int(record["cells"])
    if cells != EXPECTED_POPULATION_ROWS:
        raise AssertionError(
            "STOP_T0_ELIGIBLE_DONOR_TECHNICAL_COMPLETENESS_CELL_COUNT: %d "
            "cells consumed, expected %d" % (cells, EXPECTED_POPULATION_ROWS))
    return {"flags": flags,
            "package_root_sha256": summary["package_root_sha256"],
            "completeness_root_sha256": summary["completeness_root_sha256"],
            "cells_consumed": cells,
            "donors_covered": len(flags)}


def load_age_sex_presence(
        pkgdir: Path,
        *,
        expected_package_root_sha256: str = AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256: str = AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256: str = AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256: str = (
            AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET),
) -> dict:
    """Replay the age/sex authority as a verified parent, then emit presence only.

    The package goes through its own loader, bound to an expected package root,
    age/sex root, source digest and candidate donor set -- all supplied from
    outside the directory. Only after that are the presence booleans derived.

    One consequence is worth stating rather than leaving implicit. The age/sex
    authority parses through `exact_age` and `exact_sex`, which *refuse* a
    non-finite age or a sex outside the frozen vocabulary. So a successful replay
    already proves every donor it carries has a defined age and sex, and
    `age_present` and `sex_present` come back True for every donor by
    construction. That is not the predicate becoming vacuous: it is the predicate
    being enforced upstream, where a missing covariate makes the parent refuse to
    load rather than quietly producing an ineligible donor. It is the same
    fail-closed rule the eligible-donor authority applies to coverage gaps.

    Values are read inside this function and emitted nowhere.
    """
    replayed = ages.load_authority(
        Path(pkgdir),
        expected_package_root_sha256=str(expected_package_root_sha256),
        expected_age_sex_root_sha256=str(expected_age_sex_root_sha256),
        expected_source_sha256=str(expected_source_sha256),
        expected_candidate_donor_set_sha256=str(
            expected_candidate_donor_set_sha256))

    meta = replayed["metadata"]
    for flag in ("pathology_fields_in_emitted_schema",
                 "numeric_at8_value_read", "numeric_at8_value_emitted",
                 "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError(
                "STOP_T0_AGE_SEX_PARENT_CLAIMS_A_FORBIDDEN_FIELD: %s is %r"
                % (flag, meta.get(flag)))

    age_present, sex_present = {}, {}
    for row in replayed["rows"]:
        donor = str(row["donor_id"])
        # The parent already refused anything non-finite or out-of-vocabulary,
        # so this re-evaluates the frozen predicate on values it has proven.
        age_present[donor] = bool(math.isfinite(float(row["age"])))
        sex = row["sex"]
        sex_present[donor] = bool(sex is not None
                                  and str(sex).strip() != ""
                                  and str(sex).strip().lower() != "nan")

    return {"age_present": age_present, "sex_present": sex_present,
            "package_root_sha256": replayed["package_root_sha256"],
            "age_sex_root_sha256": replayed["age_sex_root_sha256"],
            "donors_covered": len(age_present),
            "independently_verified": True,
            "expected_roots_supplied_externally": True,
            "verified_against": {
                "package_root_sha256": str(expected_package_root_sha256),
                "age_sex_root_sha256": str(expected_age_sex_root_sha256),
                "source_sha256": str(expected_source_sha256),
                "candidate_donor_set_sha256": str(
                    expected_candidate_donor_set_sha256)},
            "presence_is_proven_upstream_by_exact_age_and_exact_sex": True,
            "covariate_values_emitted": False}


def load_candidate_universe(population_pkg: Path) -> dict:
    """The candidate donor universe, taken from the proven B2 population."""
    summary = json.loads(
        (population_pkg / "T0_B2_PRODUCTION_RUN_SUMMARY.json").read_text(
            encoding="utf-8"))
    if summary["partial"]:
        raise AssertionError(
            "the population package is a partial smoke run and does not close "
            "the candidate universe")
    records = _read_registry(population_pkg
                             / "T0_RAW_SOURCE_POPULATION_REGISTRY.csv")
    donors = sorted({str(r["donor_id"]) for r in records})
    if len(records) != int(summary["rows_proven"]):
        raise AssertionError("the registry holds %d rows but the run proved %d"
                             % (len(records), summary["rows_proven"]))
    if len(donors) != EXPECTED_CANDIDATE_DONORS:
        raise AssertionError("%d donors in the population, expected %d"
                             % (len(donors), EXPECTED_CANDIDATE_DONORS))
    return {"donors": donors,
            "rows_proven": int(summary["rows_proven"]),
            "population_raw_source_root_sha256": summary[
                "population_raw_source_root_sha256"],
            "package_root_sha256": summary["package_root_sha256"]}


def _project(mapping: dict, universe: list[str], *, name: str) -> dict:
    """Restrict a parent onto the universe, requiring it to cover all of it.

    Missing coverage is a STOP raised here with the parent named, before the
    authority module sees a mapping that would look like ineligibility.
    """
    missing = [d for d in universe if d not in mapping]
    if missing:
        raise AssertionError(
            "%s: %s covers %d of %d candidate donors; missing e.g. %s"
            % (eld.STOP_PARENT_COVERAGE, name, len(universe) - len(missing),
               len(universe), missing[:5]))
    return {d: mapping[d] for d in universe}


def run(*, outdir: Path, at8_pkg: Path, tc_pkg: Path, age_sex_pkg: Path,
        population_pkg: Path, log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%7.1fs] %s" % (time.time() - started, message))

    stamp("loading the candidate donor universe from the proven B2 population")
    universe = load_candidate_universe(population_pkg)
    stamp("  %d donors over %d proven rows"
          % (len(universe["donors"]), universe["rows_proven"]))

    stamp("replaying the AT8 availability authority (boolean only)")
    at8_parent = load_at8_availability(at8_pkg)
    stamp("  %d donors covered" % at8_parent["donors_covered"])
    stamp("    package root      %s (verified against a frozen expectation)"
          % at8_parent["package_root_sha256"])
    stamp("    availability root %s (verified against a frozen expectation)"
          % at8_parent["availability_root_sha256"])

    stamp("replaying the technical-completeness authority")
    complete = load_technical_completeness(tc_pkg)
    stamp("  %d donors, %d cells, completeness root %s"
          % (complete["donors_covered"], complete["cells_consumed"],
             complete["completeness_root_sha256"]))

    stamp("replaying the age/sex authority, then deriving definedness only")
    presence = load_age_sex_presence(age_sex_pkg)
    stamp("  %d donors covered" % presence["donors_covered"])
    stamp("    package root %s (verified against a frozen expectation)"
          % presence["package_root_sha256"])
    stamp("    age/sex root %s (verified against a frozen expectation)"
          % presence["age_sex_root_sha256"])
    stamp("    presence is proven upstream by exact_age and exact_sex")

    donors = universe["donors"]
    projections = {
        "at8_available": (at8_parent["flags"],
                          at8_parent["donors_covered"]),
        "technical_complete": (complete["flags"], complete["donors_covered"]),
        "age_present": (presence["age_present"], presence["donors_covered"]),
        "sex_present": (presence["sex_present"], presence["donors_covered"]),
    }
    projected = {name: _project(mapping, donors, name=name)
                 for name, (mapping, _n) in projections.items()}
    stamp("projected every parent onto the %d-donor universe" % len(donors))
    for name, (_m, covered) in sorted(projections.items()):
        stamp("  %-20s %d covered -> %d used" % (name, covered, len(donors)))

    stamp("applying the frozen eligibility predicate, then the frozen split")
    rows = eld.derive_eligible_donors(candidate_donors=donors, **projected)
    eligible = [r for r in rows if r["eligible"]]
    stamp("  eligible %d of %d" % (len(eligible), len(rows)))
    for role in ("CONFIRMATION", "DISCOVERY", "INELIGIBLE"):
        stamp("  %-13s %d" % (role, sum(1 for r in rows
                                        if r["donor_role"] == role)))

    # The two frozen role paths are compared on the real donor set rather than
    # argued about. The result is diagnostic and is recorded either way.
    divergence = eld.split_rule_divergence(
        donors, [r["donor_id"] for r in eligible])
    stamp("the two frozen role paths agree: %s" % divergence["paths_agree"])
    if not divergence["paths_agree"]:
        stamp("  ineligible donors inside the full-support top 18: %s"
              % divergence["ineligible_donors_inside_support_top_18"])

    parents = {
        "at8_availability_package_root_sha256": at8_parent[
            "package_root_sha256"],
        "at8_availability_root_sha256": at8_parent["availability_root_sha256"],
        "age_sex_root_sha256": presence["age_sex_root_sha256"],
        "technical_completeness_root_sha256": complete[
            "completeness_root_sha256"],
        "technical_completeness_package_root_sha256": complete[
            "package_root_sha256"],
        "age_sex_package_root_sha256": presence["package_root_sha256"],
        "population_raw_source_root_sha256": universe[
            "population_raw_source_root_sha256"],
        "b2_authority_package_root_sha256": universe["package_root_sha256"],
    }

    stamp("writing the eligible-donor authority package")
    summary = eld.build_authority(
        outdir, rows=rows, parents=parents,
        derivation_code_sha256=code_sha256("t0_eligible_donor_authority_v1.py"),
        # Not a literal: this is what the replay above actually established.
        at8_availability_independently_verified=bool(
            at8_parent["independently_verified"]),
        expected_candidate_donors=EXPECTED_CANDIDATE_DONORS)

    summary.update({
        "schema": "JEPA_T0_ELIGIBLE_DONOR_RUN_SUMMARY_V1",
        "runner_code_sha256": code_sha256(
            "t0_eligible_donor_production_run_v1.py"),
        "authority_code_sha256": code_sha256(
            "t0_eligible_donor_authority_v1.py"),
        "code_byte_semantics": "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES",
        "parents": parents,
        "parent_donor_coverage": {name: int(covered)
                                  for name, (_m, covered)
                                  in sorted(projections.items())},
        "candidate_universe_source": "B2_PROVEN_POPULATION_RAW_SOURCE",
        "population_rows_proven": universe["rows_proven"],
        "technical_completeness_cells_consumed": complete["cells_consumed"],
        "frozen_role_path_agreement": divergence,
        "numeric_at8_value_read": False,
        "numeric_covariate_values_emitted": False,
        "real_execution_ready": False,
        "parent_replay": {
            "at8_availability": {
                "independently_verified": at8_parent["independently_verified"],
                "expected_roots_supplied_externally": at8_parent[
                    "expected_roots_supplied_externally"],
                "verified_against": at8_parent["verified_against"],
            },
            "age_sex": {
                "independently_verified": presence["independently_verified"],
                "expected_roots_supplied_externally": presence[
                    "expected_roots_supplied_externally"],
                "verified_against": presence["verified_against"],
                "presence_is_proven_upstream": presence[
                    "presence_is_proven_upstream_by_exact_age_and_exact_sex"],
            },
            "technical_completeness": {
                "replayed_through_its_own_loader": True,
                "production_status_required":
                    tc.PRODUCTION_RUN_STATUS_POPULATION,
            },
            "b2_population": {
                "registry_row_count_checked_against_rows_proven": True,
            },
        },
        "elapsed_seconds": round(time.time() - started, 1),
    })
    path = Path(outdir) / "T0_ELIGIBLE_DONOR_RUN_SUMMARY.json"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    stamp("  eligible donor root  %s" % summary["eligible_donor_root_sha256"])
    stamp("  donor role root      %s" % summary["donor_role_root_sha256"])
    stamp("  parent contract root %s" % summary["parent_contract_root_sha256"])
    stamp("  package root         %s" % summary["package_root_sha256"])
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--tc-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    args = parser.parse_args(argv)

    summary = run(outdir=args.outdir, at8_pkg=args.at8_pkg, tc_pkg=args.tc_pkg,
                  age_sex_pkg=args.age_sex_pkg,
                  population_pkg=args.population_pkg)
    print()
    print(json.dumps(summary, indent=2, sort_keys=True))
    print()
    print("ELIGIBLE DONOR AUTHORITY WRITTEN. real_execution_ready=False.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
