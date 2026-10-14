from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.v5.td_unified.premerger_migration_task0 import GLOBAL_AUTHORITY

REQUIRED_GROUPS = {
    "ACTIVE_PR356_TASKS_1_4",
    "FOUNDATION_REPRESENTATION_CURRENT_STATE",
    "MULTIMODAL_SCENIC_ATAC_CUSTODY",
    "RUNTIME_TRAINING_SAFETY_HANDOFF",
    "FULL104_INFORMATION_CHANNEL_INVARIANTS",
}

REQUIRED_UNRESOLVED = {
    "U_MACHA_SYNTH_TASK1_CANONICAL_IDENTITY_ACTIVE",
    "U_MACHA_SYNTH_TASK2_CUSTODY_RNG_ACTIVE_OR_PENDING",
    "U_MACHA_SYNTH_TASK3_CALIBRATION_PROVENANCE_ACTIVE_OR_PENDING",
    "U_MACHA_SYNTH_TASK4_BIOLOGY_BLOCKED_ON_1_3_REVIEWS",
    "U_OLD_SYNTH_TASKS5_12_NO_INDEPENDENT_CONTINUATION",
    "U_FOUNDATION_REPRESENTATION_CUSTODY",
    "U_MULTIMODAL_REGULATORY_CUSTODY",
    "U_RUNTIME_TRAINING_SAFETY_CUSTODY",
    "U_FULL104_INFORMATION_CHANNEL_CUSTODY",
}

EXPECTED_OLD_SYNTH_HEAD = "ff597faf2182522a320ec5322f8db9b67c9c6094"
EXPECTED_CONTROLLER_REVIEW_PR = 382
EXPECTED_FOCUSED_RUN = 38644641042
EXPECTED_FOCUSED_JOB = 116128364543
EXPECTED_INHERITED_RUN = 38644640881
EXPECTED_CONTROLLER_STATE = "CONTROLLER_VERIFIED_REUSE_SUBSTRATE__INDEPENDENT_REVIEW_PENDING"
EXPECTED_STOPPED_STATE = "STOPPED_AFTER_MERGER__REQUIREMENTS_MIGRATE_ONLY"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _validate_pr356_current_state(synth_by_id: dict[str, dict[str, Any]]) -> None:
    expected_classifications = {
        "PR356_TASK1": "ADAPT_AND_WRAP__DIRECT_REUSE_CANDIDATE_FOR_CANONICAL_PRIMITIVES",
        "PR356_TASK2": "ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE",
    }
    for object_id in ("PR356_TASK1", "PR356_TASK2"):
        obj = synth_by_id[object_id]
        if obj.get("state") != EXPECTED_CONTROLLER_STATE:
            raise ValueError(f"{object_id} controller-verified state missing")
        if obj.get("exact_head_sha") != EXPECTED_OLD_SYNTH_HEAD:
            raise ValueError(f"{object_id} exact implementation head missing or moved")
        if obj.get("controller_review_pr") != EXPECTED_CONTROLLER_REVIEW_PR:
            raise ValueError(f"{object_id} controller review PR missing")
        if obj.get("controller_focused_run") != EXPECTED_FOCUSED_RUN:
            raise ValueError(f"{object_id} focused review run missing")
        if obj.get("controller_focused_job") != EXPECTED_FOCUSED_JOB:
            raise ValueError(f"{object_id} focused review job missing")
        if obj.get("controller_pytest_result") != "332 passed in 8.94s":
            raise ValueError(f"{object_id} focused pytest result missing")
        if obj.get("inherited_integration_run") != EXPECTED_INHERITED_RUN:
            raise ValueError(f"{object_id} inherited integration run missing")
        if obj.get("independent_review_status") != "PENDING":
            raise ValueError(f"{object_id} must not claim independent acceptance")
        if obj.get("migration_classification") != expected_classifications[object_id]:
            raise ValueError(f"{object_id} migration classification changed")

    for object_id in ("PR356_TASK3", "PR356_TASK4"):
        obj = synth_by_id[object_id]
        if obj.get("state") != EXPECTED_STOPPED_STATE:
            raise ValueError(f"{object_id} old-lane stop state missing")
        if obj.get("continue_in_old_lane") is not False:
            raise ValueError(f"{object_id} can still restart in old lane")
        if obj.get("implementation_head_required") is not False:
            raise ValueError(f"{object_id} still demands an old-lane implementation head")


