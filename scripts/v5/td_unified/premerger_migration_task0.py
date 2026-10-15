from __future__ import annotations

import json
import re
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
        "HISTORICAL_BIOLOGICAL_EVIDENCE",
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

_REQUIRED_MACHA_ARTIFACT_FIELDS = {
    "artifact_id",
    "artifact_path",
    "source_commit",
    "artifact_digest",
    "exact_identity_available",
    "migration_class",
    "current_authority",
    "scientific_role",
    "historical_evidence_retained",
    "requires_requalification",
    "requalification_reason",
    "destination_in_unified_architecture",
    "authority_basis",
    "continue_stop_or_redirect",
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
_MACHA_STREAMS_FILENAME = "PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"
_REQUIRED_MACHA_STREAMS = {
    "MACHA_REAL_TD_CORRECTED_REPLAY": {
        "MACHA_PR314_CORRECTED_REPLAY",
        "MACHA_PR316_FINE_RARE_SUCCESSOR",
        "MACHA_REAL_DATA_AUDIT",
        "MACHA_REPAIR_LINEAGE_364_369",
    },
    "MACHA_V79_BAYESIAN_KNOWN_TRUTH": {
        "MACHA_PR261_V79_BAYESIAN_HANDOFF",
        "MACHA_V79_Q00_Q11_REALIZATION_CUSTODY",
        "MACHA_V79_TERMINAL_NOT_QUALIFIED",
        "MACHA_V80_BENCHMARK_PACKAGE",
    },
}


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
        commit = record.get("source_commit")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise ValueError(f"available exact identity has invalid source_commit for {label}")
        digest = record.get("artifact_digest")
        blob = record.get("artifact_blob_sha")
        digest_ok = isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        blob_ok = isinstance(blob, str) and re.fullmatch(r"[0-9a-f]{40}", blob) is not None and bool(record.get("artifact_path"))
        if not (digest_ok or blob_ok):
            raise ValueError(f"available exact payload identity omitted for {label}")
        if not record.get("byte_custody"):
            raise ValueError(f"available exact identity missing byte_custody for {label}")
    else:
        if not record.get("identity_unavailable_reason"):
            raise ValueError(f"unavailable exact identity missing reason for {label}")
        authority = str(record.get("current_authority", ""))
        if authority.startswith("AUTHENTICATED_CALIBRATION"):
            raise ValueError(f"authority-bearing identity cannot be unavailable for {label}")


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


def _validate_macha_streams(matrix_path: Path, unresolved_ids: set[str]) -> int:
    streams_path = matrix_path.with_name(_MACHA_STREAMS_FILENAME)
    try:
        payload = _load(streams_path)
    except ValueError as exc:
        raise ValueError("Macha dual-stream custody registry missing") from exc
    _require_global_authority(payload, "Macha dual-stream custody registry")

    streams = payload.get("streams")
    if not isinstance(streams, list) or len(streams) != 2:
        raise ValueError("Macha dual-stream custody registry must contain exactly two streams")
    by_id: dict[str, dict[str, Any]] = {}
    artifact_ids: set[str] = set()
    for idx, stream in enumerate(streams):
        if not isinstance(stream, dict):
            raise ValueError(f"Macha stream {idx} is not an object")
        stream_id = stream.get("stream_id")
        if not stream_id or stream_id in by_id:
            raise ValueError(f"invalid or duplicate Macha stream id: {stream_id}")
        if stream.get("historical_scientific_custodian") != "Macha":
            raise ValueError(f"Macha historical-custodian role missing for {stream_id}")
        if not stream.get("unified_destination") or not stream.get("review_obligations"):
            raise ValueError(f"Macha stream destination/review obligations missing for {stream_id}")
        missing_unresolved = sorted(set(stream.get("unresolved_item_ids", [])) - unresolved_ids)
        if missing_unresolved:
            raise ValueError(
                f"Macha stream unresolved work disappeared for {stream_id}: {', '.join(missing_unresolved)}"
            )
        artifacts = stream.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"Macha stream artifacts missing for {stream_id}")
        for artifact_idx, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                raise ValueError(f"Macha stream artifact {stream_id}[{artifact_idx}] is not an object")
            missing = sorted(_REQUIRED_MACHA_ARTIFACT_FIELDS - artifact.keys())
            if missing:
                raise ValueError(
                    f"Macha stream artifact {stream_id}[{artifact_idx}] missing fields: {', '.join(missing)}"
                )
            artifact_id = artifact["artifact_id"]
            if artifact_id in artifact_ids:
                raise ValueError(f"duplicate Macha stream artifact id: {artifact_id}")
            artifact_ids.add(artifact_id)
            if artifact["migration_class"] not in MIGRATION_CLASSES:
                raise ValueError(f"invalid Macha migration_class for {artifact_id}")
            if not artifact["destination_in_unified_architecture"]:
                raise ValueError(f"Macha artifact destination missing for {artifact_id}")
            if artifact["historical_evidence_retained"] is not True:
                raise ValueError(f"Macha historical evidence dropped for {artifact_id}")
            if artifact["current_authority"] == "CURRENT_UNIFIED_SCIENTIFIC_AUTHORITY":
                raise ValueError(f"Macha historical artifact silently promoted: {artifact_id}")
            _validate_exact_identity(artifact, f"Macha stream artifact {artifact_id}")
            if artifact.get("authority_basis") == "PR_OR_BRANCH_NAME":
                raise ValueError(f"navigation metadata used as Macha artifact authority: {artifact_id}")
            if artifact["migration_class"] == "CLOSED_FAILED_EXPERIMENT":
                if not str(artifact["current_authority"]).startswith("NONE"):
                    raise ValueError(f"Macha failed experiment promoted: {artifact_id}")
                if artifact["requires_requalification"] is not True:
                    raise ValueError(f"Macha failed experiment missing requalification: {artifact_id}")
        by_id[stream_id] = stream

    if set(by_id) != set(_REQUIRED_MACHA_STREAMS):
        raise ValueError("Macha custody streams are incomplete or renamed")
    for stream_id, required_ids in _REQUIRED_MACHA_STREAMS.items():
        observed = {a["artifact_id"] for a in by_id[stream_id]["artifacts"]}
        missing = sorted(required_ids - observed)
        if missing:
            raise ValueError(f"Macha stream {stream_id} missing required artifacts: {', '.join(missing)}")
    return len(artifact_ids)


