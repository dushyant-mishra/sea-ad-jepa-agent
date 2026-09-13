"""Artifact-bound production dimension authority for V5.

V3 validates the real FULL104 expression-binding receipt and dimension
arithmetic. V4 preserves that validation while binding the resulting dimension
authority to both the immutable expression-closure artifact and the frozen
prospective precision authority used before decision-bearing dimension metrics
were produced.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .dimension_authority_guard_v3 import DimensionAuthorityGuardV3
from .prospective_precision_authority_v1 import FROZEN_PRECISION_AUTHORITY_SHA256


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
    precision_authority_sha256: str = FROZEN_PRECISION_AUTHORITY_SHA256

    def validate(self, receipt: Mapping[str, object]) -> dict[str, object]:
        aid = _id(self.authority_id, "authority_id")
        closure = _sha(self.expression_closure_artifact_sha256, "expression_closure_artifact_sha256")
        precision = _sha(self.precision_authority_sha256, "precision_authority_sha256")
        if precision != FROZEN_PRECISION_AUTHORITY_SHA256:
            raise RuntimeError("STOP_D_AUTHORITY_PRECISION_AUTHORITY_SUBSTITUTION")
        if self.authority_frozen_before_optimizer_start is not True:
            raise ValueError("dimension authority must be frozen before optimizer start")
        if receipt.get("precision_authority_sha256") != precision:
            raise RuntimeError("STOP_D_AUTHORITY_PRECISION_AUTHORITY_MISMATCH")
        if receipt.get("precision_authority_terminal") != "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1":
            raise RuntimeError("STOP_D_AUTHORITY_PRECISION_AUTHORITY_TERMINAL")
        if receipt.get("precision_authority_frozen_before_dimension_outcomes") is not True:
            raise RuntimeError("STOP_D_AUTHORITY_PRECISION_AUTHORITY_NOT_PROSPECTIVE")
        dimensions = self.guard_v3.validate(receipt)
        return {
            "schema": "JEPA_V5_PRODUCTION_DIMENSION_AUTHORITY_V4",
            "authority_id": aid,
            "expression_closure_artifact_sha256": closure,
            "precision_authority_sha256": precision,
            "precision_authority_terminal": "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1",
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