def validate_completeness(completeness_path: Path, unresolved_path: Path) -> dict[str, Any]:
    payload = _load(completeness_path)
    unresolved = _load(unresolved_path)
    if payload.get("schema") != "PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1":
        raise ValueError("wrong completeness schema")
    if payload.get("global_authority") != GLOBAL_AUTHORITY:
        raise ValueError("completeness global authority changed")
    if unresolved.get("global_authority") != GLOBAL_AUTHORITY:
        raise ValueError("unresolved global authority changed")
    if payload.get("task1_blocked") is not True:
        raise ValueError("Task 1 must remain blocked")

    groups = payload.get("custody_groups")
    if not isinstance(groups, list):
        raise ValueError("custody_groups must be a list")
    by_id = {group.get("group_id"): group for group in groups if isinstance(group, dict)}
    if set(by_id) != REQUIRED_GROUPS:
        raise ValueError("merged custody groups incomplete or renamed")
    for group_id, group in by_id.items():
        if not group.get("unified_destination"):
            raise ValueError(f"missing unified destination for {group_id}")
        if not group.get("review_obligations"):
            raise ValueError(f"missing review obligations for {group_id}")
        if not group.get("objects"):
            raise ValueError(f"missing custody objects for {group_id}")

    synth = by_id["ACTIVE_PR356_TASKS_1_4"]
    synth_by_id = {obj.get("object_id"): obj for obj in synth["objects"]}
    required_synth = {"PR356_TASK1", "PR356_TASK2", "PR356_TASK3", "PR356_TASK4", "PR356_TASKS5_12"}
    if not required_synth.issubset(synth_by_id):
        raise ValueError("PR356 Tasks 1-4/5-12 custody split incomplete")
    _validate_pr356_current_state(synth_by_id)
    if synth_by_id["PR356_TASKS5_12"].get("continue_independently") is not False:
        raise ValueError("old Tasks5-12 independent execution not stopped")

    representation = json.dumps(by_id["FOUNDATION_REPRESENTATION_CURRENT_STATE"], sort_keys=True)
    for token in ("SUBSPACE_ONLY", "TECHNOLOGY_INVARIANCE_NOT_QUALIFIED", "34_OF_42"):
        if token not in representation:
            raise ValueError(f"representation custody missing {token}")

    multimodal = json.dumps(by_id["MULTIMODAL_SCENIC_ATAC_CUSTODY"], sort_keys=True)
    for token in ("STAGE75F", "SCENIC", "ATAC", "SAME_NUCLEUS", "SEPARATE_NUCLEUS", "INCOMPLETE_STOPPED"):
        if token not in multimodal:
            raise ValueError(f"multimodal custody missing {token}")

    runtime = json.dumps(by_id["RUNTIME_TRAINING_SAFETY_HANDOFF"], sort_keys=True)
    for token in ("OPTIMIZER_COMPLETION_BEFORE_EMA", "Q_SAFETY", "COORDINATE_VALUE_COUPLING"):
        if token not in runtime:
            raise ValueError(f"runtime custody missing {token}")

    full104 = json.dumps(by_id["FULL104_INFORMATION_CHANNEL_INVARIANTS"], sort_keys=True)
    for token in (
        "NORMALIZATION_DENOMINATOR_SOURCE_CHANNEL",
        "ADDRESS_PARITY_NE_EVIDENCE_PARITY",
        "ZERO_FILL_CAN_CREATE_FALSE_EASE",
        "WITHIN_DONOR_METRIC_BLINDNESS",
    ):
        if token not in full104:
            raise ValueError(f"FULL104 custody missing {token}")

    unresolved_ids = {item.get("item_id") for item in unresolved.get("items", []) if isinstance(item, dict)}
    missing = sorted(REQUIRED_UNRESOLVED - unresolved_ids)
    if missing:
        raise ValueError("re-audit unresolved items missing: " + ", ".join(missing))

    return {
        "status": "PASS_PREMERGER_MERGED_CUSTODY_COMPLETENESS_V1",
        "group_count": len(by_id),
        "required_unresolved_count": len(REQUIRED_UNRESOLVED),
        "global_authority": GLOBAL_AUTHORITY,
    }
