#!/usr/bin/env python3
"""Assemble the Stage-4 executor closeout: the twelve required artifacts, bound by identity.

This is packaging, assembled AFTER the runs it describes. It is labelled as such rather
than presented as a prospective artifact. Every digest below is recomputed from the file
on disk at assembly time and every Git blob is resolved through git; nothing is copied out
of a receipt's own self-description, and no quantity is estimated. Where something was not
measured it says so.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402

D = "results/v64/phase_b_design"


def git(*a):
    r = subprocess.run(["git", *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def ident(path, role, note=None):
    if not os.path.exists(path):
        return dict(role=role, path=path, status="NOT_PRESENT")
    rel = path.replace(os.sep, "/")
    return dict(role=role, path=rel, sha256=B.sha_file(path),
                worktree_blob=git("hash-object", rel),
                git_blob_at_head=git("rev-parse", "HEAD:" + rel),
                bytes=os.path.getsize(path), note=note)


def receipt(name, keys):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        return dict(path=p, status="NOT_PRESENT")
    j = json.load(open(p))
    out = {k: j.get(k) for k in keys}
    out["path"] = p.replace(os.sep, "/")
    out["sha256"] = B.sha_file(p)
    out["git_blob_at_head"] = git("rev-parse", "HEAD:" + out["path"])
    return out


def main() -> int:
    head = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain")

    artifacts = {
        "1_s81_repair_verifier": ident("scripts/v64/verify_phase_b_consumer_semantics_v1.py",
                                       "recomputes 17 consumer-semantics gates from the "
                                       "artifacts, not from JSON restatements"),
        "2_s81_mutation_suite": ident("scripts/v64/test_phase_b_consumer_semantics_mutations_v1.py",
                                      "15 mutations applied to the real loaded arrays"),
        "3_executor_source": ident("scripts/v64/stage4_executor_v1.py",
                                   "the executor, hard-bound, one CLI flag plus the "
                                   "guarded synthetic mode"),
        "4_synthetic_world_builder": ident("scripts/v64/build_stage4_synthetic_worlds_v1.py",
                                           "four Phase-B substrates in the real on-disk "
                                           "format"),
        "5_end_to_end_suite": ident("scripts/v64/test_stage4_end_to_end_worlds_v1.py",
                                    "runs the worlds through the real entrypoint"),
        "6_helper_qualification_suite": ident(
            "scripts/v64/test_stage4_executor_synthetic_qualification_v1.py",
            "19 fixtures over the frozen mathematics"),
        "7_g17_and_antibypass": ident("scripts/v64/test_stage4_g17_and_antibypass_v1.py",
                                      "G17 static and executable, plus 21 attacks"),
        "8_independent_audit": ident("scripts/v64/audit_chatgpt_v67_lane_independent_v1.py",
                                     "independent audit of the ChatGPT lane"),
    }

    receipts = {
        "s81_consumer_semantics": receipt("V64_PHASE_B_CONSUMER_SEMANTICS_V1.json",
                                          ["n_checks", "failed", "status",
                                           "recomputed_from_artifacts"]),
        "s81_mutations": receipt("V64_PHASE_B_CONSUMER_SEMANTICS_MUTATIONS_V1.json",
                                 ["n_mutations", "n_real_tests",
                                  "every_mutation_caught_by_its_named_gate", "status"]),
        "preflight_only": receipt("V64_STAGE4_PREFLIGHT_ONLY_RECEIPT_V1.json",
                                  ["mode", "computed_correspondence_values",
                                   "a_successful_dry_run_is_not_execution_authorization",
                                   "status"]),
        "g17_and_antibypass": receipt("V64_STAGE4_G17_AND_ANTIBYPASS_V1.json",
                                      ["g17_static_checks", "g17_executable_checks",
                                       "anti_bypass_attempts", "n_checks", "n_holding",
                                       "live_artifacts_untouched",
                                       "authorisation_path_clean", "status"]),
        "helper_qualification": receipt(
            "V64_STAGE4_EXECUTOR_SYNTHETIC_QUALIFICATION_V1.json",
            ["n_fixtures", "n_holding", "status"]),
        "end_to_end_worlds": receipt("V64_STAGE4_END_TO_END_WORLDS_V1.json",
                                     ["n_checks", "n_pass", "n_limit", "n_fail",
                                      "worlds", "KNOWN_INTERPRETATION_LIMITS", "scale",
                                      "status"]),
        "synthetic_worlds_build": receipt("V64_STAGE4_SYNTHETIC_WORLDS_BUILD_V1.json",
                                          ["worlds", "reads_no_real_measurement"]),
        "independent_audit_of_chatgpt_lane": receipt(
            "V67_CLAUDE_INDEPENDENT_AUDIT_OF_CHATGPT_LANE_V1.json",
            ["contract_parent_quantities_checked",
             "contract_parent_quantities_reproducing", "n_findings", "severities",
             "status"]),
    }

    state = dict(
        WHAT_IS_NOW_TRUE=[
            "The executor exists, is bound to one canonical authority path and one "
            "canonical output path, and has no flag that can name a method, a seed, a "
            "weighting, a contract, an input root or a skip.",
            "It verifies the BYTES of every input the authority binds, in both "
            "directions, and recomputes the Git blob of each committed one.",
            "It refuses real execution, and the refusal is not a promise: with a "
            "correctly bound authorisation present it still stops, because this build "
            "contains no authorised-execution path.",
            "The whole frozen computation is implemented and has been run end to end "
            "through the real entrypoint on four synthetic worlds.",
            "No correspondence value has been computed on real data, at any scale, at "
            "any point.",
        ],
        WHAT_IS_NOT_GRANTABLE_HERE=[
            "Stage-4 execution authorisation. This closeout does not grant it and the "
            "executor does not create the artifact that would.",
            "Any claim that a positive Stage-4 result would demonstrate regulatory "
            "causation. The HIDDEN_CONFOUND world forbids that reading.",
            "Any claim that LCB95 > 0 alone establishes a non-technical origin. The "
            "MEASURED_TECHNICAL residue forbids that reading.",
        ],
        UNRESOLVED_LIMITATIONS=[
            "The end-to-end worlds are reduced scale: 60 eligible donors, 11 metacells "
            "each, 200 edges, against a real substrate of 282 donors, 3,231 metacells "
            "and 13,175 edges. Ratios are matched; runtime and memory at real scale are "
            "UNMEASURED and nothing here qualifies them.",
            "The pipeline materialises dense metacell-by-feature matrices. At real scale "
            "the ATAC matrix is 3,231 x 32,153. Its footprint has not been measured.",
            "The frozen 14-term basis carries only two depth sensitivities as technical "
            "controls. A cross-modal technical factor orthogonal to depth is not "
            "controlled for and, per the HIDDEN_CONFOUND world, is indistinguishable "
            "from biology.",
            "Six concerns against the ChatGPT lane remain open: S89 through S94.",
            "The synthetic worlds qualify the orchestration, not the biology. Nothing "
            "here says the frozen estimand is the right scientific question.",
        ],
        GOVERNANCE=dict(training="OFF", stage_4="NOT_AUTHORIZED",
                        correspondence="UNOPENED", Morabito="PROTECTED",
                        TD60="BLOCKED", recoverability_TEST="SEALED"),
    )

    out = dict(
        schema="V67_STAGE4_EXECUTOR_CLOSEOUT_V1", date="2026-10-01",
        packaging_note="assembled AFTER the runs it describes. This is post-hoc "
                       "packaging of prospective runs, not itself a prospective artifact.",
        head_commit=head, worktree_clean_at_assembly=(dirty == ""),
        uncommitted_at_assembly=[l for l in (dirty or "").splitlines()],
        artifacts=artifacts, receipts=receipts, state=state,
        end_state="EXECUTOR_IMPLEMENTED_AND_BOUND__S81_CLOSED__"
                  "G16_G17_EVIDENCE_PRESENT__PIPELINE_QUALIFIED_END_TO_END__"
                  "STAGE4_STILL_NOT_AUTHORIZED__CORRESPONDENCE_UNOPENED",
        computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)))
    p = os.path.join(D, "V67_STAGE4_EXECUTOR_CLOSEOUT_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    missing = [k for k, v in artifacts.items() if v.get("status") == "NOT_PRESENT"]
    missing += [k for k, v in receipts.items() if v.get("status") == "NOT_PRESENT"]
    print("artifacts bound : %d" % len(artifacts))
    print("receipts bound  : %d" % len(receipts))
    print("NOT_PRESENT     : %s" % (missing or "none"))
    print("worktree clean  : %s" % (dirty == ""))
    print("receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
