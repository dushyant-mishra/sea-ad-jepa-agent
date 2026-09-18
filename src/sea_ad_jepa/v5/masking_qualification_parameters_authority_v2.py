"""Explicitly re-authorized FULL104 masking parameters for independent confirmation.

The values in this authority are not production defaults and are not inferred
from terminal FULL104 outcomes.  They are the exact discovery-defined candidate
that survived the pre-FULL104 800 -> 2,000 -> 6,000 scale stress and the
outside-original-800 target challenge.  Burden is intentionally excluded and
owned by the separate FULL104 census-derived burden ladder.
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


ORIGIN_POLICY_ID = "DISCOVERY_DEFINED_CANDIDATE_FROZEN_FOR_INDEPENDENT_FULL104_CONFIRMATION_V1"
CONFIRMATION_ROLE_ID = "FULL104_CONFIRMATION_WITHOUT_PARAMETER_RETUNING_V1"
BURDEN_SEPARATION_POLICY_ID = "BURDEN_OWNED_BY_FULL104_CENSUS_LADDER_V1"

EXPECTED = {
    "targeted_partner_cap": 8,
    "ridge_candidate_pool_count": 64,
    "ridge_score_feature_count": 32,
    "ridge_alpha_numerator": 1,
    "ridge_alpha_denominator": 100,
    "prefix_inner_fold_count": 3,
    "prefix_candidate_count": 20,
    "prefix_floor_numerator": 1,
    "prefix_floor_denominator": 20,
    "prefix_reduction_numerator": 1,
    "prefix_reduction_denominator": 2,
}


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
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class MaskingQualificationParametersAuthorityV2:
    authority_id: str
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
    terminal_full104_masking_outcomes_inspected: bool = False
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
            _sha(self.discovery_expanded_validation_report_sha256, "discovery_expanded_validation_report_sha256"),
            _sha(self.discovery_universe_scale_script_sha256, "discovery_universe_scale_script_sha256"),
            _sha(self.discovery_outside800_unified_script_sha256, "discovery_outside800_unified_script_sha256"),
            _sha(self.discovery_provenance_note_sha256, "discovery_provenance_note_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("discovery provenance roots must be distinct")
        if self.parameter_origin_policy_id != ORIGIN_POLICY_ID:
            raise ValueError("parameter_origin_policy_id mismatch")
        if self.confirmation_role_id != CONFIRMATION_ROLE_ID:
            raise ValueError("confirmation_role_id mismatch")
        if self.burden_separation_policy_id != BURDEN_SEPARATION_POLICY_ID:
            raise ValueError("burden_separation_policy_id mismatch")
        if self.terminal_full104_masking_outcomes_inspected is not False:
            raise ValueError("parameters must be frozen before terminal FULL104 masking outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification parameters cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({
            "schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2",
            **asdict(self),
            "terminal_full104_masking_outcomes_inspected": False,
            "training_authorized": False,
        })
