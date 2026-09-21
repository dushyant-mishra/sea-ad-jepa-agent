"""Fail-closed preflight for FULL104 Audit-B execution.

This module performs no burden computation. It validates a frozen execution
contract and, when requested, verifies the physical bytes of every bound runtime
artifact before an Audit-B executor is allowed to start.
"""
from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .audit_b_execution_contract_v1 import AuditBExecutionContractV1


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"required file is missing: {p}")
    h = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def contract_from_payload(payload: Mapping[str, Any]) -> AuditBExecutionContractV1:
    if payload.get("schema") != "V5_AUDIT_B_EXECUTION_CONTRACT_V1":
        raise ValueError("Audit-B execution contract schema mismatch")
    names = {f.name for f in fields(AuditBExecutionContractV1)}
    missing = sorted(names - set(payload))
    if missing:
        raise ValueError(f"Audit-B execution contract missing fields: {missing[:5]}")
    values = {name: payload[name] for name in names}
    values["sample_ladder"] = tuple(values["sample_ladder"])
    values["execution_requirements"] = tuple(values["execution_requirements"])
    contract = AuditBExecutionContractV1(**values)
    contract.validate()
    declared = payload.get("contract_sha256")
    if declared != contract.canonical_digest():
        raise ValueError("Audit-B execution contract digest mismatch")
    if payload.get("execution_authorized") is not contract.execution_authorized:
        raise ValueError("Audit-B execution_authorized flag disagrees with contract state")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise ValueError("Audit-B contract payload indicates terminal outcomes were inspected")
    if payload.get("training_authorized") is not False:
        raise ValueError("Audit-B contract payload unexpectedly authorizes training")
    return contract


def load_contract(path: str | Path) -> AuditBExecutionContractV1:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"execution contract is missing: {p}")
    return contract_from_payload(json.loads(p.read_text(encoding="utf-8")))


def require_contract_ready(path: str | Path) -> AuditBExecutionContractV1:
    contract = load_contract(path)
    contract.require_execution_ready()
    return contract


def verify_runtime_bindings(
    contract: AuditBExecutionContractV1,
    *,
    sample_freeze: str | Path,
    heavy_artifact: str | Path,
    heavy_qualification_receipt: str | Path,
    rng_authority: str | Path,
    mask_plan_generator: str | Path,
    burden_estimator_source: str | Path,
    full104_manifest: str | Path,
    canonical_registry: str | Path,
) -> dict[str, str]:
    """Verify exact physical bytes against the already validated contract."""
    observed = {
        "phase_iv_sample_artifact_sha256": sha256_file(sample_freeze),
        "heavy_artifact_sha256": sha256_file(heavy_artifact),
        "heavy_qualification_receipt_sha256": sha256_file(heavy_qualification_receipt),
        "rng_authority_sha256": sha256_file(rng_authority),
        "mask_plan_generator_sha256": sha256_file(mask_plan_generator),
        "burden_estimator_source_sha256": sha256_file(burden_estimator_source),
        "full104_manifest_sha256": sha256_file(full104_manifest),
        "canonical_registry_sha256": sha256_file(canonical_registry),
    }
    expected = {
        "phase_iv_sample_artifact_sha256": contract.phase_iv_sample_artifact_sha256,
        "heavy_artifact_sha256": contract.heavy_artifact_sha256,
        "heavy_qualification_receipt_sha256": contract.heavy_qualification_receipt_sha256,
        # The contract binds the RNG authority's canonical scientific digest, not
        # the JSON file bytes. Runtime verification of that semantic digest occurs
        # below after loading the JSON.
        "mask_plan_generator_sha256": contract.mask_plan_generator_sha256,
        "burden_estimator_source_sha256": contract.burden_estimator_source_sha256,
        "full104_manifest_sha256": contract.full104_manifest_sha256,
        "canonical_registry_sha256": contract.canonical_registry_sha256,
    }
    for role, exp in expected.items():
        if role == "rng_authority_sha256":
            continue
        if observed[role] != exp:
            raise ValueError(
                f"runtime binding mismatch for {role}: "
                f"expected {exp}, observed {observed[role]}"
            )

    rng_path = Path(rng_authority)
    rng = json.loads(rng_path.read_text(encoding="utf-8"))
    if rng.get("schema") != contract.rng_authority_schema_id:
        raise ValueError("runtime RNG authority schema mismatch")
    if rng.get("authority_sha256") != contract.rng_authority_sha256:
        raise ValueError("runtime RNG authority canonical digest mismatch")
    if rng.get("target_panel_dependency") != contract.rng_target_panel_dependency_id:
        raise ValueError("runtime RNG target-panel dependency mismatch")
    if rng.get("terminal_outcomes_inspected_before_freeze") is not False:
        raise ValueError("runtime RNG authority was frozen after terminal outcomes")
    if rng.get("training_authorized") is not False:
        raise ValueError("runtime RNG authority unexpectedly authorizes training")

    heavy = json.loads(Path(heavy_qualification_receipt).read_text(encoding="utf-8"))
    if heavy.get("schema") != contract.heavy_qualification_schema_id:
        raise ValueError("runtime heavy qualification schema mismatch")
    if heavy.get("verdict") != contract.heavy_qualification_verdict_id:
        raise ValueError("runtime heavy qualification verdict mismatch")
    if heavy.get("all_104_donor_library_totals_agree") is not True:
        raise ValueError("runtime heavy qualification lacks all-donor agreement")
    if heavy.get("per_cell_source_vector_agrees") is not True:
        raise ValueError("runtime heavy qualification lacks source-vector agreement")

    return observed
