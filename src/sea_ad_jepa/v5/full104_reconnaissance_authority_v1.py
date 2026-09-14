from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from .artifact_binding_v1 import seal_artifact, validate_artifact


class Full104ReconnaissanceStop(RuntimeError):
    pass


FROZEN_RECONNAISSANCE_AUTHORITY_SHA256 = "e7b207fd15cbe62f6f4534311a2772be3325dc5170d7ffd3d5ffc75f36c7158b"
FULL104_RECONNAISSANCE_ARTIFACT_SCHEMA = "JEPA_V5_FULL104_RECONNAISSANCE_ARTIFACT_V1"
EXPECTED_FULL104_ARTIFACT_SHA256 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
_EXPECTED_GEOMETRY = {"cells": 4_553_407, "donors": 104, "operators": 42, "addresses": 41_238}
_ALLOWED_DIAGNOSTICS = (
    "donor_operator_source_study_technology_counts",
    "depth_detection_distributions",
    "sparsity_zero_support_missingness",
    "feature_variance_covariance_conditioning",
    "effective_rank_redundancy",
    "view_overlap_redundancy",
    "donor_heterogeneity_leverage",
    "technical_variable_correlations",
    "cell_state_support_across_donors",
    "matched_null_stratum_size_singleton_rates",
    "matching_state_discreteness",
    "operator_source_dataset_variance_dominance",
    "control_estimability",
    "io_memory_parallelization_mechanics",
)
_FORBIDDEN_DECISION_FIELDS = (
    "shared_matched_null_exceedance",
    "shared_subspace_stability",
    "shared_held_donor_cross_view_predictability",
    "shared_independent_view_agreement",
    "shared_measurement_shortcut_increment",
    "D_shared",
    "rank",
    "selected_rank",
    "rank_selection",
    "jointly_supported",
    "held_donor_cross_view_mean",
    "held_donor_cross_view_se",
    "one_se_threshold",
    "pass",
    "passed",
)
_REQUIRED_FALSE = (
    "d_shared_outcomes_inspected",
    "rank_selection_inspected",
    "decision_bearing_effects_inspected",
    "pathology_used",
    "protected_data_used",
    "checkpoint_outcomes_used",
    "training_authorized",
)


