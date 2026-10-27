"""Hostile successor-pointer identity and authority mutations."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_jepa_lane_handoff_v8 import POINTER,validate_pointer
ROOT=Path(__file__).resolve().parents[2]


def source():
    return json.loads((ROOT/POINTER).read_text(encoding="utf-8"))


def test_current_handoff_exact_snapshot_passes():
    validate_pointer(source(),ROOT)


@pytest.mark.parametrize("change",[
    lambda x:x.update(authority="REAL_TRAINING_ON"),
    lambda x:x.update(no_scientific_authority=False),
    lambda x:x.update(external_large_artifact_copy_to_git=True),
    lambda x:x.update(frozen_unified_task3="f"*40),
    lambda x:x["active"].update(task4="CUSTODY_ACCEPTED"),
    lambda x:x["active"].update(real_g7="E3_PASS"),
    lambda x:x["active"].update(ps_task3="TASK3_RECHECK_NOT_NEEDED"),
    lambda x:x["active"].update(ps_task1="FULLY_ACCEPTED"),
    lambda x:x["active"].update(ps_task2="13_RED_RESOLVED"),
    lambda x:x["active"].update(regulatory_e2g="TF_CAUSALITY_CONFIRMED"),
    lambda x:x["master_audit"].update(post_v8a_machine="MISSING"),
    lambda x:x["master_audit"].update(post_v8b_machine="MISSING"),
    lambda x:x["master_audit"].update(v8b_supplement="MISSING"),
    lambda x:x["handoff"].update(first_session="MISSING"),
    lambda x:x["master_audit"].update(complete_takeover_index="MISSING"),
    lambda x:x["active"].update(task5="SAME_CODE_PATH_CERTIFIED"),
    lambda x:x["active"].update(tasks6_8="REAL_TARGET_PASS"),
    lambda x:x["master_audit"].update(exact_head_at_pointer="TO_BE_FETCHED"),
    lambda x:x["master_audit"].update(pr=999),
    lambda x:x["handoff"].update(pr=322),
    lambda x:x["read_order"].reverse(),
])
def test_forged_successor_authority_and_stale_navigation_refused(change):
    obj=deepcopy(source())
    change(obj)
    with pytest.raises((ValueError,FileNotFoundError)):
        validate_pointer(obj,ROOT)


def test_old_versions_not_automatically_promoted():
    obj=source()
    assert obj["handoff"]["older_versions_historical"] is True
    assert obj["master_audit"]["ci_status_at_pointer"] in ("QUEUED__NOT_YET_VERIFIED","EXACT_HEAD_CI_GREEN","EXACT_HEAD_V8_V8A_V8B_ALL_GREEN")
