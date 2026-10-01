#!/usr/bin/env python3
"""Stage-4 execution authority: bind every input and lock every rule BEFORE any
correspondence value exists.

WHAT THIS IS NOT. It does not compute a correlation, a Delta, a residual, a test or a
confidence bound. It computes nothing about biology at all. Its entire job is to make the
rules unalterable and the inputs unambiguous while the answer is still sealed, so that
Stage 4 cannot later choose a method, a weighting, a denominator or a success definition
in the light of what it sees.

WHY THE BINDING MATTERS MORE HERE THAN ANYWHERE EARLIER. Every prior stage could be rerun
if a rule turned out wrong. Stage 4 cannot: the moment the correspondence is computed, the
outcome is open and no later choice is outcome-blind. So everything that could be chosen
has to be chosen now, and everything that could drift has to be pinned to a digest now.

THE RULES ARE NOT RESTATED HERE, THEY ARE INHERITED. The statistic, the estimand, the
weighting hierarchy, the nuisance basis, the bootstrap, the success criterion and the
anti-false-green controls already live in frozen contracts. Restating them would create a
second definition that could diverge. This contract binds each by digest and names where
it lives.

TRAINING=OFF. STAGE 4 REMAINS NOT AUTHORISED BY THIS ARTIFACT. It defines what execution
authority WOULD require; granting it is a separate decision that is not taken here.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

DIR = "results/v64/phase_b_design"
SUBD = "results/v64/phase_b_substrate"
OUT = "D:/jepa_v5_outputs_20260925/v64_phase_b"
DESIGN = "results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json"
NULLC = os.path.join(DIR, "V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json")
SUBC = os.path.join(DIR, "V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json")
FEATC = "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json"
PHASEA = "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json"
ESTIM = "scripts/v63/e2_continuous_adjustment_estimator_v1.py"


def blob(p):
    r = subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True, text=True)
    o = r.stdout.strip()
    return o if (r.returncode == 0 and len(o) == 40
                 and all(c in "0123456789abcdef" for c in o)) else "UNCOMMITTED"


def norm(p):
    """S70. os.path.join produces backslashes on Windows, and `git rev-parse HEAD:a\b`
    never resolves, so repo-resident inputs were being stamped UNCOMMITTED while their
    blobs existed. Paths are normalised once, here, before any lookup or storage."""
    return str(p).replace("\\", "/")


def bind(p, note=None):
    p = norm(p)
    d = dict(path=p, sha256=B.sha_file(p), git_blob=blob(p))
    d["repo_resident"] = not p.startswith("D:/")
    if d["repo_resident"] and d["git_blob"] == "UNCOMMITTED":
        d["git_blob_note"] = ("repo-resident input with no blob: it must be committed "
                              "before execution authority can be granted")
    if os.path.exists(p):
        d["bytes"] = os.path.getsize(p)
    if note:
        d["note"] = note
    return d


def main() -> int:
    global AGG, CLO, AV
    AGG = json.load(open(os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json")))
    CLO = json.load(open(os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json")))
    AV = json.load(open(os.path.join(DIR, "V64_PHASE_B_T3_T4_AVAILABILITY_V2.json")))
    D = json.load(open(DESIGN))
    N3 = json.load(open(NULLC))
    pe, nui = D["PRIMARY_ESTIMAND"], D["NUISANCE_ADJUSTMENT"]
    stat, succ = D["PRIMARY_CORRESPONDENCE_STATISTIC"], D["SUCCESS_CRITERION"]
    sec10 = N3["SECTION_10_ENUMERATION_REFERENCE_RULES"]
    nullsec = N3["SECTION_2_CONTROL_A_VS_CONTROL_B_NULL_CALIBRATION"]
    wh = N3["SECTION_6_DONOR_AND_STATISTICAL_MASS"]["EDGE_MASS_CONCENTRATION"][
        "WEIGHTING_HIERARCHY_IS_FIXED_AND_HAS_EXACTLY_ONE_PRIMARY"]

    C = {
      "schema": "V64_STAGE4_EXECUTION_AUTHORITY_V1", "date": "2026-09-30",
      "status": "DESIGN_ONLY__STAGE_4_NOT_AUTHORISED_BY_THIS_ARTIFACT",
      "computes_no_correspondence_value": True,
      "purpose": "Bind every Stage-4 input and lock every Stage-4 rule while the outcome "
                 "is still sealed, so no method, weighting, denominator or success "
                 "definition can be chosen in the light of a result.",
      "why_this_stage_is_different": "every earlier stage could be rerun if a rule proved "
          "wrong. Stage 4 cannot: once the correspondence is computed the outcome is open "
          "and no later choice is outcome-blind. Everything choosable is chosen now.",

      "INHERITED_NOT_RESTATED": {
        "principle": "the statistic, estimand, weighting, nuisance basis, bootstrap, "
                     "success criterion and anti-false-green controls already live in "
                     "frozen contracts. They are bound here by digest, never restated, "
                     "because a second definition can diverge from the first.",
        "correspondence_design": bind(DESIGN),
        "downstream_null_statistical_V3": bind(NULLC),
        "measurement_substrate": bind(SUBC),
        "feature_artifact_V2": bind(FEATC),
        "phase_a_population": bind(PHASEA)},

      "BOUND_PHASE_B_INPUTS": {
        "note": "Stage 4 reads ONLY these. It may not reopen the RNA or ATAC matrices.",
        "substrate_shards": {os.path.basename(p): bind(p)
                             for p in sorted(glob.glob(
                                 os.path.join(OUT, "PHASE_B_SUBSTRATE_s*.npz")))},
        "t5_donor_aggregates": bind(os.path.join(
            OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz")),
        "t3_t4_availability": bind(os.path.join(
            OUT, "PHASE_B_T3_T4_AVAILABILITY.npz")),
        "r3_conditioning_reference": bind(os.path.join(
            DIR, "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json")),
        "enumeration_intervals": bind(os.path.join(
            DIR, "V64_PHASE_B_ENUM_INTERVALS_V1.json")),
        "substrate_aggregate_receipt": bind(os.path.join(
            DIR, "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json")),
        "substrate_closeout_receipt": bind(os.path.join(
            DIR, "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json")),
        "availability_proof_receipt": bind(os.path.join(
            DIR, "V64_PHASE_B_T3_T4_AVAILABILITY_V2.json")),
        "phase_a_rows": bind("results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"),
        },
      "CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT": {
        "why_separated": "S69. The pairing permutation was listed among the bound inputs "
            "with two specially-named digest fields, which the generic digest gate did "
            "not recognise, so neither was ever verified. Since the authority itself "
            "states Stage 4 does not need it -- the substrate it reads is already paired "
            "-- it is moved out of required execution inputs and labelled corroborative. "
            "It is nonetheless verified explicitly by its own gate, because a binding "
            "that is never checked is worse than no binding: it reads as assurance.",
        "pairing_permutation": dict(
            path="D:/jepa_v5_outputs_20260925/atac_to_rna_row.npy",
            array_content_sha256="c28335d72627d195c0b997a659e3d320139a0a038f746e354ca"
                                 "6de4567b9e120",
            npy_file_sha256="2396c3e9ccef2a4354824a80815d6acb8819f662f6c641d4df72d85ba"
                            "d498828",
            digest_semantics="array_content covers perm.tobytes(); npy_file covers the "
                             "file including its 128-byte header",
            verified_by_gate="G15_PERMUTATION_COROBORATION",
            required_as_a_stage4_DATA_input=False,
            required_as_a_PROVENANCE_verification=True,
            S80_contradiction_resolved="the earlier wording said "
                "required_for_stage4_execution=false while REQUIRED_BINDINGS and G15 made "
                "its absence a STOP, which is saying both things at once. The resolution "
                "is that it is not a DATA input -- Stage 4 reads an already-paired "
                "substrate and never consults it -- but it IS a provenance prerequisite, "
                "because the substrate's correctness depends on the permutation having "
                "been right, and 1,500,790 of 1,501,089 rows are displaced. Its absence "
                "therefore remains a STOP, now for a stated reason rather than by "
                "accident.")},

      "ESTIMATOR_IMPORTED_UNMODIFIED": dict(
        **bind(ESTIM),
        requirement=nui["estimator"],
        rule="Stage 4 must import this file unmodified and verify its sha256 before use. "
             "A changed estimator is a changed method, whatever the diff looks like.",
        frozen_hyperparameters=dict(ridge_alpha=nui["ridge_alpha"],
                                    k_folds=nui["k_folds"],
                                    cross_fitting_unit=nui["cross_fitting_unit"]),
        frozen_basis=nui["frozen_basis_14_features"],
        forbidden=nui["forbidden"]),

      "METHOD_LOCKS": {
        "per_donor_per_pair_statistic": stat["per_donor_per_pair_score"],
        "pearson_is_primary_spearman_is_sensitivity": stat["why_pearson_not_spearman"],
        "sign_convention": stat["orientation_and_sign"],
        "missing_rules": {"zero_coverage": stat["zero_coverage_rule"],
                          "degenerate_variance": stat["degenerate_variance_rule"]},
        "primary_estimand": pe["definition"],
        "gene_balancing": pe["gene_balancing"],
        "weighting_hierarchy": {
          "PRIMARY": wh["PRIMARY"]["name"],
          "MANDATORY_COMPANION": wh["MANDATORY_COMPANION"]["name"],
          "PREDECLARED_SENSITIVITY": wh["PREDECLARED_SENSITIVITY"]["name"],
          "non_selection_rule": wh["NON_SELECTION_RULE"]["rule"]},
        "uncertainty": pe["uncertainty"],
        "inference": pe["inference"],
        "multiplicity": pe["multiplicity"],
        "sensitivity_arms": stat["sensitivity_arms_predeclared"]},

      "NULL_AND_STRATA_LOCKS": {
        "randomized_null_denominator": nullsec["eligible_denominator_frozen_now"],
        "excluded_structurally_forced": nullsec["class_counts"][
            "STRUCTURALLY_FORCED_IDENTICAL"],
        "excluded_partially_forced": nullsec["class_counts"][
            "PARTIALLY_FORCED_ONE_DRAW_HAD_NO_FREEDOM"],
        "not_evaluable_B_unavailable": nullsec["class_counts"][
            "B_UNAVAILABLE_NOT_EVALUABLE"],
        "enumeration_reference_rules": {
            k: dict(governs=sec10[k]["governs"],
                    count=sec10[k].get("edges") or sec10[k].get("pairs"))
            for k in ("R1_PRIMARY_EXACT_A_SIDE", "R2_EXACT_JOINT_AB",
                      "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM")},
        "R3_required_label": sec10["R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"][
            "MANDATORY_CAVEAT_ON_UNCERTAINTY"]["required_label"],
        "R3_pooling_forbidden": sec10["R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"][
            "MANDATORY_CAVEAT_ON_UNCERTAINTY"]["forbidden"],
        "control_B_role": nullsec["control_B_role"],
        "no_silent_pooling": N3["SECTION_3_UNCERTAINTY_REPORTING"]["no_silent_pooling"]},

      "SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT": {
        "PASS_requires_all_of": succ["PASS_requires_all_of"],
        "no_minimum_effect_size": succ["NO_MINIMUM_EFFECT_SIZE_IS_IMPOSED"],
        "FAIL_is_reported_with": succ["FAIL_is_reported_with"],
        "anti_false_green": D["ANTI_FALSE_GREEN_CONTROLS"],
        "the_rule_that_is_easiest_to_break": "p < 0.05 is explicitly NOT the success "
            "definition. A statistically positive but negligibly small Delta must be "
            "reported as exactly that and must not be presented as biological "
            "confirmation."},

      "CONSUMER_SCHEMA_SEMANTICS": {
        "why": "S78. Correct bytes are not enough. A future executor could hash every "
               "input successfully and still read the arrays along the wrong axis, "
               "mis-order the availability vocabulary, or silently accept a truncated "
               "table. These are the shapes and counts the accepted Phase-B closeout "
               "established; a gate verifies them against the ARTIFACTS, not against this "
               "contract's own restatement of them.",
        "source_receipts": [
          "V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json",
          "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json",
          "V64_PHASE_B_T3_T4_AVAILABILITY_V2.json"],
        "aggregate_binding_over_recomputed_shard_hashes": AGG["aggregate_binding"],
        "metacells": AGG["metacells_total"],
        "intervals": AGG["intervals"],
        "genes": AGG["genes"],
        "t3_nnz": AGG["t3_nnz"], "t4_nnz": AGG["t4_nnz"],
        "t5_rows": CLO["B1_T5"]["rows"],
        "t5_donors": CLO["B1_T5"]["donors"], "t5_pairs": CLO["B1_T5"]["pairs"],
        "availability_states_in_order": CLO["B4_AVAILABILITY"]["states"],
        "t3_shape": AV["T3"]["shape"], "t3_elements": AV["T3"]["elements"],
        "t4_shape": AV["T4"]["shape"], "t4_elements": AV["T4"]["elements"],
        "AXIS_INTERPRETATION": {
          "t3": "rows are metacell_id 0..3230, columns are the gene dictionary index; "
                "the RNA value is the LINKED GENE's, shared by an edge's LINKED, "
                "CONTROL_A and CONTROL_B rows",
          "t4": "rows are metacell_id 0..3230, columns are the interval dictionary index",
          "t5": "keyed donor x pair_key, donor-major, pair order equal to pair_keys",
          "availability": "bit-packed with numpy.packbits, big bitorder, C-order ravel; "
                          "slice to the element count before reshaping or the trailing "
                          "pad bits are read as elements",
          "pair_gene": "holds gene ID STRINGS, not indices; resolve against the gene "
                       "dictionary. Using them as positions is a real defect that already "
                       "occurred once."}},

      "REQUIRED_BINDINGS": {
        "why": "S73. G1 caught a binding whose FILE was missing, but not a binding that "
               "had been DELETED from the contract: removing an entry simply gave the "
               "walker less to walk and every remaining digest still matched. An input "
               "can therefore vanish without any gate noticing. This manifest names every "
               "binding that must exist, and presence is checked BEFORE any digest work.",
        "keys": [
          "INHERITED_NOT_RESTATED.correspondence_design",
          "INHERITED_NOT_RESTATED.downstream_null_statistical_V3",
          "INHERITED_NOT_RESTATED.measurement_substrate",
          "INHERITED_NOT_RESTATED.feature_artifact_V2",
          "INHERITED_NOT_RESTATED.phase_a_population",
          "BOUND_PHASE_B_INPUTS.t5_donor_aggregates",
          "BOUND_PHASE_B_INPUTS.t3_t4_availability",
          "BOUND_PHASE_B_INPUTS.r3_conditioning_reference",
          "BOUND_PHASE_B_INPUTS.enumeration_intervals",
          "BOUND_PHASE_B_INPUTS.substrate_aggregate_receipt",
          "BOUND_PHASE_B_INPUTS.substrate_closeout_receipt",
          "BOUND_PHASE_B_INPUTS.availability_proof_receipt",
          "BOUND_PHASE_B_INPUTS.phase_a_rows",
          "ESTIMATOR_IMPORTED_UNMODIFIED",
          "CORROBORATIVE_PROVENANCE_NOT_A_STAGE4_INPUT.pairing_permutation",
          "EXECUTION_PREREQUISITES_NOT_YET_SATISFIED.unsatisfied_prerequisites",
          "CONSUMER_SCHEMA_SEMANTICS.AXIS_INTERPRETATION"],
        "substrate_shards_required": 8,
        "rule": "every key above must be present in this contract and every shard slot "
                "filled; absence is a STOP, not a smaller walk"},

      "FAIL_CLOSED_GATES": [
        {"id": "G0_GATE_REGISTRY_AGREES", "rule": "the gate set this contract declares "
         "must equal the gate set the verifier implements, in both directions (S75)",
         "on_failure": "STOP"},
        {"id": "G1a_REQUIRED_BINDINGS_PRESENT", "rule": "every key in REQUIRED_BINDINGS "
         "must exist in this contract before any digest is checked (S73)",
         "on_failure": "STOP"},
        {"id": "G1b_REPO_INPUTS_GIT_BLOB_IDENTITY", "rule": "every repo-resident input's "
         "stored blob must EQUAL git rev-parse HEAD:<path>, not merely look like a hash "
         "(S74)", "on_failure": "STOP"},
        {"id": "G1c_PREREQUISITE_REGISTRY_INTACT", "rule": "the execution-prerequisite "
         "block must exist and must still name G16 and G17; a missing block must never "
         "read as zero unsatisfied prerequisites (S77)", "on_failure": "STOP"},
        {"id": "G18_CONSUMER_SCHEMA_SEMANTICS", "rule": "the substrate artifacts must "
         "match the accepted shapes, counts, availability vocabulary and axis "
         "interpretation, verified against the artifacts themselves (S78)",
         "on_failure": "STOP"},
        {"id": "G19_PRODUCER_CUSTODY", "rule": "this authority's producer must carry a "
         "real post-commit git blob, not path and sha256 alone (S79)",
         "on_failure": "STOP"},
        {"id": "G15_PERMUTATION_COROBORATION", "rule": "both pairing-permutation digests "
         "verify; corroborative only, not a Stage-4 execution input (S69)",
         "on_failure": "STOP"},
        {"id": "G1_INPUT_DIGESTS", "rule": "every bound input digest must match before a "
         "single correspondence value is computed", "on_failure": "STOP"},
        {"id": "G2_ESTIMATOR_UNMODIFIED", "rule": "the estimator sha256 must equal the "
         "bound value", "on_failure": "STOP"},
        {"id": "G3_NO_MATRIX_REOPEN", "rule": "Stage 4 may not open the RNA or ATAC h5ad "
         "files; it reads the frozen substrate only", "on_failure": "STOP"},
        {"id": "G4_PARTITION_NOT_REBUILT", "rule": "the metacell partition must be the "
         "persisted one, verified by digest, never recomputed", "on_failure": "STOP"},
        {"id": "G5_WEIGHTING", "rule": "the primary must be GENE_BALANCED with the "
         "PROMOTER_EQUAL companion emitted in the same table", "on_failure": "STOP"},
        {"id": "G6_BOOTSTRAP", "rule": "donor cluster bootstrap, 4000 replicates, seed "
         "20260929; donors are the sole resampling unit", "on_failure": "STOP"},
        {"id": "G7_NULL_DENOMINATOR", "rule": "the randomized-null denominator must be "
         "10654, with forced and partially forced pairs excluded and B-unavailable "
         "reported as NOT_EVALUABLE", "on_failure": "STOP"},
        {"id": "G8_R3_LABEL", "rule": "every R3-derived quantity must carry "
         "CONDITIONAL_ON_REALISED_LARGE_ARM and may not be pooled with R1/R2",
         "on_failure": "STOP"},
        {"id": "G9_CONTROL_B_NULL_ONLY", "rule": "CONTROL_B may not enter the primary "
         "contrast", "on_failure": "STOP"},
        {"id": "G10_ANTI_FALSE_GREEN", "rule": "a nonzero control-vs-control contrast "
         "makes the primary uninterpretable", "on_failure": "STOP, do not report the "
         "primary as a biological result"},
        {"id": "G11_PROTECTED", "rule": "no disease, demographic or protected attribute; "
         "Morabito untouched; TD60 blocked; training off", "on_failure": "STOP"},
        {"id": "G12_NO_THRESHOLD_ON_EFFECT", "rule": "effect magnitude is reported "
         "without a minimum-effect threshold and p<0.05 alone is not success",
         "on_failure": "STOP"},
        {"id": "G13_FUNNEL", "rule": "the attrition funnel must reconcile to 20,709",
         "on_failure": "STOP"},
        {"id": "G14_STRATA", "rule": "no statistic may be pooled across randomness strata "
         "without its per-stratum breakdown in the same table", "on_failure": "STOP"}],

      "WHAT_STAGE_4_MAY_READ": [
        "the eight frozen substrate shards", "T5 donor aggregates",
        "T3/T4 availability", "the R3 conditioning reference",
        "the enumeration intervals", "the Phase-A rows", "the frozen contracts",
        "the unmodified estimator"],
      "WHAT_STAGE_4_MAY_NOT_READ": [
        "the NIH-CARD RNA or ATAC h5ad matrices",
        "any disease, demographic or protected attribute",
        "Morabito or any protected validation outcome",
        "the paired recoverability TEST donors for any recoverability selection"],

      "EXECUTION_PREREQUISITES_NOT_YET_SATISFIED": {
        "S71": "the Stage-4 executor does not exist yet, so it cannot be bound. Until it "
               "is implemented, sha256/blob-bound and audited, execution authority is NOT "
               "GRANTABLE however many design gates pass.",
        "what_the_executor_will_do": [
          "load T3/T4/T5 and the availability columns",
          "compute per-donor-per-pair Pearson across metacells",
          "residualise on the frozen 14-feature basis via the unmodified estimator",
          "aggregate under GENE_BALANCED with the PROMOTER_EQUAL companion",
          "bootstrap over donors, 4000 replicates, seed 20260929",
          "emit the primary and null tables with per-stratum breakdowns"],
        "G3_LIMIT_STATED_HONESTLY": "G3 proves only that this CONTRACT forbids reopening "
            "the RNA and ATAC matrices. It cannot prove the future executor obeys that "
            "rule, because the executor does not exist. That proof belongs with the "
            "executor binding and is listed here as unsatisfied rather than implied by a "
            "passing gate.",
        "unsatisfied_prerequisites": [
          "G16_EXECUTOR_BOUND: the executor source sha256 and git blob",
          "G17_EXECUTOR_OPENS_NO_MATRIX: static proof the executor never opens the RNA or "
          "ATAC h5ad files"]},

      "AUTHORISATION_IS_NOT_GRANTED_HERE": {
        "statement": "this artifact defines what Stage-4 execution authority would "
                     "require. It does not grant it.",
        "granting_requires": "an explicit decision after this contract and its tests are "
                             "independently audited"},
      "governance": N3["governance"],
      "producer": dict(
        path=norm(os.path.relpath(os.path.abspath(__file__), os.getcwd())),
        sha256=B.sha_file(os.path.abspath(__file__)),
        git_blob=blob(norm(os.path.relpath(os.path.abspath(__file__), os.getcwd()))),
        blob_binding_note="S79. A producer cannot know its own blob before it is "
            "committed, so this is UNCOMMITTED at build time and bound post-commit by "
            "bind_stage4_producer_blob. The same provenance class as the B6 producer.")}

    p = os.path.join(DIR, "V64_STAGE4_EXECUTION_AUTHORITY_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(C, fh, indent=2)
    nb = len(C["BOUND_PHASE_B_INPUTS"]["substrate_shards"])
    print(f"bound {nb} substrate shards + T5 + availability + R3 + enum + Phase-A rows")
    print(f"estimator bound: {C['ESTIMATOR_IMPORTED_UNMODIFIED']['sha256']}")
    print(f"primary weighting: {C['METHOD_LOCKS']['weighting_hierarchy']['PRIMARY']}"
          f"  companion: {C['METHOD_LOCKS']['weighting_hierarchy']['MANDATORY_COMPANION']}")
    print(f"bootstrap: {C['METHOD_LOCKS']['uncertainty']['replicates']} reps "
          f"seed {C['METHOD_LOCKS']['uncertainty']['seed']}")
    print(f"null denominator: {C['NULL_AND_STRATA_LOCKS']['randomized_null_denominator']:,}")
    print(f"fail-closed gates: {len(C['FAIL_CLOSED_GATES'])}")
    print(f"\ncontract sha256 {B.sha_file(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
