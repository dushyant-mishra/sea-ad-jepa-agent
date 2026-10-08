#!/usr/bin/env python3
"""Build executable FULL104 Audit-B B4 contract V2 without opening outcomes."""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import json
from pathlib import Path
from typing import Any, Mapping

from sea_ad_jepa.v5.audit_b_execution_contract_v2 import AuditBExecutionContractV2
from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import contract_from_payload as v1_from_payload
from sea_ad_jepa.v5.audit_b_precision_rule_v2 import AuditBPrecisionRuleAuthorityV2
from sea_ad_jepa.v5.audit_b_scientific_resolution_v3 import AuditBScientificResolutionV3


def _typed(payload: Mapping[str, Any], cls):
    names = {f.name for f in fields(cls)}
    missing = sorted(names - set(payload))
    if missing:
        raise ValueError(f"{cls.__name__} missing fields: {missing[:5]}")
    return cls(**{name: payload[name] for name in names})


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required input is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return value


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parent-contract", type=Path, required=True)
    p.add_argument("--scientific-resolution", type=Path, required=True)
    p.add_argument("--precision-rule-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    if args.out.exists():
        raise SystemExit("output already exists; refuse overwrite")

    parent_payload = _load_json(args.parent_contract)
    parent = v1_from_payload(parent_payload)

    resolution_payload = _load_json(args.scientific_resolution)
    if resolution_payload.get("schema") != "V5_AUDIT_B_SCIENTIFIC_RESOLUTION_V3":
        raise ValueError("scientific resolution schema mismatch")
    resolution = _typed(resolution_payload, AuditBScientificResolutionV3)
    resolution.validate()
    if resolution_payload.get("resolution_sha256") != resolution.canonical_digest():
        raise ValueError("scientific resolution declared digest mismatch")
    if resolution.parent_preexecution_contract_sha256 != parent.canonical_digest():
        raise ValueError("scientific resolution does not bind supplied V1 parent")

    precision_payload = _load_json(args.precision_rule_authority)
    if precision_payload.get("schema") != "V5_AUDIT_B_PRECISION_RULE_AUTHORITY_V2":
        raise ValueError("precision-rule authority schema mismatch")
    precision = _typed(precision_payload, AuditBPrecisionRuleAuthorityV2)
    precision.validate()
    if precision_payload.get("authority_sha256") != precision.canonical_digest():
        raise ValueError("precision-rule authority declared digest mismatch")

    # Require the signed decision and semantic precision authority to agree
    # field-for-field before constructing executable authority.
    comparisons = {
        "precision_scope_id": precision.precision_scope_id,
        "reporting_scope_id": precision.reporting_scope_id,
        "primary_policy_id": precision.primary_policy_id,
        "primary_rung_numerator": precision.primary_rung_numerator,
        "primary_rung_denominator": precision.primary_rung_denominator,
        "precision_estimator_id": precision.precision_estimator_id,
        "relative_se_tolerance_numerator": precision.relative_se_tolerance_numerator,
        "relative_se_tolerance_denominator": precision.relative_se_tolerance_denominator,
        "absolute_se_tolerance_numerator": precision.absolute_se_tolerance_numerator,
        "absolute_se_tolerance_denominator": precision.absolute_se_tolerance_denominator,
        "absolute_tolerance_origin_id": precision.absolute_tolerance_origin_id,
        "zero_mean_rule_id": precision.zero_mean_rule_id,
    }
    for name, expected in comparisons.items():
        if getattr(resolution, name) != expected:
            raise ValueError(f"B2 resolution disagrees with precision authority: {name}")

    contract = AuditBExecutionContractV2(
        contract_id="JEPA_V5_FULL104_AUDIT_B_EXECUTION_CONTRACT_V2",
        parent_preexecution_contract_sha256=parent.canonical_digest(),
        scientific_resolution_sha256=resolution.canonical_digest(),
        precision_rule_authority_sha256=precision.canonical_digest(),
        phase_iv_sample_freeze_digest=parent.phase_iv_sample_freeze_digest,
        phase_iv_sample_artifact_sha256=parent.phase_iv_sample_artifact_sha256,
        full104_manifest_sha256=parent.full104_manifest_sha256,
        canonical_registry_sha256=parent.canonical_registry_sha256,
        heavy_artifact_sha256=parent.heavy_artifact_sha256,
        heavy_qualification_receipt_sha256=parent.heavy_qualification_receipt_sha256,
        rng_authority_sha256=parent.rng_authority_sha256,
        mask_plan_generator_sha256=parent.mask_plan_generator_sha256,
        burden_estimator_source_sha256=parent.burden_estimator_source_sha256,
        precision_scope_id=resolution.precision_scope_id,
        target_aggregation_id=resolution.target_aggregation_id,
        mandatory_robustness_aggregation_id=resolution.mandatory_robustness_aggregation_id,
        primary_policy_id=resolution.primary_policy_id,
        primary_rung_numerator=resolution.primary_rung_numerator,
        primary_rung_denominator=resolution.primary_rung_denominator,
        precision_estimator_id=resolution.precision_estimator_id,
        relative_se_tolerance_numerator=resolution.relative_se_tolerance_numerator,
        relative_se_tolerance_denominator=resolution.relative_se_tolerance_denominator,
        absolute_se_tolerance_numerator=resolution.absolute_se_tolerance_numerator,
        absolute_se_tolerance_denominator=resolution.absolute_se_tolerance_denominator,
        absolute_tolerance_origin_id=resolution.absolute_tolerance_origin_id,
        zero_mean_rule_id=resolution.zero_mean_rule_id,
        reporting_scope_id=resolution.reporting_scope_id,
        source_stratified_reporting_id=resolution.source_stratified_reporting_id,
    )
    contract.validate()
    payload = {
        "schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V2",
        **asdict(contract),
        "sample_ladder": list(contract.sample_ladder),
        "execution_requirements": list(contract.execution_requirements),
        "execution_authorized": contract.execution_authorized,
        "contract_sha256": contract.canonical_digest(),
        "terminal_masking_outcomes_inspected": False,
        "source_artifacts": {
            "parent_contract": str(args.parent_contract),
            "scientific_resolution": str(args.scientific_resolution),
            "precision_rule_authority": str(args.precision_rule_authority),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "state": "B4_EXECUTION_CONTRACT_MATERIALIZED",
                "contract_sha256": contract.canonical_digest(),
                "execution_authorized": True,
                "initial_sample_level_id": contract.initial_sample_level_id,
                "initial_sample_size": contract.initial_sample_size,
                "direct_n2_n3_execution_authorized":
                    contract.direct_n2_n3_execution_authorized,
                "terminal_masking_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
