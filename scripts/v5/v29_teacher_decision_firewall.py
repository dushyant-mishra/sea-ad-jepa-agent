#!/usr/bin/env python3
"""V29 prospective JEPA science packet fail-closed review; never issues authority."""
from __future__ import annotations
import copy, json, pathlib, sys

EXPECTED={"calibration_zip_sha256":"07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
          "extracted_sqlite_sha256":"a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913",
          "original_full104_expression_block_manifest_reference_sha256":"66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
          "frozen_pass1_sha256":"37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1",
          "total_reader_fit_donors":104,"total_reader_fit_cells":4553407,
          "operators":42,"source_donors":{"HVS":41,"NPH52":17,"SEA_AD":46},
          "strict_measured_common_core":17186}
REQUIRED_NULL={
 "teacher_state":("exact_implementation_source_sha256","target_construction_authority_root",
                  "teacher_semantics_authority_root","remaining_rna_necessity_root"),
 "split_and_scientific_weight":("named_frozen_B1_training_contract",
                  "prospective_source_stratified_heldout_fit_donor_ids","frozen_training_donor_ids",
                  "sampler_proposal_q"),
 "masking":("selected_scientific_mask","bounded_first_development_candidate","burden_fraction",
            "approved_dev_only_exception"),
 "resource_bounded_instrument":("model_width","depth","attention_heads","ffn_width",
           "model_biological_dimension_claim","ema_half_life_in_successful_scientific_presentations",
           "optimizer_lr","successful_update_budget","measured_token_microbatch_budget",
           "explicit_seed","gpu_hardware_budget_evidence"),
 "prospective_evaluation":("minimum_effect_threshold","uncertainty_precision_threshold")
}
REQUIRED_NEGATIVES={
 "QUERY_IDENTITY_ONLY","QUERY_IDENTITY_PLUS_LAWFUL_GLOBAL_CONTEXT_WITHOUT_REMAINING_RNA",
 "MEASUREMENT_SUPPORT_ONLY","SOURCE_OPERATOR_AND_LIBRARY_DEPTH_ONLY",
 "STUDENT_QUERY_SCALAR_LEAK_INJECTION_MUST_FAIL","DONOR_IDENTITY_OR_STABLE_CELL_KEY_CHEAT_MUST_FAIL"
}
CLOSED={"reader_validation22":"CLOSED","reader_oracle23":"SEALED",
        "foundation_development24":"CLOSED","foundation_sealed24":"SEALED",
        "external_siletti":"SEALED","pathology":"CLOSED","N1_terminal":"UNOPENED",
        "D_shared_G5":"UNOPENED","therapeutic_ranking":"OFF"}

def _must(value, expected, tag):
    if type(value) is not type(expected) or value!=expected:
        raise ValueError("STOP_V29_"+tag)
