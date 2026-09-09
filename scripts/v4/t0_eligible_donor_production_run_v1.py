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

import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_technical_completeness_authority_v1 as tc  # noqa: E402

EXPECTED_CANDIDATE_DONORS = 46
EXPECTED_POPULATION_ROWS = 20_804

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


def load_at8_availability(pkgdir: Path) -> dict:
    """The boolean availability flag, with a refusal of any numeric column."""
    records = _read_registry(pkgdir / AT8_REGISTRY)
    fields = tuple(records[0].keys()) if records else ()
    if fields != AT8_PERMITTED_FIELDS:
        raise AssertionError(
            "STOP_T0_AT8_AVAILABILITY_LANE_CARRIES_MORE_THAN_A_BOOLEAN: the "
            "registry fields are %r but the availability lane permits exactly "
            "%r" % (list(fields), list(AT8_PERMITTED_FIELDS)))
    eld.assert_no_pathology_in_artifact(fields)
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
            "package_root_sha256": _root_of(pkgdir, AT8_ROOT_FILE),
            "donors_covered": len(flags)}


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


def load_age_sex_presence(pkgdir: Path) -> dict:
    """Definedness of age and sex. Values are read here and emitted nowhere.

    The frozen predicate is `isfinite(age)` and `sex` non-null and non-empty,
    and that is what is evaluated: a blank, a non-numeric age, a NaN and an
    infinity are all absent, and no value is retained beyond this function.
    """
    records = _read_registry(pkgdir / AGE_SEX_REGISTRY)
    age_present, sex_present = {}, {}
    for record in records:
        donor = str(record["donor_id"])
        raw_age = str(record.get("age", "")).strip()
        try:
            age = float(raw_age)
        except (TypeError, ValueError):
            age = float("nan")
        age_present[donor] = bool(math.isfinite(age))
        raw_sex = record.get("sex")
        sex_present[donor] = bool(raw_sex is not None
                                  and str(raw_sex).strip() != ""
                                  and str(raw_sex).strip().lower() != "nan")
    return {"age_present": age_present, "sex_present": sex_present,
            "package_root_sha256": _root_of(pkgdir, AGE_SEX_ROOT_FILE),
            "donors_covered": len(age_present)}


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

    stamp("loading the AT8 availability authority (boolean only)")
    at8 = load_at8_availability(at8_pkg)
    stamp("  %d donors covered, root %s"
          % (at8["donors_covered"], at8["package_root_sha256"]))

    stamp("replaying the technical-completeness authority")
    complete = load_technical_completeness(tc_pkg)
    stamp("  %d donors, %d cells, completeness root %s"
          % (complete["donors_covered"], complete["cells_consumed"],
             complete["completeness_root_sha256"]))

    stamp("deriving age/sex definedness (values read, none emitted)")
    presence = load_age_sex_presence(age_sex_pkg)
    stamp("  %d donors covered, root %s"
          % (presence["donors_covered"], presence["package_root_sha256"]))

    donors = universe["donors"]
    projections = {
        "at8_available": (at8["flags"], at8["donors_covered"]),
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
        "at8_availability_package_root_sha256": at8["package_root_sha256"],
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
        at8_availability_independently_verified=True,
        expected_candidate_donors=EXPECTED_CANDIDATE_DONORS)

    summary.update({
        "schema": "JEPA_T0_ELIGIBLE_DONOR_RUN_SUMMARY_V1",
        "runner_code_sha256": code_sha256(
            "t0_eligible_donor_production_run_v1.py"),
        "authority_code_sha256": code_sha256(
            "t0_eligible_donor_authority_v1.py"),
        "code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
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
