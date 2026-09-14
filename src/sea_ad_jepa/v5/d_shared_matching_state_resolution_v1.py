from __future__ import annotations

from typing import Mapping, Sequence

from .artifact_binding_v1 import seal_artifact, validate_artifact


class MatchingStateResolutionStop(RuntimeError):
    pass


D_SHARED_MATCHING_STATE_RESOLUTION_ARTIFACT_SCHEMA = "JEPA_V5_D_SHARED_MATCHING_STATE_RESOLUTION_ARTIFACT_V1"
EXPECTED_FULL104_ARTIFACT_SHA256 = "eb1264489306413fb57316abe7f70205a771248881302d8c867c70b69273f1ad"
EXPECTED_D_SHARED_AUTHORITY_V2_SHA256 = "f9568eb19a22f106b0be3ce0580bc1058695ca1a2de6dd2d0475c3240a6bbda2"
_EXPECTED_SCHEMA = "JEPA_V5_D_SHARED_MATCHING_STATE_RESOLUTION_RECEIPT_V1"
_LOSSLESS_CLASSIFICATION = "LOSSLESS_DISCRETE_PREIMAGE_VERIFIED"
_CONTINUOUS_CLASSIFICATION = "CONTINUOUS_STATE_REQUIRES_V3_NULL"
_EXPECTED_TERMINAL = "PASS_D_SHARED_MATCHING_STATE_LOSSLESS_PREIMAGE_V1"
_CONTINUOUS_STOP = "STOP_D_SHARED_CONTINUOUS_MATCHING_STATE_REQUIRES_V3_NULL"
_EXPECTED_MATCHING_TUPLE = ["donor", "operator", "Q_DEPTH_COUNT", "Q_DETECT_COUNT"]
_EXPECTED_Q_DEPTH_SEMANTICS = "log1p(source_library)"
_EXPECTED_Q_DEPTH_STATE = "Q_DEPTH_COUNT=round(expm1(Q_DEPTH))"
_EXPECTED_Q_DETECT_SEMANTICS = "nonzero/max(scalar_support_count,1)"
_EXPECTED_Q_DETECT_STATE = "Q_DETECT_COUNT=round(Q_DETECT*max(SCALAR_SUPPORT_COUNT,1))"
_EXPECTED_CELLS = 4_553_407


