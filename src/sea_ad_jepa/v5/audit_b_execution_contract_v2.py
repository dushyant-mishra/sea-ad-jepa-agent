"""Executable successor contract for FULL104 Audit-B N1 (B4).

This contract is the first Audit-B contract allowed to authorize N1. It binds:
- the immutable non-executable V1 parent;
- the signed outcome-blind B2 scientific resolution V3;
- the semantic hybrid precision-rule authority V2;
- the verified RNG-V3 authority;
- the frozen Phase-IV sample and all existing runtime roots.

It authorizes only Audit-B execution under the frozen N1/N2/N3 precision ladder.
It does not authorize terminal masking, target-panel selection, TD60 or training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

from .audit_b_execution_contract_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
)
from .audit_b_precision_rule_v2 import (
    ABSOLUTE_SE_TOLERANCE,
    ABSOLUTE_TOLERANCE_ORIGIN_ID,
    PRECISION_ESTIMATOR_ID,
    PRECISION_SCOPE_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    RELATIVE_SE_TOLERANCE,
    REPORTING_SCOPE_ID,
    ZERO_MEAN_RULE_ID,
)
from .audit_b_scientific_resolution_v3 import (
    MANDATORY_ROBUSTNESS_AGGREGATION_ID,
    PRIMARY_TARGET_AGGREGATION_ID,
    SOURCE_STRATIFIED_REPORTING_ID,
)

PARENT_PREEXECUTION_CONTRACT_SHA256 = (
    "95db537de2df04e83c72d17ab788f985901ee4b644769d598243a9eed5eef398"
)
SCIENTIFIC_RESOLUTION_SHA256 = (
    "766f467f4566cf0087ca4bc22f5263575a8ae50d7e5905666886190c3ad95889"
)
PRECISION_RULE_AUTHORITY_SHA256 = (
    "0a712b3aeebc42732726667722c90b2b9d97a6110cba157c2d99aa642c0c97b4"
)
PHASE_IV_SAMPLE_ARTIFACT_SHA256 = (
    "d0ce8abbff0076071009997113f1b73ebb8bab9b0ada5d6ce9367eb786733c06"
)
HEAVY_QUALIFICATION_RECEIPT_SHA256 = (
    "21fd10f07187c8e59457cf8860a67359ab179878c194833ee119e0323a7c8d53"
)
RNG_AUTHORITY_SHA256 = (
    "775aba506982a9a8dbecccb454d8d3d68709e524bb7f67e9397bbf819b72c2fb"
)
BURDEN_ESTIMATOR_SOURCE_SHA256 = (
    "7f589f548bf94fd0bd207717f1b0289e2718958915e08d3a6d716b22164d441a"
)

PRIMARY_METRIC_ID = "B2_HELDOUT_DETECTED_TOKEN_BURDEN"
SECONDARY_METRIC_ID = "B3_HELDOUT_RAW_UMI_BURDEN__DESCRIPTIVE_ONLY"
NORMALIZATION_ID = "ADDED_MINUS_DROPPED_OVER_UNIFORM_FULL_MASK_WITH_TARGET_V1"
SAMPLE_LADDER = (256, 1024, 4096)

EXECUTION_REQUIREMENTS = (
    "policy construction uses TRAINING-side information only",
    "burden measured on held-out donors only",
    "each donor contributes through its authenticated held-out fold only",
    "every nonuniform policy x burden rung is reported",
    "reported by source x donor x fold, never only pooled",
    "source-balanced aggregation is the primary Audit-B burden estimand",
    "donor-uniform aggregation is mandatory non-gating robustness evidence",
    "only RIDGE8_CONDITIONAL at the 5 percent rung controls sample escalation",
    "primary precision uses max(1/860 absolute SE, 5 percent of abs(mean))",
    "precisely zero burden effect uses the absolute SE branch, never undefined RSE",
    "NO policy adaptation from observed burden",
    "no held-out realized zero/nonzero state may influence mask choice",
    "B3 raw-UMI burden is descriptive only and cannot drive escalation",
    "N1 is a prefix of N2 and N2 is a prefix of N3",
    "RNG-V3 seed remains fixed and target-panel independent",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class AuditBExecutionContractV2:
    contract_id: str
    parent_preexecution_contract_sha256: str
    scientific_resolution_sha256: str
    precision_rule_authority_sha256: str

    phase_iv_sample_freeze_digest: str
    phase_iv_sample_artifact_sha256: str
    full104_manifest_sha256: str
    canonical_registry_sha256: str
    heavy_artifact_sha256: str
    heavy_qualification_receipt_sha256: str
    rng_authority_sha256: str
    mask_plan_generator_sha256: str
    burden_estimator_source_sha256: str

    precision_scope_id: str
    target_aggregation_id: str
    mandatory_robustness_aggregation_id: str
    primary_policy_id: str
    primary_rung_numerator: int
    primary_rung_denominator: int
    precision_estimator_id: str
    relative_se_tolerance_numerator: int
    relative_se_tolerance_denominator: int
    absolute_se_tolerance_numerator: int
    absolute_se_tolerance_denominator: int
    absolute_tolerance_origin_id: str
    zero_mean_rule_id: str
    reporting_scope_id: str
    source_stratified_reporting_id: str

    primary_metric_id: str = PRIMARY_METRIC_ID
    secondary_metric_id: str = SECONDARY_METRIC_ID
    normalization_id: str = NORMALIZATION_ID
    sample_ladder: Tuple[int, int, int] = SAMPLE_LADDER
    execution_requirements: Tuple[str, ...] = EXECUTION_REQUIREMENTS

    audit_b_burden_outcomes_inspected_before_freeze: bool = False
    terminal_masking_outcomes_inspected_before_freeze: bool = False
    terminal_masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.contract_id, str) or not self.contract_id.strip():
            raise ValueError("contract_id must be nonempty")

        expected_sha = {
            "parent_preexecution_contract_sha256": PARENT_PREEXECUTION_CONTRACT_SHA256,
            "scientific_resolution_sha256": SCIENTIFIC_RESOLUTION_SHA256,
            "precision_rule_authority_sha256": PRECISION_RULE_AUTHORITY_SHA256,
            "phase_iv_sample_freeze_digest": PHASE_IV_SAMPLE_FREEZE_DIGEST,
            "phase_iv_sample_artifact_sha256": PHASE_IV_SAMPLE_ARTIFACT_SHA256,
            "full104_manifest_sha256": FULL104_MANIFEST_SHA256,
            "canonical_registry_sha256": CANONICAL_REGISTRY_SHA256,
            "heavy_artifact_sha256": HEAVY_ARTIFACT_SHA256,
            "heavy_qualification_receipt_sha256": HEAVY_QUALIFICATION_RECEIPT_SHA256,
            "rng_authority_sha256": RNG_AUTHORITY_SHA256,
            "mask_plan_generator_sha256": MASK_PLAN_GENERATOR_SHA256,
            "burden_estimator_source_sha256": BURDEN_ESTIMATOR_SOURCE_SHA256,
        }
        for name, expected in expected_sha.items():
            if _sha(getattr(self, name), name) != expected:
                raise ValueError(f"{name} drifted from the frozen B4 authority graph")

        expected_semantics = {
            "precision_scope_id": PRECISION_SCOPE_ID,
            "target_aggregation_id": PRIMARY_TARGET_AGGREGATION_ID,
            "mandatory_robustness_aggregation_id": MANDATORY_ROBUSTNESS_AGGREGATION_ID,
            "primary_policy_id": PRIMARY_POLICY_ID,
            "primary_rung_numerator": PRIMARY_RUNG.numerator,
            "primary_rung_denominator": PRIMARY_RUNG.denominator,
            "precision_estimator_id": PRECISION_ESTIMATOR_ID,
            "relative_se_tolerance_numerator": RELATIVE_SE_TOLERANCE.numerator,
            "relative_se_tolerance_denominator": RELATIVE_SE_TOLERANCE.denominator,
            "absolute_se_tolerance_numerator": ABSOLUTE_SE_TOLERANCE.numerator,
            "absolute_se_tolerance_denominator": ABSOLUTE_SE_TOLERANCE.denominator,
            "absolute_tolerance_origin_id": ABSOLUTE_TOLERANCE_ORIGIN_ID,
            "zero_mean_rule_id": ZERO_MEAN_RULE_ID,
            "reporting_scope_id": REPORTING_SCOPE_ID,
            "source_stratified_reporting_id": SOURCE_STRATIFIED_REPORTING_ID,
            "primary_metric_id": PRIMARY_METRIC_ID,
            "secondary_metric_id": SECONDARY_METRIC_ID,
            "normalization_id": NORMALIZATION_ID,
        }
        for name, expected in expected_semantics.items():
            if getattr(self, name) != expected:
                raise ValueError(f"{name} drifted from the signed B2 resolution")

        if tuple(self.sample_ladder) != SAMPLE_LADDER:
            raise ValueError("sample_ladder drifted")
        if tuple(self.execution_requirements) != EXECUTION_REQUIREMENTS:
            raise ValueError("execution_requirements drifted")

        for name in (
            "audit_b_burden_outcomes_inspected_before_freeze",
            "terminal_masking_outcomes_inspected_before_freeze",
            "terminal_masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    @property
    def execution_authorized(self) -> bool:
        self.validate()
        return True

    def require_execution_ready(self) -> None:
        self.validate()
        if self.execution_authorized is not True:
            raise ValueError("STOP_AUDIT_B_B4_EXECUTION_NOT_AUTHORIZED")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["sample_ladder"] = list(self.sample_ladder)
        payload["execution_requirements"] = list(self.execution_requirements)
        payload["execution_authorized"] = self.execution_authorized
        return _digest({"schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V2", **payload})