def check(d):
    _must(d.get("schema"),"V29_PROSPECTIVE_READER_FIT_TEACHER_DECISION_REQUEST_V1","SCHEMA")
    _must(d.get("document_role"),"REVIEWABLE_SCIENTIFIC_DRAFT__NOT_AUTHORITY","ROLE")
    for p in ("training_authorized","execution_authorized","protected_outcomes_authorized"):
        _must(d.get(p),False,"UNAUTHORIZED_"+p)
    _must(d.get("parent_v28_commit"),"fecd8aadaed5581fc00611bc64063c69fb119faf","PARENT_V28")
    _must(d.get("current_main_governance_commit"),"c49b13bd75c2d23716c777336db8fbfc78c09cd0","GOVERNANCE")
    _must(d.get("s9_retraction_commit"),"e00ba4ad3f6cb536a65fb25b5f80621c631893c5","S9_RETRACTION")
    m=d["authenticated_metadata"]
    for k,v in EXPECTED.items():_must(m.get(k),v,"PHYSICAL_METADATA_"+k)
    _must(m.get("full_expression_manifest_physically_rehashed_in_this_work"),False,"FALSE_PHYSICAL_LEVEL4")
    _must(m.get("no_all8915_raw_block_scan_qualification"),True,"FALSE_RAW_AUDIT")
    t=d["teacher_state"]
    for k,v in {
        "semantics_id":"BIOLOGICAL_CELLULAR_LATENT_STATE_V1",
        "query_local_id":"QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1",
        "student_query_scalar":"WITHHELD_BEFORE_ANY_STUDENT_CONTEXT_MIXING",
        "target_state":"QUERY_LOCAL_CONTEXTUAL_TEACHER_EMBEDDING__NOT_HIDDEN_GENE_SCALAR",
        "objective":"WEIGHTED_BLOCK_LATENT_STATE_MSE_WITH_DETACHED_TEACHER__NO_SCALAR_EXPRESSION_LOSS",
        "teacher_state_proven_biological":False
    }.items():_must(t.get(k),v,"TARGET_"+k)
    if "NO_DIRECT_SCALAR_REGRESSION" not in t.get("query_scalar_teacher",""):
        raise ValueError("STOP_V29_HIDDEN_SCALAR_OBJECTIVE")
    for group,fields in REQUIRED_NULL.items():
        for field in fields:
            if d[group].get(field,"MISSING") is not None:
                raise ValueError("STOP_V29_UNAPPROVED_VALUE_"+group+"_"+field)
    w=d["split_and_scientific_weight"]
    for key in ("all104_trained_cannot_be_called_unseen_donor",
                "existing_104_mass_csv_is_design_reference_not_split_specific_training_weights",
                "d1_equal_operator_weights_not_base_jepa","smallest_donor_cells_81_is_capacity_not_selected_batch"):
        _must(w.get(key),True,"WEIGHT_SCOPE_"+key)
    _must(w.get("base_jepa_training_cell_probability"),
          "1/(D_train*n_d)__D_train_AND_PER_DONOR_N_FIXED_AFTER_SPLIT","WRONG_DONOR_DENOMINATOR")
    _must(w.get("importance_rule"),"REQUIRE_EXPLICIT_P_OVER_Q_UNLESS_Q_EQUALS_P","PROPOSAL_Q_SPILLOVER")
    _must(w.get("relational_auxiliary_first_diagnostic"),False,"IMPORTED_RELATIONAL")
    _must(d["masking"].get("previous_september16_result"),"NINE_CELL_GRID_NO_QUALIFIER","FALSE_MASK_QUALIFICATION")
    _must(d["masking"].get("unqualified_uniform_candidate_is_not_training_permission"),True,"MASK_BYPASS")
    _must(d["prospective_evaluation"].get("g3_six_state_real_evaluator_qualified"),False,"G3_FAKE_REAL")
    _must(d["prospective_evaluation"].get("six_state_undefined_terms"),"NON_ESTIMABLE_NOT_ZERO","G3_ZERO_IMPUTATION")
    _must(d["prospective_evaluation"].get("no_old94_proxy_promotion"),True,"HISTORICAL94")
    if set(d["prospective_evaluation"].get("negative_controls",[]))!=REQUIRED_NEGATIVES:
        raise ValueError("STOP_V29_MISSING_NEGATIVE_CONTROL")
    auth=d["authority_dependencies"]
    for k in ("B1_frozen_named_training_contract_issued","B2_current_authority_closure_v2_issued",
              "current_final_teacher_target_package_frozen","receipt_v2_issued",
              "critical_test_and_runtime_source_authentication_complete"):
        _must(auth.get(k),False,"FAKE_AUTHORITY_"+k)
    for k,v in {"B2_upstream_slots":32,"B2_receipt_slots":33,"six_own_schema_candidates_verified":True,
                "fully_closed_roots":0,
                "V3_rng_and_parameters_incompatible_with_current_V1_closure_classes":True}.items():
        _must(auth.get(k),v,"ROOT_SPILLOVER_"+k)
    gov=d["governance"]
    for k,v in CLOSED.items():_must(gov.get(k),v,"PROTECTED_"+k)
    _must(gov.get("s9"),"RETRACTED__CANONICAL_CONDA_WITH_LIBRARY_BIN_ON_PATH","S9_REVIVED")
    _must(gov.get("prior_40of40_counter"),"WITHDRAWN_VACUOUS","FAKE_GRADIENT_GREEN")
    _must(gov.get("historical_T1_and_94_donor_numeric_defaults"),"FORBIDDEN_CURRENT104_AUTHORITY","HISTORICAL_SPILLOVER")
    _must(d.get("approval"),"NOT_REQUESTED_BY_THIS_FILE__REVIEW_ONLY","FALSE_APPROVAL")
    if len(d.get("owner_review_required",[]))<8:raise ValueError("STOP_V29_DECISIONS_SILENTLY_DROPPED")
    return "PASS_NONAUTHORIZING_V29_SCIENCE_DECISION_DRAFT__B1_AND_B2_STILL_CLOSED"

def main():
    if len(sys.argv)!=2:raise SystemExit("USAGE: firewall.py DRAFT_JSON")
    print(check(json.loads(pathlib.Path(sys.argv[1]).read_text())))
if __name__=="__main__":main()
