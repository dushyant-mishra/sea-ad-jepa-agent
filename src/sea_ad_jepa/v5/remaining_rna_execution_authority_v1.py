"""Execution evidence authority for current-V5 remaining-RNA necessity.

This object can bind only healthy current-V5 teacher evidence. Historical T1
checkpoints remain adversarial fixtures and cannot satisfy this authority.
Execution evidence is hash-bound, fail-closed on skipped/nonexecution states,
and cannot authorize training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple


APPROVED_EVIDENCE_SOURCE_IDS: Tuple[str, ...] = ("HEALTHY_CURRENT_V5_TEACHER_V1",)
APPROVED_EXECUTION_STATUSES: Tuple[str, ...] = ("EXECUTED_PASS", "EXECUTED_FAIL")
APPROVED_STATE_METRIC_IDS: Tuple[str, ...] = (
    "QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
    "QUERY_LOCAL_LATENT_STATE_COSINE_ERROR_V1",
)
APPROVED_COMPARATOR_SET_IDS: Tuple[str, ...] = (
    "FULL_RNA__IDENTITY_ONLY__IDENTITY_PLUS_LAWFUL_GLOBAL_NO_RNA_V1",
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


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class RemainingRnaExecutionAuthorityV1:
    authority_id: str
    remaining_rna_necessity_authority_sha256: str
    precision_authority_sha256: str
    target_construction_authority_sha256: str
    target_panel_authority_sha256: str
    outer_split_authority_sha256: str
    healthy_teacher_source_authority_sha256: str
    result_artifact_sha256: str
    evidence_source_id: str
    execution_status: str
    state_metric_id: str
    comparator_set_id: str
    training_authorized: bool = False

    @property
    def passed(self) -> bool:
        return self.execution_status == "EXECUTED_PASS"

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")

        root_fields = (
            "remaining_rna_necessity_authority_sha256",
            "precision_authority_sha256",
            "target_construction_authority_sha256",
            "target_panel_authority_sha256",
            "outer_split_authority_sha256",
            "healthy_teacher_source_authority_sha256",
            "result_artifact_sha256",
        )
        roots = [_sha(getattr(self, name), name) for name in root_fields]
        if len(set(roots)) != len(roots):
            raise ValueError("remaining-RNA execution authority roots must be distinct")

        _enum(self.evidence_source_id, APPROVED_EVIDENCE_SOURCE_IDS, "evidence_source_id")
        _enum(self.execution_status, APPROVED_EXECUTION_STATUSES, "execution_status")
        _enum(self.state_metric_id, APPROVED_STATE_METRIC_IDS, "state_metric_id")
        _enum(self.comparator_set_id, APPROVED_COMPARATOR_SET_IDS, "comparator_set_id")

        if self.training_authorized is not False:
            raise ValueError("remaining-RNA execution authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )

    def bind_live_authorities(
        self,
        *,
        remaining_rna_necessity: Any,
        precision: Any,
        target_construction: Any,
        target_panel: Any,
        outer_split: Any,
    ) -> None:
        self.validate()
        expected = (
            (remaining_rna_necessity, self.remaining_rna_necessity_authority_sha256, "remaining RNA necessity authority root mismatch", "remaining RNA necessity"),
            (precision, self.precision_authority_sha256, "precision authority root mismatch", "precision"),
            (target_construction, self.target_construction_authority_sha256, "target construction authority root mismatch", "target construction"),
            (target_panel, self.target_panel_authority_sha256, "target panel authority root mismatch", "target panel"),
            (outer_split, self.outer_split_authority_sha256, "outer split authority root mismatch", "outer split"),
        )
        for obj, digest, message, name in expected:
            if _live_digest(obj, name) != digest:
                raise ValueError(message)
