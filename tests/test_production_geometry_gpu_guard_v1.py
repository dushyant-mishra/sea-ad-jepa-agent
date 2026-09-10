import pytest

from sea_ad_jepa.v5.production_geometry_gpu_guard_v1 import (
    ProductionGeometryGPUAuthorityV1,
    qualify_production_geometry_gpu_receipt,
)
from sea_ad_jepa.v5.trainer_preexecution_contract_v2 import MECHANICS_CHAIN_V2


def authority(**kw):
    base = dict(
        authority_id="prod-gpu-v1",
        design_context_sha256="a" * 64,
        full_reader_expression_artifact_sha256="b" * 64,
        production_dimension_artifact_sha256="c" * 64,
        proposal_weight_invariance_artifact_sha256="d" * 64,
        packing_restart_invariance_artifact_sha256="e" * 64,
        representation_firewall_artifact_sha256="f" * 64,
        historical_c2_gpu_receipt_sha256="2" * 64,
        protected_registry_sha256="1" * 64,
        production_geometry_frozen_before_gpu_run=True,
    )
    base.update(kw)
    return ProductionGeometryGPUAuthorityV1(**base)


def receipt(a=None):
    auth = a or authority()
    return {
        "schema": "JEPA_V5_PRODUCTION_GEOMETRY_GPU_EXECUTION_RECEIPT_V1",
        "authority_id": auth.authority_id,
        "bindings": auth.bindings(),
        "environment": {"cuda_available": True, "device_name": "test-gpu"},
        "geometry": {
            "effective_batch": 64,
            "microbatch": 8,
            "model_width": 192,
            "model_depth": 6,
            "source": "DATA_DERIVED_PRODUCTION_AUTHORITY",
        },
        "mechanics_chain": MECHANICS_CHAIN_V2,
        "historical_128x8_regression_passed": True,
        "production_geometry_executed": True,
        "real_full104_reader_batch_used": True,
        "synthetic_loader_used": False,
        "protected_48": {
            "gradients_live": 48,
            "parameters_moved": 48,
            "adam_exp_avg_live": 48,
            "adam_exp_avg_sq_live": 48,
        },
        "ema_update_proved": True,
        "atomic_checkpoint_telemetry_commit_proved": True,
        "training_authorized": False,
    }


def test_true_production_receipt_is_bound_and_never_authorizes_training():
    out = qualify_production_geometry_gpu_receipt(receipt(), authority=authority())
    assert out["real_production_geometry_qualified"] is True
    assert out["historical_regression_is_supporting_only"] is True
    assert out["bindings"]["historical_c2_gpu_receipt_sha256"] == "2" * 64
    assert out["training_authorized"] is False


def test_historical_128x8_receipt_cannot_masquerade_as_production():
    with pytest.raises(RuntimeError, match="HISTORICAL_128X8_RECEIPT_IS_NOT_PRODUCTION_GEOMETRY"):
        qualify_production_geometry_gpu_receipt(
            {"schema": "JEPA_V5_C2_GPU_CRITICAL_EXECUTION_RECEIPT_V1"},
            authority=authority(),
        )


def test_dimension_artifact_substitution_stops():
    r = receipt(); r["bindings"]["production_dimension_artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_packing_artifact_substitution_stops():
    r = receipt(); r["bindings"]["packing_restart_invariance_artifact_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_historical_receipt_substitution_stops():
    r = receipt(); r["bindings"]["historical_c2_gpu_receipt_sha256"] = "9" * 64
    with pytest.raises(RuntimeError, match="BINDING_SUBSTITUTION"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_synthetic_loader_cannot_satisfy_production_geometry():
    r = receipt(); r["real_full104_reader_batch_used"] = False; r["synthetic_loader_used"] = True
    with pytest.raises(RuntimeError, match="REAL_READER_NOT_EXERCISED"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_geometry_must_be_data_derived():
    r = receipt(); r["geometry"]["source"] = "HISTORICAL_128X8"
    with pytest.raises(RuntimeError, match="GEOMETRY_NOT_DATA_DERIVED"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_dead_protected_gradient_stops():
    r = receipt(); r["protected_48"]["gradients_live"] = 47
    with pytest.raises(RuntimeError, match="PROTECTED_COUNT"):
        qualify_production_geometry_gpu_receipt(r, authority=authority())


def test_geometry_must_be_frozen_before_execution():
    a = authority(production_geometry_frozen_before_gpu_run=False)
    with pytest.raises(ValueError, match="frozen before GPU execution"):
        qualify_production_geometry_gpu_receipt(receipt(authority()), authority=a)
