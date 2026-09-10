"""Fail-closed admission guard for true V5 production-geometry GPU evidence.

The historical 128x8 C2 regression proves that the corrected update mechanics
work on the hardware. It does *not* prove that the eventual V5 model, dimensions,
scientific update membership, proposal weights and packing policy work together
at their data-derived production geometry.

This guard therefore rejects the historical C2 receipt as production evidence
and accepts only a dedicated receipt bound to the exact V5 pre-execution
artifacts. It does not itself run CUDA and never authorizes training.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .trainer_preexecution_contract_v2 import MECHANICS_CHAIN_V2

_BINDING_FIELDS = (
    "design_context_sha256",
    "full_reader_expression_artifact_sha256",
    "production_dimension_artifact_sha256",
    "proposal_weight_invariance_artifact_sha256",
    "packing_restart_invariance_artifact_sha256",
    "representation_firewall_artifact_sha256",
    "protected_registry_sha256",
)


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
class ProductionGeometryGPUAuthorityV1:
    authority_id: str
    design_context_sha256: str
    full_reader_expression_artifact_sha256: str
    production_dimension_artifact_sha256: str
    proposal_weight_invariance_artifact_sha256: str
    packing_restart_invariance_artifact_sha256: str
    representation_firewall_artifact_sha256: str
    protected_registry_sha256: str
    production_geometry_frozen_before_gpu_run: bool

    def validate(self) -> None:
        _id(self.authority_id, "authority_id")
        for name in _BINDING_FIELDS:
            _sha(getattr(self, name), name)
        if self.production_geometry_frozen_before_gpu_run is not True:
            raise ValueError("production geometry must be frozen before GPU execution")

    def bindings(self) -> dict[str, str]:
        self.validate()
        return {name: _sha(getattr(self, name), name) for name in _BINDING_FIELDS}


def qualify_production_geometry_gpu_receipt(
    receipt: Mapping[str, object],
    *,
    authority: ProductionGeometryGPUAuthorityV1,
) -> dict[str, object]:
    authority.validate()
    if not isinstance(receipt, Mapping):
        raise ValueError("receipt must be a mapping")
    if receipt.get("schema") == "JEPA_V5_C2_GPU_CRITICAL_EXECUTION_RECEIPT_V1":
        raise RuntimeError("STOP_V5_HISTORICAL_128X8_RECEIPT_IS_NOT_PRODUCTION_GEOMETRY")
    if receipt.get("schema") != "JEPA_V5_PRODUCTION_GEOMETRY_GPU_EXECUTION_RECEIPT_V1":
        raise ValueError("unexpected production GPU receipt schema")
    if receipt.get("authority_id") != authority.authority_id:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_AUTHORITY_SUBSTITUTION")

    bindings = receipt.get("bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != set(_BINDING_FIELDS):
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_BINDING_SET_MISMATCH")
    expected = authority.bindings()
    for name in _BINDING_FIELDS:
        if _sha(bindings.get(name), f"receipt.bindings[{name}]") != expected[name]:
            raise RuntimeError(f"STOP_V5_PRODUCTION_GPU_BINDING_SUBSTITUTION: {name}")

    environment = receipt.get("environment")
    if not isinstance(environment, Mapping) or environment.get("cuda_available") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_CUDA_NOT_PROVED")
    if not isinstance(environment.get("device_name"), str) or not environment.get("device_name"):
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_DEVICE_IDENTITY_MISSING")

    geometry = receipt.get("geometry")
    if not isinstance(geometry, Mapping):
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_GEOMETRY_MISSING")
    for name in ("effective_batch", "microbatch", "model_width", "model_depth"):
        value = geometry.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise RuntimeError(f"STOP_V5_PRODUCTION_GPU_GEOMETRY_INVALID: {name}")
    if geometry.get("source") != "DATA_DERIVED_PRODUCTION_AUTHORITY":
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_GEOMETRY_NOT_DATA_DERIVED")

    if tuple(receipt.get("mechanics_chain", ())) != MECHANICS_CHAIN_V2:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_MECHANICS_CHAIN_MISMATCH")
    if receipt.get("historical_128x8_regression_passed") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_HISTORICAL_REGRESSION_MISSING")
    if receipt.get("production_geometry_executed") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_GEOMETRY_NOT_EXECUTED")
    if receipt.get("real_full104_reader_batch_used") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_REAL_READER_NOT_EXERCISED")
    if receipt.get("synthetic_loader_used") is not False:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_SYNTHETIC_LOADER_MASQUERADE")

    protected = receipt.get("protected_48")
    if not isinstance(protected, Mapping):
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REPORT_MISSING")
    for name in ("gradients_live", "parameters_moved", "adam_exp_avg_live", "adam_exp_avg_sq_live"):
        if protected.get(name) != 48:
            raise RuntimeError(f"STOP_V5_PRODUCTION_GPU_PROTECTED_COUNT: {name}")
    if receipt.get("ema_update_proved") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_EMA_NOT_PROVED")
    if receipt.get("atomic_checkpoint_telemetry_commit_proved") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_ATOMIC_COMMIT_NOT_PROVED")
    if receipt.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_AUTHORITY_ESCALATION")

    return {
        "schema": "JEPA_V5_PRODUCTION_GEOMETRY_GPU_QUALIFICATION_V1",
        "authority_id": authority.authority_id,
        "bindings": expected,
        "geometry": dict(geometry),
        "cuda_device_name": environment["device_name"],
        "historical_regression_is_supporting_only": True,
        "real_production_geometry_qualified": True,
        "passed": True,
        "training_authorized": False,
    }
