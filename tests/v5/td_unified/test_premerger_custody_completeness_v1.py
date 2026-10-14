from __future__ import annotations

import json
from pathlib import Path

from scripts.v5.td_unified.premerger_custody_completeness_v1 import (
    GLOBAL_AUTHORITY,
    validate_completeness,
)

ROOT = Path(__file__).resolve().parents[3]
RESULT_DIR = ROOT / "results" / "target_discovery" / "unified_qualification_v1"
COMPLETENESS = RESULT_DIR / "PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1.json"
UNRESOLVED = RESULT_DIR / "PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json"

EXPECTED_OLD_SYNTH_HEAD = "ff597faf2182522a320ec5322f8db9b67c9c6094"
EXPECTED_FOCUSED_RUN = 38644641042
EXPECTED_FOCUSED_JOB = 116128364543
EXPECTED_INHERITED_RUN = 38644640881


def _synth_objects() -> dict[str, dict]:
    payload = json.loads(COMPLETENESS.read_text(encoding="utf-8"))
    group = next(g for g in payload["custody_groups"] if g["group_id"] == "ACTIVE_PR356_TASKS_1_4")
    return {obj["object_id"]: obj for obj in group["objects"]}


def test_premerger_merged_custody_completeness_validator_passes():
    report = validate_completeness(COMPLETENESS, UNRESOLVED)
    assert report["status"] == "PASS_PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1"
    assert report["group_count"] == 5
    assert report["required_unresolved_count"] == 9
    assert report["global_authority"] == GLOBAL_AUTHORITY


def test_pr356_tasks1_2_bind_exact_controller_verified_evidence():
    objects = _synth_objects()
    for object_id in ("PR356_TASK1", "PR356_TASK2"):
        obj = objects[object_id]
        assert obj["exact_head_sha"] == EXPECTED_OLD_SYNTH_HEAD
        assert obj["controller_review_pr"] == 382
        assert obj["controller_focused_run"] == EXPECTED_FOCUSED_RUN
        assert obj["controller_focused_job"] == EXPECTED_FOCUSED_JOB
        assert obj["controller_pytest_result"] == "332 passed in 8.94s"
        assert obj["inherited_integration_run"] == EXPECTED_INHERITED_RUN
        assert obj["independent_review_status"] == "PENDING"
        assert obj["state"] == "CONTROLLER_VERIFIED_REUSE_SUBSTRATE__INDEPENDENT_REVIEW_PENDING"


def test_old_tasks3_4_are_not_restartable_after_merger():
    objects = _synth_objects()
    for object_id in ("PR356_TASK3", "PR356_TASK4"):
        obj = objects[object_id]
        assert obj["state"] == "STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY"
        assert obj["continue_in_old_lane"] is False
        assert obj["implementation_head_required"] is False


def test_old_tasks5_12_remain_stopped_independently():
    objects = _synth_objects()
    assert objects["PR356_TASKS5_12"]["continue_independently"] is False
