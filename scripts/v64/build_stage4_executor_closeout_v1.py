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


def superseded_v1_curve_receipt():
    """The withdrawn V1 K-curve, carried with its retraction attached rather than deleted.

    S109 repaired THE_GOVERNING_INTERPRETATION_LIMIT but left this receipts block stating
    the same withdrawn conclusion verbatim, one level down in the same file. A reader who
    stops at the receipts inventory still met the retracted claim. The fix is the same
    shape as S109's: head the block, keep every measured field beneath it.
    """
    out = receipt("V64_STAGE4_G2_SENSITIVITY_CURVE_V1.json",
                  ["executes_precommitment", "cells",
                   "g2_rate_monotone_in_K",
                   "g2_rate_at_max_K_converges_on_biology_rate",
                   "READING", "primary_evidence",
                   "canonical_state_verified", "status"])
    head = {
        "SUPERSEDED_DO_NOT_CITE_AS_A_CURRENT_RESULT": (
            "This receipt describes the HISTORICAL sampling-with-replacement generator. "
            "Block labels were drawn as rng.integers(0, K, N_EDGES), so requested K was "
            "only the SIZE OF A FACTOR POOL. At K=200 over 200 edges realised occupancy "
            "averages 126.6, and the retained positive-control build records 131. The "
            "K=200 endpoint was never one factor per edge."),
        "WITHDRAWN_FIELDS": (
            "READING, g2_rate_monotone_in_K, "
            "g2_rate_at_max_K_converges_on_biology_rate and every cells.*.edges_per_block "
            "value. edges_per_block is NOMINAL N_EDGES/K bookkeeping, not realised "
            "occupancy."),
        "superseded_by": "results/v64/phase_b_design/"
                         "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json, "
                         "recorded beside this block as g2_sensitivity_curve_REPAIRED_V2. "
                         "Its G2 pass rate is NON-MONOTONE -- 0.20, 0.25, 0.40, 0.65, "
                         "0.50 -- so by the pre-committed reading no protection claim may "
                         "be made in either direction.",
        "empirical_status_now": "UNRESOLVED. Whether G2 protects against edge-specific "
                                "cross-modal confounding is not settled by either curve.",
        "structural_argument_is_separate": "that a completely edge-private latent loading "
                                           "on both RNA and ATAC can be observationally "
                                           "indistinguishable from a regulatory latent is "
                                           "a CONCEPTUAL ARGUMENT. It never depended on "
                                           "either curve and is not an empirical result.",
        "annotated_in_place": "the V1 artifact now carries this supersession in its own "
                              "bytes; its pre-annotation SHA-256 was "
                              "86c6f08ce56064f1a6431c0ded423d590b8c3292328e5d3b915fa2cdbe"
                              "b5aad3 at git blob fc5afb7f07c82f58335e5340cda1d8543fa9595"
                              "2, and nothing was deleted.",
        "RETAINED_MEASURED_FIELDS_BELOW": True,
    }
    head.update(out)
    return head


