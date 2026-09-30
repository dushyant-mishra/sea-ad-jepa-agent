#!/usr/bin/env python3
"""Freeze the downstream statistical / null treatment of the accepted Phase-A population.

This runs BEFORE any RNA or ATAC matrix value is read, so that Phase B cannot tune its
own inferential rules after seeing biology. It computes only structural quantities from
the Phase-A artifact -- draw sides, admissible-set sizes, coincidence, promoter degree --
and no correspondence statistic of any kind.

THE MEASUREMENT THAT DRIVES THE NULL DESIGN. Among the 11,012 retained edges where both
controls exist, 166 have CONTROL_A == CONTROL_B. 158 of those are structurally forced:
both draws landed on a side whose admissible set has exactly one element, so agreement
was arithmetically guaranteed and carries no information about whether the random-control
generator is calibrated. Pooling them gives 166/11,012 = 1.507% agreement; the genuinely
randomized rate is 8/10,654 = 0.075%. Pooling would therefore inflate apparent null
agreement roughly twentyfold, in the direction that makes the generator look better than
it is. That is why the eligible denominator is frozen here, before any outcome is seen.

WHAT THIS CONTRACT DOES NOT DO. It does not decide any biological question, does not
compute any linked-versus-control quantity, and does not authorise Phase B. It fixes the
rules so that when Phase B runs, the rules were not chosen with the answer in view.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED. TD60=BLOCKED.
Morabito PROTECTED. Protected correspondence UNOPENED.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
PATCHED = "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json"
DESIGN_V1 = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
FEATURE_V2 = "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json"
PHASE_A_V2 = "results/v64/V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.json"
OUT_DIR = "results/v64/phase_b_design"


def blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True).stdout.strip() or "UNCOMMITTED_AT_BUILD_TIME"


def classify(rows):
    by = defaultdict(dict)
    for r in rows:
        by[r["edge_index"]]["L" if r["population"] == "LINKED"
                            else r["control_role"]] = r
    cls, coinc = Counter(), Counter()
    for e, v in by.items():
        a = v["A"]
        if "B" not in v:
            cls["B_UNAVAILABLE_NOT_EVALUABLE"] += 1
            continue
        b = v["B"]
        na, nb = a["admissible_start_count"], b["admissible_start_count"]
        same = a["drawn_side"] == b["drawn_side"]
        if same and na == 1:
            k = "STRUCTURALLY_FORCED_IDENTICAL"
        elif na == 1 or nb == 1:
            k = "PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM"
        elif na <= 10 or nb <= 10:
            k = "FULLY_RANDOMIZED_SMALL_SUPPORT"
        else:
            k = "FULLY_RANDOMIZED_SUPPORT_GT10"
        cls[k] += 1
        if same and a["hg19_start"] == b["hg19_start"]:
            coinc[k] += 1
    return dict(cls), dict(coinc), by


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    cls, coinc, by = classify(rows)
    n_edges = len(by)
    elig = cls["FULLY_RANDOMIZED_SUPPORT_GT10"] + cls["FULLY_RANDOMIZED_SMALL_SUPPORT"]
    elig_coinc = (coinc.get("FULLY_RANDOMIZED_SUPPORT_GT10", 0)
                  + coinc.get("FULLY_RANDOMIZED_SMALL_SUPPORT", 0))
    both = n_edges - cls["B_UNAVAILABLE_NOT_EVALUABLE"]
    all_coinc = sum(coinc.values())

    strata = Counter()
    for e, v in by.items():
        n = v["A"]["admissible_start_count"]
        strata["FORCED_SINGLETON_SUPPORT_1" if n == 1 else
               "SMALL_RANDOMIZED_SUPPORT_2_TO_10" if n <= 10 else
               "RANDOMIZED_SUPPORT_GT10"] += 1

    deg = Counter(v["L"]["promoter_key"] for v in by.values())
    top = sorted(deg.values(), reverse=True)
    cut = max(1, len(deg) // 4)

    C = {
      "schema": "V64_PHASE_B_DOWNSTREAM_NULL_AND_STATISTICAL_CONTRACT_V1",
      "date": "2026-09-30",
      "status": "PROSPECTIVELY_FROZEN_BEFORE_ANY_RNA_OR_ATAC_MATRIX_VALUE_IS_READ",
      "purpose": "Fix how each Phase-A randomness stratum contributes to every downstream "
                 "analysis, so Phase B cannot tune its inferential rules after seeing "
                 "biology.",
      "authority_it_composes_with": {
        "phase_a_population": {"path": PATCHED, "sha256": B.sha_file(PATCHED),
                               "git_blob": blob(PATCHED)},
        "phase_a_contract": {"path": PHASE_A_V2, "sha256": B.sha_file(PHASE_A_V2)},
        "feature_artifact_contract": {"path": FEATURE_V2,
                                      "sha256": B.sha_file(FEATURE_V2)},
        "correspondence_design_contract": {"path": DESIGN_V1,
                                           "sha256": B.sha_file(DESIGN_V1)},
        "relationship": "This contract ADDS the randomness-stratum treatment. It does not "
                        "restate or override the aggregation, metacell, support or "
                        "independent-unit rules already frozen in the correspondence "
                        "design contract; where both speak, that contract governs."},

      "FROZEN_PHASE_A_STRUCTURAL_DIAGNOSTICS": {
        "rule": "These are final structural properties of the accepted population. They "
                "must never be recomputed from, or revised in light of, biological "
                "outcomes.",
        "retained_edges": n_edges, "retained_promoters": len(deg),
        "control_A_support_strata": dict(strata),
        "control_A_support_eq_1": strata["FORCED_SINGLETON_SUPPORT_1"],
        "control_A_support_le_10": (strata["FORCED_SINGLETON_SUPPORT_1"]
                                    + strata["SMALL_RANDOMIZED_SUPPORT_2_TO_10"]),
        "coincidence_total": all_coinc,
        "coincidence_structurally_forced": coinc.get("STRUCTURALLY_FORCED_IDENTICAL", 0),
        "coincidence_chance_capable": elig_coinc,
        "null_arm_availability": {
          "CONTROL_B_available_among_retained": both,
          "CONTROL_B_unavailable": cls["B_UNAVAILABLE_NOT_EVALUABLE"],
          "A_failed_B_succeeded_not_rescued": 2200,
          "A_passed_B_failed": cls["B_UNAVAILABLE_NOT_EVALUABLE"]}},

      "SECTION_1_PRIMARY_LINKED_VS_CONTROL_A": {
        "primary_population": "ALL retained edges",
        "n": n_edges,
        "forced_singleton_edges_included": True,
        "small_support_edges_included": True,
        "weighting_or_exclusion_by_control_support": "NONE",
        "why_no_exclusion": "Admissible-set size is a function of PU.1 and NIH-CARD track "
            "density inside the distance band. Excluding small-support edges would select "
            "the population on genomic coverage, which is itself associated with "
            "expression and openness -- the same confound already measured on this project "
            "at 4.92x detection between anchored and unanchored genes. A cleaner-looking "
            "population would be a biased one.",
        "MANDATORY_LABEL_FOR_SINGLETON_CONTROLS":
            "STRUCTURALLY_MATCHED_NOT_RANDOMIZED_WITHIN_SIDE",
        "what_that_label_means": "The control satisfies every admissibility gate -- exact "
            "C3 round-trip, hg38 PU.1 support, hg38 NIH-CARD consensus-peak support, "
            "distance band, promoter-specific exclusion -- so it is a valid matched "
            "comparator. But the admissible set on its drawn side had exactly one element, "
            "so no alternative could have been drawn and the control carries NO "
            "within-edge randomisation variance.",
        "forbidden_description": "Describing singleton controls as ordinary randomised "
            "controls, or including them in any statement whose validity rests on the "
            "control having been randomly selected.",
        "stratified_reporting": "REQUIRED. Every inferential summary is reported both "
            "pooled over the primary population and stratified by control-support class. "
            "A pooled number presented without its stratified breakdown is a contract "
            "violation."},

      "SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION": {
        "purpose": "Calibrate the random-control generator: two independent draws from the "
                   "same edge-specific admissible distribution should show no systematic "
                   "difference.",
        "eligible_denominator_frozen_now": elig,
        "eligible_classes": ["FULLY_RANDOMIZED_SUPPORT_GT10",
                             "FULLY_RANDOMIZED_SMALL_SUPPORT"],
        "eligibility_rule": "BOTH draws must come from an admissible set of size >= 2 on "
                            "their own drawn side, so each draw had genuine freedom.",
        "class_counts": cls,
        "coincidence_by_class": coinc,
        "EXCLUDED_FROM_CALIBRATION_EVIDENCE": {
          "STRUCTURALLY_FORCED_IDENTICAL": {
            "n": cls["STRUCTURALLY_FORCED_IDENTICAL"],
            "contributes": "ZERO evidence",
            "why": "both draws landed on a side with exactly one admissible start, so "
                   "A == B was arithmetically guaranteed before any randomness was used"},
          "PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM": {
            "n": cls["PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM"],
            "contributes": "reported as its own class, NOT in the randomised denominator",
            "why": "a comparison between a forced control and a free control is not a "
                   "two-independent-draws null"},
          "B_UNAVAILABLE_NOT_EVALUABLE": {
            "n": cls["B_UNAVAILABLE_NOT_EVALUABLE"],
            "contributes": "NOT_EVALUABLE, reported explicitly",
            "why": "no control-vs-control comparison exists for these edges; they must "
                   "remain visible so that 'no null was computable' is never silently "
                   "read as 'the null passed'"}},
        "THE_INFLATION_THIS_PREVENTS": {
          "pooled_all_both_available": {"coincident": all_coinc, "of": both,
                                        "rate": round(all_coinc / both, 6)},
          "eligible_only": {"coincident": elig_coinc, "of": elig,
                            "rate": round(elig_coinc / elig, 6)},
          "inflation_factor": round((all_coinc / both) / (elig_coinc / elig), 2),
          "reading": "Pooling would make the control generator appear to agree with itself "
                     "about twenty times more often than it randomly does, entirely "
                     "because of degenerate single-element admissible sets."},
        "control_B_role": "NULL AND CALIBRATION ONLY. CONTROL_B may never enter the "
                          "primary linked-versus-control contrast and may never alter "
                          "Phase-A retention."},

      "SECTION_3_UNCERTAINTY_REPORTING": {
        "independent_unit": "DONOR, per the already-frozen correspondence design contract. "
                            "Nuclei and metacells improve the measurement of a donor-level "
                            "quantity and never increase independent N.",
        "clustering_unit_for_edge_level_inference": "PROMOTER",
        "why_promoter": "edges sharing a promoter share the promoter's activity and local "
                        "chromatin context, so they are not independent; the promoter is "
                        "the block.",
        "primary_interval_method": "donor-clustered nonparametric bootstrap, resampling "
                                   "DONORS, with edges blocked by promoter",
        "per_stratum_rules": {
          "control_A_support_1": {
            "within_edge_randomisation_variance": "ZERO BY CONSTRUCTION",
            "rule": "no randomisation-based interval may be reported for these edges; "
                    "uncertainty comes from donor resampling alone, and the absence of "
                    "control randomisation is stated wherever they are summarised"},
          "control_A_support_2_to_10": {
            "rule": "the admissible set is small enough to ENUMERATE COMPLETELY, so the "
                    "exact randomisation distribution over all n possible controls is "
                    "computed rather than approximated by resampling",
            "why": "with n <= 10 an exact enumeration is both cheap and strictly better "
                   "than a sampled approximation, and it makes the discreteness of the "
                   "reference distribution explicit instead of hidden"},
          "control_B_unavailable": {
            "rule": "edge contributes to the primary contrast and contributes NOTHING to "
                    "null calibration; counted as NOT_EVALUABLE"},
          "A_B_coincide_by_chance": {
            "rule": "RETAINED as a legitimate draw from the null; it is evidence, not an "
                    "artifact"},
          "A_B_coincide_structurally": {
            "rule": "EXCLUDED from calibration evidence; the edge still contributes to the "
                    "primary contrast"}},
        "no_silent_pooling": "Any statistic pooled across strata must be accompanied, in "
                             "the same table, by its per-stratum values. Pooling without "
                             "the breakdown is a contract violation."},

      "SECTION_4_PREDECLARED_SENSITIVITY_VIEWS": {
        "rule": "The PRIMARY view is fixed here, before any outcome is seen. The others "
                "are sensitivity views, not outcome-selected alternate primaries. Which "
                "view is primary may not change after results are seen.",
        "V1_PRIMARY_all_retained": {"n": n_edges, "is_primary": True},
        "V2_exclude_forced_singletons": {
            "n": n_edges - strata["FORCED_SINGLETON_SUPPORT_1"], "is_primary": False},
        "V3_randomized_support_gt10_only": {
            "n": strata["RANDOMIZED_SUPPORT_GT10"], "is_primary": False},
        "V4_small_support_reported_separately": {
            "n": strata["SMALL_RANDOMIZED_SUPPORT_2_TO_10"], "is_primary": False},
        "divergence_handling": "If the sensitivity views disagree materially with the "
                               "primary, that disagreement IS the finding and is reported "
                               "as such. It is not resolved by promoting whichever view "
                               "looks better."},

      "SECTION_5_MISSINGNESS": {
        "required_rule": "NOT_MEASURED != 0",
        "states": ["MEASURED_AND_SUPPORTS", "MEASURED_AND_DOES_NOT_SUPPORT",
                   "NOT_MEASURED", "UNRESOLVED"],
        "representation": "a per-element availability mask carried INSIDE the artifact "
                          "consumers read, never recorded only in matrix-level metadata",
        "zero_fill": "FORBIDDEN for RNA, ATAC and regulatory evidence alike",
        "availability_must_not_become_a_hidden_outcome_label": {
          "risk": "availability is confounded with expression on this project's own data: "
                  "E2-anchored genes show about 4.92x the microglial detection rate of "
                  "unanchored measurable genes, and within anchored genes degree tracks "
                  "detection at about 5.57x",
          "rule": "availability is carried as its own recorded field and, where any "
                  "comparison conditions on it, the availability pattern of each arm is "
                  "reported alongside the result"},
        "MEASUREMENT_UNSUPPORTED_edges": "an edge or control whose interval overlaps zero "
            "consensus peaks is MEASUREMENT_UNSUPPORTED, recorded as NOT_MEASURED and "
            "counted; the identical rule applies to linked and to every control"},

      "SECTION_6_DONOR_AND_STATISTICAL_MASS": {
        "cells_are_not_independent_N": True,
        "donor_level_rules_inherited_from_design_contract": {
          "minimum_microglia_per_donor": 100, "minimum_metacells_per_donor": 4,
          "minimum_donors_per_edge": 30,
          "low_support_handling": "labelled LOW_DONOR_SUPPORT and reported as its own "
                                  "stratum, never silently dropped"},
        "reporting_requirement": "every uncertainty statement names the donor count behind "
                                 "it, with the Kish effective donor sample size alongside "
                                 "the raw donor count",
        "multiple_edges_from_one_donor": "a donor contributes to many edges; donors are the "
            "resampling unit, so a donor is resampled as a whole and all of its edge "
            "contributions move together",
        "promoter_clustering": "edges within a promoter are blocked; the promoter is the "
                               "cross-fitting unit already frozen in the design contract",
        "promoter_degree_as_nuisance": "degree enters as a declared nuisance covariate. It "
            "is NOT a clean measure of regulatory complexity -- it partly measures "
            "detectability, measured on this project at about 5.57x between degree-1 and "
            "degree>=10 genes -- so it is adjusted for rather than interpreted.",
        "EDGE_MASS_CONCENTRATION": {
          "top_quartile_promoters_hold": round(sum(top[:cut]) / n_edges, 4),
          "rule": "the edge-level primary is reported ALWAYS AND IN THE SAME TABLE "
                  "alongside a promoter-equal-weighted estimate. The companion is "
                  "mandatory, not optional.",
          "why": "edge-summing lets a small number of high-degree promoters dominate, and "
                 "degree is itself expression-confounded. Equal promoter weight removes "
                 "part of that bias. Reporting only one of the two would hide whichever "
                 "effect the weighting choice produced.",
          "divergence_handling": "material disagreement between the two weightings is "
                                 "reported as a finding, not reconciled by choosing one"}},

      "SECTION_7_HIERARCHY": {
        "levels": "donor -> promoter -> edge -> {LINKED, CONTROL_A, CONTROL_B}",
        "retained_edges": n_edges, "retained_promoters": len(deg), "retained_genes": 4372,
        "FORBIDDEN": "treating the retained edges as that many independent biological "
                     "replicates",
        "blocking_and_clustering": {
          "resampling_unit": "donor",
          "blocking_unit": "promoter",
          "edge": "an observation within a promoter block, not an independent replicate",
          "control_rows": "CONTROL_A and CONTROL_B inherit their linked edge's promoter and "
                          "move with that block"},
        "effective_unit_ceiling": "edge-level inference is bounded above by the promoter "
            "count and, for donor-level quantities, by the qualifying donor count -- never "
            "by the edge count"},

      "SECTION_8_PHASE_B_FIELD_SEMANTICS": {
        "note": "The definitions below are INHERITED verbatim from the frozen "
                "correspondence design contract. This section binds them and fixes the "
                "remaining executability details; it does not redefine them.",
        "promoter_activity": {
          "frozen_definition": "donor-level mean log1p CP10K RNA of the linked gene across "
                               "that donor's microglia metacells",
          "source_matrix": "NIH-CARD RNA .X (uint16 count-like)",
          "critical_layout_warning": "the convention is REVERSED relative to common "
              "AnnData layout -- raw/X is noninteger log-like float32 -- so the executor "
              "must assert .X integrality on a sample and STOP if violated",
          "normalisation": "per metacell: sum counts over the metacell's nuclei, divide by "
                           "that metacell's total counts over all 38,606 genes, times 1e4, "
                           "then log1p",
          "aggregation": "mean over that donor's metacells",
          "unit": "DONOR",
          "gene_identity": "E2 nearest_ensembl joined to NIH-CARD var['gene_ids']; never "
                           "the var index, which mixes symbols and Ensembl IDs",
          "cell_inclusion": "NIH-CARD nuclei with cell_type == 'MG'",
          "minimum_support": "100 microglia and 4 metacells per donor; 30 donors per edge",
          "missingness": "absent gene or insufficient support -> NOT_MEASURED, never 0"},
        "distal_accessibility": {
          "frozen_definition": "donor-level mean log1p normalised ATAC over the assigned "
                               "peak set",
          "source_matrix": "NIH-CARD ATAC .X (uint16 count-like)",
          "peak_assignment": "all consensus peaks overlapping the interval by >= 1 bp are "
                             "summed; no peak widening, no nearest-peak rescue; the number "
                             "of overlapping peaks is recorded",
          "normalisation": "per metacell: sum counts over the metacell's nuclei across the "
                           "assigned peaks, divide by that metacell's total ATAC counts "
                           "over all 521,217 peaks, times 1e4, then log1p",
          "aggregation": "mean over that donor's metacells",
          "unit": "DONOR",
          "genome_build_precondition": "the executor must verify the consensus peak build "
              "is hg38 by an outcome-blind check before any join",
          "missingness": "zero overlapping peaks -> MEASUREMENT_UNSUPPORTED / NOT_MEASURED, "
                         "never 0"},
        "metacell_partition": {
          "rule": "formed inside each donor separately by clustering that donor's microglia "
                  "on RNA ONLY; ATAC is then summed over exactly the nuclei assigned to "
                  "each metacell",
          "forbidden": "a joint RNA+ATAC embedding, because it manufactures the "
                       "correspondence under test",
          "algorithm": "k-means on the first 20 PCs of the within-donor RNA matrix, "
                       "k = floor(n_microglia_donor / 25), seed 20260929, n_init 10",
          "determinism": "the assignment is written to the artifact so the partition is "
                         "auditable"},
        "identical_computation_for_A_and_B": {
          "required": True,
          "meaning": "CONTROL_A and CONTROL_B are scored by the SAME code path, on the SAME "
                     "metacells of the SAME donors, with the SAME peak-assignment and "
                     "support rules as the linked edge",
          "why": "any asymmetry between the arms would be indistinguishable from the "
                 "biological effect the design is meant to detect"},
        "ordering_requirement": "linked-versus-control comparison may begin only after "
            "promoter_activity and distal_accessibility are computed and FROZEN for every "
            "arm. No correspondence statistic may be computed while these values are still "
            "revisable."},

      "SECTION_9_FIREWALL_OBSERVED_IN_BUILDING_THIS_CONTRACT": {
        "inspected": ["Phase-A structural artifacts", "existing frozen contracts",
                      "code and schemas", "draw sides, admissible-set sizes, coincidence",
                      "promoter degree and edge-mass concentration"],
        "NOT_inspected": ["linked-versus-control biological correspondence",
                          "RNA-ATAC correlation", "effect sizes", "residual association",
                          "disease outcomes", "Morabito", "protected validation",
                          "paired NIH-CARD TEST donors"],
        "rna_matrix_values_read": False, "atac_matrix_values_read": False,
        "statement": "No quantity that could tune a statistical rule toward a desired "
                     "answer was available while these rules were written."},

      "governance": {"training": "OFF", "phase_B": "STOPPED",
                     "stage_4": "NOT_AUTHORISED", "td60": "BLOCKED",
                     "Morabito": "PROTECTED", "correspondence_opened": False,
                     "promoter_atlas_biology": "NOT_STARTED",
                     "multimodal_teacher_training": "NOT_STARTED"},
      "producer": {"path": os.path.relpath(os.path.abspath(__file__), os.getcwd()),
                   "sha256": B.sha_file(os.path.abspath(__file__))}}

    cp = os.path.join(OUT_DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V1.json")
    with open(cp, "w", newline="\n") as fh:
        json.dump(C, fh, indent=2)

    S = {
      "schema": "V64_PHASE_B_DECISION_STATE_V1", "date": "2026-09-30",
      "contract": {"path": cp, "sha256": B.sha_file(cp)},
      "phase_a_population_locked": {"retained_edges": n_edges,
                                    "retained_promoters": len(deg),
                                    "retained_genes": 4372},
      "DECISIONS": {
        "primary_population": "ALL_RETAINED",
        "primary_n": n_edges,
        "singletons_in_primary": True,
        "singleton_label": "STRUCTURALLY_MATCHED_NOT_RANDOMIZED_WITHIN_SIDE",
        "small_support_in_primary": True,
        "weighting_by_control_support": "NONE",
        "stratified_reporting": "REQUIRED",
        "randomized_null_denominator": elig,
        "excluded_structurally_forced": cls["STRUCTURALLY_FORCED_IDENTICAL"],
        "excluded_partially_forced": cls["PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM"],
        "not_evaluable_B_unavailable": cls["B_UNAVAILABLE_NOT_EVALUABLE"],
        "resampling_unit": "DONOR", "blocking_unit": "PROMOTER",
        "exact_enumeration_when_support_le_10": True,
        "promoter_equal_companion": "MANDATORY",
        "missingness_states": 4, "zero_fill": "FORBIDDEN",
        "primary_view": "V1_PRIMARY_all_retained"},
      "RECONCILIATION": {
        "calibration_classes_sum": sum(cls.values()),
        "equals_retained_edges": sum(cls.values()) == n_edges},
      "WHAT_THIS_AUTHORISES": "nothing to execute yet",
      "governance": C["governance"]}
    sp = os.path.join(OUT_DIR, "V64_PHASE_B_DECISION_STATE_V1.json")
    with open(sp, "w", newline="\n") as fh:
        json.dump(S, fh, indent=2)

    print(json.dumps({"calibration_classes": cls, "coincidence_by_class": coinc,
                      "randomized_null_denominator": elig,
                      "inflation_if_pooled": C["SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_"
                                                "CALIBRATION"]["THE_INFLATION_THIS_"
                                                               "PREVENTS"],
                      "strata": dict(strata),
                      "reconciles": sum(cls.values()) == n_edges}, indent=2))
    print(f"\ncontract {cp}\n  sha256 {B.sha_file(cp)}")
    print(f"state    {sp}\n  sha256 {B.sha_file(sp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
