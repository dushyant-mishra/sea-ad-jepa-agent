"""Fail-closed admission guard for true V5 production-geometry GPU evidence.

Historical 128x8 C2 mechanics are supporting regression only. Current V5 GPU
evidence must bind the exact prospectively frozen data-derived geometry and the
exact production protected-tensor registry. A receipt may not self-assert its
batch/microbatch/width/depth merely by labeling them data-derived.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .production_protected_registry_authority_v1 import (
    PRODUCTION_MECHANICS_CHAIN_V1,
    ProductionProtectedRegistryAuthorityV1,
)

_BINDING_FIELDS = (
    "design_context_sha256",
    "full_reader_expression_artifact_sha256",
    "production_dimension_artifact_sha256",
    "proposal_weight_invariance_artifact_sha256",
    "packing_restart_invariance_artifact_sha256",
    "representation_firewall_artifact_sha256",
    "historical_c2_gpu_receipt_sha256",
    "protected_registry_sha256",
    "update_geometry_authority_sha256",
)
_GEOMETRY_FIELDS = ("effective_batch", "microbatch", "model_width", "model_depth")


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


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class ProductionGeometryGPUAuthorityV1:
    authority_id: str
    design_context_sha256: str
    full_reader_expression_artifact_sha256: str
    production_dimension_artifact_sha256: str
    proposal_weight_invariance_artifact_sha256: str
    packing_restart_invariance_artifact_sha256: str
    representation_firewall_artifact_sha256: str
    historical_c2_gpu_receipt_sha256: str
    protected_registry_sha256: str
    update_geometry_authority_sha256: str
    effective_batch: int
    microbatch: int
    model_width: int
    model_depth: int
    production_geometry_frozen_before_gpu_run: bool

    def validate(self) -> None:
        _id(self.authority_id, "authority_id")
        for name in _BINDING_FIELDS:
            _sha(getattr(self, name), name)
        for name in _GEOMETRY_FIELDS:
            _positive_int(getattr(self, name), name)
        if self.production_geometry_frozen_before_gpu_run is not True:
            raise ValueError("production geometry must be frozen before GPU execution")

    def bindings(self) -> dict[str, str]:
        self.validate()
        return {name: _sha(getattr(self, name), name) for name in _BINDING_FIELDS}

    def geometry(self) -> dict[str, object]:
        self.validate()
        return {
            "effective_batch": self.effective_batch,
            "microbatch": self.microbatch,
            "model_width": self.model_width,
            "model_depth": self.model_depth,
            "source": "DATA_DERIVED_PRODUCTION_AUTHORITY",
        }


def qualify_production_geometry_gpu_receipt(
    receipt: Mapping[str, object],
    *,
    authority: ProductionGeometryGPUAuthorityV1,
    protected_registry_authority: ProductionProtectedRegistryAuthorityV1,
) -> dict[str, object]:
    authority.validate()
    protected_registry_authority.validate()
    registry_sha = protected_registry_authority.registry_sha256()
    if _sha(authority.protected_registry_sha256, "authority.protected_registry_sha256") != registry_sha:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REGISTRY_AUTHORITY_MISMATCH")
    if authority.model_depth != protected_registry_authority.model_depth:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REGISTRY_DEPTH_MISMATCH")

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
    if geometry.get("source") != "DATA_DERIVED_PRODUCTION_AUTHORITY":
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_GEOMETRY_NOT_DATA_DERIVED")
    expected_geometry = authority.geometry()
    for name in _GEOMETRY_FIELDS:
        value = geometry.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise RuntimeError(f"STOP_V5_PRODUCTION_GPU_GEOMETRY_INVALID: {name}")
        if value != expected_geometry[name]:
            raise RuntimeError(f"STOP_V5_PRODUCTION_GPU_GEOMETRY_AUTHORITY_MISMATCH: {name}")
    if geometry.get("model_depth") != protected_registry_authority.model_depth:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REGISTRY_DEPTH_MISMATCH")

    if tuple(receipt.get("mechanics_chain", ())) != PRODUCTION_MECHANICS_CHAIN_V1:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_MECHANICS_CHAIN_MISMATCH")
    if receipt.get("historical_128x8_regression_passed") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_HISTORICAL_REGRESSION_MISSING")
    if receipt.get("production_geometry_executed") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_GEOMETRY_NOT_EXECUTED")
    if receipt.get("real_full104_reader_batch_used") is not True:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_REAL_READER_NOT_EXERCISED")
    if receipt.get("synthetic_loader_used") is not False:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_SYNTHETIC_LOADER_MASQUERADE")

    protected = receipt.get("protected_registry")
    if not isinstance(protected, Mapping):
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REPORT_MISSING")
    expected_count = protected_registry_authority.expected_tensors
    if protected.get("expected_tensors") != expected_count:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_EXPECTED_COUNT_MISMATCH")
    if _sha(protected.get("registry_sha256"), "protected_registry.registry_sha256") != registry_sha:
        raise RuntimeError("STOP_V5_PRODUCTION_GPU_PROTECTED_REGISTRY_RECEIPT_MISMATCH")
    for name in ("gradients_live", "parameters_moved", "adam_exp_avg_live", "adam_exp_avg_sq_live"):
        if protected.get(name) != expected_count:
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
        "geometry": expected_geometry,
        "protected_registry_authority_sha256": protected_registry_authority.canonical_digest(),
        "protected_tensors": expected_count,
        "cuda_device_name": environment["device_name"],
        "historical_regression_is_supporting_only": True,
        "real_production_geometry_qualified": True,
        "passed": True,
        "training_authorized": False,
    }
