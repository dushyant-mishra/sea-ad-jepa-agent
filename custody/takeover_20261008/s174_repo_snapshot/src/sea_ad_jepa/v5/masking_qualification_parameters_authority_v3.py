"""FULL104-bound successor for masking confirmation parameters.

V3 preserves the exact discovery-defined parameter tuple as a confirmation
hypothesis, but historical artifacts are provenance-only.  The authority is not
valid unless it is bound to the authenticated current FULL104 substrate and
current support semantics.  It does not claim that the 32-feature attacker is
capacity-matched to the eventual production JEPA.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from .masking_qualification_parameters_authority_v2 import EXPECTED

FULL104_SUBSTRATE_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
SUPPORT_ESTIMABILITY_AUTHORITY_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
TERMINAL_UNIVERSE_ID = "FULL_COMMON_CORE_17186_V1"
TERMINAL_UNIVERSE_SIZE = 17186

ORIGIN_POLICY_ID = (
    "DISCOVERY_DEFINED_CANDIDATE_REAUTHORIZED_ONLY_ON_BOUND_FULL104_SUBSTRATE_V2"
)
CONFIRMATION_ROLE_ID = (
    "FULL104_CONFIRMATION_CONDITIONAL_ON_CURRENT_32_FEATURE_ATTACKER_CLASS_V2"
)
BURDEN_SEPARATION_POLICY_ID = "BURDEN_OWNED_BY_FULL104_CENSUS_LADDER_V1"
HISTORICAL_PROVENANCE_ROLE_ID = (
    "DISCOVERY_PARAMETER_PROVENANCE_SUPPORTING_ONLY__NO_FULL104_DATA_TARGET_FOLD_"
    "BURDEN_SEED_ROW_CAP_POLICY_PASS_RUNTIME_OR_TRAINING_AUTHORITY_V1"
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
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationParametersAuthorityV3:
    authority_id: str
    full104_substrate_sha256: str
    support_estimability_authority_sha256: str
    terminal_universe_id: str
    terminal_universe_size: int

    primary_attacker_id: str
    primary_score_id: str
    targeted_partner_cap: int
    ridge_candidate_pool_count: int
    ridge_score_feature_count: int
    ridge_alpha_numerator: int
    ridge_alpha_denominator: int
    prefix_inner_fold_count: int
    prefix_candidate_count: int
    prefix_floor_numerator: int
    prefix_floor_denominator: int
    prefix_reduction_numerator: int
    prefix_reduction_denominator: int

    discovery_expanded_validation_report_sha256: str
    discovery_universe_scale_script_sha256: str
    discovery_outside800_unified_script_sha256: str
    discovery_provenance_note_sha256: str

    parameter_origin_policy_id: str
    confirmation_role_id: str
    burden_separation_policy_id: str
    historical_provenance_role_id: str
    terminal_full104_masking_outcomes_inspected: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    @property
    def ridge_alpha(self) -> float:
        self.validate()
        return self.ridge_alpha_numerator / self.ridge_alpha_denominator

    @property
    def prefix_floor(self) -> float:
        self.validate()
        return self.prefix_floor_numerator / self.prefix_floor_denominator

    @property
    def prefix_reduction(self) -> float:
        self.validate()
        return self.prefix_reduction_numerator / self.prefix_reduction_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if _sha(self.full104_substrate_sha256, "full104_substrate_sha256") != FULL104_SUBSTRATE_SHA256:
            raise ValueError("parameter authority binds a different FULL104 substrate")
        if (
            _sha(
                self.support_estimability_authority_sha256,
                "support_estimability_authority_sha256",
            )
            != SUPPORT_ESTIMABILITY_AUTHORITY_SHA256
        ):
            raise ValueError("parameter authority binds a different support authority")
        if self.terminal_universe_id != TERMINAL_UNIVERSE_ID:
            raise ValueError("terminal_universe_id mismatch")
        if self.terminal_universe_size != TERMINAL_UNIVERSE_SIZE:
            raise ValueError("terminal_universe_size mismatch")

        if self.primary_attacker_id != PRIMARY_ATTACKER_ID:
            raise ValueError(f"primary_attacker_id must equal {PRIMARY_ATTACKER_ID}")
        if self.primary_score_id != PRIMARY_SCORE_ID:
            raise ValueError(f"primary_score_id must equal {PRIMARY_SCORE_ID}")

        for field, expected in EXPECTED.items():
            observed = getattr(self, field)
            if observed != expected:
                raise ValueError(
                    f"{field} must equal the prospectively re-authorized discovery-defined "
                    f"confirmation value {expected}; observed {observed!r}"
                )

        roots = (
            _sha(
                self.discovery_expanded_validation_report_sha256,
                "discovery_expanded_validation_report_sha256",
            ),
            _sha(
                self.discovery_universe_scale_script_sha256,
                "discovery_universe_scale_script_sha256",
            ),
            _sha(
                self.discovery_outside800_unified_script_sha256,
                "discovery_outside800_unified_script_sha256",
            ),
            _sha(
                self.discovery_provenance_note_sha256,
                "discovery_provenance_note_sha256",
            ),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("discovery provenance roots must be distinct")
        if self.full104_substrate_sha256 in roots or self.support_estimability_authority_sha256 in roots:
            raise ValueError("historical provenance roots cannot occupy current FULL104 authority roles")

        if self.parameter_origin_policy_id != ORIGIN_POLICY_ID:
            raise ValueError("parameter_origin_policy_id mismatch")
        if self.confirmation_role_id != CONFIRMATION_ROLE_ID:
            raise ValueError("confirmation_role_id mismatch")
        if self.burden_separation_policy_id != BURDEN_SEPARATION_POLICY_ID:
            raise ValueError("burden_separation_policy_id mismatch")
        if self.historical_provenance_role_id != HISTORICAL_PROVENANCE_ROLE_ID:
            raise ValueError("historical_provenance_role_id mismatch")
        if self.terminal_full104_masking_outcomes_inspected is not False:
            raise ValueError("parameters must be frozen before terminal FULL104 masking outcomes")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("parameter authority cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification parameters cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3",
                **asdict(self),
                "terminal_full104_masking_outcomes_inspected": False,
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            }
        )
