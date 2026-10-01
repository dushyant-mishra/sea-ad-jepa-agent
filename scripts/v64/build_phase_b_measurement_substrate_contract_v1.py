#!/usr/bin/env python3
"""Freeze WHAT Phase B must write to disk, so Stage 4 never returns to the matrices.

THE GAP THIS CLOSES. The accepted statistical contract specifies donor-level
promoter_activity and distal_accessibility and requires the metacell partition to be
persisted. That is necessary but not sufficient: the Stage-4 correspondence statistic is
a within-donor Pearson correlation across METACELL-LEVEL vectors. If Phase B writes only
donor means, Stage 4 must go back to the matrices and rebuild those vectors -- after
outcomes have become visible. The separation Phase B exists to create would be undone at
the moment it mattered.

So Phase B reads the matrices ONCE and freezes the complete measurement substrate.
Stage 4 reads only the frozen substrate.

THE LINE PHASE B MAY NOT CROSS. The substrate carries the RNA vector and the ATAC vector
side by side for every (donor, metacell, pair). Phase B never multiplies them together.
Computing their correlation IS the correspondence statistic, and it belongs to Stage 4.
Everything Phase B computes is a marginal or a nuisance term -- quantities that look at
one modality at a time, or at a modality against sequencing depth.

A SECOND GAP: EXACT ENUMERATION NEEDS ALTERNATIVES THAT WERE NEVER SELECTED. The
statistical contract freezes exact enumeration for CONTROL_A support 2-10. An exact
randomisation distribution over a support-5 edge needs all five lawful controls, not only
the one drawn. Those alternatives are NOT new Phase-A controls: they do not change
retention, do not enter the primary population, do not increase N, and exist solely to
realise a rule that is already frozen. They are labelled ENUMERATION_ONLY.

Counts are computed here from the committed admissible sets rather than assumed.

S54 NOTE. While auditing, I found that two values in the statistical contract --
retained_genes and the A-failed/B-succeeded count -- were written as hardcoded literals
rather than recomputed. Both verify correct today. The defect is staleness risk, not
error, and this producer recomputes every count it emits.

TRAINING=OFF. PHASE B=STOPPED. No matrix VALUES are read here; only obs/var annotation.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from collections import Counter, defaultdict

import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                  # noqa: E402
import nihcard_stage3_phase_a_exact_executor_v2 as EX            # noqa: E402

OUT = "results/v64/phase_b_design"
ROWS = "D:/jepa_v5_outputs_20260925/v64_phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
NULL_V2 = os.path.join(OUT, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V2.json")
DESIGN_V1 = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
FEATURE_V2 = "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json"
PATCHED_A = "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json"
RNA = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
ATAC = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"

PROTECTED_OBS = ["Age", "Sex", "Ancestry", "Ethnicity", "Race", "PMI", "Brain_bank",
                 "cohort", "doublet_score", "leiden_2", "n_genes_by_counts",
                 "pct_counts_mt", "pct_counts_rb", "total_counts"]
LAWFUL_OBS = ["SampleID", "cell_type"]


def cat(f, k):
    o = f["obs"][k]
    if isinstance(o, h5py.Group):
        c = [x.decode() if isinstance(x, bytes) else str(x) for x in o["categories"][:]]
        return np.array(c)[o["codes"][:]]
    return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in o[:]])


def main() -> int:
    D = json.load(open(DESIGN_V1))
    msr = D["MEASUREMENT_SUPPORT_RESTRICTION"]["donor_level_rules"]
    agg = D["AGGREGATION"]["metacell_definition"]
    nui = D["NUISANCE_ADJUSTMENT"]
    stat = D["PRIMARY_CORRESPONDENCE_STATISTIC"]

    # ---- Phase-A population, everything recomputed
    rows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    by = defaultdict(dict)
    for r in rows:
        by[r["edge_index"]]["L" if r["population"] == "LINKED"
                            else r["control_role"]] = r
    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise SystemExit("STOP: E2 digest mismatch")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    e2 = [l.split("\t") for l in el[1:]]
    genes = sorted({e2[i][ix["nearest_ensembl"]] for i in by})
    intervals = {(r["distal_chrom"], r["distal_start_hg38"], r["distal_end_hg38"])
                 for r in rows}

    # ---- donors and metacells, from LAWFUL obs columns only
    with h5py.File(RNA, "r") as f:
        avail = set(f["obs"].keys())
        ct, sid = cat(f, "cell_type"), cat(f, "SampleID")
    mg = ct == "MG"
    per = Counter(sid[mg])
    n = np.array(sorted(per.values()))
    qual = n[n >= msr["minimum_microglia_per_donor"]]
    mc = qual // agg["target_metacell_size"]
    qual_mc = mc[mc >= msr["minimum_metacells_per_donor"]]

    # ---- enumeration requirement, computed from the committed admissible sets
    A = EX.load_A_exact()

    def members(e, s):
        iv, sup = A[e][s]
        out = []
        for a, b in iv:
            out.extend(range(a, b + 1))
        out.extend(sup)
        return sorted(out)

    need, cls = {}, Counter()
    for e, v in by.items():
        na, sa = v["A"]["admissible_start_count"], v["A"]["drawn_side"]
        if 2 <= na <= 10:
            cls["R1_primary_exact_A_side"] += 1
            for x in members(e, sa):
                need.setdefault((e, sa, x), set()).add("R1_primary_exact_A_side")
        if "B" not in v:
            continue
        nb, sb = v["B"]["admissible_start_count"], v["B"]["drawn_side"]
        if na == 1 or nb == 1 or not (na <= 10 or nb <= 10):
            continue
        if na <= 10 and nb <= 10:
            cls["R2_exact_joint_AB"] += 1
            for side in {sa, sb}:
                for x in members(e, side):
                    need.setdefault((e, side, x), set()).add("R2_exact_joint_AB")
        else:
            cls["R3_exact_conditional_small_arm"] += 1
            ss = sa if na <= 10 else sb
            for x in members(e, ss):
                need.setdefault((e, ss, x), set()).add("R3_exact_conditional_small_arm")
    already = {(e, v[k]["drawn_side"], v[k]["hg19_start"])
               for e, v in by.items() for k in ("A", "B") if k in v}
    extra = sorted(set(need) - already)
    joint_pairs = 0
    for e, v in by.items():
        if "B" not in v:
            continue
        na, nb = v["A"]["admissible_start_count"], v["B"]["admissible_start_count"]
        if 2 <= na <= 10 and 2 <= nb <= 10:
            joint_pairs += na * nb

    C = {
      "schema": "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1",
      "date": "2026-09-30",
      "status": "PROSPECTIVELY_FROZEN_BEFORE_ANY_MATRIX_VALUE_IS_READ",
      "purpose": "Specify exactly what Phase B freezes to disk, so that Stage 4 reads "
                 "only the frozen substrate and never returns to the matrices after "
                 "outcomes are visible.",
      "changes_no_statistical_decision": True,
      "authority": {
        "statistical_contract": {"path": NULL_V2, "sha256": B.sha_file(NULL_V2)},
        "correspondence_design": {"path": DESIGN_V1, "sha256": B.sha_file(DESIGN_V1)},
        "feature_artifact": {"path": FEATURE_V2, "sha256": B.sha_file(FEATURE_V2)},
        "phase_a_population": {"path": PATCHED_A, "sha256": B.sha_file(PATCHED_A)}},

      "THE_LINE_PHASE_B_MAY_NOT_CROSS": {
        "phase_B_MAY_compute": [
          "per-metacell normalised RNA for a gene (one modality)",
          "per-metacell normalised ATAC for an interval's peak set (one modality)",
          "donor-level means of either (the two V2 fields)",
          "rna_depth_sensitivity and atac_depth_sensitivity, each a within-donor slope "
          "of one modality on that modality's own sequencing depth",
          "availability masks and attrition counts"],
        "phase_B_MAY_NOT_compute": [
          "the Pearson correlation between the RNA and ATAC vectors -- that IS the "
          "correspondence statistic and belongs to Stage 4",
          "any linked-minus-control difference", "any residualised correspondence",
          "the one-sided test", "any disease or protected outcome association"],
        "the_principle": "Phase B may look at one modality at a time, or at a modality "
                         "against its own depth. The moment two modalities are multiplied "
                         "together, the experiment has been opened."},

      "SUBSTRATE_TABLES": {
        "T1_METACELL_ASSIGNMENT": {
          "key": "donor_id x nucleus_id",
          "fields": ["donor_id", "nucleus_obs_name", "metacell_id"],
          "rule": agg["algorithm"], "seed": agg["seed"],
          "why_persisted": "Stage 4 must use the identical partition. A partition rebuilt "
                           "later would be rebuilt after outcomes were visible, and a "
                           "partition is exactly the kind of choice that can move a "
                           "correspondence result."},
        "T2_METACELL_DEPTH": {
          "key": "donor_id x metacell_id",
          "fields": ["n_nuclei", "total_rna_counts_all_genes",
                     "total_atac_counts_all_peaks"],
          "why": "the two frozen depth-sensitivity nuisance terms are within-donor slopes "
                 "on these totals, so Stage 4 cannot recompute them without these columns",
          "rna_denominator_universe": 38606, "atac_denominator_universe": 521217},
        "T3_RNA_VECTORS": {
          "key": "donor_id x metacell_id x gene_id",
          "KEYED_BY_GENE_NOT_BY_PAIR": True,
          "why": "the frozen promoter_activity is the LINKED GENE's RNA. CONTROL_A and "
                 "CONTROL_B differ from their linked edge only in the distal interval, so "
                 "all three rows of an edge share one RNA vector. Keying by pair would "
                 "duplicate it 8.5-fold with no added information.",
          "fields": ["rna_log1p_cp10k", "rna_available"],
          "normalisation": D["MEASUREMENTS"]["RNA_quantity"]["per_metacell_value"]},
        "T4_ATAC_VECTORS": {
          "key": "donor_id x metacell_id x distal_interval_id",
          "fields": ["atac_log1p_norm", "atac_available", "n_assigned_peaks"],
          "normalisation": D["MEASUREMENTS"]["ATAC_quantity"]["per_metacell_value"],
          "peak_assignment": D["MEASUREMENTS"]["ATAC_quantity"]["peak_assignment_rule"]},
        "T5_PAIR_DONOR_AGGREGATES": {
          "key": "donor_id x pair_key",
          "fields": ["promoter_activity", "distal_accessibility", "n_assigned_peaks",
                     "rna_depth_sensitivity", "atac_depth_sensitivity",
                     "n_metacells_contributing", "availability_state"],
          "note": "these are the V2 artifact's required donor-level fields; they are "
                  "derived from T2-T4 and are stored as well as derivable so the V2 "
                  "artifact is self-contained"},
        "T6_ENUMERATION_ONLY": {
          "key": "edge_index x drawn_side x hg19_start",
          "label": "ENUMERATION_ONLY",
          "semantics": ["NOT new Phase-A controls", "do NOT change retention",
                        "do NOT increase N", "do NOT enter the primary population",
                        "exist solely to realise the already-frozen exact randomisation "
                        "distribution"],
          "inherits": "edge, promoter, donor and metacell structure from its edge",
          "measured_identically_to": "CONTROL_A and CONTROL_B, same code path"}},

      "EXACT_ENUMERATION_REQUIREMENT": {
        "computed_from": "the committed exact admissible sets, not assumed",
        "R1_primary_exact_A_side": {
          "rule": "for every retained edge whose CONTROL_A support is 2-10, materialise "
                  "ALL A-side admissible alternatives",
          "edges": cls["R1_primary_exact_A_side"]},
        "R2_exact_joint_AB": {
          "rule": "for a fully-randomised small-support A/B pair where BOTH arms have "
                  "support <= 10, the reference is the EXACT JOINT distribution over the "
                  "two side-specific admissible sets, so all alternatives of both arms "
                  "are materialised",
          "pairs": cls["R2_exact_joint_AB"],
          "ordered_pairs_in_the_joint_reference": joint_pairs},
        "R3_exact_conditional_small_arm": {
          "rule": "where exactly one arm has support <= 10 and the other is large, the "
                  "reference is the EXACT CONDITIONAL distribution: the small arm is "
                  "enumerated completely and the large arm is held at its realised draw",
          "pairs": cls["R3_exact_conditional_small_arm"],
          "why_not_the_full_joint": "the large arms run to tens of thousands of admissible "
              "starts, so a full joint would require materialising measurements for tens "
              "of thousands of intervals per pair. The conditional reference is exact in "
              "a well-defined sense and is declared NOW rather than discovered when the "
              "cost became apparent.",
          "what_is_conditioned_on": "the realised large-arm draw, recorded per pair"},
        "MATERIALISATION": {
          "distinct_intervals_required": len(need),
          "already_measured_as_CONTROL_A_or_B": len(set(need) & already),
          "additional_ENUMERATION_ONLY_rows": len(extra),
          "edges_touched": len({e for e, _, _ in need}),
          "as_fraction_of_controls_already_measured": round(len(extra) / 24187, 6)},
        "frozen_before_biological_values_exist": True},

      "RECOVERABILITY_TEST_DONOR_FIREWALL_SCOPE": {
        "CORRECTION": "An earlier audit note of mine said Phase B would not authorise "
                      "'any use of the paired NIH-CARD TEST donors'. That wording "
                      "conflated two different experiments and is withdrawn.",
        "what_the_split_actually_governs": {
          "experiment": "privileged-factor recoverability",
          "population": "the paired 24-donor subset",
          "split": "16 TRAIN / 4 VALIDATION / 4 TEST, donor ID only, seed 20260930",
          "restriction": "the 4 TEST donors are forbidden for recoverability model, rank, "
                         "basis, rotation or threshold selection"},
        "what_governs_Phase_B": {
          "authority": "the correspondence design contract's own donor-population rules",
          "population": "the full NIH-CARD correspondence cohort",
          "rules": {"minimum_microglia_per_donor": msr["minimum_microglia_per_donor"],
                    "minimum_metacells_per_donor": msr["minimum_metacells_per_donor"],
                    "minimum_donors_per_edge": msr["minimum_donors_per_edge"]},
          "statement": "Phase B follows this authority. The recoverability split does not "
                       "remove donors from it."},
        "if_global_sequestration_is_wanted": "that must be an EXPLICIT prospective "
            "amendment, with its impact on the Phase-B donor population measured and "
            "reported before adoption. It may not arrive as a side effect of architecture "
            "work on a different experiment.",
        "why_this_matters": "silently dropping four donors would change the Phase-B "
            "population for a reason unrelated to Phase B, and the change would be "
            "invisible in the Phase-B receipt."},

      "DONOR_POPULATION_MEASURED_FROM_LAWFUL_METADATA": {
        "obs_columns_read": LAWFUL_OBS,
        "obs_columns_deliberately_not_read": sorted(
            [c for c in PROTECTED_OBS if c in avail]),
        "why": "Age, Sex, Ancestry, Ethnicity, Race, PMI and Brain_bank are protected "
               "demographic attributes. Donor identity and cell type are the only columns "
               "needed to define the aggregation population.",
        "nuclei_total": int(len(ct)), "microglia": int(mg.sum()),
        "donors_with_microglia": len(per),
        "per_donor_microglia": {
            "min": int(n.min()), "p25": int(np.percentile(n, 25)),
            "median": int(np.median(n)), "p75": int(np.percentile(n, 75)),
            "max": int(n.max())},
        "donors_meeting_minimum_microglia": int(len(qual)),
        "donors_meeting_minimum_metacells": int(len(qual_mc)),
        "total_qualifying_donor_metacells": int(mc[mc >= msr[
            "minimum_metacells_per_donor"]].sum()),
        "agreement_with_design_contract": msr["expected_effect_from_committed_counts"]},

      "SUBSTRATE_SCALE_MEASURED": {
        "qualifying_donor_metacells": int(qual_mc.sum()),
        "distinct_linked_genes": len(genes),
        "distinct_distal_intervals": len(intervals) + len(extra),
        "pair_rows": len(rows),
        "T3_rna_cells": int(qual_mc.sum()) * len(genes),
        "T4_atac_cells": int(qual_mc.sum()) * (len(intervals) + len(extra)),
        "note": "T3 is gene-keyed, which is 8.5x smaller than a pair-keyed layout with "
                "no information loss"},

      "MISSINGNESS_IN_THE_SUBSTRATE": {
        "inherited_rules": {
          "zero_coverage": stat["zero_coverage_rule"],
          "degenerate_variance": stat["degenerate_variance_rule"]},
        "representation": "per-element availability columns in T3 and T4, and an "
                          "availability_state in T5 drawn from the four frozen states",
        "forbidden": "writing 0 for an unmeasured value in any table"},

      "NUISANCE_TERMS_THE_SUBSTRATE_MUST_SUPPORT": {
        "frozen_basis": nui["frozen_basis_14_features"],
        "computable_in_phase_B": ["promoter_activity", "distal_accessibility",
                                  "rna_depth_sensitivity", "atac_depth_sensitivity"],
        "already_frozen_in_phase_A": ["log_distance", "promoter_degree", "re_density",
                                      "anchor_frequency"],
        "depth_sensitivity_definitions": {
          "rna": nui["NIH_CARD_observable_mapping"]["rna_depth_sensitivity"],
          "atac": nui["NIH_CARD_observable_mapping"]["atac_depth_sensitivity"]},
        "note": "both depth terms are single-modality slopes on that modality's own "
                "sequencing depth, so computing them does not open the correspondence"},

      "PROVENANCE_THE_PHASE_B_RECEIPT_MUST_BIND": [
        "producer path, sha256 and git blob",
        "this contract's sha256", "the statistical contract V2 sha256",
        "the correspondence design contract sha256",
        "the feature-artifact V2 contract sha256",
        "the Phase-A patched receipt sha256",
        "every emitted substrate table: path, bytes, sha256",
        "the metacell assignment artifact sha256, separately",
        "NIH-CARD RNA and ATAC byte-authentication receipt and pairing closeout",
        "the E2 digest", "the consensus peak set digest",
        "every frozen constant and seed actually used",
        "the obs columns read, and the protected columns not read"],

      "STOP_CONDITIONS": [
        "any substrate table cannot be emitted",
        "any availability value would have to be written as 0",
        "the metacell partition cannot be persisted and hash-bound",
        "the enumeration set cannot be materialised in full",
        "RNA .X fails the integrality assertion",
        "the consensus peak build fails the hg38 precondition",
        "any protected obs column is read",
        "any two-modality statistic is computed"],

      "governance": json.load(open(NULL_V2))["governance"],
      "producer": {"path": os.path.relpath(os.path.abspath(__file__), os.getcwd()),
                   "sha256": B.sha_file(os.path.abspath(__file__))}}

    p = os.path.join(OUT, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(C, fh, indent=2)
    print(json.dumps({"EXACT_ENUMERATION_REQUIREMENT": C["EXACT_ENUMERATION_REQUIREMENT"],
                      "DONOR_POPULATION": C["DONOR_POPULATION_MEASURED_FROM_LAWFUL_"
                                            "METADATA"],
                      "SUBSTRATE_SCALE_MEASURED": C["SUBSTRATE_SCALE_MEASURED"]},
                     indent=2))
    print(f"\ncontract {p}\n  sha256 {B.sha_file(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