def _sha64(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_BAD_SHA:{field}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_BAD_SHA:{field}") from exc
    return value.lower()


def _int(value: object, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_BAD_INTEGER:{field}")
    return value


def _number(value: object, field: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_BAD_NUMBER:{field}")
    out = float(value)
    if out < minimum:
        raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_BAD_NUMBER:{field}")
    return out


def _validate_occupancy(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_OCCUPANCY")
    cells_total = _int(value.get("cells_total"), "occupancy.cells_total")
    if cells_total != _EXPECTED_CELLS:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_OCCUPANCY_CELLS")
    strata_total = _int(value.get("strata_total"), "occupancy.strata_total", minimum=1)
    buckets = {
        "cells_in_singleton_strata": _int(value.get("cells_in_singleton_strata"), "occupancy.cells_in_singleton_strata"),
        "cells_in_size_2_3_strata": _int(value.get("cells_in_size_2_3_strata"), "occupancy.cells_in_size_2_3_strata"),
        "cells_in_size_4_7_strata": _int(value.get("cells_in_size_4_7_strata"), "occupancy.cells_in_size_4_7_strata"),
        "cells_in_size_ge_8_strata": _int(value.get("cells_in_size_ge_8_strata"), "occupancy.cells_in_size_ge_8_strata"),
    }
    if sum(buckets.values()) != cells_total:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_OCCUPANCY_PARTITION")
    size_min = _int(value.get("stratum_size_min"), "occupancy.stratum_size_min", minimum=1)
    size_median = _number(value.get("stratum_size_median"), "occupancy.stratum_size_median", minimum=1.0)
    size_p95 = _number(value.get("stratum_size_p95"), "occupancy.stratum_size_p95", minimum=1.0)
    size_max = _int(value.get("stratum_size_max"), "occupancy.stratum_size_max", minimum=1)
    if not (size_min <= size_median <= size_p95 <= size_max):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_OCCUPANCY_ORDER")
    if strata_total > cells_total:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_OCCUPANCY_STRATA")
    return {
        "cells_total": cells_total,
        "strata_total": strata_total,
        **buckets,
        "stratum_size_min": size_min,
        "stratum_size_median": size_median,
        "stratum_size_p95": size_p95,
        "stratum_size_max": size_max,
    }


def _validate_payload(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_NOT_MAPPING")
    if receipt.get("schema") != _EXPECTED_SCHEMA:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_SCHEMA")
    if receipt.get("d_shared_authority_v2_sha256") != EXPECTED_D_SHARED_AUTHORITY_V2_SHA256:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_AUTHORITY_PARENT")
    if receipt.get("full104_dimension_input_artifact_sha256") != EXPECTED_FULL104_ARTIFACT_SHA256:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_FULL104_PARENT")

    classification = receipt.get("resolution_classification")
    if classification == _CONTINUOUS_CLASSIFICATION:
        if receipt.get("terminal") != _CONTINUOUS_STOP:
            raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_V3_NULL_TERMINAL")
        raise MatchingStateResolutionStop(_CONTINUOUS_STOP)
    if classification != _LOSSLESS_CLASSIFICATION:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_CLASSIFICATION")

    if receipt.get("arbitrary_binning_used") is not False or receipt.get("bin_edges") is not None:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_BINNING_FORBIDDEN")

    if receipt.get("q_depth_source_semantics") != _EXPECTED_Q_DEPTH_SEMANTICS or receipt.get("q_depth_discrete_state") != _EXPECTED_Q_DEPTH_STATE:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DEPTH_SEMANTICS")
    if _int(receipt.get("q_depth_rows_checked"), "q_depth_rows_checked") != _EXPECTED_CELLS:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DEPTH_ROWS")
    if _int(receipt.get("q_depth_reconstruction_mismatches"), "q_depth_reconstruction_mismatches") != 0:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DEPTH_LOSSY")
    if receipt.get("q_depth_integer_domain_valid") is not True:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DEPTH_DOMAIN")

    if receipt.get("q_detect_source_semantics") != _EXPECTED_Q_DETECT_SEMANTICS or receipt.get("q_detect_discrete_state") != _EXPECTED_Q_DETECT_STATE:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DETECT_SEMANTICS")
    if _int(receipt.get("q_detect_rows_checked"), "q_detect_rows_checked") != _EXPECTED_CELLS:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DETECT_ROWS")
    if _int(receipt.get("q_detect_reconstruction_mismatches"), "q_detect_reconstruction_mismatches") != 0:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DETECT_LOSSY")
    if receipt.get("q_detect_integer_domain_valid") is not True:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_Q_DETECT_DOMAIN")

    if receipt.get("support_measurability_redundant_with_operator") is not True:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_SUPPORT_REDUNDANCY_UNRESOLVED")
    support_identity_sha = _sha64(
        receipt.get("support_measurability_operator_identity_sha256"),
        "support_measurability_operator_identity_sha256",
    )

    matching_tuple = receipt.get("effective_matching_tuple")
    if not isinstance(matching_tuple, Sequence) or isinstance(matching_tuple, (str, bytes)):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_TUPLE")
    if list(matching_tuple) != _EXPECTED_MATCHING_TUPLE:
        if "support_measurability" in list(matching_tuple):
            raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_REDUNDANT_SUPPORT_KEY")
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_TUPLE")

    for field in ("d_shared_outcomes_inspected", "rank_selection_inspected", "decision_bearing_effects_inspected"):
        if receipt.get(field) is not False:
            raise MatchingStateResolutionStop(f"STOP_D_SHARED_MATCHING_STATE_OUTCOME_FEEDBACK:{field}")
    if receipt.get("training_authorized") is not False:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_AUTHORITY_ESCALATION")
    if receipt.get("terminal") != _EXPECTED_TERMINAL:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_TERMINAL")

    occupancy = _validate_occupancy(receipt.get("occupancy"))
    out = dict(receipt)
    out["support_measurability_operator_identity_sha256"] = support_identity_sha
    out["effective_matching_tuple"] = list(_EXPECTED_MATCHING_TUPLE)
    out["occupancy"] = occupancy
    out["d_shared_real_outcome_access_authorized"] = False
    out["training_authorized"] = False
    return out


def _parents(payload: Mapping[str, object]) -> dict[str, str]:
    return {
        "d_shared_authority_v2_sha256": EXPECTED_D_SHARED_AUTHORITY_V2_SHA256,
        "full104_dimension_input_artifact_sha256": EXPECTED_FULL104_ARTIFACT_SHA256,
        "support_measurability_operator_identity_sha256": _sha64(
            payload.get("support_measurability_operator_identity_sha256"),
            "support_measurability_operator_identity_sha256",
        ),
    }


def seal_d_shared_matching_state_resolution_v1(receipt: Mapping[str, object]) -> dict[str, object]:
    payload = _validate_payload(receipt)
    return seal_artifact(D_SHARED_MATCHING_STATE_RESOLUTION_ARTIFACT_SCHEMA, payload, _parents(payload))


def validate_d_shared_matching_state_resolution_v1(envelope: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(envelope, Mapping):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_ENVELOPE_NOT_MAPPING")
    raw_payload = envelope.get("payload")
    if not isinstance(raw_payload, Mapping):
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_PAYLOAD_NOT_MAPPING")
    try:
        payload = validate_artifact(
            envelope,
            expected_schema=D_SHARED_MATCHING_STATE_RESOLUTION_ARTIFACT_SCHEMA,
            expected_parents=_parents(raw_payload),
        )
    except (ValueError, RuntimeError, MatchingStateResolutionStop) as exc:
        raise MatchingStateResolutionStop("STOP_D_SHARED_MATCHING_STATE_ARTIFACT_INVALID") from exc
    return _validate_payload(payload)
