#!/usr/bin/env python3
"""Proposed scientific teacher-target *decision packet* firewall: not issuance."""
from __future__ import annotations
import json, pathlib, sys
EXPECTED_CALIBRATION="07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
EXPECTED_SQLITE="a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
EXPECTED_LEVEL4="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
NULL_NUMERICS=("provisional_width","provisional_depth","provisional_heads","provisional_ffn_width",
    "ema_half_life_accepted_presentations","optimizer_lr","update_budget","gpu_token_microbatch_budget","seeds")
def check(d):
    if d.get("schema")!="V27_PROSPECTIVE_TEACHER_TARGET_DECISION_DRAFT_V1":
        raise ValueError("STOP_PROPOSAL_SCHEMA")
    if d.get("document_role")!="SCIENTIFIC_DECISION_REQUEST_ONLY__NOT_A_TARGET_PACKAGE_OR_AUTHORITY_RECEIPT":
        raise ValueError("STOP_PROPOSAL_ROLE")
    if any(d.get(k) is not False for k in ("training_authorized","execution_authorized","protected_outcomes_authorized")):
        raise ValueError("STOP_FALSE_AUTHORITY")
    g=d["current_v5_governance"]
    if g["reader_fit"]!="ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY" or g["development_contract"]!="NOT_ISSUED" or g["frozen_teacher_target_package"]!="NOT_ISSUED" or g["closure_v2"]!="NOT_ISSUED" or g["receipt_v2"]!="NOT_ISSUED" or g["closed_roots"]!=0:
        raise ValueError("STOP_PREMATURE_AUTHORITY")
    if g["authority_root_slots"]!=33 or g["validated_own_schema_candidates"]!=6:
        raise ValueError("STOP_UNSUPPORTED_ROOT_CENSUS")
    m=d["full104_existing_metadata"]
    fixed={"fit_donors":104,"fit_cells":4553407,"operators":42,"donor_operator_groups":1400,
           "strict_common_measured_all42":17186,"any_operator_each_source":17346,
           "calibration_zip_sha256":EXPECTED_CALIBRATION,"sqlite_sha256":EXPECTED_SQLITE,
           "current_full104_level4_manifest_reference_sha256":EXPECTED_LEVEL4,
           "level4_manifest_physically_rehashed_in_this_cycle":False}
    if any(m.get(k)!=v for k,v in fixed.items()):raise ValueError("STOP_DATASET_SCOPE_SPILLOVER")
    if d["weighting"]["actually_frozen_training_donors"] is not None:
        raise ValueError("STOP_UNAPPROVED_TRAINING_DONOR_SET")
    if d["weighting"]["unseen_donor_claim_permitted_for_all104_training"] is not False:
        raise ValueError("STOP_FAKE_HELDOUT")
    mask=d["masking"]
    if any(mask.get(k) is not None for k in ("scientifically_qualified_policy","first_development_candidate","mask_fraction")):
        raise ValueError("STOP_IMPORTED_MASKING")
    geom=d["model_and_schedule"]
    if any(geom.get(k) is not None for k in (*NULL_NUMERICS,"model_geometry_authority")):
        raise ValueError("STOP_UNJUSTIFIED_GEOMETRY_OR_EMA")
    e=d["evaluation"]
    if e["development_scoring_plan"] is not None or e["protected_reader_validation22"]!="CLOSED" or e["protected_reader_oracle23"]!="SEALED":
        raise ValueError("STOP_PROTECTED_OR_UNAPPROVED_SCORING")
    if d["scientific_goal"]["query_scalar_policy_id"]!="QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1" or d["scientific_goal"]["scalar_expression_objective_policy_id"]!="SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1":
        raise ValueError("STOP_WRONG_ESTIMAND")
    return "PASS_NON_AUTHORIZING_TEACHER_DECISION_PACKET__ALL_UNRESOLVED_SETTINGS_EXPLICIT"
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("USAGE: python v27_teacher_proposal_firewall.py DECISION_DRAFT_JSON")
    print(check(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))))
