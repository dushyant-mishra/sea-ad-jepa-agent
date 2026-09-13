from __future__ import annotations

import pytest

from sea_ad_jepa.v5.production_protected_registry_authority_v1 import (
    PRODUCTION_MECHANICS_CHAIN_V1,
    ProductionProtectedRegistryAuthorityV1,
)
from sea_ad_jepa.v5.production_geometry_gpu_guard_v1 import (
    ProductionGeometryGPUAuthorityV1,
    qualify_production_geometry_gpu_receipt,
)


def _records(depth: int):
    roles = ("attention_norm", "attention.query", "attention.key", "attention.value")
    params = ("weight", "bias")
    return [
        {"block_index": block, "role": role, "parameter": parameter, "tensor_name": f"blocks.{block}.{role}.{parameter}"}
        for block in range(depth) for role in roles for parameter in params
    ]


def _registry(depth: int = 8) -> ProductionProtectedRegistryAuthorityV1:
    return ProductionProtectedRegistryAuthorityV1(
        authority_id=f"protected-registry-depth-{depth}", model_depth=depth, records=_records(depth)
    )


def _gpu_authority(registry: ProductionProtectedRegistryAuthorityV1):
    return ProductionGeometryGPUAuthorityV1(
        authority_id="prod-gpu-v1",
        design_context_sha256="a" * 64,
        full_reader_expression_artifact_sha256="b" * 64,
        production_dimension_artifact_sha256="c" * 64,
        proposal_weight_invariance_artifact_sha256="d" * 64,
        packing_restart_invariance_artifact_sha256="e" * 64,
        representation_firewall_artifact_sha256="f" * 64,
        historical_c2_gpu_receipt_sha256="2" * 64,
        protected_registry_sha256=registry.registry_sha256(),
        update_geometry_authority_sha256="3" * 64,
        effective_batch=64,
        microbatch=8,
        model_width=192,
        model_depth=registry.model_depth,
        production_geometry_frozen_before_gpu_run=True,
    )


def _receipt(registry: ProductionProtectedRegistryAuthorityV1):
    authority = _gpu_authority(registry)
    expected = registry.expected_tensors
    return {
        "schema": "JEPA_V5_PRODUCTION_GEOMETRY_GPU_EXECUTION_RECEIPT_V1",
        "authority_id": authority.authority_id,
        "bindings": authority.bindings(),
        "environment": {"cuda_available": True, "device_name": "test-gpu"},
        "geometry": authority.geometry(),
        "mechanics_chain": PRODUCTION_MECHANICS_CHAIN_V1,
        "historical_128x8_regression_passed": True,
        "production_geometry_executed": True,
        "real_full104_reader_batch_used": True,
        "synthetic_loader_used": False,
        "protected_registry": {
            "expected_tensors": expected,
            "registry_sha256": registry.registry_sha256(),
            "gradients_live": expected,
            "parameters_moved": expected,
            "adam_exp_avg_live": expected,
            "adam_exp_avg_sq_live": expected,
        },
        "ema_update_proved": True,
        "atomic_checkpoint_telemetry_commit_proved": True,
        "training_authorized": False,
    }


def _qualify(registry, receipt):
    return qualify_production_geometry_gpu_receipt(
        receipt, authority=_gpu_authority(registry), protected_registry_authority=registry
    )


def test_depth8_production_registry_has_64_protected_tensors_and_passes_gpu_guard():
    registry = _registry(8)
    assert registry.expected_tensors == 64
    out = _qualify(registry, _receipt(registry))
    assert out["protected_tensors"] == 64
    assert out["geometry"]["model_depth"] == 8


def test_depth8_receipt_with_historical_48_counts_is_rejected():
    registry = _registry(8); receipt = _receipt(registry); receipt["protected_registry"]["gradients_live"] = 48
    with pytest.raises(RuntimeError, match="PROTECTED_COUNT"): _qualify(registry, receipt)


def test_registry_depth_must_equal_data_derived_gpu_depth():
    registry = _registry(8); receipt = _receipt(registry); receipt["geometry"]["model_depth"] = 6
    with pytest.raises(RuntimeError, match="GEOMETRY_AUTHORITY_MISMATCH|PROTECTED_REGISTRY_DEPTH_MISMATCH"): _qualify(registry, receipt)


def test_gpu_receipt_cannot_self_assert_a_different_positive_model_width():
    registry = _registry(8); receipt = _receipt(registry); receipt["geometry"]["model_width"] = 384
    with pytest.raises(RuntimeError, match="GEOMETRY_AUTHORITY_MISMATCH"): _qualify(registry, receipt)
