from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GLOBAL_AUTHORITY = (
    "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__"
    "REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
)

MIGRATION_CLASSES = frozenset(
    {
        "REUSABLE_SHARED_INFRASTRUCTURE",
        "KNOWN_TRUTH_SUBSTRATE",
        "KNOWN_TRUTH_CHALLENGE_ASSET",
        "DEVELOPMENT_FIXTURE",
        "HISTORICAL_NEGATIVE_CONTROL",
        "PRODUCTION_INTERFACE_DEPENDENCY",
        "SUPERSEDED_PARALLEL_IMPLEMENTATION",
        "CLOSED_FAILED_EXPERIMENT",
        "NEEDS_REVIEW_BEFORE_CLASSIFICATION",
    }
)

_REQUIRED_ARTIFACT_FIELDS = {
    "artifact_id",
    "artifact_path",
    "artifact_digest",
    "source_branch",
    "source_commit",
    "original_role",
    "scientific_role",
    "migration_class",
    "current_authority",
    "qualification_stage_if_applicable",
    "active_lineage_status_if_applicable",
    "known_defects",
    "tests_or_receipts",
    "reusable_components",
    "superseded_components",
    "destination_in_unified_architecture",
    "requires_requalification",
    "requalification_reason",
    "historical_evidence_retained",
    "authority_basis",
    "continue_stop_or_redirect",
    "unresolved_item_ids",
    "exact_identity_available",
}

_REQUIRED_DECOMPOSITION_CHILD_FIELDS = {
    "child_artifact_id",
    "scientific_role",
    "migration_class",
    "current_authority",
    "destination_in_unified_architecture",
    "continue_stop_or_redirect",
    "historical_evidence_retained",
    "requires_requalification",
    "requalification_reason",
    "reusable_components",
    "superseded_components",
    "source_commit",
    "artifact_digest",
    "exact_identity_available",
    "authority_basis",
}

_REQUIRED_UNRESOLVED_FIELDS = {
    "item_id",
    "missing_dependency",
    "why_missing",
    "who_owns_resolution",
    "can_known_truth_lane_finish_now",
    "requires_merged_lane_interface",
    "requires_real_data",
    "blocks_same_code_path",
    "blocks_known_truth_qualification",
    "blocks_real_reference_ready",
    "blocks_human_execution",
}

_EXPECTED_BOUNDARIES = {
    "candidate_outcomes_opened": False,
    "reader_validation_opened": False,
    "reader_oracle_opened": False,
    "real_data_recomputed": False,
}

_DECOMPOSITION_FILENAME = "PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing Task 0 output: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Task 0 output must be a JSON object: {path}")
    return payload


def _require_global_authority(payload: dict[str, Any], label: str) -> None:
    if payload.get("global_authority") != GLOBAL_AUTHORITY:
        raise ValueError(f"{label} global authority changed")


def _validate_exact_identity(record: dict[str, Any], label: str) -> None:
    if "exact_identity_available" not in record:
        raise ValueError(f"{label} missing required field: exact_identity_available")
    if not isinstance(record["exact_identity_available"], bool):
        raise ValueError(f"{label} exact_identity_available must be boolean")
    if record["exact_identity_available"]:
        if not record.get("source_commit") or not record.get("artifact_digest"):
            raise ValueError(f"available exact identity omitted for {label}")


