"""Cross-artifact dependency closure for V5 pre-execution evidence.

This guard proves the exact chain

FULL104 data -> dimensions -> proposal weights -> packing/restart -> production GPU

while also binding the representation firewall, exact production protected
registry, exact update-geometry authority, and the exact historical C2 GPU
receipt used as supporting regression evidence. Individually valid PASS
artifacts from different configurations cannot be mixed into one qualification
run. This guard never authorizes training.
"""
from __future__ import annotations

from typing import Mapping

PRE_EXECUTION_BASE_EVIDENCE_V2 = (
    "full_reader_expression_closure",
    "production_dimension_authority",
    "representation_firewall",
    "qc_policy_freeze",
    "proposal_weight_invariance",
    "packing_order_restart_invariance",
    "cuda_historical_mechanics_regression",
    "cuda_production_geometry_qualification",
)

_GPU_BINDING_FIELDS = (
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


def _rows(evidence: Mapping[str, Mapping[str, object]]) -> dict[str, dict[str, str]]:
    if not isinstance(evidence, Mapping) or set(evidence) != set(PRE_EXECUTION_BASE_EVIDENCE_V2):
        raise RuntimeError("STOP_V5_PREEXECUTION_DEPENDENCY_EVIDENCE_SET_MISMATCH")
    expected = {"status", "artifact_sha256", "authority_id", "training_authorized"}
    out = {}
    for name in PRE_EXECUTION_BASE_EVIDENCE_V2:
        row = evidence[name]
        if not isinstance(row, Mapping) or set(row) != expected:
            raise ValueError(f"{name} evidence schema mismatch")
        if row.get("status") != "EXECUTED_PASS":
            raise RuntimeError(f"STOP_V5_PREEXECUTION_DEPENDENCY_NOT_PASS: {name}")
        if row.get("training_authorized") is not False:
            raise RuntimeError(f"STOP_V5_PREEXECUTION_COMPONENT_CLAIMS_TRAINING_AUTHORITY: {name}")
        out[name] = {
            "artifact_sha256": _sha(row.get("artifact_sha256"), f"{name}.artifact_sha256"),
            "authority_id": _id(row.get("authority_id"), f"{name}.authority_id"),
        }
    return out


def validate_preexecution_dependencies(
    evidence: Mapping[str, Mapping[str, object]],
    *,
    design_context_sha256: str,
    dimension_report: Mapping[str, object],
    proposal_weight_report: Mapping[str, object],
    packing_restart_report: Mapping[str, object],
    production_gpu_report: Mapping[str, object],
    dependency_authority_id: str,
) -> dict[str, object]:
    rows = _rows(evidence)
    context = _sha(design_context_sha256, "design_context_sha256")
    dep_authority = _id(dependency_authority_id, "dependency_authority_id")

    if not isinstance(dimension_report, Mapping) or dimension_report.get("schema") != "JEPA_V5_PRODUCTION_DIMENSION_AUTHORITY_V4":
        raise ValueError("unexpected dimension report schema")
    if dimension_report.get("passed") is not True or dimension_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_DIMENSION_REPORT_INVALID")
    if dimension_report.get("authority_id") != rows["production_dimension_authority"]["authority_id"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_DIMENSION_AUTHORITY_SUBSTITUTION")
    if _sha(dimension_report.get("expression_closure_artifact_sha256"), "dimension.expression_closure_artifact_sha256") != rows["full_reader_expression_closure"]["artifact_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_DIMENSION_DATA_SUBSTITUTION")

    if not isinstance(proposal_weight_report, Mapping) or proposal_weight_report.get("schema") != "JEPA_V5_PROPOSAL_WEIGHT_INVARIANCE_V1":
        raise ValueError("unexpected proposal-weight report schema")
    if proposal_weight_report.get("passed") is not True or proposal_weight_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_PROPOSAL_REPORT_INVALID")
    if proposal_weight_report.get("authority_id") != rows["proposal_weight_invariance"]["authority_id"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PROPOSAL_AUTHORITY_SUBSTITUTION")
    if _sha(proposal_weight_report.get("full_reader_expression_artifact_sha256"), "proposal.full_reader_expression_artifact_sha256") != rows["full_reader_expression_closure"]["artifact_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PROPOSAL_DATA_SUBSTITUTION")
    schedule_sha = _sha(proposal_weight_report.get("schedule_artifact_sha256"), "proposal.schedule_artifact_sha256")
    schedule_id = _id(proposal_weight_report.get("schedule_authority_id"), "proposal.schedule_authority_id")

    if not isinstance(packing_restart_report, Mapping) or packing_restart_report.get("schema") != "JEPA_V5_PACKING_ORDER_RESTART_INVARIANCE_V1":
        raise ValueError("unexpected packing/restart report schema")
    if packing_restart_report.get("passed") is not True or packing_restart_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_REPORT_INVALID")
    if packing_restart_report.get("authority_id") != rows["packing_order_restart_invariance"]["authority_id"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_AUTHORITY_SUBSTITUTION")
    if _sha(packing_restart_report.get("proposal_weight_artifact_sha256"), "packing.proposal_weight_artifact_sha256") != rows["proposal_weight_invariance"]["artifact_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_PROPOSAL_SUBSTITUTION")
    if _sha(packing_restart_report.get("dimension_authority_artifact_sha256"), "packing.dimension_authority_artifact_sha256") != rows["production_dimension_authority"]["artifact_sha256"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_DIMENSION_SUBSTITUTION")
    if _sha(packing_restart_report.get("scientific_schedule_artifact_sha256"), "packing.scientific_schedule_artifact_sha256") != schedule_sha:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_SCHEDULE_ARTIFACT_SUBSTITUTION")
    if packing_restart_report.get("scientific_schedule_authority_id") != schedule_id:
        raise RuntimeError("STOP_V5_PREEXECUTION_PACKING_SCHEDULE_AUTHORITY_SUBSTITUTION")
    _sha(packing_restart_report.get("keyed_rng_contract_sha256"), "packing.keyed_rng_contract_sha256")

    if not isinstance(production_gpu_report, Mapping) or production_gpu_report.get("schema") != "JEPA_V5_PRODUCTION_GEOMETRY_GPU_QUALIFICATION_V1":
        raise ValueError("unexpected production GPU report schema")
    if production_gpu_report.get("passed") is not True or production_gpu_report.get("training_authorized") is not False:
        raise RuntimeError("STOP_V5_PREEXECUTION_PRODUCTION_GPU_REPORT_INVALID")
    if production_gpu_report.get("authority_id") != rows["cuda_production_geometry_qualification"]["authority_id"]:
        raise RuntimeError("STOP_V5_PREEXECUTION_PRODUCTION_GPU_AUTHORITY_SUBSTITUTION")
    bindings = production_gpu_report.get("bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != set(_GPU_BINDING_FIELDS):
        raise RuntimeError("STOP_V5_PREEXECUTION_GPU_BINDING_SET_MISMATCH")
    expected_gpu_bindings = {
        "design_context_sha256": context,
        "full_reader_expression_artifact_sha256": rows["full_reader_expression_closure"]["artifact_sha256"],
        "production_dimension_artifact_sha256": rows["production_dimension_authority"]["artifact_sha256"],
        "proposal_weight_invariance_artifact_sha256": rows["proposal_weight_invariance"]["artifact_sha256"],
        "packing_restart_invariance_artifact_sha256": rows["packing_order_restart_invariance"]["artifact_sha256"],
        "representation_firewall_artifact_sha256": rows["representation_firewall"]["artifact_sha256"],
        "historical_c2_gpu_receipt_sha256": rows["cuda_historical_mechanics_regression"]["artifact_sha256"],
    }
    for name, expected in expected_gpu_bindings.items():
        if _sha(bindings.get(name), f"gpu.bindings[{name}]") != expected:
            raise RuntimeError(f"STOP_V5_PREEXECUTION_GPU_DEPENDENCY_SUBSTITUTION: {name}")
    protected_registry_sha256 = _sha(bindings.get("protected_registry_sha256"), "gpu.bindings[protected_registry_sha256]")
    update_geometry_authority_sha256 = _sha(
        bindings.get("update_geometry_authority_sha256"),
        "gpu.bindings[update_geometry_authority_sha256]",
    )

    if production_gpu_report.get("real_production_geometry_qualified") is not True:
        raise RuntimeError("STOP_V5_PREEXECUTION_REAL_PRODUCTION_GPU_NOT_QUALIFIED")
    if production_gpu_report.get("historical_regression_is_supporting_only") is not True:
        raise RuntimeError("STOP_V5_PREEXECUTION_HISTORICAL_GPU_ROLE_INVALID")

    return {
        "schema": "JEPA_V5_PREEXECUTION_DEPENDENCY_CLOSURE_V1",
        "authority_id": dep_authority,
        "design_context_sha256": context,
        "evidence_artifact_sha256": {name: rows[name]["artifact_sha256"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2},
        "evidence_authority_ids": {name: rows[name]["authority_id"] for name in PRE_EXECUTION_BASE_EVIDENCE_V2},
        "protected_registry_sha256": protected_registry_sha256,
        "update_geometry_authority_sha256": update_geometry_authority_sha256,
        "production_gpu_geometry": dict(production_gpu_report.get("geometry", {})),
        "data_to_dimension_bound": True,
        "data_to_proposal_bound": True,
        "proposal_and_dimension_to_packing_bound": True,
        "all_preexecution_artifacts_to_production_gpu_bound": True,
        "passed": True,
        "training_authorized": False,
    }
