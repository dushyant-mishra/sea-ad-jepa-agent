"""Stage A estimability preflight over the real eligible donor set.

R6 item 3: the pre-real-T0 donor-role / nuisance-rank / estimability preflight,
run without numeric AT8.

What it answers
---------------
Whether the frozen parent nuisance design `[1, age_c, age_c^2, sex]` is full rank
on the roles the eligible-donor authority assigned, and on every discovery LOODO
fold. The LOODO folds are the point: the frozen discovery fit refits with each
donor held out, so a design that is full rank on all 28 discovery donors can
still be deficient in one fold, and that fold would fail during fitting rather
than here.

This is Stage A only. Stages B and C need STATE_SCORE, IMMUNE_FRACTION and
TAIL_PREVALENCE, which do not exist before real T0 runs, and supplying a response
to a blind check is refused by the preflight itself.

Why it is pathology-blind
-------------------------
Estimability is a property of the design matrix. No response, no pathology value
and no AT8 magnitude enters. Age and sex *values* are required — rank cannot be
computed without them — and they come from the replayed age/sex authority bound
to frozen external roots. The emitted report carries ranks and roots, never a
donor covariate value.

What a failure means
--------------------
`STOP_T0_DESIGN_NOT_ESTIMABLE`, and it is a design failure to elevate, not a
biological NOT_MEASURABLE. In particular a single-sex role set makes
`nuisance_design` refuse, and the frozen split must not be altered to rescue it.

Usage
-----
    python t0_estimability_preflight_production_run_v1.py
        --outdir outputs/t0_estimability_preflight_20260909
        --eligible-pkg outputs/t0_eligible_donor_20260909
        --age-sex-pkg outputs/t0_age_sex_20260908
        --at8-pkg outputs/t0_at8_availability_20260908
        --tc-pkg outputs/t0_technical_completeness_20260909
        --population-pkg outputs/t0_b2_production_20260909
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

import t0_age_sex_authority_v1 as ages  # noqa: E402
import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as ed_runner  # noqa: E402
import t0_estimability_preflight_v1 as pre  # noqa: E402

SCHEMA = "JEPA_T0_ESTIMABILITY_PREFLIGHT_PRODUCTION_V1"
REPORT = "T0_ESTIMABILITY_PREFLIGHT_STAGE_A_REPORT.json"
ROOT_FILE = "T0_ESTIMABILITY_PREFLIGHT_PACKAGE_ROOT_SHA256.txt"

EXPECTED_CONFIRMATION = 18
MINIMUM_DISCOVERY = 18

STOP_ROLE_SET = "STOP_T0_PREFLIGHT_ROLE_SET_NOT_FROM_THE_ELIGIBLE_AUTHORITY"
STOP_COVARIATE_LEAK = "STOP_T0_PREFLIGHT_COVARIATE_VALUE_IN_EMITTED_REPORT"
STOP_RESPONSE = "STOP_T0_PREFLIGHT_RESPONSE_OR_PATHOLOGY_SUPPLIED"

# No emitted field may carry a covariate value or a pathology endpoint. Ranks,
# counts, donor identifiers and digests only.
FORBIDDEN_REPORT_SUBSTRINGS = ("Female", "Male", "at8", "AT8", "braak",
                               "cerad", "thal", "ptau", "6e10")


def code_sha256(filename: str) -> str:
    """SHA-256 over the LF-normalized file content, as the lane computes it.

    Deliberately not called a Git blob digest: a Git blob digest frames content
    as b"blob <len>\\0" + content and is a different value. See the provenance
    finding in the pre-real-T0 review package.
    """
    path = Path(__file__).resolve().parent / filename
    digest = hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()
    if len(digest) != 64:
        raise AssertionError("%s yielded a %d-character digest, not SHA-256"
                             % (filename, len(digest)))
    return digest


def load_roles(eligible_pkg: Path, *, universe) -> dict:
    """Read the role assignment from the replayed eligible-donor authority.

    The roles are not recomputed here from a rule of this module's own: they are
    taken from the authority that owns them, after that authority has been
    replayed and its roots re-derived from its parents.
    """
    summary = json.loads(
        (eligible_pkg / "T0_ELIGIBLE_DONOR_RUN_SUMMARY.json").read_text(
            encoding="utf-8"))
    replayed = eld.load_authority(
        eligible_pkg,
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_eligible_donor_root_sha256=summary[
            "eligible_donor_root_sha256"],
        expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"],
        expected_candidate_donors=universe)
    rows = replayed["rows"]
    eld.assert_predicate_holds_on_every_row(rows)
    eld.assert_roles_agree_with_frozen_rule(rows)

    roles: dict[str, list[str]] = {"CONFIRMATION": [], "DISCOVERY": [],
                                   "INELIGIBLE": []}
    for row in rows:
        roles[str(row["donor_role"])].append(str(row["donor_id"]))
    if len(roles["CONFIRMATION"]) != EXPECTED_CONFIRMATION:
        raise AssertionError("%s: %d CONFIRMATION donors, frozen design needs %d"
                             % (STOP_ROLE_SET, len(roles["CONFIRMATION"]),
                                EXPECTED_CONFIRMATION))
    if len(roles["DISCOVERY"]) < MINIMUM_DISCOVERY:
        raise AssertionError("%s: %d DISCOVERY donors, frozen minimum %d"
                             % (STOP_ROLE_SET, len(roles["DISCOVERY"]),
                                MINIMUM_DISCOVERY))
    return {"roles": roles,
            "eligible_donor_root_sha256": replayed[
                "eligible_donor_root_sha256"],
            "donor_role_root_sha256": replayed["donor_role_root_sha256"],
            "package_root_sha256": replayed["package_root_sha256"]}


def load_covariates(age_sex_pkg: Path) -> dict:
    """Age and sex values from the replayed age/sex authority.

    Values are needed here, because rank is not computable without them. They
    are read from a parent bound to frozen external roots, they stay inside this
    process, and nothing derived from them beyond a rank reaches the report.
    """
    replayed = ages.load_authority(
        Path(age_sex_pkg),
        expected_package_root_sha256=ed_runner.AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256=ed_runner.AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256=ed_runner.AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256=(
            ed_runner.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET))
    meta = replayed["metadata"]
    if meta.get("pathology_fields_in_emitted_schema") is not False:
        raise AssertionError("%s: the age/sex parent declares pathology fields"
                             % STOP_RESPONSE)
    sex_map = {"Female": 0.0, "Male": 1.0}
    records = {}
    for row in replayed["rows"]:
        donor = str(row["donor_id"])
        sex = str(row["sex"])
        if sex not in sex_map:
            raise AssertionError(
                "%s: %s carries sex %r, which is outside the frozen binary "
                "encoding" % (pre.STOP_SEX_NOT_BINARY, donor, sex))
        records[donor] = {"age": float(row["age"]), "sex": sex_map[sex]}
    return {"records": records,
            "age_sex_root_sha256": replayed["age_sex_root_sha256"],
            "package_root_sha256": replayed["package_root_sha256"],
            "sex_encoding": dict(sorted(sex_map.items()))}


def assert_no_covariate_value_in_report(report) -> bool:
    """The emitted report carries ranks and identities, never a covariate value."""
    text = json.dumps(report, sort_keys=True)
    for needle in FORBIDDEN_REPORT_SUBSTRINGS:
        if needle in text:
            raise AssertionError("%s: the report contains %r"
                                 % (STOP_COVARIATE_LEAK, needle))
    return True


def run(*, outdir: Path, eligible_pkg: Path, age_sex_pkg: Path, at8_pkg: Path,
        tc_pkg: Path, population_pkg: Path, log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%6.1fs] %s" % (time.time() - started, message))

    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("output directory must be absent or empty: %s"
                             % out)

    stamp("replaying the parent chain")
    universe = ed_runner.load_candidate_universe(Path(population_pkg))
    at8_parent = ed_runner.load_at8_availability(Path(at8_pkg))
    complete = ed_runner.load_technical_completeness(Path(tc_pkg))
    stamp("  %d candidate donors, %d cells complete, AT8 verified: %s"
          % (len(universe["donors"]), complete["cells_consumed"],
             at8_parent["independently_verified"]))

    stamp("reading the role assignment from the eligible-donor authority")
    assigned = load_roles(Path(eligible_pkg), universe=universe["donors"])
    roles = assigned["roles"]
    stamp("  CONFIRMATION %d   DISCOVERY %d   INELIGIBLE %d"
          % (len(roles["CONFIRMATION"]), len(roles["DISCOVERY"]),
             len(roles["INELIGIBLE"])))

    stamp("replaying the age/sex authority for design values")
    covariates = load_covariates(Path(age_sex_pkg))
    records = covariates["records"]
    stamp("  %d donor records; values stay in-process" % len(records))

    # Authoritative order: donor id ascending by UTF-8 bytes, as the frozen role
    # authority orders each role before building its design.
    def order(donors):
        return tuple(sorted((str(d) for d in donors),
                            key=lambda value: value.encode("utf-8")))

    discovery_order = order(roles["DISCOVERY"])
    confirmation_order = order(roles["CONFIRMATION"])
    for name, ids in (("DISCOVERY", discovery_order),
                      ("CONFIRMATION", confirmation_order)):
        missing = [d for d in ids if d not in records]
        if missing:
            raise AssertionError(
                "%s: the age/sex authority does not cover %d %s donors: %s"
                % (eld.STOP_PARENT_COVERAGE, len(missing), name, missing[:5]))

    discovery_records = {d: records[d] for d in discovery_order}
    confirmation_records = {d: records[d] for d in confirmation_order}
    fields = ("age", "sex")
    discovery_root = pre.records_root(discovery_order, discovery_records, fields)
    confirmation_root = pre.records_root(confirmation_order,
                                         confirmation_records, fields)

    stamp("running Stage A: parent nuisance rank on both roles and every "
          "DISCOVERY LOODO fold")
    stage_a = pre.stage_a_parent_nuisance(
        discovery_order=discovery_order,
        discovery_records=discovery_records,
        expected_discovery_records_root_sha256=discovery_root,
        confirmation_order=confirmation_order,
        confirmation_records=confirmation_records,
        expected_confirmation_records_root_sha256=confirmation_root)
    pre.assert_stage_order([stage_a])

    checks = stage_a["checks"]
    stamp("  DISCOVERY nuisance rank      %d" % checks["DISCOVERY"])
    stamp("  CONFIRMATION nuisance rank   %d" % checks["CONFIRMATION"])
    stamp("  DISCOVERY LOODO folds        %d, all full rank"
          % checks["DISCOVERY_LOODO_FOLDS"])
    ranks = sorted(set(stage_a["loodo_ranks"].values()))
    stamp("  distinct LOODO fold ranks    %s" % ranks)

    preflight = pre.preflight_root([stage_a])

    report = {
        "schema": SCHEMA,
        "stage": pre.STAGES[0],
        "stages_b_and_c_run": False,
        "stages_b_and_c_reason": (
            "Stage B needs STATE_SCORE and IMMUNE_FRACTION and Stage C needs "
            "TAIL_PREVALENCE. None exists before real T0 runs, and supplying a "
            "response to a pathology-blind check is refused by the preflight."),
        "nuisance_design": "[1, age_c, age_c^2, sex]",
        "nuisance_design_columns": 4,
        "confirmation_donors": len(confirmation_order),
        "discovery_donors": len(discovery_order),
        "confirmation_nuisance_rank": int(checks["CONFIRMATION"]),
        "discovery_nuisance_rank": int(checks["DISCOVERY"]),
        "discovery_loodo_folds": int(checks["DISCOVERY_LOODO_FOLDS"]),
        "discovery_loodo_fold_ranks": {str(k): int(v) for k, v
                                       in sorted(stage_a["loodo_ranks"].items())},
        "all_loodo_folds_full_rank": bool(
            set(stage_a["loodo_ranks"].values()) == {4}),
        "donor_bound": bool(stage_a["donor_bound"]),
        "discovery_records_root_sha256": discovery_root,
        "confirmation_records_root_sha256": confirmation_root,
        "preflight_root_sha256": preflight,
        "confirmation_donor_ids": list(confirmation_order),
        "discovery_donor_ids": list(discovery_order),
        "sex_encoding": covariates["sex_encoding"],
        "parents": {
            "eligible_donor_root_sha256": assigned[
                "eligible_donor_root_sha256"],
            "donor_role_root_sha256": assigned["donor_role_root_sha256"],
            "eligible_donor_package_root_sha256": assigned[
                "package_root_sha256"],
            "age_sex_root_sha256": covariates["age_sex_root_sha256"],
            "age_sex_package_root_sha256": covariates["package_root_sha256"],
            "at8_availability_root_sha256": at8_parent[
                "availability_root_sha256"],
            "technical_completeness_root_sha256": complete[
                "completeness_root_sha256"],
            "population_raw_source_root_sha256": universe[
                "population_raw_source_root_sha256"],
        },
        "runner_code_sha256": code_sha256(
            "t0_estimability_preflight_production_run_v1.py"),
        "preflight_code_sha256": code_sha256("t0_estimability_preflight_v1.py"),
        "code_byte_semantics": (
            "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT"
            "__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES"),
        "response_supplied": False,
        "pathology_values_read": False,
        "numeric_at8_value_read": False,
        "covariate_values_emitted": False,
        "real_execution_ready": False,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    assert_no_covariate_value_in_report(report)

    out.mkdir(parents=True, exist_ok=True)
    blob = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with io.open(out / REPORT, "wb") as handle:
        handle.write(blob)
    with io.open(out / ROOT_FILE, "w", encoding="utf-8", newline="\n") as h:
        h.write(hashlib.sha256(blob).hexdigest() + "\n")
    stamp("  preflight root %s" % preflight)
    stamp("  report digest  %s" % hashlib.sha256(blob).hexdigest())
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--eligible-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--tc-pkg", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    args = parser.parse_args(argv)

    report = run(outdir=args.outdir, eligible_pkg=args.eligible_pkg,
                 age_sex_pkg=args.age_sex_pkg, at8_pkg=args.at8_pkg,
                 tc_pkg=args.tc_pkg, population_pkg=args.population_pkg)
    print()
    print(json.dumps(report, indent=2, sort_keys=True))
    print()
    print("STAGE A ESTIMABILITY PREFLIGHT PASS. Stages B and C not run. "
          "real_execution_ready=False.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
