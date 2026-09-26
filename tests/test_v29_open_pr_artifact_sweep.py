"""Independent bounded artifact sweep: exact snapshot accounting and hostile metadata mutants."""
import copy,json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/"docs/agent/JEPA_V29_ALL_OPEN_PR_AUTHORITY_CANDIDATE_SWEEP_20260926.json"
def get():return json.loads(P.read_text())
def check(s):
    if s.get("schema")!="JEPA_V29_OPEN_PR_CANDIDATE_PATH_BLOB_SWEEP_V1":
        raise ValueError("STOP_SCOPE_SCHEMA")
    if s.get("open_pr_count_at_snapshot")!=114 or s.get("unique_open_pr_heads_scanned")!=114 or s.get("tip_trees_failed_or_truncated")!=0:
        raise ValueError("STOP_INCOMPLETE_PR_HEAD_SCAN")
    prs=s.get("pr_tip_snapshot")
    if not isinstance(prs,list) or len(prs)!=114 or len({p["pr"] for p in prs})!=114 or len({p["head"] for p in prs})!=114:
        raise ValueError("STOP_PR_SNAPSHOT_CARDINALITY")
    if any(not isinstance(p.get("head"),str) or len(p["head"])!=40 for p in prs):
        raise ValueError("STOP_PR_SHA_SHAPE")
    a=s.get("unique_novel_candidates")
    if not isinstance(a,list) or len(a)!=18 or s.get("unique_novel_path_blob_candidates")!=18 or s.get("novel_pr_head_candidate_occurrences")!=87:
        raise ValueError("STOP_NOVEL_BLOB_CARDINALITY")
    seen=set()
    for x in a:
        key=(x["path"],x["git_blob_sha1"])
        if key in seen or len(x["git_blob_sha1"])!=40 or x["bytes"]<=0:
            raise ValueError("STOP_NONUNIQUE_OR_UNBOUND_BLOB")
        seen.add(key)
        if x["path_scope_classification"] not in (
            "HISTORICAL_TARGET_SOURCE_ESTIMABILITY_NOT_CURRENT_V5_ROOT",
            "N1_OR_BOUNDED_PREEXECUTION_OTHER_AUTHORITY_SCOPE",
            "RARE_TAIL_SEPARATE_OUTCOME_BLIND_PREQUALIFICATION",
            "HISTORICAL_HANDOFF_OR_PROVENANCE_INDEX"):
            raise ValueError("STOP_ROOT_ROLE_FABRICATION")
        if x.get("current_v5_own_class_validator_run_by_this_sweep") is not False or x.get("proves_any_v2_root_closed") is not False:
            raise ValueError("STOP_FALSE_VALIDATION")
        if not x["pr_numbers"] or any(p not in {y["pr"] for y in prs} for p in x["pr_numbers"]):
            raise ValueError("STOP_PR_ATTRIBUTION")
    if s.get("current_v5_new_own_schema_validations_executed_by_this_sweep")!=0 or s.get("fully_closed_current_v5_roots_proven_by_this_sweep")!=0:
        raise ValueError("STOP_FALSE_ROOT_PROMOTION")
    if s.get("previous_own_schema_candidates")!=6 or s.get("previous_full_closure_roots")!=0:
        raise ValueError("STOP_REWRITTEN_HISTORICAL_EVIDENCE")
    for k in ("remote_gpu_disk_scanned","orphan_branches_all_scanned","training_authorized","protected_outcomes_opened"):
        if s.get(k) is not False: raise ValueError("STOP_FALSE_GLOBAL_ACCESS_"+k)
    if "NOT_ALL_REPO_BRANCHES_OR_REMOTE_GPU_DRIVE" not in s.get("scan_population",""):
        raise ValueError("STOP_FALSE_GLOBAL_COMPLETENESS")
    return "PASS_114_HEADS_18_UNIQUE_BLOBS__NO_NEW_VALIDATED_ROOT"
def fail(edit):
    x=get();edit(x)
    with pytest.raises(ValueError,match="STOP_"):check(x)
def test_positive_original_snapshot_has_full_scoped_inventory():assert check(get()).startswith("PASS")
def test_suppressed_pr_tip_cannot_pass():fail(lambda x:x["pr_tip_snapshot"].pop())
def test_duplicate_pr_tip_cannot_pass():fail(lambda x:x["pr_tip_snapshot"].__setitem__(0,x["pr_tip_snapshot"][1]))
def test_missing_tree_cannot_be_reported_complete():fail(lambda x:x.update(tip_trees_failed_or_truncated=1))
def test_missing_new_candidate_cannot_be_hidden():fail(lambda x:x["unique_novel_candidates"].pop())
def test_duplicate_git_path_blob_pair_detected():fail(lambda x:x["unique_novel_candidates"].__setitem__(0,x["unique_novel_candidates"][1]))
def test_scope_splicing_n1_as_v5_detected():fail(lambda x:x["unique_novel_candidates"][0].update(path_scope_classification="CURRENT_V5_AUTHORITY_CLOSED"))
def test_claimed_own_schema_validation_fails():fail(lambda x:x["unique_novel_candidates"][0].update(current_v5_own_class_validator_run_by_this_sweep=True))
def test_claimed_closed_root_fails():fail(lambda x:x.update(fully_closed_current_v5_roots_proven_by_this_sweep=1))
def test_false_gpu_scan_fails():fail(lambda x:x.update(remote_gpu_disk_scanned=True))
def test_false_all_branch_scan_fails():fail(lambda x:x.update(orphan_branches_all_scanned=True))
def test_false_training_authority_fails():fail(lambda x:x.update(training_authorized=True))
def test_historical_six_candidate_rewrite_fails():fail(lambda x:x.update(previous_own_schema_candidates=25))
def test_unsupported_pr_reference_fails():fail(lambda x:x["unique_novel_candidates"][0].update(pr_numbers=[999]))