def _validate_decompositions(matrix_path: Path, artifacts: list[dict[str, Any]]) -> int:
    mixed = {a["artifact_id"] for a in artifacts if a.get("mixed_historical_object") is True}
    if not mixed:
        return 0

    decomposition_path = matrix_path.with_name(_DECOMPOSITION_FILENAME)
    try:
        decomposition = _load(decomposition_path)
    except ValueError as exc:
        raise ValueError("mixed artifact decomposition registry missing") from exc
    _require_global_authority(decomposition, "mixed artifact decomposition registry")

    entries = decomposition.get("decompositions")
    if not isinstance(entries, list) or not entries:
        raise ValueError("mixed artifact decomposition registry must contain decompositions")

    by_parent: dict[str, dict[str, Any]] = {}
    child_ids: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"decomposition {idx} is not an object")
        parent = entry.get("parent_artifact_id")
        if not parent or parent in by_parent:
            raise ValueError(f"invalid or duplicate decomposition parent: {parent}")
        children = entry.get("children")
        if not isinstance(children, list) or len(children) < 2:
            raise ValueError(f"mixed artifact decomposition incomplete for {parent}")
        classes: set[str] = set()
        for child_idx, child in enumerate(children):
            if not isinstance(child, dict):
                raise ValueError(f"decomposition child {parent}[{child_idx}] is not an object")
            missing = sorted(_REQUIRED_DECOMPOSITION_CHILD_FIELDS - child.keys())
            if missing:
                raise ValueError(
                    f"decomposition child {parent}[{child_idx}] missing fields: {', '.join(missing)}"
                )
            child_id = child["child_artifact_id"]
            if child_id in child_ids:
                raise ValueError(f"duplicate decomposition child id: {child_id}")
            child_ids.add(child_id)
            migration_class = child["migration_class"]
            if migration_class not in MIGRATION_CLASSES:
                raise ValueError(f"invalid migration_class for decomposition child {child_id}")
            classes.add(migration_class)
            _validate_exact_identity(child, f"decomposition child {child_id}")
            if child.get("authority_basis") == "PR_OR_BRANCH_NAME":
                raise ValueError(f"navigation metadata used as authority for decomposition child {child_id}")
            if migration_class == "SUPERSEDED_PARALLEL_IMPLEMENTATION":
                if child["continue_stop_or_redirect"] != "STOP_AND_FREEZE":
                    raise ValueError(f"parallel decomposition child still active: {child_id}")
                if child["current_authority"] not in {
                    "NONE__HISTORICAL_EVIDENCE_ONLY",
                    "SUPERSEDED__NO_NEW_SCIENTIFIC_AUTHORITY",
                }:
                    raise ValueError(f"ambiguous authority for superseded decomposition child: {child_id}")
            if migration_class == "CLOSED_FAILED_EXPERIMENT":
                if not str(child["current_authority"]).startswith("NONE"):
                    raise ValueError(f"failed decomposition child promoted: {child_id}")
                if child["requires_requalification"] is not True:
                    raise ValueError(f"failed decomposition child missing requalification: {child_id}")
        if len(classes) < 2:
            raise ValueError(f"mixed artifact decomposition does not separate migration classes: {parent}")
        by_parent[parent] = entry

    missing_parents = sorted(mixed - by_parent.keys())
    if missing_parents:
        raise ValueError(
            "mixed artifact decomposition missing parents: " + ", ".join(missing_parents)
        )
    extra_parents = sorted(by_parent.keys() - {a["artifact_id"] for a in artifacts})
    if extra_parents:
        raise ValueError(
            "mixed artifact decomposition references unknown parents: " + ", ".join(extra_parents)
        )
    return len(child_ids)


