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

#: Only these files take part in a mutation arm. Copying the whole scripts/ tree
#: per arm moved ~1.3 GB for a suite whose fixtures are kilobytes, which is not a
#: cost worth paying on a shared machine.
ARM_FILES = (EXTRACT, CONSENSUS, CUSTODY, TESTFILE,
             "scripts/v69/v69_barcode_identity.py")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v69_custody import read_text_utf8 as _rd  # noqa: E402
from v69_custody import write_text_utf8 as _wr  # noqa: E402


def _replace_once(root: Path, rel: str, old: str, new: str) -> None:
    p = root / rel
    s = _rd(p)
    if s.count(old) != 1:
        raise SystemExit("mutation anchor matched %d times in %s" % (s.count(old), rel))
    _wr(p, s.replace(old, new))


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
    lines = _rd(p).split("\n")
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
    _wr(p, "\n".join(lines))


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


def m_disable_qc_recount_check(root: Path) -> None:
    nl = chr(10)
    _replace_once(
        root, EXTRACT,
        "        if disagree:" + nl + "            q = staged.quarantine_failed()",
        "        if False:" + nl + "            q = staged.quarantine_failed()")


def m_restore_peaks_only_denominator(root: Path) -> None:
    _replace_once(root, CONSENSUS,
                  '    submitted = sorted({pseudobulk_meta[k]["donor"]'
                  ' for k in submitted_keys})',
                  '    submitted = sorted({pseudobulk_meta[k]["donor"]'
                  ' for k in keys_with_peaks})')


def m_let_broad_handler_mask_named_states(root: Path) -> None:
    nl = chr(10)
    _replace_once(root, EXTRACT,
                  "    except FailClosed:" + nl
                  + "        # A named state raised inside the loop must keep its name.",
                  "    except _NeverRaised:" + nl
                  + "        # A named state raised inside the loop must keep its name.")
    _replace_once(root, EXTRACT, "class FailClosed(Exception):",
                  "class _NeverRaised(Exception):" + nl + "    pass" + nl + nl + nl
                  + "class FailClosed(Exception):")


def m_drop_ascii_guard(root: Path) -> None:
    _replace_once(root, EXTRACT, "                        if not payload.isascii():",
                  "                        if False:")


def m_skip_four_field_records(root: Path) -> None:
    """The exact slip that happened: a stray continue in the four-field branch."""
    nl = chr(10)
    q = root / EXTRACT
    lines = _rd(q).split(nl)
    hits = [k for k, L in enumerate(lines) if L.strip().startswith("f[3] = f[3].rstrip")]
    if len(hits) != 1:
        raise SystemExit("four-field anchor matched %d lines" % len(hits))
    lines.insert(hits[0] + 1, " " * 20 + "continue")
    _wr(q, nl.join(lines))


def m_write_receipts_with_naive_pathlib(root: Path) -> None:
    """Undo the byte-faithful writer: receipts go back to platform line endings."""
    _replace_once(root, CUSTODY,
                  '    with open(path, "w", encoding="utf-8", newline="' + chr(92)
                  + 'n") as fh:',
                  '    with open(path, "w", encoding="utf-8") as fh:')


def m_drop_blacklist_policy_gate(root: Path) -> None:
    _replace_once(root, CONSENSUS,
                  "    blacklist_policy = assert_blacklist_policy_satisfied(",
                  "    blacklist_policy = _ungated_blacklist_policy(")
    _replace_once(root, CONSENSUS, "BLACKLIST_POLICY_DECIDED = ",
                  "def _ungated_blacklist_policy(blacklist, override):" + chr(10)
                  + "    return {'policy_decided': 'ON', 'satisfied_by': 'UNGATED'}"
                  + chr(10) + chr(10) + chr(10) + "BLACKLIST_POLICY_DECIDED = ")


