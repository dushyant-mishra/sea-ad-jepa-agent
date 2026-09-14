from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping, Sequence

from .artifact_binding_v1 import seal_artifact, validate_artifact


class MeasurementQualificationStop(RuntimeError):
    pass


FROZEN_REQUIREMENTS_SHA256 = "1eb3f09d04d38b6bdddbad6b83f17d933e29c09e4d6a70c975908fa23ad5d30f"
EXPECTED_FULL104_ARTIFACT_SHA256 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
MEASUREMENT_QUALIFICATION_ARTIFACT_SCHEMA = "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_ARTIFACT_V1"
_EXPECTED_REQUIREMENTS_SCHEMA = "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_REQUIREMENTS_V1"
_EXPECTED_REQUIREMENTS_STATUS = "FROZEN_REQUIREMENTS__NUMERIC_CONTROL_PLAN_PENDING_OUTCOME_BLIND_RECONNAISSANCE"
_EXPECTED_AUTHORITY_SCHEMA = "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_AUTHORITY_V1"
_EXPECTED_AUTHORITY_STATUS = "FROZEN_BEFORE_CONTROL_EXECUTION_AND_D_SHARED_OUTCOME_ACCESS"
_REQUIRED_FAILURE_POLICY = "UNCONDITIONAL__FAILURES_NONQUALIFYING_AND_REPORTED_SEPARATELY"
_REQUIRED_INFLUENCE = ["donor_leverage", "top_k_concentration", "leave_one_donor_sensitivity"]
_REQUIRED_NUISANCE = "EXPLICIT_NUISANCE_OR_SIMPLER_COMPARATOR_MATCHED_TO_EVALUATION_POPULATION"
_SCIENTIFIC_STOPPING_RULE = {
    "rank_envelope": [1, 512],
    "qualified_negative_terminal": "D_SHARED_0__CURRENT_SHARED_STATE_HYPOTHESIS_NOT_QUALIFIED",
    "forbidden_after_real_outcome_access": [
        "threshold_relaxation",
        "alternate_null",
        "new_matching_bins",
        "rank_expansion",
        "post_outcome_replication_tuning",
        "same_run_redesign",
    ],
}
_REQUIRED_AUTHORITY_FIELDS = [
    "schema",
    "status",
    "full104_dimension_input_artifact_sha256",
    "feature_lineage_artifact_sha256",
    "reconnaissance_artifact_sha256",
    "negative_control_generator_sha256",
    "positive_control_generator_sha256",
    "difficulty_curve_signal_strengths",
    "control_replicates",
    "negative_control_max_false_qualification_rate",
    "positive_control_min_recovery_rate",
    "difficulty_curve_detection_definition",
    "failure_population_policy",
    "influence_diagnostics",
    "nuisance_comparator",
    "scientific_stopping_rule",
    "post_outcome_tuning_forbidden",
    "d_shared_outcomes_used",
    "protected_data_used",
    "pathology_used",
    "checkpoint_outcomes_used",
    "training_authorized",
]


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    if not isinstance(value, Mapping):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_QUALIFICATION_NOT_MAPPING")
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha64(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_QUALIFICATION_BAD_SHA:{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_QUALIFICATION_BAD_SHA:{field}") from exc
    return value.lower()


def _probability(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_QUALIFICATION_BAD_PROBABILITY:{field}")
    out = float(value)
    if not math.isfinite(out) or out < 0.0 or out > 1.0:
        raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_QUALIFICATION_BAD_PROBABILITY:{field}")
    return out


def validate_measurement_qualification_requirements_v1(requirements: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(requirements, Mapping):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_NOT_MAPPING")
    digest = hashlib.sha256(_canonical_bytes(requirements)).hexdigest()
    if digest != FROZEN_REQUIREMENTS_SHA256:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_BYTES_MISMATCH")
    if requirements.get("schema") != _EXPECTED_REQUIREMENTS_SCHEMA:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_SCHEMA")
    if requirements.get("status") != _EXPECTED_REQUIREMENTS_STATUS:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_STATUS")
    if requirements.get("governing_rule") != "UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED":
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_GOVERNING_RULE")
    if requirements.get("prospective_authority_required_fields") != _REQUIRED_AUTHORITY_FIELDS:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_FIELDS")
    families = requirements.get("required_control_families")
    if not isinstance(families, Mapping):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_CONTROL_FAMILIES")
    negative = families.get("negative")
    positive = families.get("positive")
    difficulty = families.get("difficulty_curve")
    if not isinstance(negative, Mapping) or negative.get("geometry") != "REAL_FULL104_GEOMETRY_PRESERVED" or negative.get("break_only") != "SHARED_RELATIONSHIP_UNDER_TEST" or negative.get("toy_independent_gaussian_authority_allowed") is not False or negative.get("full_d_shared_procedure_required") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_NEGATIVE_CONTROL")
    if not isinstance(positive, Mapping) or positive.get("geometry") != "REAL_FULL104_GEOMETRY_PRESERVED" or positive.get("signal") != "CONTROLLED_SHARED_SIGNAL_IMPLANT" or positive.get("protected_or_pathology_outcomes_allowed") is not False or positive.get("full_d_shared_procedure_required") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_POSITIVE_CONTROL")
    if not isinstance(difficulty, Mapping) or difficulty.get("prospectively_fixed_signal_strengths_required") is not True or difficulty.get("minimum_distinct_nonzero_strengths") != 3 or difficulty.get("same_geometry_and_procedure_required") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_DIFFICULTY_CURVE")
    if requirements.get("required_failure_population_policy") != _REQUIRED_FAILURE_POLICY:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_FAILURE_POLICY")
    if requirements.get("required_influence_diagnostics") != _REQUIRED_INFLUENCE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_INFLUENCE")
    if requirements.get("required_nuisance_comparator") != _REQUIRED_NUISANCE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_NUISANCE")
    if requirements.get("scientific_stopping_rule") != _SCIENTIFIC_STOPPING_RULE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_STOPPING_RULE")
    if requirements.get("numeric_control_plan_frozen") is not False:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_NUMERIC_PLAN_PREMATURE")
    if requirements.get("d_shared_real_outcome_access_authorized") is not False or requirements.get("training_authorized") is not False:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_REQUIREMENTS_AUTHORITY_ESCALATION")
    return {
        "passed": True,
        "terminal": "PASS_D_SHARED_MEASUREMENT_QUALIFICATION_REQUIREMENTS_V1",
        "requirements_sha256": FROZEN_REQUIREMENTS_SHA256,
        "numeric_control_plan_frozen": False,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
        "scientific_stopping_rule": dict(_SCIENTIFIC_STOPPING_RULE),
    }


def measurement_qualification_authority_sha256(authority: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes(authority)).hexdigest()


def validate_prospective_measurement_qualification_authority_v1(
    authority: Mapping[str, object], requirements: Mapping[str, object]
) -> dict[str, object]:
    validate_measurement_qualification_requirements_v1(requirements)
    if not isinstance(authority, Mapping):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_NOT_MAPPING")
    missing = [field for field in _REQUIRED_AUTHORITY_FIELDS if field not in authority]
    if missing:
        raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_AUTHORITY_MISSING:{','.join(missing)}")
    if authority.get("schema") != _EXPECTED_AUTHORITY_SCHEMA or authority.get("status") != _EXPECTED_AUTHORITY_STATUS:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_SCHEMA_OR_STATUS")
    if authority.get("full104_dimension_input_artifact_sha256") != EXPECTED_FULL104_ARTIFACT_SHA256:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_FULL104_PARENT")
    feature_sha = _sha64(authority.get("feature_lineage_artifact_sha256"), "feature_lineage_artifact_sha256")
    reconnaissance_sha = _sha64(authority.get("reconnaissance_artifact_sha256"), "reconnaissance_artifact_sha256")
    _sha64(authority.get("negative_control_generator_sha256"), "negative_control_generator_sha256")
    _sha64(authority.get("positive_control_generator_sha256"), "positive_control_generator_sha256")
    if authority.get("control_geometry") != "REAL_FULL104_GEOMETRY_PRESERVED" or authority.get("toy_independent_gaussian_authority") is not False:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_REAL_GEOMETRY_REQUIRED")
    strengths = authority.get("difficulty_curve_signal_strengths")
    if not isinstance(strengths, Sequence) or isinstance(strengths, (str, bytes)):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_DIFFICULTY_STRENGTHS")
    normalized_strengths: list[float] = []
    for value in strengths:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
            raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_DIFFICULTY_STRENGTHS")
        normalized_strengths.append(float(value))
    if len(set(normalized_strengths)) < 3 or normalized_strengths != sorted(normalized_strengths):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_DIFFICULTY_STRENGTHS")
    replicates = authority.get("control_replicates")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates <= 0:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_CONTROL_REPLICATES")
    _probability(authority.get("negative_control_max_false_qualification_rate"), "negative_control_max_false_qualification_rate")
    _probability(authority.get("positive_control_min_recovery_rate"), "positive_control_min_recovery_rate")
    if not isinstance(authority.get("difficulty_curve_detection_definition"), str) or not authority.get("difficulty_curve_detection_definition"):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_DIFFICULTY_DEFINITION")
    if authority.get("failure_population_policy") != _REQUIRED_FAILURE_POLICY:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_FAILURE_POLICY")
    if authority.get("influence_diagnostics") != _REQUIRED_INFLUENCE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_INFLUENCE")
    if authority.get("nuisance_comparator") != _REQUIRED_NUISANCE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_NUISANCE")
    if authority.get("scientific_stopping_rule") != _SCIENTIFIC_STOPPING_RULE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_STOPPING_RULE")
    if authority.get("numeric_control_plan_frozen") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_NUMERIC_PLAN_NOT_FROZEN")
    if authority.get("post_outcome_tuning_forbidden") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_AUTHORITY_POST_OUTCOME_TUNING")
    for field in ("d_shared_outcomes_used", "protected_data_used", "pathology_used", "checkpoint_outcomes_used", "training_authorized"):
        if authority.get(field) is not False:
            raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_AUTHORITY_FORBIDDEN:{field}")
    return {
        "passed": True,
        "terminal": "PASS_D_SHARED_PROSPECTIVE_MEASUREMENT_QUALIFICATION_AUTHORITY_V1",
        "measurement_qualification_authority_sha256": measurement_qualification_authority_sha256(authority),
        "feature_lineage_artifact_sha256": feature_sha,
        "reconnaissance_artifact_sha256": reconnaissance_sha,
        "numeric_control_plan_frozen": True,
        "d_shared_real_outcome_access_authorized": False,
        "training_authorized": False,
    }


def _parents(authority: Mapping[str, object]) -> dict[str, str]:
    return {
        "measurement_qualification_requirements_sha256": FROZEN_REQUIREMENTS_SHA256,
        "measurement_qualification_authority_sha256": measurement_qualification_authority_sha256(authority),
        "full104_dimension_input_artifact_sha256": EXPECTED_FULL104_ARTIFACT_SHA256,
        "feature_lineage_artifact_sha256": _sha64(authority.get("feature_lineage_artifact_sha256"), "feature_lineage_artifact_sha256"),
        "reconnaissance_artifact_sha256": _sha64(authority.get("reconnaissance_artifact_sha256"), "reconnaissance_artifact_sha256"),
    }


def _validate_receipt_payload(authority: Mapping[str, object], receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping) or receipt.get("schema") != "JEPA_V5_D_SHARED_MEASUREMENT_QUALIFICATION_RECEIPT_V1":
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_RECEIPT_SCHEMA")
    authority_sha = measurement_qualification_authority_sha256(authority)
    if receipt.get("measurement_qualification_authority_sha256") != authority_sha:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_RECEIPT_AUTHORITY_PARENT")
    negative_rate = _probability(receipt.get("negative_control_false_qualification_rate"), "negative_control_false_qualification_rate")
    positive_rate = _probability(receipt.get("positive_control_recovery_rate"), "positive_control_recovery_rate")
    if negative_rate > float(authority["negative_control_max_false_qualification_rate"]):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_NEGATIVE_CONTROL_FAILED")
    if positive_rate < float(authority["positive_control_min_recovery_rate"]):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_POSITIVE_CONTROL_FAILED")
    curve = receipt.get("difficulty_curve")
    expected_strengths = [float(x) for x in authority["difficulty_curve_signal_strengths"]]
    if not isinstance(curve, Sequence) or isinstance(curve, (str, bytes)) or len(curve) != len(expected_strengths):
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_DIFFICULTY_CURVE_MISMATCH")
    seen_strengths: list[float] = []
    for row in curve:
        if not isinstance(row, Mapping):
            raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_DIFFICULTY_CURVE_MISMATCH")
        value = row.get("signal_strength")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_DIFFICULTY_CURVE_MISMATCH")
        seen_strengths.append(float(value))
        _probability(row.get("recovery_rate"), "difficulty_curve.recovery_rate")
    if seen_strengths != expected_strengths:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_DIFFICULTY_CURVE_MISMATCH")
    if receipt.get("unconditional_failure_accounting") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_UNCONDITIONAL_FAILURE_ACCOUNTING_REQUIRED")
    if receipt.get("survivor_only_metrics_used") is not False:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_SURVIVOR_ONLY_FORBIDDEN")
    if receipt.get("influence_diagnostics_emitted") != _REQUIRED_INFLUENCE:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_INFLUENCE_NOT_EMITTED")
    if receipt.get("nuisance_comparator_emitted") is not True:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_NUISANCE_NOT_EMITTED")
    for field in ("post_outcome_tuning_used", "d_shared_unknown_outcomes_inspected", "protected_data_used", "pathology_used", "checkpoint_outcomes_used", "training_authorized"):
        if receipt.get(field) is not False:
            raise MeasurementQualificationStop(f"STOP_D_SHARED_MEASUREMENT_RECEIPT_FORBIDDEN:{field}")
    if receipt.get("terminal") != "PASS_D_SHARED_MEASUREMENT_PROCEDURE_QUALIFICATION_V1":
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_RECEIPT_TERMINAL")
    out = dict(receipt)
    out["d_shared_real_outcome_access_authorized"] = False
    out["training_authorized"] = False
    return out


def seal_measurement_qualification_receipt_v1(
    authority: Mapping[str, object], requirements: Mapping[str, object], receipt: Mapping[str, object]
) -> dict[str, object]:
    validate_prospective_measurement_qualification_authority_v1(authority, requirements)
    payload = _validate_receipt_payload(authority, receipt)
    return seal_artifact(MEASUREMENT_QUALIFICATION_ARTIFACT_SCHEMA, payload, _parents(authority))


def validate_measurement_qualification_receipt_v1(
    authority: Mapping[str, object], requirements: Mapping[str, object], envelope: Mapping[str, object]
) -> dict[str, object]:
    validate_prospective_measurement_qualification_authority_v1(authority, requirements)
    try:
        payload = validate_artifact(
            envelope,
            expected_schema=MEASUREMENT_QUALIFICATION_ARTIFACT_SCHEMA,
            expected_parents=_parents(authority),
        )
    except (ValueError, RuntimeError) as exc:
        raise MeasurementQualificationStop("STOP_D_SHARED_MEASUREMENT_ARTIFACT_INVALID") from exc
    return _validate_receipt_payload(authority, payload)


def enforce_d_shared_scientific_stopping_rule_v1(
    requirements: Mapping[str, object], adjudication: Mapping[str, object]
) -> dict[str, object]:
    validate_measurement_qualification_requirements_v1(requirements)
    if not isinstance(adjudication, Mapping):
        raise MeasurementQualificationStop("STOP_D_SHARED_SCIENTIFIC_TERMINAL_NOT_MAPPING")
    if adjudication.get("D_shared") != 0:
        raise MeasurementQualificationStop("STOP_D_SHARED_SCIENTIFIC_TERMINAL_NOT_NEGATIVE")
    if adjudication.get("terminal") != _SCIENTIFIC_STOPPING_RULE["qualified_negative_terminal"]:
        raise MeasurementQualificationStop("STOP_D_SHARED_SCIENTIFIC_TERMINAL_MISMATCH")
    return {
        "D_shared": 0,
        "terminal": _SCIENTIFIC_STOPPING_RULE["qualified_negative_terminal"],
        "rank_expansion_authorized": False,
        "threshold_relaxation_authorized": False,
        "alternate_null_authorized": False,
        "new_matching_bins_authorized": False,
        "post_outcome_replication_tuning_authorized": False,
        "same_run_redesign_authorized": False,
        "training_authorized": False,
    }
