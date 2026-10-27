"""Static claim-custody validator for PR479 V2 observation-depth fixture delta.

Does not fetch GitHub logs, authenticate physical reads, or certify real G7.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = "results/target_discovery/unified_qualification_v1/JEPA_NORMALIZATION_VIEW_V2_FIXTURE_DELTA_20261027.json"
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
BLOBS = {
    "scripts/v5/td_unified/observation_normalization_view_v2_fixture.py":"fd573764d8c7d19b8cbbf12683d3e79065385cef",
    "tests/v5/td_unified/test_observation_normalization_view_v2_fixture.py":"61349d4a69a1ace95d7f9d714e983e4aeb0fefd7",
    "docs/agent/JEPA_TD_NORMALIZATION_VIEW_V2_FIXTURE_CONTRACT_20261027.md":"08a85a9f4459b0d5f58965390b0cc9664d8160c6",
    ".github/workflows/td-observation-normalization-view-v2-fixture.yml":"8a91bf44022e279723770858487df17398fc8fde",
}

def require(ok, reason):
    if not ok:
        raise ValueError("V2_NORMALIZATION_AUDIT_NONPROMOTION_REFUSAL: "+reason)

def verify(d):
    require(d.get("schema")=="JEPA_TD_OBSERVATION_NORMALIZATION_VIEW_V2_FIXTURE_AUDIT_DELTA_V1","schema")
    require(d.get("classification")=="APPEND_ONLY_SOURCE_EXECUTED_MECHANICS__NO_SCIENTIFIC_AUTHORITY","classification")
    require(d.get("standing_authority")==AUTH,"authority")
    require(d.get("historical_v8e_qualified_head")=="a271164554076d0acda3bd0cf0b1bf957c0fdfd3","prior frozen authority")
    w=d.get("source_work",{})
    require(w.get("pr")==479 and w.get("head")=="ae762d7096a94ac663a0788f6f577ba404e37536"
            and w.get("base_review_pr")==478 and w.get("base_producer_pr")==474
            and w.get("original_producer_unchanged") is True
            and w.get("legacy_casebundle_git_blob")=="23bbdcfc3234b7d621beb870fa019b34822446af",
            "source exact head and legacy blob")
    require({x["path"]:x["git_blob"] for x in w["new_files"]}==BLOBS,"new source blobs changed")
    m=d.get("mechanics",{})
    for key in ("separate_student_and_teacher_functions","canonical_exact_builtins_source_snapshot",
                "private_whole_physical_total_never_returned","observable_hash_excludes_private_whole_library",
                "explicit_query_outside_base_required"):
        require(m.get(key) is True, "missing essential V2 fixture law "+key)
    for key in ("legacy_library_size_field_reused","original_casebundle_v1_modified",
                "original_g7_modified","real_issuer_authenticated","independent_scientific_acceptance"):
        require(m.get(key) is False,"false production or legacy claim "+key)
    require(m.get("unaccounted_source_mass")=="NOT_ESTIMABLE","unmapped molecule refusal")
    c=d.get("run_receipts",{})
    require(c.get("initial_red_run")==40591276863 and c.get("second_red_run")==40591445532,
            "historical RED-first CI erased")
    require(c.get("final_run")==40591648499 and c.get("final_exact_head")==w.get("head")
            and c.get("final_conclusion")=="SUCCESS" and c.get("total_tests_passed")==124
            and c.get("original_producer_and_prior_independent_tests")==106
            and c.get("new_v2_tests")==18 and
            c.get("commit_workflow_count")==6 and c.get("commit_workflow_successes")==6,
            "executed exact head evidence")
    require(c.get("v1_casebundle_legacy_semantics_asserted") is True
            and c.get("g7_cross_head_executed") is False,"cross-head false claim")
    blockers=d.get("upstream_blockers",{})
    require(blockers.get("g7_R1_R1D_R2")=="RED" and blockers.get("ps_T2D")=="RED"
            and blockers.get("ps_task4_biological_generator")=="ABSENT_IN_REVIEWED_BRANCHES"
            and blockers.get("cross_head_g7_v2")=="NOT_TESTED"
            and blockers.get("ps_task3_calibration_issuer")=="NOT_AUTHENTICATED",
            "current external science blockers")
    require(len(d.get("scientific_constraints",[]))>=5,"science limits disappeared")

if __name__=="__main__":
    verify(json.loads((ROOT/DATA).read_text()))
    print("NORMALIZATION_V2_SOURCE_CUSTODY_124_PASS__G7_CROSS_HEAD_UNTESTED__NO_AUTHORITY")
