"""Fail-closed preflight for executable FULL104 Audit-B contract V2 (B4).

No burden or mask is computed here. The preflight validates the executable
contract and verifies every physical/semantic runtime binding before N1 may run.
"""
from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
from typing import Any, Mapping

from .audit_b_execution_contract_v2 import AuditBExecutionContractV2
from .audit_b_execution_preflight_v1 import (
    sha256_file,
    verify_phase_iv_sample_freeze,
)
from .audit_b_precision_rule_v2 import AuditBPrecisionRuleAuthorityV2
from .audit_b_scientific_resolution_v3 import AuditBScientificResolutionV3
from .masking_rng_replay_authority_v3 import MaskingRngReplayAuthorityV3


def _typed(payload: Mapping[str, Any], cls):
    names = {f.name for f in fields(cls)}
    missing = sorted(names - set(payload))
    if missing:
        raise ValueError(f"{cls.__name__} missing fields: {missing[:5]}")
    values = {name: payload[name] for name in names}
    if "sample_ladder" in values:
        values["sample_ladder"] = tuple(values["sample_ladder"])
    if "execution_requirements" in values:
        values["execution_requirements"] = tuple(values["execution_requirements"])
    return cls(**values)


def contract_from_payload(payload: Mapping[str, Any]) -> AuditBExecutionContractV2:
    if payload.get("schema") != "V5_AUDIT_B_EXECUTION_CONTRACT_V2":
        raise ValueError("Audit-B B4 execution contract schema mismatch")
    contract = _typed(payload, AuditBExecutionContractV2)
    contract.validate()
    if payload.get("contract_sha256") != contract.canonical_digest():
        raise ValueError("Audit-B B4 execution contract digest mismatch")
    if payload.get("execution_authorized") is not True:
        raise ValueError("Audit-B B4 payload must explicitly authorize Audit-B execution")
    if payload.get("terminal_masking_authorized") is not False:
        raise ValueError("Audit-B B4 cannot authorize terminal masking")
    if payload.get("training_authorized") is not False:
        raise ValueError("Audit-B B4 cannot authorize training")
    return contract


def load_contract(path: str | Path) -> AuditBExecutionContractV2:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"B4 execution contract is missing: {p}")
    return contract_from_payload(json.loads(p.read_text(encoding="utf-8")))


def require_contract_ready(path: str | Path) -> AuditBExecutionContractV2:
    contract = load_contract(path)
    contract.require_execution_ready()
    return contract


def _load_resolution(
    path: str | Path,
    contract: AuditBExecutionContractV2,
) -> AuditBScientificResolutionV3:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"B2 scientific resolution is missing: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if payload.get("schema") != contract.scientific_resolution_schema_id:
        raise ValueError("B2 scientific resolution schema mismatch")
    resolution = _typed(payload, AuditBScientificResolutionV3)
    resolution.validate()
    digest = resolution.canonical_digest()
    if payload.get("resolution_sha256") != digest:
        raise ValueError("B2 scientific resolution declared digest mismatch")
    if digest != contract.scientific_resolution_sha256:
        raise ValueError("B4 binds a different B2 scientific resolution")
    if (
        resolution.parent_preexecution_contract_sha256
        != contract.parent_preexecution_contract_sha256
    ):
        raise ValueError("B2 resolution and B4 disagree on immutable V1 parent")
    return resolution


def _load_precision_rule(
    path: str | Path,
    contract: AuditBExecutionContractV2,
) -> AuditBPrecisionRuleAuthorityV2:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"precision-rule authority is missing: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if payload.get("schema") != contract.precision_rule_authority_schema_id:
        raise ValueError("precision-rule authority schema mismatch")
    authority = _typed(payload, AuditBPrecisionRuleAuthorityV2)
    authority.validate()
    digest = authority.canonical_digest()
    if payload.get("authority_sha256") != digest:
        raise ValueError("precision-rule authority declared digest mismatch")
    if digest != contract.precision_rule_authority_sha256:
        raise ValueError("B4 binds a different precision-rule authority")
    return authority


def _load_rng(
    path: str | Path,
    contract: AuditBExecutionContractV2,
) -> MaskingRngReplayAuthorityV3:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"RNG authority is missing: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if payload.get("schema") != contract.rng_authority_schema_id:
        raise ValueError("runtime RNG authority schema mismatch")
    rng = MaskingRngReplayAuthorityV3(
        authority_id=str(payload["authority_id"]),
        full104_substrate_sha256=str(payload["full104_substrate_sha256"]),
        canonical_registry_sha256=str(payload["canonical_registry_sha256"]),
        outer_split_receipt_sha256=str(payload["outer_split_receipt_sha256"]),
        qualification_parameters_authority_sha256=str(
            payload["qualification_parameters_authority_sha256"]
        ),
        burden_ladder_authority_sha256=str(payload["burden_ladder_authority_sha256"]),
        seed_namespace_id=str(payload["seed_namespace_id"]),
        method_exclusion_policy_id=str(payload["method_exclusion_policy_id"]),
        replay_policy_id=str(payload["replay_policy_id"]),
        terminal_outcomes_inspected_before_freeze=bool(
            payload["terminal_outcomes_inspected_before_freeze"]
        ),
        training_authorized=bool(payload["training_authorized"]),
    )
    rng.validate()
    if rng.canonical_digest() != contract.rng_authority_sha256:
        raise ValueError("runtime RNG authority canonical digest mismatch")
    if payload.get("authority_sha256") != rng.canonical_digest():
        raise ValueError("runtime RNG authority declared digest mismatch")
    if int(payload.get("global_seed", -1)) != rng.global_seed:
        raise ValueError("runtime RNG authority global_seed mismatch")
    if payload.get("target_panel_dependency") != contract.rng_target_panel_dependency_id:
        raise ValueError("runtime RNG target-panel dependency mismatch")
    return rng