def canonical_reconnaissance_authority_bytes(authority: Mapping[str, object]) -> bytes:
    if not isinstance(authority, Mapping):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_NOT_MAPPING")
    return (json.dumps(authority, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise Full104ReconnaissanceStop(f"STOP_FULL104_RECONNAISSANCE_BAD_SHA:{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise Full104ReconnaissanceStop(f"STOP_FULL104_RECONNAISSANCE_BAD_SHA:{field}") from exc
    return value.lower()


def validate_full104_reconnaissance_authority_v1(authority: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(authority, Mapping):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_NOT_MAPPING")
    if hashlib.sha256(canonical_reconnaissance_authority_bytes(authority)).hexdigest() != FROZEN_RECONNAISSANCE_AUTHORITY_SHA256:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_BYTES_MISMATCH")
    if authority.get("schema") != "JEPA_V5_FULL104_RECONNAISSANCE_AUTHORITY_V1":
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_SCHEMA")
    if authority.get("status") != "FROZEN_BEFORE_D_SHARED_OUTCOME_ACCESS":
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_STATUS")
    if authority.get("full104_dimension_input_artifact_sha256") != EXPECTED_FULL104_ARTIFACT_SHA256:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_FULL104_PARENT")
    if authority.get("expected_geometry") != _EXPECTED_GEOMETRY:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_GEOMETRY")
    if authority.get("allowed_diagnostics") != list(_ALLOWED_DIAGNOSTICS):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_DIAGNOSTIC_ALLOWLIST")
    if authority.get("forbidden_decision_fields") != list(_FORBIDDEN_DECISION_FIELDS):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_FORBIDDEN_FIELD_SET")
    required_flags = authority.get("required_outcome_blind_flags")
    if not isinstance(required_flags, Mapping) or set(required_flags) != set(_REQUIRED_FALSE) or any(required_flags.get(k) is not False for k in _REQUIRED_FALSE):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_OUTCOME_BLIND_POLICY")
    if authority.get("receipt_terminal") != "PASS_FULL104_OUTCOME_BLIND_RECONNAISSANCE_V1":
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_TERMINAL_POLICY")
    if authority.get("d_shared_real_outcome_access_authorized") is not False or authority.get("training_authorized") is not False:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_ESCALATION")
    return {
        "passed": True,
        "terminal": "PASS_V5_FULL104_RECONNAISSANCE_AUTHORITY_V1",
        "allowed_diagnostics": list(_ALLOWED_DIAGNOSTICS),
        "forbidden_decision_fields": list(_FORBIDDEN_DECISION_FIELDS),
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
    }


def _validate_receipt_payload(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_RECEIPT_NOT_MAPPING")
    if receipt.get("schema") != "JEPA_V5_FULL104_RECONNAISSANCE_RECEIPT_V1":
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_RECEIPT_SCHEMA")
    if receipt.get("full104_dimension_input_artifact_sha256") != EXPECTED_FULL104_ARTIFACT_SHA256:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_FULL104_PARENT")
    for field, expected in _EXPECTED_GEOMETRY.items():
        value = receipt.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise Full104ReconnaissanceStop(f"STOP_FULL104_RECONNAISSANCE_GEOMETRY:{field}")
    diagnostics = receipt.get("diagnostics_completed")
    if not isinstance(diagnostics, Sequence) or isinstance(diagnostics, (str, bytes)) or list(diagnostics) != list(_ALLOWED_DIAGNOSTICS):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_DIAGNOSTICS_INCOMPLETE")
    for field in _FORBIDDEN_DECISION_FIELDS:
        if field in receipt:
            raise Full104ReconnaissanceStop(f"STOP_FULL104_RECONNAISSANCE_DECISION_FIELD_PRESENT:{field}")
    for field in _REQUIRED_FALSE:
        if receipt.get(field) is not False:
            if field == "training_authorized":
                raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_ESCALATION")
            raise Full104ReconnaissanceStop(f"STOP_FULL104_RECONNAISSANCE_OUTCOME_ACCESS:{field}")
    if receipt.get("terminal") != "PASS_FULL104_OUTCOME_BLIND_RECONNAISSANCE_V1":
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_RECEIPT_TERMINAL")
    out = dict(receipt)
    out["reconnaissance_authority_sha256"] = FROZEN_RECONNAISSANCE_AUTHORITY_SHA256
    out["d_shared_real_outcome_access_authorized"] = False
    out["training_authorized"] = False
    return out


def seal_full104_reconnaissance_receipt_v1(authority: Mapping[str, object], receipt: Mapping[str, object]) -> dict[str, object]:
    validate_full104_reconnaissance_authority_v1(authority)
    payload = _validate_receipt_payload(receipt)
    return seal_artifact(
        FULL104_RECONNAISSANCE_ARTIFACT_SCHEMA,
        payload,
        {
            "full104_dimension_input_artifact_sha256": EXPECTED_FULL104_ARTIFACT_SHA256,
            "reconnaissance_authority_sha256": FROZEN_RECONNAISSANCE_AUTHORITY_SHA256,
        },
    )


def validate_full104_reconnaissance_receipt_v1(envelope: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(envelope, Mapping):
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_ENVELOPE_NOT_MAPPING")
    try:
        payload = validate_artifact(
            envelope,
            expected_schema=FULL104_RECONNAISSANCE_ARTIFACT_SCHEMA,
            expected_parents={
                "full104_dimension_input_artifact_sha256": EXPECTED_FULL104_ARTIFACT_SHA256,
                "reconnaissance_authority_sha256": FROZEN_RECONNAISSANCE_AUTHORITY_SHA256,
            },
        )
    except (ValueError, RuntimeError) as exc:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_ARTIFACT_INVALID") from exc
    if payload.get("reconnaissance_authority_sha256") != FROZEN_RECONNAISSANCE_AUTHORITY_SHA256:
        raise Full104ReconnaissanceStop("STOP_FULL104_RECONNAISSANCE_AUTHORITY_PARENT_MISMATCH")
    return _validate_receipt_payload(payload)
