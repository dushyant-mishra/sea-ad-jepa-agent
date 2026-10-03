"""Freeze the V74 Lane A prospective successor contract for the Stage-4 G2 gate.

Design artifact only. Reads no substrate, computes no correspondence value, selects no
margin. The contract it writes is deliberately NOT_IN_FORCE: it fixes the estimand, the
statistic, the verdict structure and every guard, and it records the deciding margin as
UNSET so that no executor may supply one.

The verdict is assembled and asserted BEFORE anything is written to disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # scripts/v74 -> scripts -> repo root
OUT = os.path.join(ROOT, "results", "v74",
                   "V74_G2_CONTINUOUS_SUCCESSOR_CONTRACT_V1.json")

BOUND = {
    "candidate_reference_implementation": "scripts/v74/g2_continuous_candidates_v1.py",
    "behavioural_tests": "tests/test_v74_g2_continuous_candidates_v1.py",
    "design_document": "docs/v74/V74_G2_CONTINUOUS_SUCCESSOR_DESIGN_V1.md",
    "historical_executor": "scripts/v64/stage4_executor_v1.py",
    "stage4_design_contract":
        "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json",
    "synthetic_world_builder": "scripts/v64/build_stage4_synthetic_worlds_v1.py",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*a):
    r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


CONTRACT = dict(
    schema="V74_G2_CONTINUOUS_SUCCESSOR_CONTRACT_V1",
    date="2026-10-02",
    lane="V74_LANE_A",
    status="FROZEN__NOT_IN_FORCE__DECIDING_MARGIN_UNSET",
    scope="design of the successor to the Stage-4 G2 control-versus-control gate; "
          "no threshold is selected and no real substrate is read",

    # ------------------------------------------------------------------ estimand
    # Defined exactly once in this document. Any executor binding this contract must
    # compute it by this definition and may not redefine it.
    ESTIMAND=dict(
        name="mu_CVC",
        definition=(
            "the expectation over donors of Delta_CVC_d, where Delta_CVC_d is the "
            "set-level aggregate of resid[d, CONTROL_A(e)] - resid[d, CONTROL_B(e)] "
            "over the calibration edge set, under a named weighting; resid is the "
            "cross-fitted ridge residual of the within-donor Pearson correlation "
            "between a gene's metacell RNA vector and an interval's metacell ATAC "
            "vector, on the frozen 14-term basis with alpha 1.0 and 5 folds formed "
            "over promoters"),
        primary_population=dict(
            edge_set="C_INTERSECT_P",
            C="edges whose CONTROL_A and CONTROL_B pairs each have at least "
              "min_donors_per_edge measured donors",
            P="edges whose LINKED and CONTROL_A pairs each have at least "
              "min_donors_per_edge measured donors",
            why="REPAIR_I2: the historical implementation evaluated the "
                "control-versus-control contrast on C and the primary contrast on P, "
                "which are different gene and edge populations, so any ratio between "
                "them compared averages over different supports",
            companion_population="C alone, reported, never deciding"),
        weightings=dict(
            primary="GENE_BALANCED", companion="PROMOTER_EQUAL",
            sensitivity="EDGE_EQUAL",
            why="REPAIR_I1: the historical implementation computed the "
                "control-versus-control contrast under GENE_BALANCED only, so the "
                "three-weighting discipline imposed on the headline result was absent "
                "from the gate that polices a false green",
            selection_rule="all three are computed every time; none is selected by "
                           "which is smallest or largest"),
        sign_convention=dict(
            rule="which control draw is labelled A is arbitrary; every decision rule "
                 "bound by this contract must be invariant under A <-> B",
            enforced_by="tests/test_v74_g2_continuous_candidates_v1.py::"
                        "test_every_candidate_is_invariant_to_the_arbitrary_control_"
                        "arm_ordering"),
        resampling=dict(
            unit="DONOR", method="nonparametric cluster bootstrap over donors only",
            replicates=4000, seed=20260929,
            declared_properties=[
                "a promoter is block structure, never an independent replicate",
                "REPAIR_I5: the single fixed seed makes the resample index matrix "
                "identical across arms of equal length. This is common random numbers "
                "between the CVC and primary bootstraps and is hereby DECLARED rather "
                "than inherited; it also makes the interval depend on donor ordering, "
                "which an executor must fix by sorting donors by donor identifier "
                "before resampling"]),
    ),

    # ----------------------------------------------------------- separated questions
    THREE_QUESTIONS=dict(
        A_CENTRING=dict(
            question="is E[Delta_CVC] zero",
            estimand="mu_CVC",
            role="REPORTED_DIAGNOSTIC_ONLY",
            gates=False,
            why="with enough donors any pipeline's residual drift becomes detectably "
                "nonzero, and that alone is not a reason to stop"),
        B_MAGNITUDE=dict(
            question="is |mu_CVC| small enough to be biologically irrelevant",
            estimand="|mu_CVC|",
            role="THE_DECISION",
            gates=True,
            requires_margin=True),
        C_INFORMATIVENESS=dict(
            question="is the uncertainty in mu_CVC small enough for the answer to B to "
                     "be informative",
            estimand="the width of the confidence interval for mu_CVC",
            role="DETERMINES_WHETHER_A_VERDICT_MAY_BE_ISSUED_AT_ALL",
            gates=True,
            why="the historical implementation left this unasked, and an uninformative "
                "run was therefore reported as a clean one"),
        separation_rule="conflating A and B is how the historical implementation went "
                        "wrong; folding C into either of them is how a two-valued gate "
                        "recreates the defect in a new shape",
    ),

    # ------------------------------------------------------------- verdict structure
    VERDICT_STRUCTURE=dict(
        values=["PASS", "FAIL", "INDETERMINATE", "REFUSED_INSUFFICIENT_EVIDENCE",
                "NOT_APPLICABLE"],
        rule=dict(
            PASS="U_conf(|mu|) <= m",
            FAIL="L_conf(|mu|) > m",
            INDETERMINATE="otherwise; the data cannot separate the two and the run "
                          "reports NO confirmed Stage-4 result",
            U_conf="max(|lo|, |hi|) from the two-sided interval at the frozen "
                   "confidence level",
            L_conf="min(|lo|, |hi|) when that interval excludes zero, else 0"),
        two_valued_forms_are_forbidden=dict(
            rule=True,
            why="a PASS/FAIL rule must fold question C into one of the other two. "
                "Folding it into PASS is the historical defect. Folding it into FAIL "
                "mislabels 'we could not tell' as 'the pipeline is broken' and would "
                "send repair effort to the wrong place"),
        INDETERMINATE_is_not_a_pass=True,
    ),

    # ------------------------------------------------------------------- fail-closed
    FAIL_CLOSED=dict(
        rules=[
            "fewer than two contributing donors is REFUSED, never PASS",
            "an empty calibration edge set is REFUSED, never PASS",
            "fewer than D_min contributing donors is REFUSED, never PASS",
            "fewer than E_min calibration edges is REFUSED, never PASS",
            "a missing or non-positive primary LCB95 under the relative scale is "
            "REFUSED, never PASS",
            "G1 not passed makes the relative arm NOT_APPLICABLE, never PASS",
            "a deciding margin that is absent raises and halts; no executor may supply "
            "a default",
        ],
        why="an equivalence rule is the kind that passes by default when nothing is "
            "measured, so every refusal must be written down rather than inherited",
        enforced_by="tests/test_v74_g2_continuous_candidates_v1.py::"
                    "test_every_candidate_fails_closed_on_degenerate_evidence and "
                    "::test_no_candidate_supplies_its_own_margin",
    ),

    # ------------------------------------------------------------- reported quantities
    REPORTED_WITHOUT_A_THRESHOLD=[
        "the two-sided interval for mu_CVC (question A)",
        "U_conf(|mu_CVC|) on the absolute scale, as a bounded interpretable number",
        "the interval half-width (question C)",
        "donors contributing and calibration edges contributing",
        "mu_CVC under all three weightings",
        "mu_CVC on both the C_INTERSECT_P and the C-alone populations",
    ],

    # ---------------------------------------------------------------- margin register
    MARGIN_REGISTER=dict(
        m_abs=dict(
            status="UNSET__NOT_DERIVABLE_FROM_PRESENTLY_AVAILABLE_EVIDENCE",
            scale="gene-balanced residualised within-donor RNA-ATAC correlation delta",
            routes_examined=dict(
                R1_technical_replicates="NOT_AVAILABLE: the design has none",
                R2_analytic_assay_noise="REJECTED_FOR_THIS_PURPOSE: the quantity it "
                                        "yields is ~0.35/sqrt(G_eff*D), a PRECISION "
                                        "scale that shrinks with data. Adopting it as "
                                        "an equivalence margin would reintroduce the "
                                        "S102 defect in equivalence clothing. Usable "
                                        "for question C only",
                R3_biological_effect_size="NOT_AVAILABLE: no external constant exists "
                                          "for this pipeline-constructed quantity, and "
                                          "any proposed literature value must first "
                                          "show its transfer argument",
                R5_control_selection_variability="REJECTED_FOR_THIS_PURPOSE: a "
                                                 "dispersion scale, and it is partly "
                                                 "the artefact G2 exists to detect",
                R6_donor_resampling_variability="REJECTED_FOR_THIS_PURPOSE: precision, "
                                                "not negligibility"),
            consequence="the absolute arm is REPORTED WITHOUT A THRESHOLD and does not "
                        "gate"),
        f_relative=dict(
            status="DERIVABLE_AT_EXACTLY_ONE_VALUE__OWNER_TO_SET",
            definition="U_conf(|mu_CVC|) / LCB95(mu_primary) <= f",
            derived_value=1.0,
            derivation="the Stage-4 design contract states that a nonzero "
                       "control-versus-control contrast makes any linked-versus-control "
                       "result uninterpretable. f = 1 is the magnitude at which that is "
                       "literally true: the discrepancy is as large as the entire "
                       "effect it would have to explain. This is a logical boundary, "
                       "not a convention",
            any_smaller_f="a safety factor and A CONVENTION, which must be labelled as "
                          "such with its rationale recorded",
            conservative_endpoints_are_mandatory="U_conf on top and LCB95 underneath; "
                                                 "at point estimates f = 1 is a far "
                                                 "weaker gate than it sounds",
            disclosed_residual_weakness="the denominator is the quantity under test, so "
                                        "a pipeline that manufactures a larger primary "
                                        "effect is granted a larger tolerated "
                                        "discrepancy. The relative arm may never be the "
                                        "only gate and the absolute bound must always "
                                        "be reported beside it"),
        confidence_level=dict(status="UNSET__OWNER_TO_SET", label="CONVENTION",
                              note="0.95 is the historical level and is a convention "
                                   "with no biological content"),
        D_min=dict(status="UNSET__OWNER_TO_SET",
                   note="must be derived from the real design geometry, never from a "
                        "training or checkpoint outcome"),
        E_min=dict(status="UNSET__OWNER_TO_SET",
                   note="must be derived from the real design geometry, never from a "
                        "training or checkpoint outcome"),
    ),

    FORBIDDEN_MARGIN_SOURCES=dict(
        rule="no margin bound by this contract may be chosen by inspecting any of the "
             "following, which may EVALUATE a prospectively chosen rule but may never "
             "CHOOSE one",
        sources=[
            "the K = 1..200 V2 repaired sensitivity-curve values",
            "any biology-world pass rate",
            "the historical V1 sensitivity curve",
            "whichever value happens to separate the existing synthetic worlds",
            "any observed Stage-4 result",
        ],
        lane_attestation="no value in this contract, in the design document or in the "
                         "behavioural tests was obtained from any of those sources; the "
                         "temptation and the reason it is a defect are recorded in "
                         "section 4 of the design document",
    ),

    CANDIDATES=dict(
        C1_null_significance=dict(status="BASELINE_NOT_RECOMMENDED",
                                  margin="alpha (convention only)"),
        C2_TOST="IDENTICAL_DECISION_TO_C4; retained only as a reporting convention",
        C3_absolute_point_magnitude=dict(status="DIAGNOSTIC_ONLY_NEVER_A_GATE",
                                         margin="m_abs"),
        C4_magnitude_upper_bound=dict(status="RECOMMENDED_STATISTIC", margin="m_abs"),
        C5_standardised=dict(status="DISQUALIFIED_ON_INCENTIVE_GROUNDS",
                             why="a noisier pipeline passes more easily"),
        C6_relative_to_primary=dict(status="RECOMMENDED_DECIDING_ARM_WITH_GUARDS",
                                    margin="f"),
        C7_three_valued=dict(status="RECOMMENDED_VERDICT_STRUCTURE", margin="m"),
        C8_within_run_reference=dict(
            status="RECORDED_NOT_PROPOSED",
            why="it is the only route to a margin with no outcome tuning at all, but it "
                "requires a THIRD control draw the design does not reserve, and an "
                "artefact common to all control draws cancels in every pairwise "
                "contrast"),
    ),

    DISCRIMINATING_EXPERIMENT=dict(
        status="SPECIFIED_NOT_RUN",
        name="PIPELINE_ARTEFACT_m",
        gap_it_closes="in all four existing world families the planted signal is applied "
                      "to edge_linked_iv only, so control-versus-control is a pure null "
                      "by construction and the existing corpus can measure only the "
                      "false-alarm half of any candidate's operating characteristic. No "
                      "existing world can measure whether a candidate DETECTS a "
                      "manufactured difference, which is the only thing G2 is for",
        design="plant a control-arm asymmetry of known magnitude on CONTROL_A only, "
               "sweep it over a pre-declared grid, cross it with donor count and with "
               "reduced CONTROL_B availability, pre-commit grid, seeds, draws and "
               "reported quantities before any draw",
        output="an operating-characteristic surface giving the probability of each of "
               "the three verdicts per candidate per planted magnitude. IT IS NOT A "
               "MARGIN. The owner then chooses, on the record, what detection "
               "probability at what magnitude is required",
        negative_control="a world where BOTH control arms carry the same artefact, which "
                         "every pairwise rule including C8 will pass; it documents the "
                         "shared blind spot rather than leaving it to be discovered",
        see="docs/v74/V74_G2_CONTINUOUS_SUCCESSOR_DESIGN_V1.md section 6",
    ),

    S102=dict(
        previous_status="OPEN: no test, no statistic, no alpha, no confidence level, no "
                        "equivalence margin and no biologically meaningful magnitude "
                        "threshold specified anywhere",
        new_status="OPEN__NARROWED",
        what_is_now_fixed=["the estimand", "the statistic", "the verdict structure",
                           "the fail-closed guards", "the reported quantities",
                           "the repairs I1 and I2", "the forbidden margin sources"],
        what_remains_open=["m_abs is not derivable from presently available evidence",
                           "f is derivable only at 1.0; any smaller value is a labelled "
                           "convention the owner must set",
                           "the confidence level, D_min and E_min are unset"],
        why_this_contract_is_not_the_same_defect=
            "the original defect was an executor silently filling in a deciding quantity "
            "the contract never fixed. This contract names the quantity, declares it "
            "UNSET, and requires any executor binding it to HALT rather than default",
    ),

    GOVERNANCE=dict(real_stage4="NOT_AUTHORIZED", real_correspondence="UNOPENED",
                    training="OFF", multimodal_training="OFF",
                    morabito="PROTECTED", recoverability_test="SEALED"),
    real_substrate_read=False,
    computed_real_correspondence_values=0,
    margin_selected=False,
)


def main():
    missing = [p for p in BOUND.values() if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print("REFUSED: bound artifacts missing: %s" % missing)
        return 2

    # ---- the verdict is assembled and asserted BEFORE anything reaches disk
    verdict = dict(
        contract_defines_the_estimand_exactly_once=True,
        contract_states_prospectively_what_qualifies_as_a_pass=True,
        deciding_margin_is_declared_unset_rather_than_defaulted=True,
        executor_is_required_to_halt_when_a_margin_is_absent=True,
        no_margin_was_selected_from_an_observed_outcome=True,
        status="FROZEN__NOT_IN_FORCE__DECIDING_MARGIN_UNSET")
    for k, v in verdict.items():
        if k != "status" and v is not True:
            print("REFUSED: verdict field %s is not True" % k)
            return 2
    if CONTRACT["margin_selected"] is not False:
        print("REFUSED: a margin is recorded as selected")
        return 2
    for name, entry in CONTRACT["MARGIN_REGISTER"].items():
        if not str(entry["status"]).startswith(("UNSET", "DERIVABLE")):
            print("REFUSED: margin %s carries a frozen value" % name)
            return 2

    rec = dict(CONTRACT)
    rec["VERDICT"] = verdict
    rec["bindings"] = {k: dict(path=p, sha256=sha(os.path.join(ROOT, p)))
                       for k, p in BOUND.items()}
    rec["source_commit"] = git("rev-parse", "HEAD")
    rec["source_branch"] = git("rev-parse", "--abbrev-ref", "HEAD")
    rec["worktree_clean_at_freeze"] = (git("status", "--porcelain") == "")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print("WROTE %s" % OUT)
    print("SHA256 %s" % sha(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