def _validate_b1_b5_repair_guards(matrix_path: Path, unresolved_ids: set[str], artifacts: list[dict[str, Any]]) -> None:
    by_artifact = {a["artifact_id"]: a for a in artifacts}
    decomp = _load(matrix_path.with_name("PREMERGER_MIXED_ARTIFACT_DECOMPOSITION_V1.json"))
    pr356 = next((x for x in decomp.get("decompositions", []) if x.get("parent_artifact_id") == "PR356_SYNTH_PLAN"), None)
    if pr356 is None:
        raise ValueError("B1 PR356 decomposition missing")
    children = {x["child_artifact_id"]: x for x in pr356.get("children", [])}
    required_children = {"OLD_TASK1_IMPLEMENTATION", "OLD_TASK2_IMPLEMENTATION", "OLD_TASK3_REQUIREMENTS", "OLD_TASK4_REQUIREMENTS", "OLD_TASKS5_12"}
    if set(children) != required_children:
        raise ValueError("B1 PR356 decomposition does not match merged stop law")
    old_head = "ff597faf2182522a320ec5322f8db9b67c9c6094"
    if children["OLD_TASK1_IMPLEMENTATION"].get("source_commit") != old_head or children["OLD_TASK2_IMPLEMENTATION"].get("source_commit") != old_head:
        raise ValueError("B1 old Tasks1-2 exact implementation head not bound")
    if children["OLD_TASK4_REQUIREMENTS"].get("continue_stop_or_redirect") != "REDIRECT":
        raise ValueError("B1 old Task4 requirements were dropped instead of migrated")

    streams = _load(matrix_path.with_name("PREMERGER_MACHA_DUAL_STREAM_CUSTODY_V1.json"))
    stream_rows = {a["artifact_id"]: a for s in streams.get("streams", []) for a in s.get("artifacts", [])}
    for artifact_id in set(by_artifact) & set(stream_rows):
        if by_artifact[artifact_id].get("current_authority") != stream_rows[artifact_id].get("current_authority"):
            raise ValueError(f"B3 conflicting authority across Task0 surfaces for {artifact_id}")
    audit = by_artifact.get("MACHA_REAL_DATA_AUDIT", {})
    for fact in audit.get("protected_partition_facts", []):
        if fact.get("use_class") != "PROSPECTIVE_CONVENTION_STRESS_ONLY" or fact.get("calibration_authorized") is not False:
            raise ValueError("B3 protected-partition fact routed into calibration")

    required_unresolved = {*(f"U_TASK2_REUSE_O{i}" for i in range(1, 9)), "U_TASK2_REUSE_D1_EXCEPTION_WRAPPING", "U_TASK2_E2_PRECOMMITMENT_ERRATUM", "U_TASK2_POST_REVEAL_FRESH_FAMILY", "U_TASK3_READER_FIT_CALIBRATION_STATUS"}
    missing = sorted(required_unresolved - unresolved_ids)
    if missing:
        raise ValueError("B4 Task1-2 reuse obligations missing: " + ", ".join(missing))

    taxonomy = _load(matrix_path.with_name("TASK0_MIGRATION_TAXONOMY_V1.json"))
    if set(taxonomy.get("allowed_migration_classes", [])) != set(MIGRATION_CLASSES):
        raise ValueError("B5 taxonomy does not match validator enum")
    if taxonomy.get("controlling_plan_amendment_head") != "5b6bf07e7d8b69b286ea430b09765a5ee4743325":
        raise ValueError("B5 controlling taxonomy amendment head mismatch")
    if taxonomy.get("controlling_plan_amendment_blob_sha") != "7f20050c2a8d0f80f0c6418c007bc12f7fc1083f":
        raise ValueError("B5 controlling taxonomy amendment blob mismatch")
    if taxonomy.get("historical_biological_evidence_authority") != "RETROSPECTIVELY_RATIFIED_20261014":
        raise ValueError("B5 taxonomy chronology not truthfully classified")


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
            "HISTORICAL_BIOLOGICAL_EVIDENCE",
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

    macha_stream_artifact_count = _validate_macha_streams(matrix_path, unresolved_ids)
    _validate_b1_b5_repair_guards(matrix_path, unresolved_ids, artifacts)

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
        "macha_stream_artifact_count": macha_stream_artifact_count,
        "unresolved_count": len(items),
        "global_authority": GLOBAL_AUTHORITY,
    }
