"""Recover the existing V5 base-training scientific estimand without widening old mechanics.

This module binds current V5 to the previously established reader-fit scientific
population target. It deliberately excludes proposal coefficients, presentation
horizons, packing geometry, model/rank authority, masking policy, optimizer
configuration, and EMA timescale. Those remain separate authorities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .base_training_estimand_authority_v1 import BaseTrainingEstimandAuthorityV1

EXPECTED_TARGET_AUTHORITY_SHA256 = "2dff2f86b4a46d90db6a26bba1cc999115e745c3206a95fc50eb4a6538d57d51"
EXPECTED_FULL_READER_REPLAY_SHA256 = "18e4199aabb90195945558a35b8278a5c4fba1b08810deb81a70abc4c18907f5"
EXPECTED_POPULATION_AUTHORITY_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
EXPECTED_SUPPORT_ESTIMABILITY_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
EXPECTED_SUPPORT_ELIGIBILITY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_ESTIMAND_ID = "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1"
EXPECTED_TARGET_PROBABILITY_FORMULA = "1/(D*n_d)"
EXPECTED_WEIGHT_NORMALIZATION_ID = "MEAN_OVER_DONORS__MEAN_OVER_ELIGIBLE_CELLS_WITHIN_DONOR"
EXPECTED_WEIGHT_UNIT_ID = "SCIENTIFIC_CELL_MASS"
EXPECTED_SOURCE_MASS_POLICY_ID = "SOURCE_IS_DOMAIN_AND_ROBUSTNESS_STRATUM__NOT_AUTOMATIC_OBJECTIVE_MASS"
EXPECTED_OPERATOR_MASS_POLICY_ID = "OPERATOR_DOES_NOT_SET_BASE_SCIENTIFIC_MASS"
EXPECTED_PROPOSAL_SEPARATION_POLICY_ID = "PROPOSAL_Q_MAY_DIFFER__EXACT_P_OVER_Q_CORRECTION_REQUIRED"


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
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
class RecoveredScientificWeightLawV1:
    authority_id: str
    source_scientific_target_authority_sha256: str
    source_full_reader_replay_sha256: str
    population_authority_sha256: str
    support_estimability_authority_sha256: str
    support_eligibility_authority_sha256: str
    estimand_id: str
    target_probability_formula: str
    weight_normalization_id: str
    weight_unit_id: str
    source_mass_policy_id: str
    operator_mass_policy_id: str
    proposal_separation_policy_id: str
    training_authorized: bool = False

    def validate(self) -> None:
        _nonempty(self.authority_id, "authority_id")
        for name in (
            "source_scientific_target_authority_sha256",
            "source_full_reader_replay_sha256",
            "population_authority_sha256",
            "support_estimability_authority_sha256",
            "support_eligibility_authority_sha256",
        ):
            _sha(getattr(self, name), name)
        for name in (
            "estimand_id",
            "target_probability_formula",
            "weight_normalization_id",
            "weight_unit_id",
            "source_mass_policy_id",
            "operator_mass_policy_id",
            "proposal_separation_policy_id",
        ):
            _nonempty(getattr(self, name), name)
        if self.training_authorized is not False:
            raise ValueError("recovered scientific weight law cannot authorize training")

    def validate_current_binding(self) -> None:
        self.validate()
        expected = {
            "source_scientific_target_authority_sha256": EXPECTED_TARGET_AUTHORITY_SHA256,
            "source_full_reader_replay_sha256": EXPECTED_FULL_READER_REPLAY_SHA256,
            "population_authority_sha256": EXPECTED_POPULATION_AUTHORITY_SHA256,
            "support_estimability_authority_sha256": EXPECTED_SUPPORT_ESTIMABILITY_SHA256,
            "support_eligibility_authority_sha256": EXPECTED_SUPPORT_ELIGIBILITY_SHA256,
            "estimand_id": EXPECTED_ESTIMAND_ID,
            "target_probability_formula": EXPECTED_TARGET_PROBABILITY_FORMULA,
            "weight_normalization_id": EXPECTED_WEIGHT_NORMALIZATION_ID,
            "weight_unit_id": EXPECTED_WEIGHT_UNIT_ID,
            "source_mass_policy_id": EXPECTED_SOURCE_MASS_POLICY_ID,
            "operator_mass_policy_id": EXPECTED_OPERATOR_MASS_POLICY_ID,
            "proposal_separation_policy_id": EXPECTED_PROPOSAL_SEPARATION_POLICY_ID,
        }
        mismatches = {
            name: {"expected": expected_value, "actual": getattr(self, name)}
            for name, expected_value in expected.items()
            if getattr(self, name) != expected_value
        }
        if mismatches:
            raise ValueError(f"current recovered estimand binding mismatch: {mismatches}")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_RECOVERED_SCIENTIFIC_WEIGHT_LAW_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )


def build_current_recovered_base_estimand_v1(
    weight_law: RecoveredScientificWeightLawV1,
) -> BaseTrainingEstimandAuthorityV1:
    weight_law.validate_current_binding()
    authority = BaseTrainingEstimandAuthorityV1(
        authority_id="CURRENT_V5_RECOVERED_BASE_TRAINING_ESTIMAND_V1",
        population_authority_sha256=weight_law.population_authority_sha256,
        support_estimability_authority_sha256=weight_law.support_estimability_authority_sha256,
        support_eligibility_authority_sha256=weight_law.support_eligibility_authority_sha256,
        estimand_id=weight_law.estimand_id,
        scientific_weight_artifact_sha256=weight_law.canonical_digest(),
        scientific_weight_schema_id="V5_RECOVERED_SCIENTIFIC_WEIGHT_LAW_V1",
        weight_normalization_id=weight_law.weight_normalization_id,
        weight_unit_id=weight_law.weight_unit_id,
        training_authorized=False,
    )
    authority.validate()
    return authority


def validate_current_recovered_base_estimand_v1(
    weight_law: RecoveredScientificWeightLawV1,
    authority: BaseTrainingEstimandAuthorityV1,
) -> None:
    weight_law.validate_current_binding()
    authority.validate()
    expected = build_current_recovered_base_estimand_v1(weight_law)
    if authority != expected:
        raise ValueError("base-training estimand does not match recovered current V5 authority")