def m_loosen_the_override_token(root: Path) -> None:
    """Accept any truthy override string instead of the exact named token."""
    _replace_once(root, CONSENSUS,
                  "    if policy_override == NO_BLACKLIST_OVERRIDE:",
                  "    if policy_override:")


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
        "id": "M6_DISABLE_QC_RECOUNT_CHECK",
        "repair_removed": "REPAIR_1_EXTENDED_QC_TABLE_BOUND_TO_VERIFIED_BYTES",
        "what_it_undoes": ("the per-cell QC counts are trusted instead of re-derived "
                           "from the bytes this run digested"),
        "apply": m_disable_qc_recount_check,
        "must_fail": [
            "test_qc_counts_that_disagree_with_the_verified_pass_fail_closed",
        ],
    },
    {
        "id": "M7_RESTORE_PEAKS_ONLY_RECURRENCE_DENOMINATOR",
        "repair_removed": "RECURRENCE_DENOMINATOR_IS_DONORS_SUBMITTED",
        "what_it_undoes": ("the denominator reverts to donors that produced a peak, so "
                           "a donor that called nothing silently leaves it"),
        "apply": m_restore_peaks_only_denominator,
        "must_fail": [
            "test_a_donor_that_called_no_peak_stays_in_the_denominator",
        ],
    },
    {
        "id": "M8_LET_BROAD_HANDLER_MASK_NAMED_STATES",
        "repair_removed": "NAMED_STATES_SURVIVE_THE_BROAD_EXCEPT",
        "what_it_undoes": ("a named fail-closed state raised inside the streaming loop "
                           "is relabelled as a decompression failure"),
        "apply": m_let_broad_handler_mask_named_states,
        "must_fail": [
            "test_a_non_ascii_record_in_a_written_cell_fails_closed",
        ],
    },
    {
        "id": "M9_DROP_ASCII_GUARD",
        "repair_removed": "ASCII_CHECK_ON_WRITTEN_RECORDS",
        "what_it_undoes": ("the validity check that per-line decoding used to perform "
                           "is dropped when the loop moves to bytes"),
        "apply": m_drop_ascii_guard,
        "must_fail": [
            "test_a_non_ascii_record_in_a_written_cell_fails_closed",
        ],
    },
    {
        "id": "M10_SKIP_FOUR_FIELD_RECORDS",
        "repair_removed": "FOUR_FIELD_RECORDS_ARE_ROUTED_NOT_SKIPPED",
        "what_it_undoes": ("a stray continue in the four-field branch, which the "
                           "five-field-only fixture could not reach"),
        "apply": m_skip_four_field_records,
        "must_fail": [
            "test_a_four_field_fragment_record_is_parsed_not_skipped",
        ],
    },
    {
        "id": "M11_NAIVE_RECEIPT_WRITER",
        "repair_removed": "BYTE_FAITHFUL_TEXT_IO",
        "what_it_undoes": ("the receipt writer drops newline=LF and reverts to platform "
                           "line endings"),
        "apply": m_write_receipts_with_naive_pathlib,
        "must_fail": [
            "test_write_text_utf8_emits_lf_and_read_text_utf8_round_trips",
            "test_the_producer_writes_its_receipt_as_lf_utf8",
        ],
    },
    {
        "id": "M12_DROP_BLACKLIST_POLICY_GATE",
        "repair_removed": "BLACKLIST_POLICY_IS_ENFORCED_NOT_NOTED",
        "what_it_undoes": ("the consensus step goes back to recording the absence of a "
                           "blacklist in a receipt note instead of refusing to build"),
        "apply": m_drop_blacklist_policy_gate,
        "declaration_note": (
            "This mutation bypasses the CALL SITE, leaving the gate function itself "
            "intact, so only the tests that go through consensus.run() can see it. "
            "test_a_wrong_override_string_does_not_open_the_gate calls the function "
            "directly and is covered by M13 instead. I first declared it here, the "
            "driver refused to report PASS, and the declaration was wrong -- not the "
            "test."),
        "must_fail": [
            "test_consensus_refuses_to_build_without_a_declared_blacklist_policy",
            "test_the_gate_fires_before_any_peak_calling_work",
        ],
    },
    {
        "id": "M13_LOOSEN_THE_OVERRIDE_TOKEN",
        "repair_removed": "ONLY_THE_EXACT_OVERRIDE_TOKEN_OPENS_THE_GATE",
        "what_it_undoes": ("any truthy string opens the blacklist gate, so a near miss "
                           "like 'none' or 'true' silently authorises a build that "
                           "departs from the decided policy"),
        "apply": m_loosen_the_override_token,
        "must_fail": [
            "test_a_wrong_override_string_does_not_open_the_gate",
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


def _materialise(worktree: Path, root: Path) -> None:
    """Copy only the files an arm can touch, preserving their relative paths."""
    if root.exists():
        shutil.rmtree(root)
    for rel in ARM_FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(worktree / rel, dst)


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
    _materialise(wt, baseline_root)
    baseline = _run_suite(baseline_root)

    results, all_proven = [], True
    for m in MUTATIONS:
        root = scratch / m["id"]
        _materialise(wt, root)
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
        "files_materialised_per_arm": list(ARM_FILES),
        "baseline_unmutated": baseline,
        "mutations": results,
        "status": ("PASS__EVERY_CUSTODY_TEST_DEMONSTRATED_REACHABLE_FAILURE"
                   if all_proven and baseline["returncode"] == 0
                   else "FAIL__AT_LEAST_ONE_TEST_COULD_NOT_BE_MADE_TO_FAIL"),
    }
    out_p = Path(a.receipt)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    _wr(out_p, json.dumps(receipt, indent=2) + "\n")
    on_disk = json.loads(_rd(out_p))
    print(json.dumps(on_disk, indent=2)[:4000])
    print("RECEIPT_ON_DISK_STATUS=" + on_disk["status"])
    return 0 if on_disk["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
