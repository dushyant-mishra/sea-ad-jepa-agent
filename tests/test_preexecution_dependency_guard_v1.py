import copy
import pytest

from sea_ad_jepa.v5.preexecution_dependency_guard_v1 import (
    PRE_EXECUTION_BASE_EVIDENCE_V2,
    validate_preexecution_dependencies,
)


def rows():
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(PRE_EXECUTION_BASE_EVIDENCE_V2)
    }


def reports(r):
    proposal = {
        "schema": "JEPA_V5_PROPOSAL_WEIGHT_INVARIANCE_V1",
        "authority_id": r["proposal_weight_invariance"]["authority_id"],
        "full_reader_expression_artifact_sha256": r["full_reader_expression_closure"]["artifact_sha256"],
        "schedule_artifact_sha256": "a" * 64,
        "schedule_authority_id": "schedule-v1",
        "passed": True, "training_authorized": False,
    }
    packing = {
        "schema": "JEPA_V5_PACKING_ORDER_RESTART_INVARIANCE_V1",
        "authority_id": r["packing_order_restart_invariance"]["authority_id"],
        "proposal_weight_artifact_sha256": r["proposal_weight_invariance"]["artifact_sha256"],
        "dimension_authority_artifact_sha256": r["production_dimension_authority"]["artifact_sha256"],
        "scientific_schedule_artifact_sha256": "a" * 64,
        "scientific_schedule_authority_id": "schedule-v1",
        "keyed_rng_contract_sha256": "b" * 64,
        "passed": True, "training_authorized": False,
    }
    gpu_bindings = {
        "design_context_sha256": "c" * 64,
        "full_reader_expression_artifact_sha256": r["full_reader_expression_closure"]["artifact_sha256"],
        "production_dimension_artifact_sha256": r["production_dimension_authority"]["artifact_sha256"],
        "proposal_weight_invariance_artifact_sha256": r["proposal_weight_invariance"]["artifact_sha256"],
        "packing_restart_invariance_artifact_sha256": r["packing_order_restart_invariance"]["artifact_sha256"],
        "representation_firewall_artifact_sha256": r["representation_firewall"]["artifact_sha256"],
        "historical_c2_gpu_receipt_sha256": r["cuda_historical_mechanics_regression"]["artifact_sha256"],
        "protected_registry_sha256": "d" * 64,
    }
    gpu = {
        "schema": "JEPA_V5_PRODUCTION_GEOMETRY_GPU_QUALIFICATION_V1",
        "authority_id": r["cuda_production_geometry_qualification"]["authority_id"],
        "bindings": gpu_bindings,
        "real_production_geometry_qualified": True,
        "historical_regression_is_supporting_only": True,
        "passed": True, "training_authorized": False,
    }
    dimension = {
        "schema": "JEPA_V5_PRODUCTION_DIMENSION_AUTHORITY_V4",
        "authority_id": r["production_dimension_authority"]["authority_id"],
        "expression_closure_artifact_sha256": r["full_reader_expression_closure"]["artifact_sha256"],
        "passed": True, "training_authorized": False,
    }
    return dimension, proposal, packing, gpu


def run(r=None, mutate=None):
    evidence = r or rows()
    d, p, k, g = reports(evidence)
    if mutate:
        mutate(d, p, k, g)
    return validate_preexecution_dependencies(
        evidence, design_context_sha256="c" * 64,
        dimension_report=d, proposal_weight_report=p,
        packing_restart_report=k, production_gpu_report=g,
        dependency_authority_id="predep-v1",
    )


def test_complete_preexecution_dependency_graph_closes():
    out = run()
    assert out["data_to_dimension_bound"] is True
    assert out["proposal_and_dimension_to_packing_bound"] is True
    assert out["all_preexecution_artifacts_to_production_gpu_bound"] is True
    assert out["training_authorized"] is False


def test_dimension_cannot_bind_other_full_reader_artifact():
    def m(d, p, k, g): d["expression_closure_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="DIMENSION_DATA_SUBSTITUTION"):
        run(mutate=m)


def test_packing_cannot_bind_other_proposal_artifact():
    def m(d, p, k, g): k["proposal_weight_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="PACKING_PROPOSAL_SUBSTITUTION"):
        run(mutate=m)


def test_packing_and_proposal_must_share_exact_schedule():
    def m(d, p, k, g): k["scientific_schedule_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="PACKING_SCHEDULE_ARTIFACT_SUBSTITUTION"):
        run(mutate=m)


def test_gpu_cannot_bind_other_dimension_artifact():
    def m(d, p, k, g): g["bindings"]["production_dimension_artifact_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="GPU_DEPENDENCY_SUBSTITUTION"):
        run(mutate=m)


def test_gpu_cannot_bind_other_historical_c2_receipt():
    def m(d, p, k, g): g["bindings"]["historical_c2_gpu_receipt_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="GPU_DEPENDENCY_SUBSTITUTION"):
        run(mutate=m)


def test_historical_regression_cannot_be_promoted_to_production_role():
    def m(d, p, k, g): g["historical_regression_is_supporting_only"] = False
    with pytest.raises(RuntimeError, match="HISTORICAL_GPU_ROLE_INVALID"):
        run(mutate=m)
