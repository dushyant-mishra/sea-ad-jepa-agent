from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Sequence

from .artifact_binding_v1 import seal_artifact, validate_artifact

_METRIC_SCHEMAS = {
    "shared": "JEPA_V5_D_SHARED_METRICS_ARTIFACT_V1",
    "private": "JEPA_V5_D_PRIVATE_METRICS_ARTIFACT_V1",
    "observation": "JEPA_V5_D_OBS_METRICS_ARTIFACT_V1",
}
_SELECTION_SCHEMAS = {
    "shared": "JEPA_V5_D_SHARED_SELECTION_ARTIFACT_V1",
    "private": "JEPA_V5_D_PRIVATE_SELECTION_ARTIFACT_V1",
    "observation": "JEPA_V5_D_OBS_SELECTION_ARTIFACT_V1",
}
_DIMENSION_KEYS = {"shared": "D_shared", "private": "D_private", "observation": "D_obs"}
_ALLOWED_TERMINALS = {
    "shared": {"PASS_D_SHARED_SELECTED", "EXPAND_SHARED_SEARCH_ENVELOPE"},
    "private": {"PASS_D_PRIVATE_SELECTED", "EXPAND_PRIVATE_SEARCH_ENVELOPE"},
    "observation": {"PASS_D_OBS_SELECTED", "EXPAND_OBSERVATION_SEARCH_ENVELOPE"},
}


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _kind(kind: object) -> str:
    if not isinstance(kind, str) or kind not in _METRIC_SCHEMAS:
        raise ValueError("kind must be one of shared, private, observation")
    return kind


def _rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("rows must be a nonempty sequence")
    out: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("metric rows must be mappings")
        out.append(deepcopy(dict(row)))
    return out


def _metric_parents(
    *,
    kind: str,
    full104_dimension_input_artifact_sha256: object,
    execution_receipt_sha256: object,
    shared_selection_artifact_sha256: object | None,
) -> dict[str, str]:
    parents = {
        "full104_dimension_input": _sha(
            full104_dimension_input_artifact_sha256,
            "full104_dimension_input_artifact_sha256",
        ),
        "execution_receipt": _sha(execution_receipt_sha256, "execution_receipt_sha256"),
    }
    if kind == "private":
        if shared_selection_artifact_sha256 is None:
            raise ValueError("private dimension metrics require a frozen shared selection artifact")
        parents["shared_selection"] = _sha(
            shared_selection_artifact_sha256,
            "shared_selection_artifact_sha256",
        )
    elif shared_selection_artifact_sha256 is not None:
        raise ValueError("only private dimension metrics may declare a shared selection parent")
    return parents


def seal_dimension_metric_artifact(
    *,
    kind: str,
    rows: Sequence[Mapping[str, object]],
    full104_dimension_input_artifact_sha256: str,
    execution_receipt_sha256: str,
    shared_selection_artifact_sha256: str | None = None,
) -> dict[str, object]:
    k = _kind(kind)
    payload = {
        "kind": k,
        "rows": _rows(rows),
        "population_mode": "FULL_READER_FIT_STREAM",
        "full_stream_execution": True,
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }
    return seal_artifact(
        _METRIC_SCHEMAS[k],
        payload,
        _metric_parents(
            kind=k,
            full104_dimension_input_artifact_sha256=full104_dimension_input_artifact_sha256,
            execution_receipt_sha256=execution_receipt_sha256,
            shared_selection_artifact_sha256=shared_selection_artifact_sha256,
        ),
    )


def validate_dimension_metric_artifact(
    envelope: Mapping[str, object],
    *,
    kind: str,
    expected_full104_dimension_input_artifact_sha256: str,
    expected_execution_receipt_sha256: str,
    expected_shared_selection_artifact_sha256: str | None = None,
) -> dict[str, object]:
    k = _kind(kind)
    payload = validate_artifact(
        envelope,
        expected_schema=_METRIC_SCHEMAS[k],
        expected_parents=_metric_parents(
            kind=k,
            full104_dimension_input_artifact_sha256=expected_full104_dimension_input_artifact_sha256,
            execution_receipt_sha256=expected_execution_receipt_sha256,
            shared_selection_artifact_sha256=expected_shared_selection_artifact_sha256,
        ),
    )
    if payload.get("kind") != k:
        raise RuntimeError("STOP_V5_DIMENSION_METRIC_KIND_MISMATCH")
    if payload.get("population_mode") != "FULL_READER_FIT_STREAM" or payload.get("full_stream_execution") is not True:
        raise RuntimeError("STOP_V5_DIMENSION_METRIC_NOT_FULL_STREAM")
    for field in ("synthetic_data_used", "pathology_used", "checkpoint_outcomes_used", "training_authorized"):
        if payload.get(field) is not False:
            raise RuntimeError(f"STOP_V5_DIMENSION_METRIC_FORBIDDEN_STATE:{field}")
    payload["rows"] = _rows(payload.get("rows"))
    return payload


def seal_dimension_selection_artifact(
    *, kind: str, selection: Mapping[str, object], metric_artifact_sha256: str
) -> dict[str, object]:
    k = _kind(kind)
    if not isinstance(selection, Mapping):
        raise ValueError("selection must be a mapping")
    payload = deepcopy(dict(selection))
    if payload.get("training_authorized") is not False:
        raise ValueError("selection must explicitly deny training authority")
    if payload.get("terminal") not in _ALLOWED_TERMINALS[k]:
        raise ValueError("selection terminal does not match dimension kind")
    if _DIMENSION_KEYS[k] not in payload:
        raise ValueError(f"selection missing {_DIMENSION_KEYS[k]}")
    return seal_artifact(
        _SELECTION_SCHEMAS[k], payload, {"metric_artifact": _sha(metric_artifact_sha256, "metric_artifact_sha256")}
    )


def validate_dimension_selection_artifact(
    envelope: Mapping[str, object], *, kind: str, expected_metric_artifact_sha256: str
) -> dict[str, object]:
    k = _kind(kind)
    payload = validate_artifact(
        envelope,
        expected_schema=_SELECTION_SCHEMAS[k],
        expected_parents={"metric_artifact": _sha(expected_metric_artifact_sha256, "expected_metric_artifact_sha256")},
    )
    if payload.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_DIMENSION_SELECTION_AUTHORITY_ESCALATION")
    if payload.get("terminal") not in _ALLOWED_TERMINALS[k] or _DIMENSION_KEYS[k] not in payload:
        raise RuntimeError("STOP_V5_DIMENSION_SELECTION_SEMANTICS_MISMATCH")
    return payload
