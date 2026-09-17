"""Executed current-V5 measurement-robustness authority.

This successor binds a state-level same-cell measurement-depth perturbation,
prospective precision/stratification guards, exact execution source/results, and
an explicit executed status. It cannot silently substitute hidden-gene expression
metrics for latent-state robustness and cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_PRIMARY_METRIC_IDS: Tuple[str, ...] = (
    "QUERY_LOCAL_LATENT_STATE_COSINE_STABILITY_V1",
)
APPROVED_PERTURBATION_SEMANTICS_IDS: Tuple[str, ...] = (
    "SAME_CELL_MEASUREMENT_DEPTH_PERTURBATION_V1",
)
APPROVED_FAILURE_SEMANTICS_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_ON_STATE_INSTABILITY_OR_INSUFFICIENT_PRECISION_V1",
)
APPROVED_EXECUTION_STATUSES: Tuple[str, ...] = (
    "EXECUTED_PASS",
    "EXECUTED_FAIL",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of {approved!r}, got {value!r}")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class MeasurementRobustnessAuthorityV2:
    authority_id: str
    representation_authority_sha256: str
    teacher_target_semantics_sha256: str
    precision_authority_sha256: str
    perturbation_protocol_authority_sha256: str
    stratification_guardrail_authority_sha256: str
    execution_source_sha256: str
    result_artifact_sha256: str
    primary_metric_id: str
    perturbation_semantics_id: str
    failure_semantics_id: str
    execution_status: str
    training_authorized: bool = False

    @property
    def passed(self) -> bool:
        return self.execution_status == "EXECUTED_PASS"

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        root_fields = (
            "representation_authority_sha256",
            "teacher_target_semantics_sha256",
            "precision_authority_sha256",
            "perturbation_protocol_authority_sha256",
            "stratification_guardrail_authority_sha256",
            "execution_source_sha256",
            "result_artifact_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("measurement-robustness authority roots must be distinct")
        _enum(self.primary_metric_id, APPROVED_PRIMARY_METRIC_IDS, "primary_metric_id")
        _enum(
            self.perturbation_semantics_id,
            APPROVED_PERTURBATION_SEMANTICS_IDS,
            "perturbation_semantics_id",
        )
        _enum(self.failure_semantics_id, APPROVED_FAILURE_SEMANTICS_IDS, "failure_semantics_id")
        _enum(self.execution_status, APPROVED_EXECUTION_STATUSES, "execution_status")
        if self.training_authorized is not False:
            raise ValueError("measurement-robustness authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2",
                **asdict(self),
                "training_authorized": False,
            }
        )