def repaired_v2_curve_receipt():
    """The exact-K successor, with the one field a machine reader could misread guarded.

    g2_rate_at_max_K_converges_on_biology_rate is true here while g2_rate_monotone_in_K is
    false. The frozen reading requires BOTH, so the convergence flag on its own licenses
    nothing, and it is recorded with that stated rather than left to be read alone.
    """
    out = receipt("V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED.json",
                  ["executes_precommitment", "historical_v1_preserved",
                   "historical_v1_scope", "S102_status", "cells",
                   "g2_rate_monotone_in_K",
                   "g2_rate_at_max_K_converges_on_biology_rate",
                   "READING", "primary_evidence", "status"])
    head = {
        "WHAT_THIS_SETTLES": "nothing in either direction. The pass rate is 0.20, 0.25, "
                             "0.40, 0.65, 0.50 at K = 1, 5, 20, 50, 200: NON-MONOTONE. By "
                             "the pre-committed reading no protection claim may be made "
                             "either way, and the Wilson intervals at K=50 and K=200 "
                             "overlap too heavily to distinguish 0.65 from 0.50 at 20 "
                             "draws per cell.",
        "CONVERGENCE_FLAG_ALONE_LICENSES_NOTHING": (
            "g2_rate_at_max_K_converges_on_biology_rate is true below, but the frozen "
            "reading requires monotonicity AND overlap together, and monotonicity "
            "failed. The overlap test is weak by construction: at 20 draws against a "
            "25-of-40 reference it fails only below about 3 of 20 or at 20 of 20."),
        "INHERITED_CONTRACT_TEXT_IS_NOT_A_DESCRIPTION_OF_THIS_RUN": (
            "the V2 artifact's convergence_test block still carries the frozen sentence "
            "'a monotone rise ... is unmistakable'. That is the pre-committed READING "
            "RULE, written by the runner into every receipt it emits, not a statement "
            "about this run, which was not monotone."),
        "empirical_status": "UNRESOLVED",
        "structural_argument_is_separate_and_is_not_a_measurement": (
            "that a completely edge-private latent loading on both RNA and ATAC can be "
            "observationally indistinguishable from a regulatory latent is a CONCEPTUAL "
            "ARGUMENT under this observation model. It never depended on either curve."),
        "MEASURED_FIELDS_BELOW": True,
    }
    head.update(out)
    return head


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
        "11_g2_sensitivity_curve": ident(
            "scripts/v64/run_stage4_g2_sensitivity_curve_v1.py",
            "varies how shared a hidden confound is and watches what G2 does"),
        "12_calibration_sweeps": ident(
            "scripts/v64/run_stage4_calibration_sweep_v2.py",
            "four worlds, two donor counts, the complete five-gate decision"),
        "9_seed_robustness": ident("scripts/v64/test_stage4_world_seed_robustness_v1.py",
                                   "rebuilds the worlds at four seed bases and asks "
                                   "which conclusions are a property of the method"),
        "10_real_scale_capacity": ident("scripts/v64/audit_stage4_real_scale_capacity_v1.py",
                                        "footprint from declared shapes; reads no "
                                        "payload"),
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
        "calibration_sweep_v2": receipt("V64_STAGE4_CALIBRATION_SWEEP_V2.json",
                                        ["executes_precommitment", "readings",
                                         "scale_reading", "canonical_state_verified",
                                         "status"]),
        "g2_sensitivity_curve_SUPERSEDED_V1": superseded_v1_curve_receipt(),
        "g2_sensitivity_curve_REPAIRED_V2": repaired_v2_curve_receipt(),
        "confound_block_geometry_verification": receipt(
            "V64_CONFOUND_BLOCK_GEOMETRY_VERIFICATION_V1.json",
            ["why", "all_K_recovered_exactly", "ALL_REPAIRED_K_GEOMETRY_QUALIFIED",
             "status"]),
        "world_seed_robustness": receipt("V64_STAGE4_WORLD_SEED_ROBUSTNESS_V1.json",
                                         ["seed_bases", "n_checks", "n_seed_stable",
                                          "seed_dependent",
                                          "thresholds_unchanged_after_seeing_the_failures",
                                          "canonical_state_verified", "status"]),
        "real_scale_capacity": receipt("V64_STAGE4_REAL_SCALE_CAPACITY_V1.json",
                                       ["plausible_peak_gb", "machine",
                                        "calculated_peak_fits_in_80pct_of_available",
                                        "this_is_a_calculation_not_a_measured_peak"]),
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
        THE_GOVERNING_INTERPRETATION_LIMIT=dict(
            STATUS="UNRESOLVED. The empirical half of this was withdrawn on 2026-10-02 "
                   "and the block below is retained only to show what was claimed and "
                   "why it did not survive.",
            what_was_retracted="that G2 contributes nothing against an edge-specific "
                               "cross-modal artifact. That rested on the V1 curve, whose "
                               "generator sampled block labels WITH REPLACEMENT, so its "
                               "K=200 endpoint carried about 127 factors across 200 edges "
                               "and was never one-factor-per-edge.",
            what_replaced_it="the repaired exact-K curve, "
                             "V64_STAGE4_G2_SENSITIVITY_CURVE_V2_PARTITION_REPAIRED, 100 "
                             "draws at 282 donors with realised occupancy equal to "
                             "requested K at every point. Its G2 pass rate is NON-MONOTONE "
                             "-- 0.20, 0.25, 0.40, 0.65, 0.50 -- so by the pre-committed "
                             "reading no protection claim may be made in either "
                             "direction, and the Wilson intervals at K=50 and K=200 "
                             "overlap too heavily to distinguish 0.65 from 0.50 at 20 "
                             "draws per cell.",
            what_still_stands="the STRUCTURAL argument, which never depended on the "
                              "curve: a factor varying across metacells within a donor, "
                              "loading on both modalities of one edge, and drawn "
                              "independently per edge is the same statistical object as "
                              "regulation, so nothing analysing RNA-ATAC covariation can "
                              "separate them. That is an argument, not a measurement, and "
                              "it is not established by any experiment run so far.",
            consequence_now="a positive Stage-4 result still may not be presented as "
                            "evidence of regulation, but the REASON is the structural "
                            "argument plus an unresolved empirical question, not a "
                            "demonstrated gate failure. The distinction matters because "
                            "the earlier wording claimed more than the evidence carries.",
            RETAINED_ORIGINAL_CLAIM_BELOW_FOR_THE_RECORD=True,
            statement="the frozen Stage-4 decision cannot distinguish an EDGE-SPECIFIC "
                      "cross-modal artifact from regulation, and this is a limit in "
                      "principle rather than a defect to repair.",
            why_in_principle="a factor that varies across metacells within a donor, loads "
                             "on both modalities of one edge's linked arm, and is drawn "
                             "independently per edge is the SAME statistical object as "
                             "the planted biology. Nothing analysing RNA-ATAC covariation "
                             "can separate them because there is nothing to separate.",
            evidence="V64_STAGE4_G2_SENSITIVITY_CURVE_V1. As the confound becomes less "
                     "shared across edges the G2 pass rate rises monotonically 0.15, "
                     "0.15, 0.25, 0.45, 0.55 at K = 1, 5, 20, 50, 200, and at K=200 its "
                     "interval overlaps the rate at which G2 passes genuine biology. G1 "
                     "and G3 pass in 100 percent of draws at every K, so ALL_FIVE equals "
                     "the G2 rate throughout and the entire discriminating power of the "
                     "five-gate decision against this family was one gate responding to "
                     "SHARING.",
            magnitude_does_not_help="the confound's delta is 0.972 to 1.020 times genuine "
                                    "biology at every K, so the contract's rule that a "
                                    "negligibly small Delta must not be presented as "
                                    "confirmation does not reach it.",
            consequence="a positive Stage-4 result is evidence of within-donor cross-modal "
                        "co-variation. It is not, by itself, evidence of regulation, and "
                        "it cannot be made so by any gate in the frozen design. External "
                        "corroboration with a DIFFERENT failure mode is required before a "
                        "regulatory claim.",
            supersedes="the single-draw reading in SUPERSEDED_BY_S99, which reported the "
                       "hidden confound as passing all five gates and did not yet know "
                       "that G2's apparent rejection came from how I had built the "
                       "confound"),
        OPEN_SPECIFICATION_GAP_S102=dict(
            gate="G2, control versus control",
            what_the_contract_specifies="that the contrast must not show excess. No test, "
                                        "no statistic and no level is frozen anywhere.",
            what_the_executor_implements="a two-sided 95 percent donor-bootstrap interval "
                                         "containing zero, chosen by me",
            why_it_matters="a null test of no-difference becomes stricter as the donor "
                           "count rises, so the gate rejects more with more data "
                           "regardless of whether the pipeline is sound. The V2 "
                           "observation that G2 rejects genuine biology in 22 percent of "
                           "draws at 60 donors and 38 percent at 282 is the signature of "
                           "that tightening and may be an artifact of my choice rather "
                           "than a property of the design.",
            status="OPEN. The choice belongs to the contract owner. The executor discloses "
                   "the gap in every result and reports a scale-free magnitude ratio "
                   "beside the gate, without a threshold, so both readings are visible."),
        WHAT_IS_NOT_GRANTABLE_HERE=[
            "Stage-4 execution authorisation. This closeout does not grant it and the "
            "executor does not create the artifact that would.",
            "Any claim that a positive Stage-4 result would demonstrate regulation. The "
            "structural argument forbids it; the repaired curve neither confirms nor "
            "refutes the gate behaviour and must not be cited either way.",
            "Any claim that LCB95 > 0 alone establishes a non-technical origin. The "
            "MEASURED_TECHNICAL residue forbids that reading.",
        ],
        SUPERSEDED_BY_S99_DO_NOT_CITE_WITHOUT_THIS_NOTE=dict(
            what="every limit and rate below was measured against a synthetic control arm "
                 "drawn uniformly at random, not against the frozen "
                 "PROMOTER_FIXED_DISTAL_MATCHED_CONTROL construction. They are retained "
                 "because deleting a measurement because it became inconvenient is worse "
                 "than carrying it with its qualification, but none of them characterises "
                 "the frozen Stage-4 design.",
            what_replaced_it="with the matched control in place, the measured-technical "
                             "world produces no effect at all (adjusted Delta -0.0041, "
                             "bound below zero) and is independently flagged by the "
                             "balance gate at 1.781. The design handles measured depth "
                             "confounding. The hidden confound, however, passes ALL FIVE "
                             "frozen gates at Delta +0.5937 against genuine biology's "
                             "+0.5543 -- larger than the real signal, so the contract's "
                             "no-negligible-Delta defence does not reach it.",
            status="single runs per world. The V2 calibration, pre-committed at "
                   "46f7c3342c0e88dd296a430365b52cf791324e133ce066ab54f0ea31fb9e3175, is "
                   "measuring the rates and is not yet complete. Until it lands, the "
                   "hidden-confound result is one draw per world and must be stated as "
                   "such."),
        LIMITS_FOUND_BY_RESAMPLING_THE_WORLDS=[
            "The TRUE_NULL world produced a nominally significant result in 1 of 4 seed "
            "draws: delta +0.0063 with LCB95 +0.0010, where nothing was planted. A "
            "one-sided 95% bound is permitted to do this; what matters is that it "
            "demonstrably does at this donor count. Four draws cannot estimate the rate "
            "and none is claimed.",
            "The depth residue excludes zero in 3 of 4 draws, not always. The earlier "
            "statement that a purely technical world still ends with LCB95 > 0 is "
            "weaker than it was first reported. The surviving warning is milder: a small "
            "positive LCB95 is not by itself evidence of a non-technical origin.",
            "Control-versus-control exceeded a tenth of the biology delta in 1 of 16 "
            "world-draws, in the hidden-confound world, where the confound perturbs the "
            "control arms unequally.",
            "Stable across every draw: planted biology is recovered, most of a pure "
            "depth effect is removed, and the hidden confound fools the method at 63 to "
            "74 percent of genuine biology with LCB95 always above zero.",
        ],
        UNRESOLVED_LIMITATIONS=[
            "Real-scale memory is now CALCULATED, not measured: about 6.0 GB plausible "
            "peak against 31.8 GB physical, dominated by three live copies of the 1.10 "
            "GB design tensor. It is arithmetic on declared shapes and ignores "
            "fragmentation, so it indicates feasibility and does not guarantee it. "
            "Real-scale RUNTIME remains UNMEASURED.",
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
            "S99: the synthetic control arm did not implement the frozen matched-control "
            "construction until 51b4de5a. Every control-arm number produced before that "
            "commit measured a design the project does not use. The fixture is repaired "
            "and audited, but the receipts produced before it are superseded.",
            "The post-repair world results are ONE DRAW PER WORLD. The V2 calibration "
            "sweep measuring the rates is running and not yet complete, so the "
            "hidden-confound finding is currently a single observation, not a rate.",
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