def verify_runtime_bindings(
    contract: AuditBExecutionContractV2,
    *,
    scientific_resolution: str | Path,
    precision_rule_authority: str | Path,
    sample_freeze: str | Path,
    heavy_artifact: str | Path,
    heavy_qualification_receipt: str | Path,
    rng_authority: str | Path,
    mask_plan_generator: str | Path,
    burden_estimator_source: str | Path,
    full104_manifest: str | Path,
    canonical_registry: str | Path,
    repo_root: str | Path,
    successor: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    contract.require_execution_ready()

    resolution = _load_resolution(scientific_resolution, contract)
    precision = _load_precision_rule(precision_rule_authority, contract)
    rng = _load_rng(rng_authority, contract)

    # ``successor`` defaults to None, so V2 stays fail-closed on any bound-input
    # drift unless a validated successor record is supplied explicitly.
    frozen_inputs = verify_phase_iv_sample_freeze(
        sample_freeze, repo_root=repo_root, successor=successor
    )

    observed = {
        "phase_iv_sample_artifact_sha256": sha256_file(sample_freeze),
        "heavy_artifact_sha256": sha256_file(heavy_artifact),
        "heavy_qualification_receipt_sha256": sha256_file(
            heavy_qualification_receipt
        ),
        "rng_authority_file_sha256": sha256_file(rng_authority),
        "mask_plan_generator_sha256": sha256_file(mask_plan_generator),
        "burden_estimator_source_sha256": sha256_file(burden_estimator_source),
        "full104_manifest_sha256": sha256_file(full104_manifest),
        "canonical_registry_sha256": sha256_file(canonical_registry),
    }
    expected = {
        "phase_iv_sample_artifact_sha256": contract.phase_iv_sample_artifact_sha256,
        "heavy_artifact_sha256": contract.heavy_artifact_sha256,
        "heavy_qualification_receipt_sha256":
            contract.heavy_qualification_receipt_sha256,
        "mask_plan_generator_sha256": contract.mask_plan_generator_sha256,
        "burden_estimator_source_sha256": contract.burden_estimator_source_sha256,
        "full104_manifest_sha256": contract.full104_manifest_sha256,
        "canonical_registry_sha256": contract.canonical_registry_sha256,
    }
    for role, exp in expected.items():
        if observed[role] != exp:
            raise ValueError(
                f"runtime binding mismatch for {role}: "
                f"expected {exp}, observed {observed[role]}"
            )

    heavy = json.loads(
        Path(heavy_qualification_receipt).read_text(encoding="utf-8")
    )
    if heavy.get("schema") != contract.heavy_qualification_schema_id:
        raise ValueError("runtime heavy qualification schema mismatch")
    if heavy.get("verdict") != contract.heavy_qualification_verdict_id:
        raise ValueError("runtime heavy qualification verdict mismatch")
    if heavy.get("block_manifest_sha256") != contract.full104_manifest_sha256:
        raise ValueError("runtime heavy qualification FULL104 manifest mismatch")
    if heavy.get("artifact_sha256") != contract.heavy_artifact_sha256:
        raise ValueError("runtime heavy qualification artifact mismatch")
    if heavy.get("rows_traversed") != 4_553_407:
        raise ValueError("runtime heavy qualification row count drifted")
    if heavy.get("donors") != 104 or heavy.get("core_addresses") != 17_186:
        raise ValueError("runtime heavy qualification geometry drifted")
    if heavy.get("three_route_total_agreement") is not True:
        raise ValueError("runtime heavy qualification lacks total-library agreement")
    if heavy.get("all_104_donor_library_totals_agree") is not True:
        raise ValueError("runtime heavy qualification lacks all-donor agreement")
    if heavy.get("per_cell_source_vector_agrees") is not True:
        raise ValueError("runtime heavy qualification lacks source-vector agreement")

    return {
        **observed,
        "scientific_resolution_sha256": resolution.canonical_digest(),
        "precision_rule_authority_sha256": precision.canonical_digest(),
        "rng_authority_sha256": rng.canonical_digest(),
        **{
            f"phase_iv_bound::{role}": digest
            for role, digest in frozen_inputs.items()
        },
    }
