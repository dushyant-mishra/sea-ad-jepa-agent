import copy
import pytest

from sea_ad_jepa.v5.preexecution_dependency_guard_v1 import PRE_EXECUTION_BASE_EVIDENCE_V2
from sea_ad_jepa.v5.preexecution_qualification_bundle_v2 import (
    DEPENDENCY_EVIDENCE_ID,
    PRE_EXECUTION_EVIDENCE_V2,
    build_preexecution_bundle_v2,
    validate_preexecution_bundle_v2,
)


def rows():
    out = {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(PRE_EXECUTION_BASE_EVIDENCE_V2)
    }
    out[DEPENDENCY_EVIDENCE_ID] = {
        "status": "EXECUTED_PASS",
        "artifact_sha256": "f" * 64,
        "authority_id": "predep-v1",
        "training_authorized": False,
    }
    return out


def dep_report(e):
    return {
        "schema": "JEPA_V5_PREEXECUTION_DEPENDENCY_CLOSURE_V1",
        "authority_id": "predep-v1",
        "design_context_sha256": "c" * 64,
        "evidence_artifact_sha256": {name: e[name]["artifact_sha256"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2},
        "evidence_authority_ids": {name: e[name]["authority_id"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2},
        "data_to_dimension_bound": True,
        "data_to_proposal_bound": True,
        "proposal_and_dimension_to_packing_bound": True,
        "all_preexecution_artifacts_to_production_gpu_bound": True,
        "passed": True,
        "training_authorized": False,
    }


def build(e=None, d=None):
    evidence = e or rows()
    return build_preexecution_bundle_v2(
        evidence,
        design_context_sha256="c" * 64,
        dependency_closure_report=d or dep_report(evidence),
        dependency_closure_artifact_sha256="f" * 64,
        optimizer_started=False,
    )


def test_v2_requires_true_production_gpu_and_dependency_closure():
    out = build()
    assert set(out["required_evidence"]) == set(PRE_EXECUTION_EVIDENCE_V2)
    assert out["historical_gpu_regression_is_supporting_only"] is True
    assert out["production_geometry_gpu_required"] is True
    assert out["dependency_closure_required"] is True
    assert out["qualification_run_eligible"] is True
    assert out["production_training_authorized"] is False


def test_old_single_cuda_gate_evidence_cannot_satisfy_v2():
    e = rows(); del e["cuda_production_geometry_qualification"]; e["cuda_gate2_mechanics"] = {
        "status": "EXECUTED_PASS", "artifact_sha256": "9" * 64,
        "authority_id": "old", "training_authorized": False,
    }
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        build(e=e)


def test_missing_dependency_closure_stops():
    e = rows(); del e[DEPENDENCY_EVIDENCE_ID]
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        build(e=e)


def test_stale_dependency_graph_stops_after_artifact_change():
    e = rows(); d = dep_report(e)
    e["proposal_weight_invariance"]["artifact_sha256"] = "8" * 64
    with pytest.raises(RuntimeError, match="ARTIFACT_GRAPH_MISMATCH"):
        build(e=e, d=d)


def test_dependency_flag_cannot_be_false():
    e = rows(); d = dep_report(e); d["all_preexecution_artifacts_to_production_gpu_bound"] = False
    with pytest.raises(RuntimeError, match="DEPENDENCY_FLAG_NOT_CLOSED"):
        build(e=e, d=d)


def test_bundle_tamper_stops_on_revalidation():
    out = build()
    tampered = copy.deepcopy(out)
    tampered["required_evidence"]["production_dimension_authority"]["artifact_sha256"] = "8" * 64
    with pytest.raises(RuntimeError):
        validate_preexecution_bundle_v2(
            tampered,
            dependency_closure_report=dep_report(rows()),
            dependency_closure_artifact_sha256="f" * 64,
        )