def validate_migration_outputs(matrix_path: Path, unresolved_path: Path) -> dict[str, Any]:
    matrix = _load(matrix_path)
    unresolved = _load(unresolved_path)

    _require_global_authority(matrix, "migration matrix")
    _require_global_authority(unresolved, "unresolved ledger")

    if matrix.get("audit_boundaries") != _EXPECTED_BOUNDARIES:
        raise ValueError("migration matrix audit boundaries changed or are incomplete")
    if unresolved.get("audit_boundaries") != _EXPECTED_BOUNDARIES:
        raise ValueError("unresolved ledger audit boundaries changed or are incomplete")

    artifacts = matrix.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("artifacts must be a non-empty list")
    items = unresolved.get("items")
    if not isinstance(items, list):
        raise ValueError("unresolved items must be a list")

    artifact_ids: set[str] = set()
    for idx, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ValueError(f"artifact {idx} is not an object")
        missing = sorted(_REQUIRED_ARTIFACT_FIELDS - artifact.keys())
        if missing:
            raise ValueError(f"artifact {idx} missing required fields: {', '.join(missing)}")
        artifact_id = artifact["artifact_id"]
        if artifact_id in artifact_ids:
            raise ValueError(f"duplicate artifact_id without decomposition: {artifact_id}")
        artifact_ids.add(artifact_id)
        migration_class = artifact["migration_class"]
        if migration_class not in MIGRATION_CLASSES:
            raise ValueError(f"invalid migration_class for {artifact_id}: {migration_class}")
        _validate_exact_identity(artifact, f"artifact {artifact_id}")
        if artifact.get("authority_basis") == "PR_OR_BRANCH_NAME":
            raise ValueError(f"navigation metadata used as authority for {artifact_id}")
        if migration_class == "SUPERSEDED_PARALLEL_IMPLEMENTATION":
            if artifact["continue_stop_or_redirect"] != "STOP_AND_FREEZE":
                raise ValueError(f"parallel implementation still active: {artifact_id}")
            if artifact["current_authority"] not in {
                "NONE__HISTORICAL_EVIDENCE_ONLY",
                "SUPERSEDED__NO_NEW_SCIENTIFIC_AUTHORITY",
            }:
                raise ValueError(f"ambiguous authority for superseded implementation: {artifact_id}")
        if migration_class == "CLOSED_FAILED_EXPERIMENT":
            if not str(artifact["current_authority"]).startswith("NONE"):
                raise ValueError(f"failed experiment promoted: {artifact_id}")
            if artifact["requires_requalification"] is not True:
                raise ValueError(f"failed experiment missing prospective requalification requirement: {artifact_id}")
        if migration_class in {
            "REUSABLE_SHARED_INFRASTRUCTURE",
            "KNOWN_TRUTH_SUBSTRATE",
            "KNOWN_TRUTH_CHALLENGE_ASSET",
            "HISTORICAL_NEGATIVE_CONTROL",
        }:
            if not artifact["destination_in_unified_architecture"]:
                raise ValueError(f"reusable work discarded without destination: {artifact_id}")
            if artifact["historical_evidence_retained"] is not True:
                raise ValueError(f"historical evidence not retained: {artifact_id}")
        if artifact.get("mixed_historical_object") and not artifact.get("decomposition_note"):
            raise ValueError(f"mixed artifact lacks decomposition note: {artifact_id}")

    decomposition_child_count = _validate_decompositions(matrix_path, artifacts)

    unresolved_ids: set[str] = set()
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"unresolved item {idx} is not an object")
        missing = sorted(_REQUIRED_UNRESOLVED_FIELDS - item.keys())
        if missing:
            raise ValueError(f"unresolved item {idx} missing fields: {', '.join(missing)}")
        item_id = item["item_id"]
        if item_id in unresolved_ids:
            raise ValueError(f"duplicate unresolved item: {item_id}")
        unresolved_ids.add(item_id)

    for artifact in artifacts:
        missing_ids = sorted(set(artifact.get("unresolved_item_ids", [])) - unresolved_ids)
        if missing_ids:
            raise ValueError(
                f"unresolved work disappeared for {artifact['artifact_id']}: {', '.join(missing_ids)}"
            )

    required_lessons = set(matrix.get("required_scientific_lessons", []))
    expected_lessons = {
        "MEASURED_ZERO_NE_UNSUPPORTED",
        "UNSUPPORTED_NE_UNRESOLVED",
        "UNRESOLVED_NE_NUMERICAL_FAILURE",
        "NUMERICAL_FAILURE_NE_BIOLOGICAL_FAIL",
        "SUPPORT_CANNOT_BE_MANUFACTURED",
        "SOURCE_FAILURES_CANNOT_BE_AVERAGED_AWAY",
        "COUNTS_AND_NORMALIZATION_LIBRARY_THIN_TOGETHER",
        "EVIDENCE_ACQUISITION_NE_MEASUREMENT_DEPTH",
        "SYNTHETIC_KNOWN_TRUTH_NE_HUMAN_BIOLOGICAL_TRUTH",
        "STABLE_SUBSPACE_NE_STABLE_AXES",
        "TARGET_NONE_IS_LAWFUL",
        "FALSE_CERTAINTY_AND_FALSE_ABSTENTION_BOTH_FAIL_QUALIFICATION",
        "READER_FIT_HELDOUT_MEANS_DETERMINISTIC_CROSSFIT",
        "READER_VALIDATION_AND_ORACLE_PROTECTED",
    }
    if not expected_lessons.issubset(required_lessons):
        raise ValueError("required scientific lessons are incomplete")

    return {
        "status": "PASS_TASK0_PREMERGER_MIGRATION_CUSTODY_VALIDATION",
        "artifact_count": len(artifacts),
        "decomposition_child_count": decomposition_child_count,
        "unresolved_count": len(items),
        "global_authority": GLOBAL_AUTHORITY,
    }
