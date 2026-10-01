#!/usr/bin/env python3
"""Statistical contract V3: freeze the enumeration reference rules R1, R2 and R3.

WHY THIS EXISTS. The measurement substrate contract introduced R3 -- when one arm of a
small-support A/B pair is large, enumerate the small arm completely and hold the large arm
at its realised draw -- while declaring `changes_no_statistical_decision = true`. Those two
statements cannot both be true. R3 determines the reference distribution for 21 pairs, which
is inferential semantics, not a storage choice. The design may be sound; the authority was
in the wrong document.

So the rules move upstream, into the statistical contract where a reference distribution
belongs, and this contract states plainly that it DOES make a statistical decision. The
substrate contract is then rebuilt to bind this digest and merely implement what is frozen
here.

Nothing about the choice is retrospective: R3 was fixed before any RNA or ATAC matrix value
was read, and remains so.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import copy
import gzip
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import nihcard_stage3_phase_a_exact_executor_v2 as EX            # noqa: E402

DIR = "results/v64/phase_b_design"
SRC = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V2.json")
DST = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
STATE2 = os.path.join(DIR, "V64_PHASE_B_DECISION_STATE_V2.json")
STATE3 = os.path.join(DIR, "V64_PHASE_B_DECISION_STATE_V3.json")
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"


class Stop(Exception):
    pass


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def main() -> int:
    C = json.load(open(SRC))
    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    by = defaultdict(dict)
    for r in rows:
        by[r["edge_index"]]["L" if r["population"] == "LINKED"
                            else r["control_role"]] = r
    A = EX.load_A_exact()

    def members(e, s):
        iv, sup = A[e][s]
        o = []
        for a, b in iv:
            o.extend(range(a, b + 1))
        o.extend(sup)
        return o

    r1, r2, r3 = [], [], []
    for e, v in by.items():
        na, sa = v["A"]["admissible_start_count"], v["A"]["drawn_side"]
        if 2 <= na <= 10:
            r1.append(e)
        if "B" not in v:
            continue
        nb, sb = v["B"]["admissible_start_count"], v["B"]["drawn_side"]
        if na == 1 or nb == 1 or not (na <= 10 or nb <= 10):
            continue
        (r2 if (na <= 10 and nb <= 10) else r3).append(
            dict(edge=e, n_A=na, n_B=nb, side_A=sa, side_B=sb,
                 small_arm="A" if na <= nb else "B", same_side=sa == sb))
    joint_pairs = sum(p["n_A"] * p["n_B"] for p in r2)
    small_is_A = [p for p in r3 if p["small_arm"] == "A"]
    r3_same_side = [p for p in r3 if p["same_side"]]
    r3_A_already_in_r1 = [p for p in small_is_A if p["edge"] in set(r1)]

    N = copy.deepcopy(C)
    N["schema"] = "V64_PHASE_B_DOWNSTREAM_NULL_AND_STATISTICAL_CONTRACT_V3"
    N["supersedes"] = {"path": SRC, "sha256": B.sha_file(SRC),
                       "reason": "V2 froze exact enumeration for CONTROL_A support 2-10 "
                                 "but did not state what the reference is when an A/B "
                                 "pair has one small and one large arm. That rule was "
                                 "introduced downstream in a contract claiming to change "
                                 "no statistical decision, which was not true of it."}
    N["THIS_CONTRACT_MAKES_A_STATISTICAL_DECISION"] = {
        "declared": True,
        "which": "the enumeration reference rules R1, R2 and R3 below, and in particular "
                 "the conditional reference R3",
        "when": "before any RNA or ATAC matrix value was read; the outcome remains sealed",
        "why_declared_explicitly": "an inferential rule introduced inside a document that "
            "declares itself statistically neutral is a rule nobody audited as a "
            "statistical choice. Placing it here makes it reviewable as one."}

    N["SECTION_10_ENUMERATION_REFERENCE_RULES"] = {
      "scope": "These rules define the REFERENCE DISTRIBUTION used wherever the frozen "
               "exact-enumeration requirement applies. They do not alter the primary "
               "population, the retained counts, the randomized-null denominator, or the "
               "weighting hierarchy.",
      "R1_PRIMARY_EXACT_A_SIDE": {
        "governs": "the exact randomisation reference for the primary linked-versus-"
                   "CONTROL_A contrast on edges whose CONTROL_A support is small",
        "eligibility": "retained edge with CONTROL_A admissible support in [2, 10]",
        "rule": "enumerate ALL admissible alternatives on CONTROL_A's drawn side and "
                "compute the exact randomisation distribution over them",
        "edges": len(r1),
        "exactness": "UNCONDITIONAL and exact. The whole reference set is materialised."},
      "R2_EXACT_JOINT_AB": {
        "governs": "the CONTROL_A versus CONTROL_B null calibration reference",
        "eligibility": "fully-randomised A/B pair with BOTH arms' support in [2, 10]",
        "rule": "the reference is the exact JOINT distribution over independent re-draws "
                "of both arms from their own side-specific admissible sets",
        "pairs": len(r2), "ordered_pairs_in_reference": joint_pairs,
        "exactness": "UNCONDITIONAL and exact."},
      "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM": {
        "governs": "the CONTROL_A versus CONTROL_B null calibration reference for pairs "
                   "where a full joint cannot be materialised. It governs NOTHING in the "
                   "primary linked-versus-control contrast.",
        "eligibility": "fully-randomised A/B pair where exactly one arm has admissible "
                       "support in [2, 10] and the other has support greater than 10",
        "pairs": len(r3),
        "which_arm_is_small": {
          "recorded_per_pair": True,
          "CONTROL_A_is_the_small_arm": len(small_is_A),
          "CONTROL_B_is_the_small_arm": len(r3) - len(small_is_A)},
        "arm_geometry_measured": {
          "pairs_drawing_on_the_SAME_side": len(r3_same_side),
          "pairs_drawing_on_DIFFERENT_sides": len(r3) - len(r3_same_side),
          "small_arm_support_sizes": sorted(min(p["n_A"], p["n_B"]) for p in r3),
          "large_arm_support_min": min(max(p["n_A"], p["n_B"]) for p in r3),
          "large_arm_support_max": max(max(p["n_A"], p["n_B"]) for p in r3)},
        "rule": "enumerate the SMALL arm completely over its own side-specific admissible "
                "set, and hold the LARGE arm fixed at its already-realised draw. The "
                "realised large-arm start is recorded per pair alongside the reference.",
        "WHY_THE_CONDITIONAL_IS_THE_ESTIMAND_AND_NOT_AN_APPROXIMATION": {
          "claim": "R3 targets a conditional estimand exactly. It does not approximate "
                   "the joint estimand of R2.",
          "argument": "CONTROL_A and CONTROL_B are drawn independently from their own "
              "side-specific admissible sets. Conditioning on the realised value of one "
              "draw therefore leaves the other draw exactly uniform over its own set. The "
              "enumerated reference is thus the exact conditional distribution of the "
              "small arm given the realised large arm -- an exact statement about a "
              "narrower question, not an approximate statement about a wider one.",
          "what_the_narrower_question_is": "given this particular large-arm control, how "
              "unusual is the small-arm control's realised position among its lawful "
              "alternatives?",
          "measured_support_for_the_independence_premise": "all "
              f"{len(r3) - len(r3_same_side)} of the {len(r3)} R3 pairs draw on DIFFERENT "
              "sides, so the two arms range over disjoint admissible sets and the "
              "independence of the draws is structural rather than assumed."},
        "MANDATORY_CAVEAT_ON_UNCERTAINTY": {
          "statement": "A conditional reference captures ONLY small-arm randomisation "
                       "variability. Large-arm variability is excluded by construction, "
                       "so any interval or tail probability derived under R3 is NARROWER "
                       "than its unconditional counterpart would be.",
          "required_label": "CONDITIONAL_ON_REALISED_LARGE_ARM",
          "forbidden": "pooling an R3 quantity with R1 or R2 quantities, or comparing "
                       "them side by side, without that label present",
          "why_frozen_now": "an unlabelled conditional interval read as an unconditional "
                            "one understates uncertainty, and the direction of that error "
                            "is toward over-confidence"},
        "why_not_the_full_joint": f"the large arms range from "
            f"{min(max(p['n_A'], p['n_B']) for p in r3):,} to "
            f"{max(max(p['n_A'], p['n_B']) for p in r3):,} admissible starts. A joint "
            "reference would require materialising donor-by-metacell measurements for "
            "that many intervals per pair, which is not feasible and would dwarf the "
            "entire Phase-B substrate.",
        "alternative_considered_and_rejected": {
          "option": "Monte Carlo sampling over the large arm with a frozen replicate "
                    "count and seed",
          "rejected_because": "it would substitute a sampling approximation where an "
              "exact conditional statement is available, and it would require choosing "
              "WHICH large-arm alternatives to materialise -- a new selection rule needing "
              "its own justification and its own audit."},
        "overlap_with_R1": {
          "R3_pairs_whose_small_arm_is_CONTROL_A": len(small_is_A),
          "of_those_already_required_by_R1": len(r3_A_already_in_r1),
          "reading": "where the small arm is CONTROL_A, R1 already requires that arm's "
                     "full enumeration, so R3 adds no new materialisation for those "
                     "pairs. R3's genuinely additional requirement is the small CONTROL_B "
                     f"arm in the remaining {len(r3) - len(small_is_A)} pairs."}},
      "CROSS_CONTRACT_REQUIREMENT": {
        "rule": "Any enumeration rule implemented by the measurement substrate contract "
                "must exist here, by the same identifier and with the same eligibility "
                "and reference definition. A substrate rule with no counterpart here is a "
                "statistical decision placed outside statistical authority.",
        "rule_identifiers": ["R1_PRIMARY_EXACT_A_SIDE", "R2_EXACT_JOINT_AB",
                             "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"]},
      "what_these_rules_do_NOT_change": [
        "the retained population", "the randomized-null denominator",
        "the randomness strata", "the weighting hierarchy",
        "the resampling unit, replicate count or seed",
        "which comparisons are eligible for null calibration"]}

    PRESERVE = ["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS",
                "SECTION_1_PRIMARY_LINKED_VS_CONTROL_A",
                "SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION",
                "SECTION_4_PREDECLARED_SENSITIVITY_VIEWS", "SECTION_5_MISSINGNESS",
                "SECTION_6_DONOR_AND_STATISTICAL_MASS", "SECTION_7_HIERARCHY",
                "SECTION_8_PHASE_B_FIELD_SEMANTICS",
                "SECTION_9_FIREWALL_OBSERVED_IN_BUILDING_THIS_CONTRACT", "governance"]
    bad = [k for k in PRESERVE if canon(C[k]) != canon(N[k])]
    if bad:
        raise Stop(f"V3 altered preserved blocks: {bad}")
    if canon(C["SECTION_3_UNCERTAINTY_REPORTING"]) != canon(
            N["SECTION_3_UNCERTAINTY_REPORTING"]):
        raise Stop("V3 altered the uncertainty section")

    with open(DST, "w", newline="\n") as fh:
        json.dump(N, fh, indent=2)

    S = json.load(open(STATE2))
    S["schema"] = "V64_PHASE_B_DECISION_STATE_V3"
    S["supersedes"] = {"path": STATE2, "sha256": B.sha_file(STATE2)}
    S["contract"] = {"path": DST, "sha256": B.sha_file(DST)}
    S["DECISIONS"]["enumeration_rules"] = ["R1_PRIMARY_EXACT_A_SIDE",
                                           "R2_EXACT_JOINT_AB",
                                           "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"]
    S["DECISIONS"]["R1_edges"] = len(r1)
    S["DECISIONS"]["R2_pairs"] = len(r2)
    S["DECISIONS"]["R3_pairs"] = len(r3)
    S["DECISIONS"]["R3_reference"] = "EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"
    S["DECISIONS"]["R3_required_label"] = "CONDITIONAL_ON_REALISED_LARGE_ARM"
    with open(STATE3, "w", newline="\n") as fh:
        json.dump(S, fh, indent=2)

    print("STATISTICAL CONTRACT V3 WRITTEN -- R1/R2/R3 now frozen as statistical authority")
    print(f"  preserved blocks altered : 0 of {len(PRESERVE) + 1}")
    print(f"  R1 edges {len(r1)}   R2 pairs {len(r2)} ({joint_pairs} ordered)   "
          f"R3 pairs {len(r3)}")
    print(f"  R3 small arm is A in {len(small_is_A)}, B in {len(r3) - len(small_is_A)}; "
          f"{len(r3) - len(r3_same_side)} of {len(r3)} draw on different sides")
    print(f"  R3 A-small pairs already covered by R1: {len(r3_A_already_in_r1)}"
          f" of {len(small_is_A)}")
    print(f"  contract V3 sha256 {B.sha_file(DST)}")
    print(f"  state V3    sha256 {B.sha_file(STATE3)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
