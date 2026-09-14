from __future__ import annotations

from typing import Mapping

from .artifact_binding_v1 import seal_artifact, validate_artifact


class FeatureLineageStop(RuntimeError):
    pass


FULL104_FEATURE_LINEAGE_ARTIFACT_SCHEMA = "JEPA_V5_FULL104_FEATURE_LINEAGE_ARTIFACT_V1"
EXPECTED_FULL104_ARTIFACT_SHA256 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
HISTORICAL_FEATURE_MATRIX_ROOT_SHA256 = "c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef"
HISTORICAL_MULTIVIEW_ROOT_SHA256 = "d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1"
_EXPECTED_GEOMETRY = {"cells": 4_553_407, "donors": 104, "operators": 42, "addresses": 41_238}
_EXPECTED_SHAPES = {
    "A_full": [4_553_407, 512],
    "B_full": [4_553_407, 512],
    "A_views": [4_553_407, 4, 512],
    "B_views": [4_553_407, 4, 512],
}
_ALLOWED_CLASSIFICATIONS = {"CERTIFIABLE_EXACT_DERIVATION", "CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY"}
_FORBIDDEN_TRUE = (
    "filtering_applied",
    "cell_capping_applied",
    "sampling_applied",
    "pathology_used",
    "protected_data_used",
    "checkpoint_outcomes_used",
    "adaptive_outcome_choice_used",
    "d_shared_outcomes_inspected",
    "d_shared_real_outcome_access_authorized",
    "training_authorized",
)


