#!/usr/bin/env python3
"""V74 LANE 1: prove the custody tests can FAIL.

A test suite that passes proves nothing on its own. This driver copies the producers
and the test file into a scratch tree OUTSIDE the worktree, removes one repair at a
time, runs the suite, and records which tests stopped holding. The worktree is never
mutated, and nothing here writes into any lane's output directory except this lane's.

For each mutation the expected failures are declared BEFORE the run, and a mutation
whose observed failures do not cover its declared set is reported as
UNPROVEN_TEST_CANNOT_FAIL -- the specific defect this project keeps finding.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTRACT = "scripts/v69/routeb_extract_pseudobulk_fragments_v1.py"
CONSENSUS = "scripts/v69/routeb_call_peaks_and_consensus_v1.py"
CUSTODY = "scripts/v69/v69_custody.py"
TESTFILE = "tests/test_v74_routeb_custody_v1.py"


def _replace_once(root: Path, rel: str, old: str, new: str) -> None:
    p = root / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        raise SystemExit("mutation anchor matched %d times in %s" % (s.count(old), rel))
    p.write_text(s.replace(old, new), encoding="utf-8")


def m_disable_digest_comparison(root: Path) -> None:
    _replace_once(root, CUSTODY, "    if o != e:\n        raise CustodyError(",
                  "    if False:\n        raise CustodyError(")


def m_restore_v69_size_only_fragment_check(root: Path) -> None:
    _replace_once(
        root, EXTRACT,
        "        if observed_sha.lower() != str(expected_frag_sha).strip().lower():",
        "        if False:")
    _replace_once(
        root, EXTRACT,
        '            "observed_sha256": observed_sha,\n            "verified": True,',
        '            "observed_sha256": str(expected_frag_sha).strip().lower(),'
        '\n            "verified": True,')


def m_restore_v69_dict_zip_collapse(root: Path) -> None:
    p = root / EXTRACT
    lines = p.read_text(encoding="utf-8").split("\n")
    hits = [k for k, L in enumerate(lines) if "audit_barcode_authority_frame(bc)" in L]
    if len(hits) != 1:
        raise SystemExit("dict-collapse anchor matched %d lines" % len(hits))
    i = hits[0]
    if "barcode_to_donor, barcode_to_sub, authority_evidence" not in lines[i - 1]:
        raise SystemExit("unexpected line above the audit call")
    lines[i - 1:i + 1] = [
        '        barcode_to_donor = dict(zip(bc["barcode"].astype(str),'
        ' bc["donor"].astype(str)))',
        '        barcode_to_sub = dict(zip(bc["barcode"].astype(str),'
        ' bc["subcluster"].astype(str)))',
        '        authority_evidence = {"n_rows_in": len(bc), "n_distinct_barcodes":'
        ' len(barcode_to_donor), "n_exact_duplicate_rows_collapsed": 0}',
    ]
    p.write_text("\n".join(lines), encoding="utf-8")


def m_restore_v69_absent_qc_row_as_failure(root: Path) -> None:
    _replace_once(
        root, EXTRACT,
        '    if unmeasured:\n'
        '        raise FailClosed("FAIL__COHORT_BARCODE_HAS_NO_QC_VERDICT",',
        '    if False:\n'
        '        raise FailClosed("FAIL__COHORT_BARCODE_HAS_NO_QC_VERDICT",')


def m_disable_empty_consensus_guard(root: Path) -> None:
    _replace_once(
        root, CONSENSUS,
        "    n = 0 if cdf is None else int(len(cdf))\n    if n == 0:",
        "    n = 0 if cdf is None else int(len(cdf))\n    if False:")


MUTATIONS = [
    {
        "id": "M1_DISABLE_DIGEST_COMPARISON",
        "repair_removed": "REPAIR_3_CONTENT_BINDING",
        "what_it_undoes": "bind_file stops comparing the observed digest to the authority",
        "apply": m_disable_digest_comparison,
        "must_fail": [
            "test_bind_file_refuses_a_changed_file",
            "test_editing_the_barcode_authority_without_restamping_it_refuses_the_run",
            "test_editing_the_qc_table_without_restamping_it_refuses_the_run",
            "test_pointing_the_cohort_receipt_at_a_different_file_refuses_the_run",
            "test_consensus_refuses_when_a_bound_input_changed_on_disk",
        ],
    },
    {
        "id": "M2_RESTORE_V69_SIZE_ONLY_FRAGMENT_CHECK",
        "repair_removed": "REPAIR_1_FRAGMENT_BYTE_IDENTITY",
        "what_it_undoes": ("the producer goes back to checking the fragment file's "
                           "SIZE and copying the acquisition receipt's digest"),
        "apply": m_restore_v69_size_only_fragment_check,
        "must_fail": [
            "test_same_size_different_bytes_is_refused",
            "test_receipt_status_written_to_disk_matches_the_exit_code",
        ],
    },
    {
        "id": "M3_RESTORE_V69_DICT_ZIP_COLLAPSE",
        "repair_removed": "REPAIR_2_BARCODE_AUTHORITY",
        "what_it_undoes": ("the barcode table is collapsed with dict(zip(...)) with no "
                           "pre-collapse audit"),
        "apply": m_restore_v69_dict_zip_collapse,
        "must_fail": [
            "test_conflicting_donor_mapping_fails_the_real_producer_closed",
            "test_conflicting_subcluster_mapping_fails_the_real_producer_closed",
            "test_benign_exact_duplicate_rows_are_allowed_and_counted",
            "test_a_blank_identifier_is_not_coerced_into_a_value",
        ],
    },
    {
        "id": "M4_RESTORE_V69_ABSENT_QC_ROW_AS_FAILURE",
        "repair_removed": "REPAIR_3_NOT_MEASURED_IS_NOT_A_MEASURED_FAILURE",
        "what_it_undoes": ("a cohort cell with no QC row is silently counted as a QC "
                           "exclusion"),
        "apply": m_restore_v69_absent_qc_row_as_failure,
        "must_fail": [
            "test_a_cohort_cell_with_no_qc_row_is_not_treated_as_a_qc_failure",
        ],
    },
    {
        "id": "M5_DISABLE_EMPTY_CONSENSUS_GUARD",
        "repair_removed": "REPAIR_4_EMPTY_CONSENSUS",
        "what_it_undoes": "the named zero-region fail-closed state stops firing",
        "apply": m_disable_empty_consensus_guard,
        "must_fail": [
            "test_zero_region_consensus_emits_the_named_state",
            "test_none_is_treated_as_empty_not_as_a_crash",
        ],
    },
]

_FAILED = re.compile(r"^FAILED [^:]+::([A-Za-z0-9_]+)", re.M)


def _run_suite(root: Path) -> dict:
    cp = subprocess.run([sys.executable, "-m", "pytest", TESTFILE, "-q",
                         "-p", "no:cacheprovider"],
                        cwd=str(root), capture_output=True, text=True)
    return {"returncode": cp.returncode,
            "failed_tests": sorted(set(_FAILED.findall(cp.stdout))),
            "summary_line": (cp.stdout.strip().split("\n") or [""])[-1]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    wt, scratch = Path(a.worktree), Path(a.scratch)

    baseline_root = scratch / "BASELINE"
    if baseline_root.exists():
        shutil.rmtree(baseline_root)
    baseline_root.mkdir(parents=True)
    shutil.copytree(wt / "scripts", baseline_root / "scripts")
    shutil.copytree(wt / "tests", baseline_root / "tests")
    baseline = _run_suite(baseline_root)

    results, all_proven = [], True
    for m in MUTATIONS:
        root = scratch / m["id"]
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        shutil.copytree(wt / "scripts", root / "scripts")
        shutil.copytree(wt / "tests", root / "tests")
        m["apply"](root)
        out = _run_suite(root)
        missing = [t for t in m["must_fail"] if t not in out["failed_tests"]]
        verdict = ("PROVEN_CAN_FAIL" if not missing and out["returncode"] != 0
                   else "UNPROVEN_TEST_CANNOT_FAIL")
        all_proven = all_proven and verdict == "PROVEN_CAN_FAIL"
        results.append({
            "mutation_id": m["id"], "repair_removed": m["repair_removed"],
            "what_it_undoes": m["what_it_undoes"],
            "declared_must_fail": m["must_fail"],
            "observed_failed_tests": out["failed_tests"],
            "declared_tests_that_did_not_fail": missing,
            "pytest_returncode": out["returncode"],
            "pytest_summary": out["summary_line"], "verdict": verdict,
        })

    receipt = {
        "schema": "V74_ROUTEB_CUSTODY_MUTATION_EVIDENCE_V1",
        "run_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": ("Demonstrate that each custody test can FAIL. A passing suite is "
                    "not evidence; a suite that still passes with the repair removed "
                    "is evidence of nothing at all."),
        "worktree": str(wt), "scratch_root": str(scratch),
        "baseline_unmutated": baseline,
        "mutations": results,
        "status": ("PASS__EVERY_CUSTODY_TEST_DEMONSTRATED_REACHABLE_FAILURE"
                   if all_proven and baseline["returncode"] == 0
                   else "FAIL__AT_LEAST_ONE_TEST_COULD_NOT_BE_MADE_TO_FAIL"),
    }
    out_p = Path(a.receipt)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(receipt, indent=2) + "\n")
    on_disk = json.loads(out_p.read_text())
    print(json.dumps(on_disk, indent=2)[:4000])
    print("RECEIPT_ON_DISK_STATUS=" + on_disk["status"])
    return 0 if on_disk["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
