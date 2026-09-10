"""Artifact-bound production dimension authority for V5.

V3 validates the real FULL104 expression-binding receipt and dimension
arithmetic. V4 preserves that validation while binding the resulting dimension
authority to the immutable artifact identity of the exact expression closure it
consumed. This creates the data -> dimensions edge required by pre-execution
qualification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .dimension_authority_guard_v3 import DimensionAuthorityGuardV3


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class DimensionAuthorityV4:
    authority_id: str
    expression_closure_artifact_sha256: str
    guard_v3: DimensionAuthorityGuardV3
    authority_frozen_before_optimizer_start: bool

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        aid = _id(self.authority_id, "authority_id")
        closure = _sha(self.expression_closure_artifact_sha256, "expression_closure_artifact_sha256")
        if self.authority_frozen_before_optimizer_start is not True:
            raise ValueError("dimension authority must be frozen before optimizer start")
        dimensions = self.guard_v3.validate(receipt)
        return {
            "schema": "JEPA_V5_PRODUCTION_DIMENSION_AUTHORITY_V4",
            "authority_id": aid,
            "expression_closure_artifact_sha256": closure,
            "metadata_sqlite_sha256": receipt["metadata_sqlite_sha256"],
            "block_manifest_sha256": receipt["block_manifest_sha256"],
            "materialization_contract_sha256": receipt["materialization_contract_sha256"],
            "materialization_audit_sha256": receipt["materialization_audit_sha256"],
            "D_shared": dimensions["D_shared"],
            "D_private": dimensions["D_private"],
            "D_total": dimensions["D_total"],
            "D_obs": dimensions["D_obs"],
            "passed": True,
            "training_authorized": False,
        }