def _sha64(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_BAD_SHA:{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_BAD_SHA:{field}") from exc
    return value.lower()


def _gitsha40(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_BAD_GIT_SHA:{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_BAD_GIT_SHA:{field}") from exc
    return value.lower()


def _validate_payload(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping):
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_NOT_MAPPING")
    if receipt.get("schema") != "JEPA_V5_FULL104_FEATURE_LINEAGE_RECEIPT_V1":
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_SCHEMA")

    classification = receipt.get("certification_classification")
    if classification == "NOT_CERTIFIABLE_REBUILD_FROM_AUTHENTICATED_FULL104_REQUIRED":
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_REBUILD_REQUIRED")
    if classification not in _ALLOWED_CLASSIFICATIONS:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_CERTIFICATION_CLASS")

    if receipt.get("full104_dimension_input_artifact_sha256") != EXPECTED_FULL104_ARTIFACT_SHA256:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_FULL104_PARENT")
    if receipt.get("source_feature_matrix_root_sha256") != HISTORICAL_FEATURE_MATRIX_ROOT_SHA256:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_SOURCE_ROOT:feature_matrix")
    if receipt.get("source_multiview_root_sha256") != HISTORICAL_MULTIVIEW_ROOT_SHA256:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_SOURCE_ROOT:multiview")

    certified_feature = _sha64(receipt.get("certified_feature_matrix_root_sha256"), "certified_feature_matrix_root_sha256")
    certified_multiview = _sha64(receipt.get("certified_multiview_root_sha256"), "certified_multiview_root_sha256")
    scripts = receipt.get("producer_script_sha256")
    if not isinstance(scripts, Mapping) or not scripts:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_PRODUCER_SCRIPTS")
    for path, digest in scripts.items():
        if not isinstance(path, str) or not path:
            raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_PRODUCER_SCRIPT_PATH")
        _sha64(digest, f"producer_script_sha256[{path}]")
    _gitsha40(receipt.get("producer_commit_sha256"), "producer_commit_sha256")
    transform_sha = _sha64(receipt.get("transformation_contract_sha256"), "transformation_contract_sha256")
    _sha64(receipt.get("row_identity_digest_sha256"), "row_identity_digest_sha256")
    _sha64(receipt.get("address_identity_digest_sha256"), "address_identity_digest_sha256")

    for field, expected in _EXPECTED_GEOMETRY.items():
        value = receipt.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_GEOMETRY:{field}")
    if receipt.get("shapes") != _EXPECTED_SHAPES:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_SHAPE_MISMATCH")

    if receipt.get("row_identity_closed") is not True or receipt.get("row_identity_mismatches") != 0 or receipt.get("row_identity_missing") != 0:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_ROW_IDENTITY")
    if receipt.get("address_identity_closed") is not True or receipt.get("address_identity_mismatches") != 0:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_ADDRESS_IDENTITY")
    if receipt.get("a_b_view_partition_disjoint") is not True or receipt.get("view_construction_reproduced") is not True:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_VIEW_CONSTRUCTION")

    for field in ("clipping_applied", "winsorization_applied", "imputation_applied"):
        if receipt.get(field) not in (True, False):
            raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_TRANSFORM_DISCLOSURE:{field}")
    for field in _FORBIDDEN_TRUE:
        if receipt.get(field) is not False:
            raise FeatureLineageStop(f"STOP_FULL104_FEATURE_LINEAGE_FORBIDDEN:{field}")
    if receipt.get("deterministic_reproduction_passed") is not True:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_DETERMINISTIC_REPRODUCTION")
    if receipt.get("semantic_transform_unchanged") is not True:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_SEMANTIC_TRANSFORM_CHANGED")

    repair_applied = receipt.get("mechanics_repair_applied")
    repair_sha = receipt.get("mechanics_repair_receipt_sha256")
    if classification == "CERTIFIABLE_EXACT_DERIVATION":
        if repair_applied is not False or repair_sha is not None:
            raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_EXACT_WITH_REPAIR")
        if certified_feature != HISTORICAL_FEATURE_MATRIX_ROOT_SHA256 or certified_multiview != HISTORICAL_MULTIVIEW_ROOT_SHA256:
            raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_EXACT_CERTIFIED_ROOT_MISMATCH")
    else:
        if repair_applied is not True:
            raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_REPAIR_NOT_APPLIED")
        try:
            _sha64(repair_sha, "mechanics_repair_receipt_sha256")
        except FeatureLineageStop as exc:
            raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_REPAIR_RECEIPT") from exc

    if receipt.get("terminal") != "PASS_FULL104_FEATURE_LINEAGE_V1":
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_TERMINAL")

    out = dict(receipt)
    out["certified_feature_matrix_root_sha256"] = certified_feature
    out["certified_multiview_root_sha256"] = certified_multiview
    out["transformation_contract_sha256"] = transform_sha
    out["d_shared_real_outcome_access_authorized"] = False
    out["training_authorized"] = False
    return out


def _parents(payload: Mapping[str, object]) -> dict[str, str]:
    return {
        "full104_dimension_input_artifact_sha256": EXPECTED_FULL104_ARTIFACT_SHA256,
        "source_feature_matrix_root_sha256": HISTORICAL_FEATURE_MATRIX_ROOT_SHA256,
        "source_multiview_root_sha256": HISTORICAL_MULTIVIEW_ROOT_SHA256,
        "certified_feature_matrix_root_sha256": _sha64(payload.get("certified_feature_matrix_root_sha256"), "certified_feature_matrix_root_sha256"),
        "certified_multiview_root_sha256": _sha64(payload.get("certified_multiview_root_sha256"), "certified_multiview_root_sha256"),
        "transformation_contract_sha256": _sha64(payload.get("transformation_contract_sha256"), "transformation_contract_sha256"),
    }


def seal_full104_feature_lineage_v1(receipt: Mapping[str, object]) -> dict[str, object]:
    payload = _validate_payload(receipt)
    return seal_artifact(FULL104_FEATURE_LINEAGE_ARTIFACT_SCHEMA, payload, _parents(payload))


def validate_full104_feature_lineage_v1(envelope: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(envelope, Mapping):
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_ENVELOPE_NOT_MAPPING")
    raw_payload = envelope.get("payload")
    if not isinstance(raw_payload, Mapping):
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_PAYLOAD_NOT_MAPPING")
    try:
        payload = validate_artifact(
            envelope,
            expected_schema=FULL104_FEATURE_LINEAGE_ARTIFACT_SCHEMA,
            expected_parents=_parents(raw_payload),
        )
    except (ValueError, RuntimeError) as exc:
        raise FeatureLineageStop("STOP_FULL104_FEATURE_LINEAGE_ARTIFACT_INVALID") from exc
    return _validate_payload(payload)
