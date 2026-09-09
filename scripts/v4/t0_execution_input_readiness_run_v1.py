"""Materialize and replay the repaired execution-input readiness authority.

R7. Runs Stage 1 parent verification **live**, builds the bindings from what it
actually verified, and only then materializes the production authority whose
readiness is derived from them.

Why the bindings are not hand-written
-------------------------------------
`assert_production_authority_lawful` compares each binding to the accepted value
frozen in committed code. That proves the package *cites* the accepted roots. It
does not prove those roots still reproduce from their sources. So this runner
re-verifies every parent from disk first — replaying the B2 population, the
technical-completeness authority, the AT8 availability authority against frozen
external roots, the age/sex authority against four frozen expectations, and the
eligible-donor authority with its roles re-derived — and constructs the bindings
from the values those replays return. Citation and reproduction are then both
established, and the two checks are independent.

The donor-set digests are computed from the replayed eligible-donor registry
rather than copied, so a changed role assignment cannot pass by citing an old
digest.

Pathology
---------
This runner binds the AT8 endpoint identity and the pathology source digest. It
reads **no numeric AT8 value**. It confirms the pathology source's digest by
hashing the file, which reads bytes without parsing the endpoint column, and the
emitted authority records `numeric_at8_value_read: False`.

Usage
-----
    python t0_execution_input_readiness_run_v1.py
        --outdir outputs/t0_execution_input_readiness_20260909
        --population-pkg outputs/t0_b2_production_20260909
        --tc-pkg outputs/t0_technical_completeness_20260909
        --at8-pkg outputs/t0_at8_availability_20260908
        --age-sex-pkg outputs/t0_age_sex_20260908
        --eligible-pkg outputs/t0_eligible_donor_20260909
        --preflight-pkg outputs/t0_estimability_preflight_20260909
        --authorization-record docs/agent/T0_REAL_RUN_AUTHORIZATION_RECORD_20260909.md
        --pathology-source "<sea_ad_mtg_donor_pathology_targets.csv>"
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

import t0_eligible_donor_authority_v1 as eld  # noqa: E402
import t0_eligible_donor_production_run_v1 as ed  # noqa: E402
import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_input_dependency_contract_v1 as contract  # noqa: E402

RUN_SUMMARY = "T0_EXECUTION_INPUT_READINESS_RUN_SUMMARY.json"

STOP_STAGE1 = "STOP_T0_READINESS_STAGE1_PARENT_VERIFICATION_FAILED"
STOP_SOURCE = "STOP_T0_READINESS_PATHOLOGY_SOURCE_DIGEST_MISMATCH"


def code_sha256(filename: str) -> str:
    """SHA-256 over LF-normalized file content. Not a Git blob digest."""
    path = Path(__file__).resolve().parent / filename
    digest = hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()
    if len(digest) != 64:
        raise AssertionError("%s yielded a %d-character digest, not SHA-256"
                             % (filename, len(digest)))
    return digest


def _lf_digest(path: Path) -> str:
    """Digest of a text artifact over LF-normalized content, CRLF-safe."""
    return hashlib.sha256(
        Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
        .encode("utf-8")).hexdigest()


def _raw_digest(path: Path) -> str:
    """Digest of raw bytes, for a data source whose exact bytes are the identity.

    Reading bytes is not parsing a column. This confirms the pathology source is
    the frozen one without looking at the endpoint.
    """
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_endpoint(at8: dict) -> str:
    """The AT8 endpoint identity, from the verified parent or not at all."""
    identity = at8.get("at8_endpoint_identity")
    if not isinstance(identity, str) or not identity.strip():
        raise AssertionError(
            "%s: the AT8 availability parent did not surface an endpoint "
            "identity, and this runner will not substitute a hand-written one"
            % STOP_STAGE1)
    if at8.get("numeric_at8_value_parsed") is not False:
        raise AssertionError(
            "%s: the availability parent claims it parsed a magnitude"
            % STOP_STAGE1)
    return identity


def verify_stage1_parents(*, population_pkg: Path, tc_pkg: Path, at8_pkg: Path,
                          age_sex_pkg: Path, eligible_pkg: Path,
                          preflight_pkg: Path, log=print) -> dict:
    """Replay every pathology-blind parent and return what was verified."""
    universe = ed.load_candidate_universe(population_pkg)
    log("  B2 population        %d donors, %d proven rows"
        % (len(universe["donors"]), universe["rows_proven"]))

    complete = ed.load_technical_completeness(tc_pkg)
    log("  technical completeness %d donors, %d cells"
        % (complete["donors_covered"], complete["cells_consumed"]))

    at8 = ed.load_at8_availability(at8_pkg)
    log("  AT8 availability     %d donors, verified against frozen roots: %s"
        % (at8["donors_covered"], at8["independently_verified"]))

    presence = ed.load_age_sex_presence(age_sex_pkg)
    log("  age/sex              %d donors, verified: %s"
        % (presence["donors_covered"], presence["independently_verified"]))

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
        expected_candidate_donors=universe["donors"])
    eld.assert_predicate_holds_on_every_row(replayed["rows"])
    eld.assert_roles_agree_with_frozen_rule(replayed["rows"])

    roles: dict[str, list[str]] = {}
    for row in replayed["rows"]:
        roles.setdefault(str(row["donor_role"]), []).append(str(row["donor_id"]))
    counts = {k: len(v) for k, v in roles.items()}
    counts.setdefault("INELIGIBLE", 0)
    log("  eligible donors      %s" % counts)

    frozen_counts = {"CONFIRMATION": readiness.CONFIRMATION_DONORS,
                     "DISCOVERY": readiness.DISCOVERY_DONORS,
                     "INELIGIBLE": readiness.INELIGIBLE_DONORS}
    if counts != frozen_counts:
        raise AssertionError("%s: donor roles are %r, frozen design is %r"
                             % (STOP_STAGE1, counts, frozen_counts))

    preflight = json.loads(
        (preflight_pkg / "T0_ESTIMABILITY_PREFLIGHT_STAGE_A_REPORT.json"
         ).read_text(encoding="utf-8"))
    if not preflight["all_loodo_folds_full_rank"]:
        raise AssertionError("%s: Stage A reports a rank-deficient LOODO fold"
                             % STOP_STAGE1)
    log("  Stage A preflight    CONF rank %d, DISC rank %d, %d folds full rank"
        % (preflight["confirmation_nuisance_rank"],
           preflight["discovery_nuisance_rank"],
           preflight["discovery_loodo_folds"]))

    audit = contract.audit_byte_semantics_labels()
    contract.assert_provenance_waiver_set_unchanged()
    contract.assert_contract_wellformed()
    log("  byte-semantics audit new false labels allowed: %s"
        % audit["allows_new_false_labels"])

    return {
        "universe": universe, "complete": complete, "at8": at8,
        "presence": presence, "eligible": replayed, "roles": roles,
        "donor_role_counts": counts, "preflight": preflight, "audit": audit,
        "contract_root": contract.contract_root(),
    }


def run(*, outdir: Path, population_pkg: Path, tc_pkg: Path, at8_pkg: Path,
        age_sex_pkg: Path, eligible_pkg: Path, preflight_pkg: Path,
        authorization_record: Path, pathology_source: Path,
        log=print) -> dict:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%5.1fs] %s" % (time.time() - started, message))

    stamp("Stage 1 — verifying every pathology-blind parent from disk")
    verified = verify_stage1_parents(
        population_pkg=population_pkg, tc_pkg=tc_pkg, at8_pkg=at8_pkg,
        age_sex_pkg=age_sex_pkg, eligible_pkg=eligible_pkg,
        preflight_pkg=preflight_pkg, log=log)

    stamp("confirming the pathology source identity without parsing it")
    source_digest = _raw_digest(pathology_source)
    expected_source = readiness.ACCEPTED_BINDINGS["pathology_source_sha256"]
    if source_digest != expected_source:
        raise AssertionError("%s: the source hashes to %s, frozen identity is %s"
                             % (STOP_SOURCE, source_digest, expected_source))
    stamp("  source digest %s (bytes hashed, endpoint column not read)"
          % source_digest)

    stamp("computing the donor-set digests from the replayed role assignment")
    discovery_digest = readiness.donor_set_digest(
        "DISCOVERY", verified["roles"]["DISCOVERY"])
    confirmation_digest = readiness.donor_set_digest(
        "CONFIRMATION", verified["roles"]["CONFIRMATION"])
    stamp("  DISCOVERY    %s" % discovery_digest)
    stamp("  CONFIRMATION %s" % confirmation_digest)

    authorization_digest = _lf_digest(authorization_record)
    stamp("  authorization record %s" % authorization_digest)

    # Bindings assembled from what the replays returned, not typed by hand.
    bindings = {
        "b2_population_raw_source_root_sha256":
            verified["universe"]["population_raw_source_root_sha256"],
        "b2_authority_package_root_sha256":
            verified["universe"]["package_root_sha256"],
        "technical_completeness_root_sha256":
            verified["complete"]["completeness_root_sha256"],
        "technical_completeness_package_root_sha256":
            verified["complete"]["package_root_sha256"],
        "at8_availability_root_sha256":
            verified["at8"]["availability_root_sha256"],
        "at8_availability_package_root_sha256":
            verified["at8"]["package_root_sha256"],
        "age_sex_root_sha256": verified["presence"]["age_sex_root_sha256"],
        "age_sex_package_root_sha256":
            verified["presence"]["package_root_sha256"],
        "eligible_donor_root_sha256":
            verified["eligible"]["eligible_donor_root_sha256"],
        "donor_role_root_sha256":
            verified["eligible"]["donor_role_root_sha256"],
        "eligible_donor_package_root_sha256":
            verified["eligible"]["package_root_sha256"],
        "stage_a_preflight_root_sha256":
            verified["preflight"]["preflight_root_sha256"],
        "input_dependency_contract_root_sha256": verified["contract_root"],
        "authorization_record_root_sha256": authorization_digest,
        # Taken from the verified AT8 parent. No fallback to a hand-written
        # constant: a first draft of this runner had one, which would have made
        # the endpoint identity self-supplied rather than verified, defeating the
        # point of binding it at all.
        "at8_endpoint_identity": _require_endpoint(verified["at8"]),
        "pathology_source_sha256": source_digest,
        "discovery_donor_set_sha256": discovery_digest,
        "confirmation_donor_set_sha256": confirmation_digest,
        "code_byte_semantics_audit":
            "NO_NEW_FALSE_LABELS"
            if verified["audit"]["allows_new_false_labels"] is False
            else "NEW_FALSE_LABELS_PERMITTED",
    }

    stamp("materializing the production authority — readiness is derived here")
    result = readiness.materialize_production_authority(
        outdir,
        bindings=bindings,
        staged_authorization={
            "token": readiness.STAGED_AUTHORIZATION_TOKEN,
            "scope": readiness.STAGED_AUTHORIZATION_SCOPE,
            "record_sha256": authorization_digest,
            "record_path": str(authorization_record).replace("\\", "/"),
        },
        forbidden_gates_opened={g: False for g in readiness.FORBIDDEN_GATES},
        donor_role_counts=verified["donor_role_counts"])
    stamp("  real_execution_ready = %s (derived, not assigned)"
          % result["real_execution_ready"])
    stamp("  readiness root %s" % result["readiness_root_sha256"])
    stamp("  package root   %s" % result["package_root_sha256"])

    record = {
        "schema": "JEPA_T0_EXECUTION_INPUT_READINESS_RUN_SUMMARY_V1",
        "readiness_root_sha256": result["readiness_root_sha256"],
        "package_root_sha256": result["package_root_sha256"],
        "real_execution_ready": result["real_execution_ready"],
        "readiness_derivation": readiness.READINESS_DERIVATION,
        "readiness_derivation_statement":
            readiness.READINESS_DERIVATION_STATEMENT,
        "bindings": bindings,
        "donor_role_counts": verified["donor_role_counts"],
        "stage1_parents_verified_live": True,
        "pathology_source_digest_confirmed": True,
        "numeric_at8_value_read": False,
        "at8_endpoint_column_parsed": False,
        "dev_opened": False,
        "sealed_opened": False,
        "scientific_design_unchanged": True,
        "frozen_v20_package_modified": False,
        "runner_code_sha256": code_sha256(
            "t0_execution_input_readiness_run_v1.py"),
        "authority_code_sha256": code_sha256(
            "t0_execution_input_readiness_authority_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    path = Path(outdir) / RUN_SUMMARY
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def replay(*, pkgdir: Path, log=print) -> dict:
    """Reload the authority and re-derive readiness from committed expectations."""
    summary = json.loads((Path(pkgdir) / RUN_SUMMARY).read_text(
        encoding="utf-8"))
    loaded = readiness.load_production_authority(
        Path(pkgdir),
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_readiness_root_sha256=summary["readiness_root_sha256"])
    obj = loaded["authority"]
    log("  package root      %s" % loaded["package_root_sha256"])
    log("  readiness root    %s" % loaded["readiness_root_sha256"])
    log("  readiness         %s, derivation %s"
        % (obj["real_execution_ready"], obj["readiness_derivation"]))
    log("  frozen v2 gate would be satisfied: %s"
        % loaded["frozen_v2_gate_satisfied"])
    if obj["real_execution_ready"] is not True:
        raise AssertionError("a replayed production authority must be ready")
    if obj["numeric_at8_value_read"] is not False:
        raise AssertionError("the readiness authority must read no numeric AT8")
    for gate, opened in obj["forbidden_gates_opened"].items():
        if opened is not False:
            raise AssertionError("forbidden gate %s reported open" % gate)
    log("  every forbidden gate declared shut; no numeric AT8 read")
    return {
        "schema": "JEPA_T0_EXECUTION_INPUT_READINESS_REPLAY_REPORT_V1",
        "package_root_sha256": loaded["package_root_sha256"],
        "readiness_root_sha256": loaded["readiness_root_sha256"],
        "real_execution_ready": obj["real_execution_ready"],
        "readiness_derivation": obj["readiness_derivation"],
        "frozen_v2_gate_satisfied": loaded["frozen_v2_gate_satisfied"],
        "stored_equals_recomputed_equals_expected": True,
        "numeric_at8_value_read": False,
        "forbidden_gates_all_shut": True,
        "donor_role_counts": obj["donor_role_counts"],
        "bindings": obj["bindings"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument("--tc-pkg", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--eligible-pkg", required=True, type=Path)
    parser.add_argument("--preflight-pkg", required=True, type=Path)
    parser.add_argument("--authorization-record", required=True, type=Path)
    parser.add_argument("--pathology-source", required=True, type=Path)
    parser.add_argument("--replay-only", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    if not args.replay_only:
        run(outdir=args.outdir, population_pkg=args.population_pkg,
            tc_pkg=args.tc_pkg, at8_pkg=args.at8_pkg,
            age_sex_pkg=args.age_sex_pkg, eligible_pkg=args.eligible_pkg,
            preflight_pkg=args.preflight_pkg,
            authorization_record=args.authorization_record,
            pathology_source=args.pathology_source)
        print()
    print("replaying the readiness authority from disk")
    report = replay(pkgdir=args.outdir)
    print()
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report is not None:
        with io.open(args.report, "w", encoding="utf-8", newline="\n") as h:
            h.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print()
    print("EXECUTION INPUT READINESS AUTHORITY DONE AND REPLAYED. "
          "No numeric AT8 read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
