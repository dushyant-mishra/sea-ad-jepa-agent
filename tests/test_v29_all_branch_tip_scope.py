"""V29 all-branch-tip head sweep: documentary self-audit, no authority issuance."""
import copy,json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/"docs/agent/JEPA_V29_ALL_BRANCH_TIP_AUTHORITY_SCOPE_20260926.json"
def source():return json.loads(P.read_text())
def check(d):
    if d.get("schema")!="JEPA_V29_ALL_GITHUB_BRANCH_TIP_SCOPE_AUDIT_V1":
        raise ValueError("STOP_SCHEMA")
    expected={"branch_count":263,"distinct_branch_tip_heads":232,"covered_by_previous_open_pr_tip_scans":114,
       "new_unique_branch_tip_heads_scanned":118,"new_tree_failures_or_truncations":0,
       "new_branch_tip_candidate_appearances":233,"distinct_additional_branch_tip_candidate_blobs":41,
       "prior_open_pr_distinct_novel_blobs":18,"new_unique_path_blob_candidates_not_seen_on_prior_open_pr_tips":31,
       "union_unique_novel_path_blobs":49,"exact_source_roles_actually_schema_inspected_here":9,
       "new_current_v5_defining_class_validations_executed":0,"new_current_v5_closure_roots_validated":0}
    for k,v in expected.items():
        if type(d.get(k))!=int or d[k]!=v:raise ValueError("STOP_COUNTER_DRIFT_"+k)
    all=d.get("all_branch_heads")
    if not isinstance(all,list) or len(all)!=263 or len({x["branch"] for x in all})!=263 or len({x["head"] for x in all})!=232:
        raise ValueError("STOP_BRANCH_CENSUS")
    for x in all:
        if not isinstance(x["head"],str) or len(x["head"])!=40:raise ValueError("STOP_BRANCH_SHA_SHAPE")
    rows=d.get("additional_unique_candidate_path_blobs")
    if not isinstance(rows,list) or len(rows)!=31 or len({(x["path"],x["sha"]) for x in rows})!=31:
        raise ValueError("STOP_CANDIDATE_DEDUPLICATION")
    present={x["branch"] for x in all}
    if any(not x["branches"] or any(y not in present for y in x["branches"]) for x in rows):
        raise ValueError("STOP_BRANCH_PROVENANCE")
    for x in rows:
        if x.get("current_v5_own_class_validated_in_this_branch_sweep") is not False or x.get("current_v5_closure_qualified_in_this_branch_sweep") is not False:
            raise ValueError("STOP_FALSE_AUTHORITY_PROMOTION")
    for k in ("source_parent_bytes_physically_authenticated","remote_gpu_disk_scanned","training_authorized","protected_outcomes_opened"):
        if d.get(k) is not False:raise ValueError("STOP_FALSE_PHYSICAL_OR_EXECUTION_"+k)
    if d.get("all_263_branch_tips_rechecked_unchanged_before_publication") is not True:
        raise ValueError("STOP_STALE_BRANCH_TIPS")
    if "EXCLUDES_REMOTE_GPU_DISK" not in d.get("scan_population",""):
        raise ValueError("STOP_FALSE_GLOBAL_COMPLETENESS")
    return "PASS_263_BRANCH_NAMES_232_TIPS_31_EXTRA_PATH_BLOBS__NO_AUTHORITY"
def fail(m):
    d=source();m(d)
    with pytest.raises(ValueError,match="STOP_"):check(d)
def test_complete_snapshot_positive_control():assert check(source()).startswith("PASS")
def test_missing_branch_ref_fails():fail(lambda d:d["all_branch_heads"].pop())
def test_duplicate_branch_ref_fails():fail(lambda d:d["all_branch_heads"].__setitem__(0,d["all_branch_heads"][1]))
def test_missing_distinct_tip_is_detected():fail(lambda d:d.update(distinct_branch_tip_heads=231))
def test_false_increase_in_open_pr_coverage_fails():fail(lambda d:d.update(covered_by_previous_open_pr_tip_scans=115))
def test_missing_candidate_blob_fails():fail(lambda d:d["additional_unique_candidate_path_blobs"].pop())
def test_duplicate_candidate_blob_fails():fail(lambda d:d["additional_unique_candidate_path_blobs"].__setitem__(0,d["additional_unique_candidate_path_blobs"][1]))
def test_historical_candidate_cannot_be_own_class_promoted():
    fail(lambda d:d["additional_unique_candidate_path_blobs"][0].update(current_v5_own_class_validated_in_this_branch_sweep=True))
def test_synthetic_old_critical_manifest_cannot_be_training_authority():
    fail(lambda d:d.update(new_current_v5_closure_roots_validated=1))
def test_false_gpu_disk_scan_rejected():fail(lambda d:d.update(remote_gpu_disk_scanned=True))
def test_false_full_authentication_rejected():fail(lambda d:d.update(source_parent_bytes_physically_authenticated=True))
def test_false_training_authority_rejected():fail(lambda d:d.update(training_authorized=True))
def test_false_protected_opening_rejected():fail(lambda d:d.update(protected_outcomes_opened=True))
def test_unresolved_api_error_cannot_be_false_green():fail(lambda d:d.update(new_tree_failures_or_truncations=1))
def test_stale_unrechecked_branch_names_cannot_be_false_green():fail(lambda d:d.update(all_263_branch_tips_rechecked_unchanged_before_publication=False))
