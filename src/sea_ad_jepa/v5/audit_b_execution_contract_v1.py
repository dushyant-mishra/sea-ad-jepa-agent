"""Prospective execution contract for FULL104 Audit B.

The Phase-IV target-sample freeze (c2c5e1b5...) is immutable and remains the
authority for WHICH targets may be opened at N1/N2/N3. Its original digest does
not cover all scientific execution semantics, however. This successor contract
binds those semantics separately BEFORE any Audit-B burden result is opened.

Nothing in this module authorizes terminal masking or training.

Most importantly, precision scope is explicit. Until an outcome-blind scientific
review resolves what "RSE of the primary burden statistic" means, the only lawful
state is UNRESOLVED and execution is forbidden.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

PHASE_IV_SAMPLE_FREEZE_DIGEST = (
    "c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac"
)
HEAVY_ARTIFACT_SHA256 = (
    "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
)
FULL104_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
CANONICAL_REGISTRY_SHA256 = (
    "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
)
MASK_PLAN_GENERATOR_SHA256 = (
    "fdc0cec140132b71fd0c01af5ec97c323bac091055191754dfcf81111ee6441e"
)

PRIMARY_METRIC_ID = "B2_HELDOUT_DETECTED_TOKEN_BURDEN"
SECONDARY_METRIC_ID = "B3_HELDOUT_RAW_UMI_BURDEN__DESCRIPTIVE_ONLY"
NORMALIZATION_ID = "ADDED_MINUS_DROPPED_OVER_UNIFORM_FULL_MASK_WITH_TARGET_V1"
TARGET_AGGREGATION_ID = (
    "SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1"
)
PRECISION_ESTIMATOR_ID = "TARGET_SAMPLE_SD_OVER_SQRT_N__RELATIVE_TO_ABS_MEAN_V1"

PHASE_IV_SAMPLE_SCHEMA_ID = "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1"
HEAVY_QUALIFICATION_SCHEMA_ID = "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2"
HEAVY_QUALIFICATION_VERDICT_ID = "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE"
RNG_AUTHORITY_SCHEMA_ID = "V5_MASKING_RNG_REPLAY_AUTHORITY_V3"
RNG_TARGET_PANEL_DEPENDENCY_ID = "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"

PRECISION_SCOPE_UNRESOLVED = "UNRESOLVED__EXECUTION_FORBIDDEN"
PRECISION_SCOPE_SINGLE_PRIMARY = "ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1"
PRECISION_SCOPE_ALL_POLICY_RUNG = "ALL_3_NONUNIFORM_X_6_RUNG_CELLS_V1"
ALLOWED_PRECISION_SCOPES = (
    PRECISION_SCOPE_UNRESOLVED,
    PRECISION_SCOPE_SINGLE_PRIMARY,
    PRECISION_SCOPE_ALL_POLICY_RUNG,
)

SAMPLE_LADDER = (256, 1024, 4096)
MAX_RELATIVE_STANDARD_ERROR = 0.05

EXECUTION_REQUIREMENTS = (
    "policy construction uses TRAINING-side information only",
    "burden measured on held-out donors only",
    "each donor contributes through its authenticated held-out fold only",
    "reported by source x donor x fold, never only pooled",
    "donors equal-weighted within source",
    "sources equal-weighted within target",
    "targets equal-weighted across the frozen target sample",
    "NO policy adaptation from observed burden",
    "no held-out realized zero/nonzero state may influence mask choice",
    "B3 raw-UMI burden is descriptive only and cannot drive escalation",
    "sample escalation depends on precision only",
    "N1 is a prefix of N2 and N2 is a prefix of N3",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class AuditBExecutionContractV1:
    contract_id: str
    phase_iv_sample_freeze_digest: str
    phase_iv_sample_artifact_sha256: str
    full104_manifest_sha256: str
    canonical_registry_sha256: str
    heavy_artifact_sha256: str
    heavy_qualification_receipt_sha256: str
    rng_authority_sha256: str
    mask_plan_generator_sha256: str
    burden_estimator_source_sha256: str
    phase_iv_sample_schema_id: str = PHASE_IV_SAMPLE_SCHEMA_ID
    heavy_qualification_schema_id: str = HEAVY_QUALIFICATION_SCHEMA_ID
    heavy_qualification_verdict_id: str = HEAVY_QUALIFICATION_VERDICT_ID
    rng_authority_schema_id: str = RNG_AUTHORITY_SCHEMA_ID
    rng_target_panel_dependency_id: str = RNG_TARGET_PANEL_DEPENDENCY_ID
    precision_scope_id: str = PRECISION_SCOPE_UNRESOLVED
    primary_metric_id: str = PRIMARY_METRIC_ID
    secondary_metric_id: str = SECONDARY_METRIC_ID
    normalization_id: str = NORMALIZATION_ID
    target_aggregation_id: str = TARGET_AGGREGATION_ID
    precision_estimator_id: str = PRECISION_ESTIMATOR_ID
    max_relative_standard_error: float = MAX_RELATIVE_STANDARD_ERROR
    sample_ladder: Tuple[int, int, int] = SAMPLE_LADDER
    execution_requirements: Tuple[str, ...] = EXECUTION_REQUIREMENTS
    terminal_masking_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.contract_id, str) or not self.contract_id.strip():
            raise ValueError("contract_id must be nonempty")
        if (
            _sha(self.phase_iv_sample_freeze_digest, "phase_iv_sample_freeze_digest")
            != PHASE_IV_SAMPLE_FREEZE_DIGEST
        ):
            raise ValueError("execution contract binds a different Phase-IV sample freeze")
        _sha(self.phase_iv_sample_artifact_sha256, "phase_iv_sample_artifact_sha256")
        if _sha(self.full104_manifest_sha256, "full104_manifest_sha256") != FULL104_MANIFEST_SHA256:
            raise ValueError("execution contract binds a different FULL104 manifest")
        if _sha(self.canonical_registry_sha256, "canonical_registry_sha256") != CANONICAL_REGISTRY_SHA256:
            raise ValueError("execution contract binds a different canonical registry")
        if _sha(self.heavy_artifact_sha256, "heavy_artifact_sha256") != HEAVY_ARTIFACT_SHA256:
            raise ValueError("execution contract binds a different heavy artifact")
        _sha(self.heavy_qualification_receipt_sha256, "heavy_qualification_receipt_sha256")
        _sha(self.rng_authority_sha256, "rng_authority_sha256")
        if _sha(self.mask_plan_generator_sha256, "mask_plan_generator_sha256") != MASK_PLAN_GENERATOR_SHA256:
            raise ValueError("execution contract binds a different frozen mask-plan generator")
        _sha(self.burden_estimator_source_sha256, "burden_estimator_source_sha256")

        roots = (
            self.phase_iv_sample_artifact_sha256,
            self.full104_manifest_sha256,
            self.canonical_registry_sha256,
            self.heavy_artifact_sha256,
            self.heavy_qualification_receipt_sha256,
            self.rng_authority_sha256,
            self.mask_plan_generator_sha256,
            self.burden_estimator_source_sha256,
        )
        if len(set(roots)) != len(roots):
            raise ValueError("execution-contract hashes must remain role-distinct")

        if self.phase_iv_sample_schema_id != PHASE_IV_SAMPLE_SCHEMA_ID:
            raise ValueError("Phase-IV sample schema drifted")
        if self.heavy_qualification_schema_id != HEAVY_QUALIFICATION_SCHEMA_ID:
            raise ValueError("heavy qualification schema drifted")
        if self.heavy_qualification_verdict_id != HEAVY_QUALIFICATION_VERDICT_ID:
            raise ValueError("heavy qualification verdict drifted")
        if self.rng_authority_schema_id != RNG_AUTHORITY_SCHEMA_ID:
            raise ValueError("RNG authority schema drifted")
        if self.rng_target_panel_dependency_id != RNG_TARGET_PANEL_DEPENDENCY_ID:
            raise ValueError("RNG target-panel dependency drifted")
        if self.precision_scope_id not in ALLOWED_PRECISION_SCOPES:
            raise ValueError("unknown precision_scope_id")
        if self.primary_metric_id != PRIMARY_METRIC_ID:
            raise ValueError("primary burden metric drifted")
        if self.secondary_metric_id != SECONDARY_METRIC_ID:
            raise ValueError("secondary burden metric drifted")
        if self.normalization_id != NORMALIZATION_ID:
            raise ValueError("burden normalization drifted")
        if self.target_aggregation_id != TARGET_AGGREGATION_ID:
            raise ValueError("target aggregation drifted")
        if self.precision_estimator_id != PRECISION_ESTIMATOR_ID:
            raise ValueError("precision estimator drifted")
        if self.max_relative_standard_error != MAX_RELATIVE_STANDARD_ERROR:
            raise ValueError("relative-standard-error threshold drifted")
        if tuple(self.sample_ladder) != SAMPLE_LADDER:
            raise ValueError("sample ladder drifted")
        if tuple(self.execution_requirements) != EXECUTION_REQUIREMENTS:
            raise ValueError("execution requirements drifted")
        if self.terminal_masking_outcomes_inspected_before_freeze is not False:
            raise ValueError("execution contract must freeze before Audit-B/terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("Audit-B execution contract cannot authorize training")

    @property
    def execution_authorized(self) -> bool:
        """V1 is a pre-execution binding contract and can NEVER authorize N1.

        A reviewed scientific decision about precision scope/weighting must be
        represented by a successor contract, not activated by changing one V1 field.
        """
        self.validate()
        return False

    def require_execution_ready(self) -> None:
        self.validate()
        raise ValueError(
            "STOP_AUDIT_B_V1_PREEXECUTION_ONLY: V1 intentionally cannot authorize "
            "Phase-IV N1. A successor execution contract is required after outcome-blind "
            "scientific review resolves precision scope and weighting."
        )

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["sample_ladder"] = list(self.sample_ladder)
        payload["execution_requirements"] = list(self.execution_requirements)
        payload["execution_authorized"] = self.execution_authorized
        return _digest({"schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V1", **payload})
