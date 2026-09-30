#!/usr/bin/env python3
"""Design-only successor patch: restore the inherited GENE-BALANCED primary weighting.

THE DEFECT. The V1 downstream-null contract wrote, under edge-mass concentration, that
"the edge-level primary is reported ALWAYS AND IN THE SAME TABLE alongside a
promoter-equal-weighted estimate." That names an edge-level primary. But the
correspondence design contract already froze the primary estimand as the donor-averaged,
GENE-BALANCED mean difference, with EDGE_EQUAL_WEIGHTING as a predeclared sensitivity --
and its FORBIDDEN_TUNING_ACTIONS list includes, verbatim, "choosing between gene-balanced
and edge-equal weighting after the outcome". So the V1 wording did not merely create an
ambiguity; it recreated the exact choice the older contract forbids, inside a document
that declares it does not override that contract where both speak.

Left unrepaired, three weighting schemes would have been live -- gene-balanced,
edge-equal, promoter-equal -- and once biology became visible someone could have claimed
whichever looked cleanest had been intended.

WHAT THE PROMOTER-EQUAL COMPANION IS FOR, NOW THAT IT IS CORRECTLY SUBORDINATE. The older
contract's stated reason for gene-balancing is that edge-equal weighting "would let a
single high-degree promoter region determine the set-level result", which is the same
concern that motivated the companion. But gene-balanced and promoter-equal are not the
same operation: a gene may carry several promoters, so balancing genes does not equalise
promoters. The companion therefore remains a genuine additional diagnostic of the 53.1%
edge-mass concentration measured on the repaired Phase-A population. It is additive, and
it is never primary.

THE RESAMPLING CLARIFICATION. V1 said "donor resampling, promoter blocks", which could be
read as a nested donor-by-promoter resampling algorithm. No such algorithm was ever
frozen. The inherited contract freezes a nonparametric cluster bootstrap over DONORS,
4,000 replicates, seed 20260929. This patch states that donors are the SOLE resampling
unit and that promoter identity defines within-donor dependence and cross-fitting
structure only -- it never becomes an additional independent biological resampling unit.

No structural count changes. No matrix value is read. Phase A is not rerun.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
SRC = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V1.json")
DST = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V2.json")
STATE = os.path.join(DIR, "V64_PHASE_B_DECISION_STATE_V1.json")
STATE2 = os.path.join(DIR, "V64_PHASE_B_DECISION_STATE_V2.json")
DESIGN_V1 = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"


class Stop(Exception):
    pass


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def main() -> int:
    C = json.load(open(SRC))
    D = json.load(open(DESIGN_V1))

    # ---- read the inherited primary rather than restating it from memory
    pe = D["PRIMARY_ESTIMAND"]
    if "GENE-BALANCED" not in pe["definition"].upper():
        raise Stop("inherited contract does not declare a gene-balanced primary")
    if pe["predeclared_sensitivity"].split(",")[0].strip() != "EDGE_EQUAL_WEIGHTING":
        raise Stop("inherited sensitivity is not EDGE_EQUAL_WEIGHTING")
    unc = pe["uncertainty"]
    forbidden = D["FORBIDDEN_TUNING_ACTIONS"]
    tuning_clause = next((f for f in forbidden if "gene-balanced" in f.lower()), None)
    if tuning_clause is None:
        raise Stop("inherited contract has no weighting-choice prohibition to cite")

    N = copy.deepcopy(C)
    N["schema"] = "V64_PHASE_B_DOWNSTREAM_NULL_AND_STATISTICAL_CONTRACT_V2"
    N["supersedes"] = {"path": SRC, "sha256": B.sha_file(SRC),
                       "reason": "V1 named an edge-weighted estimate as primary, "
                                 "contradicting the inherited gene-balanced primary"}

    N["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["EDGE_MASS_CONCENTRATION"] = {
      "top_quartile_promoters_hold":
          C["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["EDGE_MASS_CONCENTRATION"][
              "top_quartile_promoters_hold"],
      "WEIGHTING_HIERARCHY_IS_FIXED_AND_HAS_EXACTLY_ONE_PRIMARY": {
        "PRIMARY": {
          "name": "GENE_BALANCED",
          "status": "INHERITED, not introduced here",
          "definition": pe["gene_balancing"],
          "estimand": pe["definition"],
          "why_it_is_primary": pe["why_gene_balanced_is_primary"],
          "source": {"path": DESIGN_V1, "sha256": B.sha_file(DESIGN_V1),
                     "key": "PRIMARY_ESTIMAND"}},
        "MANDATORY_COMPANION": {
          "name": "PROMOTER_EQUAL",
          "status": "ADDED HERE, prospectively, and never primary",
          "definition": "within a donor, the mean over promoters of the within-promoter "
                        "mean over that promoter's edges",
          "why_added": "the repaired Phase-A population concentrates 53.1% of retained "
                       "edges in the top quartile of promoters. Gene-balancing does not "
                       "equalise promoters, because a gene may carry several, so this is "
                       "a genuinely different diagnostic rather than a restatement of "
                       "the primary.",
          "reporting": "MANDATORY. Reported in the same table as the primary, always."},
        "PREDECLARED_SENSITIVITY": {
          "name": "EDGE_EQUAL",
          "status": "INHERITED, unchanged",
          "source": {"path": DESIGN_V1, "key": "PRIMARY_ESTIMAND.predeclared_sensitivity"},
          "reporting": pe["predeclared_sensitivity"]},
        "NON_SELECTION_RULE": {
          "rule": "Disagreement among the three weighting views is REPORTED. It is never "
                  "resolved by promoting whichever weighting is outcome-favourable.",
          "inherited_prohibition_this_enforces": tuning_clause,
          "corollary": "No result may be described using a weighting other than "
                       "GENE_BALANCED without the gene-balanced value stated beside it."},
        "why_this_section_was_repaired":
          "V1 of this contract described the edge-weighted estimate as the primary one, "
          "which named a third weighting as primary and thereby recreated exactly the "
          "post-hoc choice the inherited contract forbids. The repair restores the "
          "inherited primary and demotes the new diagnostic to a mandatory companion.",
        "guard": "the successor is checked to contain no live rule naming an "
                 "edge-weighted quantity as primary; the check is run over the emitted "
                 "contract, not over this description of it"}}

    N["SECTION_3_UNCERTAINTY_REPORTING"]["RESAMPLING_UNIT_CLARIFICATION"] = {
      "sole_resampling_unit": "DONOR",
      "method": unc["method"], "replicates": unc["replicates"], "seed": unc["seed"],
      "source": {"path": DESIGN_V1, "key": "PRIMARY_ESTIMAND.uncertainty"},
      "role_of_promoter": "Promoter identity defines WITHIN-DONOR dependence and block "
                          "structure, and is the cross-fitting unit. It does NOT become "
                          "an additional independent biological resampling unit.",
      "no_new_algorithm_is_introduced": "V1's phrase 'donor resampling, promoter blocks' "
          "could be read as a nested donor-by-promoter resampling scheme. No such scheme "
          "was ever frozen, and none is introduced. The inferential procedure is exactly "
          "the inherited donor cluster bootstrap.",
      "forbidden": ["any resampling scheme whose unit is the nucleus or the metacell",
                    "treating the promoter as an independent replication unit",
                    "any replicate count or seed other than the inherited ones"]}
    N["SECTION_3_UNCERTAINTY_REPORTING"]["primary_interval_method"] = (
        f"{unc['method']}, {unc['replicates']} replicates, seed {unc['seed']}; donors are "
        f"the sole resampling unit and promoter identity provides within-donor block "
        f"structure only")

    N["SECTION_8_PHASE_B_FIELD_SEMANTICS"]["METACELL_PARTITION_MUST_BE_PERSISTED"] = {
      "requirement": "Phase B must WRITE the metacell assignment it uses, per donor and "
                     "per nucleus, into a committed artifact bound by sha256.",
      "why": "the Stage-4 correspondence statistic is computed from metacell-level "
             "vectors within donor. If the partition were rebuilt at Stage 4, it would be "
             "rebuilt after outcomes had become visible, and a partition is exactly the "
             "kind of choice that can move a correspondence result. Persisting it makes "
             "Stage 4 use the identical partition by construction rather than by "
             "intention.",
      "binding": "the artifact's sha256 is recorded in the Phase-B receipt and Stage 4 "
                 "must verify it before use",
      "seed_and_algorithm": "unchanged from the inherited aggregation rules"}

    N["PATCH"] = {
      "schema": "V64_PHASE_B_NULL_CONTRACT_WEIGHTING_PATCH_V2", "date": "2026-09-30",
      "scope": "DESIGN ONLY. No structural count, stratum, denominator, population or "
               "Phase-A quantity is changed. No matrix value is read. Phase A is not "
               "rerun.",
      "what_changed": [
        "restored GENE_BALANCED as the sole primary weighting, read from the inherited "
        "correspondence design contract rather than restated from memory",
        "demoted the promoter-equal estimate from 'primary companion' to MANDATORY "
        "COMPANION, never primary",
        "kept EDGE_EQUAL as the inherited predeclared sensitivity",
        "added a non-selection rule citing the inherited prohibition verbatim",
        "clarified that donors are the sole resampling unit and promoter identity is "
        "block/cross-fitting structure only, with the inherited bootstrap method, "
        "replicate count and seed restated from source",
        "required the metacell partition to be persisted and hash-bound for Stage 4"],
      "what_did_not_change": ["every structural count", "the randomness strata",
                              "the randomized-null denominator", "the primary population",
                              "missingness rules", "the firewall"]}

    # ---- prove design-only: every structural block byte-identical
    STRUCTURAL = ["FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS",
                  "SECTION_1_PRIMARY_LINKED_VS_CONTROL_A",
                  "SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION",
                  "SECTION_4_PREDECLARED_SENSITIVITY_VIEWS",
                  "SECTION_5_MISSINGNESS", "SECTION_7_HIERARCHY",
                  "SECTION_9_FIREWALL_OBSERVED_IN_BUILDING_THIS_CONTRACT",
                  "governance"]
    bad = [k for k in STRUCTURAL if canon(C[k]) != canon(N[k])]
    if bad:
        raise Stop(f"patch altered structural blocks: {bad}")
    # the only permitted edits inside section 3 and 6
    if canon(C["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["promoter_degree_as_nuisance"]) != \
       canon(N["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["promoter_degree_as_nuisance"]):
        raise Stop("patch altered the degree-nuisance rule")
    if "edge-level primary" in canon(N).lower():
        raise Stop("the offending phrase survives in the successor")

    with open(DST, "w", newline="\n") as fh:
        json.dump(N, fh, indent=2)

    S = json.load(open(STATE))
    S["schema"] = "V64_PHASE_B_DECISION_STATE_V2"
    S["supersedes"] = {"path": STATE, "sha256": B.sha_file(STATE)}
    S["contract"] = {"path": DST, "sha256": B.sha_file(DST)}
    S["DECISIONS"]["primary_weighting"] = "GENE_BALANCED"
    S["DECISIONS"]["mandatory_companion_weighting"] = "PROMOTER_EQUAL"
    S["DECISIONS"]["predeclared_sensitivity_weighting"] = "EDGE_EQUAL"
    S["DECISIONS"]["n_primary_weightings"] = 1
    S["DECISIONS"]["sole_resampling_unit"] = "DONOR"
    S["DECISIONS"]["bootstrap_replicates"] = unc["replicates"]
    S["DECISIONS"]["bootstrap_seed"] = unc["seed"]
    S["DECISIONS"]["promoter_role"] = "BLOCK_AND_CROSS_FITTING_ONLY"
    S["DECISIONS"]["metacell_partition_persisted_for_stage4"] = True
    S["DECISIONS"].pop("promoter_equal_companion", None)
    with open(STATE2, "w", newline="\n") as fh:
        json.dump(S, fh, indent=2)

    print("DESIGN-ONLY WEIGHTING PATCH WRITTEN")
    print(f"  structural blocks altered : 0 of {len(STRUCTURAL)}")
    print(f"  PRIMARY                   : GENE_BALANCED (inherited)")
    print(f"  MANDATORY COMPANION       : PROMOTER_EQUAL (added, never primary)")
    print(f"  PREDECLARED SENSITIVITY   : EDGE_EQUAL (inherited)")
    print(f"  resampling                : {unc['method']}, {unc['replicates']} reps, "
          f"seed {unc['seed']}; promoter = block/cross-fitting only")
    print(f"  contract V2 sha256        : {B.sha_file(DST)}")
    print(f"  state V2 sha256           : {B.sha_file(STATE2)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
