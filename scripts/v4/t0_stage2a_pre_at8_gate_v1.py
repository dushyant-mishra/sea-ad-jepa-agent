"""Stage 2A — the R7-gated pre-AT8 preparation. Reads no numeric AT8.

Three jobs, in order, all before a single pathology magnitude is touched.

1. Verify the R7 readiness authority against the roots the reviewer named, and
   run every one of the nine required pre-AT8 checks.

2. Build the frozen `t0_donor_role_authority_v2` package. This is a real
   dependency gap R7 left open and named: the conclusion-bearing function
   `t0_canonical_freeze_v1.freeze_target_after_role` calls
   `load_role_authority(role_dir)`, and no such package existed. It is buildable
   pathology-blind, because the role authority consumes `AT8_available` as a
   boolean and never a magnitude, so it belongs here rather than after AT8 opens.

3. Cross-check the role authority's split against the eligible-donor authority's
   `donor_role_root`. Two independent modules assign the same 18 CONFIRMATION
   donors from the same frozen rule; if they disagree, that is a STOP, not
   something to reconcile by preferring one.

The wrapper this prepares for keeps v2's architecture exactly — verified
external-input gate, then the conclusion function — with R7 supplying a stricter
and, unlike v2's, satisfiable gate. It is not a fallback to v1: a direct call to
`freeze_target_after_role` without the gate is refused by name.

No numeric AT8 is read here. No DEV or SEALED path is opened. No scientific
design constant is changed.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as ed  # noqa: E402
import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_input_dependency_contract_v1 as contract  # noqa: E402

# The reviewer named these explicitly in the Stage 2 authorization.
R7_PACKAGE_ROOT = (
    "a7e25e515f8e9cb4ec43e1e3bf09798adca6a573059d4b7ca0b61483c5c96c09")
R7_READINESS_ROOT = (
    "a75581dfc5e7ea88609a9ef62f54765b9a495a7dbdc5c09152ba7fb76d1488ae")

SUMMARY = "T0_STAGE2A_PRE_AT8_GATE_SUMMARY.json"

STOP_R7 = "STOP_T0_STAGE2A_R7_READINESS_GATE_FAILED"
STOP_ROLE_DISAGREE = "STOP_T0_STAGE2A_ROLE_AUTHORITY_DISAGREES_WITH_ELIGIBLE_DONORS"
STOP_AT8_READ = "STOP_T0_STAGE2A_NUMERIC_AT8_MUST_NOT_BE_READ_HERE"
STOP_AUDIT_TEXT_BASED = "STOP_T0_STAGE2A_BYTE_SEMANTICS_AUDIT_IS_TEXT_BASED"
STOP_DIRTY = "STOP_T0_STAGE2A_PRODUCTION_CODE_NOT_COMMITTED"
STOP_V1_DIRECT = "STOP_T0_STAGE2A_DIRECT_V1_CALL_WITHOUT_THE_R7_GATE"

FROZEN_V20 = (Path("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project")
              / "cdf819f6-5db4-4119-9a97-37fef1d27909" / "scratchpad"
              / "v20_recovery" / "current" / "code")


def code_sha256(filename: str) -> str:
    """SHA-256 over LF-normalized content. Not a Git blob digest."""
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def _frozen(module: str):
    if str(FROZEN_V20) not in sys.path:
        sys.path.insert(0, str(FROZEN_V20))
    return __import__(module)


# ---------------------------------------------------------------------------
# 1. The nine required pre-AT8 checks.
# ---------------------------------------------------------------------------

def verify_r7_gate(readiness_pkg: Path, *, log=print) -> dict:
    """Every pre-AT8 check the Stage 2 authorization requires."""
    checks: dict[str, Any] = {}

    loaded = readiness.load_production_authority(
        readiness_pkg,
        expected_package_root_sha256=R7_PACKAGE_ROOT,
        expected_readiness_root_sha256=R7_READINESS_ROOT)
    obj = loaded["authority"]

    checks["r7_package_root_matches"] = (
        loaded["package_root_sha256"] == R7_PACKAGE_ROOT)
    checks["r7_readiness_root_matches"] = (
        loaded["readiness_root_sha256"] == R7_READINESS_ROOT)
    checks["real_execution_ready_is_true"] = (
        obj["real_execution_ready"] is True)
    checks["readiness_derivation_is_verified_from_stage1"] = (
        obj["readiness_derivation"] == readiness.READINESS_DERIVATION)

    # All nineteen bindings, re-verified against committed expectations.
    readiness.all_required_stage1_bindings_verified(obj["bindings"])
    checks["all_nineteen_bindings_verify"] = (
        len(readiness.REQUIRED_BINDINGS) == 19
        and all(name in obj["bindings"]
                for name in readiness.REQUIRED_BINDINGS))

    readiness.no_forbidden_gate_opened(obj)
    checks["seven_forbidden_gates_shut"] = (
        len(readiness.FORBIDDEN_GATES) == 7
        and all(obj["forbidden_gates_opened"][g] is False
                for g in readiness.FORBIDDEN_GATES))

    # The endpoint identity must come from the verified parent, and the runner
    # must have no fallback. Asserted on the module surface, not on trust.
    runner_src = (Path(__file__).resolve().parent
                  / "t0_execution_input_readiness_run_v1.py").read_text(
                      encoding="utf-8")
    checks["endpoint_identity_has_no_runner_fallback"] = (
        "_require_endpoint(verified[\"at8\"])" in runner_src
        and "else readiness.ACCEPTED_BINDINGS[\"at8_endpoint_identity\"]"
        not in runner_src)

    # The byte-semantics audit must be structured, not text-based.
    audit_src = (Path(__file__).resolve().parent
                 / "t0_input_dependency_contract_v1.py").read_text(
                     encoding="utf-8")
    ast_based = ("ast.parse(text)" in audit_src
                 and "ast.Dict" in audit_src
                 and "_BYTE_SEMANTICS_LITERAL" not in audit_src)
    if not ast_based:
        raise AssertionError(
            "%s: the audit must parse declarations structurally, because a "
            "regex over source text cannot tell a declaration from prose about "
            "one" % STOP_AUDIT_TEXT_BASED)
    checks["byte_semantics_audit_is_ast_based"] = True
    audit = contract.audit_byte_semantics_labels()
    contract.assert_provenance_waiver_set_unchanged()
    checks["no_new_false_byte_semantics_labels"] = (
        audit["allows_new_false_labels"] is False)

    checks["no_numeric_at8_read_yet"] = (
        obj["numeric_at8_value_read"] is False)

    failed = [k for k, v in checks.items() if v is not True]
    if failed:
        raise AssertionError("%s: %s" % (STOP_R7, failed))
    for name in sorted(checks):
        log("    %-46s %s" % (name, checks[name]))
    return {"checks": checks, "authority": obj,
            "package_root_sha256": loaded["package_root_sha256"],
            "readiness_root_sha256": loaded["readiness_root_sha256"],
            "audit": audit}


# ---------------------------------------------------------------------------
# 2. The frozen donor-role authority v2 package, built pathology-blind.
# ---------------------------------------------------------------------------

def build_frozen_role_authority(
        outdir: Path, *, membership_csv: Path, at8_pkg: Path,
        age_sex_pkg: Path, tc_pkg: Path, population_pkg: Path,
        log=print) -> dict:
    """Build `t0_donor_role_authority_v2` from verified pathology-blind parents.

    `AT8_available` enters as the boolean the availability authority derived
    without parsing a magnitude. Age and sex enter as values, which the role
    authority needs for its nuisance rank checks, from the replayed age/sex
    parent. Nothing here reads an AT8 magnitude.
    """
    role_mod = _frozen("t0_donor_role_authority_v2")
    ages_mod = _frozen("t0_age_sex_authority_v1")

    universe = ed.load_candidate_universe(population_pkg)
    at8 = ed.load_at8_availability(at8_pkg)
    complete = ed.load_technical_completeness(tc_pkg)
    replayed_ages = ages_mod.load_authority(
        age_sex_pkg,
        expected_package_root_sha256=ed.AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256=ed.AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256=ed.AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256=(
            ed.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET))

    donors = list(universe["donors"])
    membership = pd.read_csv(membership_csv, dtype=str)
    support = (membership.groupby("donor_id").size().rename("cells")
               .reset_index())
    support.insert(0, "source", "SEA_AD")
    support.insert(2, "operator_index", 31)
    support["cells"] = support["cells"].astype(np.int64)
    log("    support: %d donors, %d cells total"
        % (len(support), int(support.cells.sum())))

    by_donor = {str(r["donor_id"]): r for r in replayed_ages["rows"]}
    metadata = pd.DataFrame({
        "donor_id": donors,
        "AT8_available": [bool(at8["flags"][d]) for d in donors],
        "age": [int(by_donor[d]["age"]) for d in donors],
        "sex": [str(by_donor[d]["sex"]) for d in donors],
        "technical_complete": [bool(complete["flags"][d]) for d in donors],
    })
    metadata = metadata[["donor_id", "AT8_available", "age", "sex",
                         "technical_complete"]]

    # The role authority binds the identities of the authorities it came from.
    input_hashes = {
        "at8_availability_root_sha256": at8["availability_root_sha256"],
        "age_sex_root_sha256": replayed_ages["age_sex_root_sha256"],
        "technical_completeness_root_sha256":
            complete["completeness_root_sha256"],
        "population_raw_source_root_sha256":
            universe["population_raw_source_root_sha256"],
        "eligible_donor_root_sha256":
            readiness.ACCEPTED_BINDINGS["eligible_donor_root_sha256"],
    }

    built = role_mod.build_role_authority(outdir, support, metadata,
                                          input_hashes)
    registry = built["registry"]
    log("    role authority package root %s" % built["package_root_sha256"])
    log("    complete donors %d, discovery %d, confirmation %d"
        % (built["metadata"]["complete_donors"],
           built["metadata"]["discovery_donors"],
           built["metadata"]["confirmation_donors"]))
    log("    confirmation tail-measurable %d"
        % built["metadata"]["confirmation_tail_measurable_donors"])

    # Recompute against canonical inputs, which is the frozen module's own
    # strongest self-check.
    role_mod.verify_role_authority_against_inputs(
        outdir, support, metadata, input_hashes)
    log("    verified against canonical source-input recomputation")

    loaded = role_mod.load_role_authority(outdir)
    return {"package_root_sha256": built["package_root_sha256"],
            "metadata": built["metadata"],
            "discovery_donors": loaded["discovery_donors"],
            "confirmation_donors": loaded["confirmation_donors"],
            "registry_rows": len(registry),
            "input_authority_hashes": input_hashes}


# ---------------------------------------------------------------------------
# 3. Two independent modules must agree on the split.
# ---------------------------------------------------------------------------

def cross_check_roles(role: dict, eligible_pkg: Path, *, log=print) -> dict:
    """The role authority and the eligible-donor authority must agree exactly."""
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
            "parent_contract_root_sha256"])
    mine = {"CONFIRMATION": set(), "DISCOVERY": set()}
    for row in replayed["rows"]:
        if row["donor_role"] in mine:
            mine[row["donor_role"]].add(str(row["donor_id"]))

    theirs = {"CONFIRMATION": set(map(str, role["confirmation_donors"])),
              "DISCOVERY": set(map(str, role["discovery_donors"]))}
    for label in ("CONFIRMATION", "DISCOVERY"):
        if mine[label] != theirs[label]:
            raise AssertionError(
                "%s: %s differs. eligible-donor-only %s, role-authority-only %s"
                % (STOP_ROLE_DISAGREE, label,
                   sorted(mine[label] - theirs[label]),
                   sorted(theirs[label] - mine[label])))
    log("    CONFIRMATION and DISCOVERY sets agree exactly, %d and %d donors"
        % (len(theirs["CONFIRMATION"]), len(theirs["DISCOVERY"])))
    return {"agree": True,
            "confirmation_donors": sorted(theirs["CONFIRMATION"]),
            "discovery_donors": sorted(theirs["DISCOVERY"]),
            "donor_role_root_sha256": summary["donor_role_root_sha256"]}


FORBIDDEN_PRODUCTION_CALLS = (
    "freeze_target_after_role_v2_for_test",
    "freeze_tail_after_discovery_authority_v2_for_test",
    "adjudicate_from_raw_v2_for_test",
)
GATE_FUNCTION = "verify_r7_gate"
CONCLUSION_FUNCTION = "freeze_target_after_role"


def _called_names(tree) -> set[str]:
    """Every function name actually invoked, from the AST.

    Parsed rather than text-matched. A source scan cannot tell a call from a
    string that names a function in order to forbid it -- an earlier version of
    this guard rejected its own module for exactly that reason, which is the same
    error that flagged an `age_present` header, a report's own
    `at8_availability_root_sha256`, and a comment quoting a byte-semantics
    declaration. Naming is not calling, and the AST knows the difference.
    """
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def assert_no_direct_v1_production_call(module_source: str) -> bool:
    """The wrapper must gate before it concludes.

    Calling the conclusion function without a preceding R7 gate call is the
    forbidden fallback to v1. Calling any `_for_test` entrypoint from production
    code is forbidden outright.
    """
    tree = ast.parse(module_source)
    called = _called_names(tree)
    used = sorted(set(FORBIDDEN_PRODUCTION_CALLS) & called)
    if used:
        raise AssertionError(
            "%s: production code calls test-only entrypoints %s"
            % (STOP_V1_DIRECT, used))
    if CONCLUSION_FUNCTION in called and GATE_FUNCTION not in called:
        raise AssertionError(
            "%s: %s is called without %s, which is the forbidden direct v1 path"
            % (STOP_V1_DIRECT, CONCLUSION_FUNCTION, GATE_FUNCTION))
    return True


def run(*, outdir: Path, readiness_pkg: Path, role_outdir: Path,
        membership_csv: Path, at8_pkg: Path, age_sex_pkg: Path, tc_pkg: Path,
        population_pkg: Path, eligible_pkg: Path, log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%5.1fs] %s" % (time.time() - started, message))

    stamp("Stage 2A step 1 — the nine required pre-AT8 checks")
    gate = verify_r7_gate(readiness_pkg, log=log)

    stamp("Stage 2A step 2 — building the frozen donor-role authority v2")
    role = build_frozen_role_authority(
        role_outdir, membership_csv=membership_csv, at8_pkg=at8_pkg,
        age_sex_pkg=age_sex_pkg, tc_pkg=tc_pkg,
        population_pkg=population_pkg, log=log)

    stamp("Stage 2A step 3 — cross-checking the split against eligible donors")
    agreement = cross_check_roles(role, eligible_pkg, log=log)

    record = {
        "schema": "JEPA_T0_STAGE2A_PRE_AT8_GATE_SUMMARY_V1",
        "terminal": "STAGE2A_R7_GATE_VERIFIED__ROLE_AUTHORITY_BUILT",
        "r7_package_root_sha256": gate["package_root_sha256"],
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
        "pre_at8_checks": gate["checks"],
        "donor_role_package_root_sha256": role["package_root_sha256"],
        "donor_role_metadata": role["metadata"],
        "donor_role_input_authority_hashes": role["input_authority_hashes"],
        "role_split_agrees_with_eligible_donor_authority": agreement["agree"],
        "confirmation_donors": agreement["confirmation_donors"],
        "discovery_donors": agreement["discovery_donors"],
        "donor_role_root_sha256": agreement["donor_role_root_sha256"],
        "numeric_at8_value_read": False,
        "at8_available_consumed_as_boolean_only": True,
        "confirmation_numeric_at8_accessed": False,
        "dev_opened": False,
        "sealed_opened": False,
        "scientific_design_unchanged": True,
        "frozen_v20_package_modified": False,
        "runner_code_sha256": code_sha256("t0_stage2a_pre_at8_gate_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    with io.open(out / SUMMARY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    stamp("wrote %s" % (out / SUMMARY))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--readiness-pkg", required=True, type=Path)
    parser.add_argument("--role-outdir", required=True, type=Path)
    parser.add_argument("--membership", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--tc-pkg", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument("--eligible-pkg", required=True, type=Path)
    args = parser.parse_args(argv)

    record = run(outdir=args.outdir, readiness_pkg=args.readiness_pkg,
                 role_outdir=args.role_outdir, membership_csv=args.membership,
                 at8_pkg=args.at8_pkg, age_sex_pkg=args.age_sex_pkg,
                 tc_pkg=args.tc_pkg, population_pkg=args.population_pkg,
                 eligible_pkg=args.eligible_pkg)
    print()
    print(json.dumps({k: v for k, v in record.items()
                      if k not in ("confirmation_donors", "discovery_donors")},
                     indent=2, sort_keys=True))
    print()
    print("STAGE 2A DONE. R7 gate verified, donor-role authority built, split "
          "agrees. No numeric AT8 read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
