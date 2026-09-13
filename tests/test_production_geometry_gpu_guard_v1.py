import pytest

from sea_ad_jepa.v5.production_protected_registry_authority_v1 import (
    PRODUCTION_MECHANICS_CHAIN_V1,
    PROTECTED_PARAMETERS,
    PROTECTED_ROLES,
    ProductionProtectedRegistryAuthorityV1,
)
from sea_ad_jepa.v5.production_geometry_gpu_guard_v1 import (
    ProductionGeometryGPUAuthorityV1,
    qualify_production_geometry_gpu_receipt,
)


def registry(depth=6):
    return ProductionProtectedRegistryAuthorityV1(
        authority_id=f"prod-registry-{depth}",
        model_depth=depth,
        records=[
            {"block_index": b, "role": r, "parameter": p, "tensor_name": f"blocks.{b}.{r}.{p}"}
            for b in range(depth) for r in PROTECTED_ROLES for p in PROTECTED_PARAMETERS
        ],
    )


def authority(reg=None, **kw):
    reg = reg or registry()
    base = dict(
        authority_id="prod-gpu-v1",
        design_context_sha256="a" * 64,
        full_reader_expression_artifact_sha256="b" * 64,
        production_dimension_artifact_sha256="c" * 64,
        proposal_weight_invariance_artifact_sha256="d" * 64,
        packing_restart_invariance_artifact_sha256="e" * 64,
        representation_firewall_artifact_sha256="f" * 64,
        historical_c2_gpu_receipt_sha256="2" * 64,
        protected_registry_sha256=reg.registry_sha256(),
        update_geometry_authority_sha256="3" * 64,
        effective_batch=64,
        microbatch=8,
        model_width=192,
        model_depth=reg.model_depth,
        production_geometry_frozen_before_gpu_run=True,
    )
    base.update(kw)
    return ProductionGeometryGPUAuthorityV1(**base)


def receipt(a=None, reg=None):
    reg = reg or registry()
    auth = a or authority(reg)
    n = reg.expected_tensors
    return {
        "schema": "JEPA_V5_PRODUCTION_GEOMETRY_GPU_EXECUTION_RECEIPT_V1",
        "authority_id": auth.authority_id,
        "bindings": auth.bindings(),
        "environment": {"cuda_available": True, "device_name": "test-gpu"},
        "geometry": auth.geometry(),
        "mechanics_chain": PRODUCTION_MECHANICS_CHAIN_V1,
        "historical_128x8_regression_passed": True,
        "production_geometry_executed": True,
        "real_full104_reader_batch_used": True,
        "synthetic_loader_used": False,
        "protected_registry": {
            "expected_tensors": n,
            "registry_sha256": reg.registry_sha256(),
            "gradients_live": n,
            "parameters_moved": n,
            "adam_exp_avg_live": n,
            "adam_exp_avg_sq_live": n,
        },
        "ema_update_proved": True,
        "atomic_checkpoint_telemetry_commit_proved": True,
        "training_authorized": False,
    }


def qualify(r=None, a=None, reg=None):
    reg = reg or registry(); a = a or authority(reg); r = r or receipt(a, reg)
    return qualify_production_geometry_gpu_receipt(r, authority=a, protected_registry_authority=reg)


def test_true_production_receipt_is_bound_and_never_authorizes_training():
    out = qualify()
    assert out["real_production_geometry_qualified"] is True
    assert out["historical_regression_is_supporting_only"] is True
    assert out["bindings"]["historical_c2_gpu_receipt_sha256"] == "2" * 64
    assert out["bindings"]["update_geometry_authority_sha256"] == "3" * 64
    assert out["protected_tensors"] == 48
    assert out["training_authorized"] is False


def test_historical_128x8_receipt_cannot_masquerade_as_production():
    reg = registry()
    with pytest.raises(RuntimeError, match="HISTORICAL_128X8_RECEIPT_IS_NOT_PRODUCTION_GEOMETRY"):
        qualify_production_geometry_gpu_receipt(
            {"schema": "JEPA_V5_C2_GPU_CRITICAL_EXECUTION_RECEIPT_V1"},
            authority=authority(reg), protected_registry_authority=reg,
        )


def test_dimension_artifact_substitution_stops():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["bindings"]["production_dimension_artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"): qualify(r, a, reg)


def test_packing_artifact_substitution_stops():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["bindings"]["packing_restart_invariance_artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"): qualify(r, a, reg)


def test_historical_receipt_substitution_stops():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["bindings"]["historical_c2_gpu_receipt_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"): qualify(r, a, reg)


def test_update_geometry_authority_substitution_stops():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["bindings"]["update_geometry_authority_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"): qualify(r, a, reg)


def test_synthetic_loader_cannot_satisfy_production_geometry():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["real_full104_reader_batch_used"] = False; r["synthetic_loader_used"] = True
    with pytest.raises(RuntimeError, match="REAL_READER_NOT_EXERCISED"): qualify(r, a, reg)


def test_geometry_must_be_data_derived():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["geometry"]["source"] = "HISTORICAL_128X8"
    with pytest.raises(RuntimeError, match="GEOMETRY_NOT_DATA_DERIVED"): qualify(r, a, reg)


def test_positive_but_wrong_geometry_is_rejected():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["geometry"]["model_width"] = 384
    with pytest.raises(RuntimeError, match="GEOMETRY_AUTHORITY_MISMATCH"): qualify(r, a, reg)


def test_dead_protected_gradient_stops():
    reg = registry(); a = authority(reg); r = receipt(a, reg); r["protected_registry"]["gradients_live"] = reg.expected_tensors - 1
    with pytest.raises(RuntimeError, match="PROTECTED_COUNT"): qualify(r, a, reg)


def test_geometry_must_be_frozen_before_execution():
    reg = registry(); good = authority(reg); bad = authority(reg, production_geometry_frozen_before_gpu_run=False)
    with pytest.raises(ValueError, match="frozen before GPU execution"):
        qualify_production_geometry_gpu_receipt(receipt(good, reg), authority=bad, protected_registry_authority=reg)


def test_registry_sha_must_match_gpu_authority():
    reg = registry(6); other = registry(8)
    with pytest.raises(RuntimeError, match="PROTECTED_REGISTRY_AUTHORITY_MISMATCH"):
        qualify_production_geometry_gpu_receipt(receipt(authority(reg), reg), authority=authority(reg), protected_registry_authority=other)
