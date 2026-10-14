"""Fail-closed G8 contract after hostile real-data review.

V2 incorrectly treated repeated technical thinnings of one fixed real unit as
sufficient split-conformal calibration observations for a deciding quantity
that compares a full-count anchor to a thinned realization. External review did
not establish the exchangeability required for that claim.

V3 therefore separates two statements:
1. the observation operator can be mechanically repaired and qualified; and
2. human/reference G8 statistical generation remains blocked until a separate
   statistical estimand and exchangeability argument are prospectively frozen
   and independently qualified.

No typed token or draw count can self-authorize that missing statistical layer.
"""
from __future__ import annotations


class G8V3ContractError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_G8_REALIZATION_CONTRACT_V3"
REQUIRED_THINNING_SCHEMA = "JEPA_TD_REAL_MEASUREMENT_THINNING_V2"
BLOCKED_STATUS = "BLOCKED_G8_STATISTICAL_CONTRACT_NOT_QUALIFIED"
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def validate_statistical_claim(*, calibration_observation: str, deciding_quantity: str, claim: str) -> None:
    values = [calibration_observation, deciding_quantity, claim]
    if any(not isinstance(value, str) or not value for value in values):
        raise G8V3ContractError("statistical claim fields must be nonempty strings")

    if (
        calibration_observation == "REPEATED_RNG_THINNING_OF_FIXED_REAL_UNIT"
        and deciding_quantity == "FULL_COUNT_TO_THINNED_DISPLACEMENT"
        and claim == "SPLIT_CONFORMAL_PREDICTION_BOUND"
    ):
        raise G8V3ContractError(
            "exchangeability is not established between repeated thinning-pair calibration observations "
            "and the full-count-to-thinned deciding quantity"
        )

    raise G8V3ContractError(
        "no G8 statistical claim is currently qualified for human/reference generation"
    )


def reference_generation_readiness(
    *,
    observation_thinning_schema: str,
    exact_input_bound: bool,
    metric_contract_bound: bool,
    support_contract_bound: bool,
    technical_draws_available: int,
) -> dict:
    if observation_thinning_schema != REQUIRED_THINNING_SCHEMA:
        raise G8V3ContractError("G8 requires the repaired observation-aware thinning schema")
    for value, label in (
        (exact_input_bound, "exact_input_bound"),
        (metric_contract_bound, "metric_contract_bound"),
        (support_contract_bound, "support_contract_bound"),
    ):
        if value is not True:
            raise G8V3ContractError(f"{label} must be true before statistical qualification can be considered")
    if isinstance(technical_draws_available, bool) or not isinstance(technical_draws_available, int):
        raise G8V3ContractError("technical_draws_available must be an integer")
    if technical_draws_available < 0:
        raise G8V3ContractError("technical_draws_available must be nonnegative")

    return {
        "schema": SCHEMA,
        "status": BLOCKED_STATUS,
        "observation_operator_ready": True,
        "reference_generation_authorized": False,
        "human_g8_adjudication_authorized": False,
        "technical_draws_available": technical_draws_available,
        "technical_draws_increase_biological_n": False,
        "biological_replication_unit": "DONOR",
        "blocking_reason": (
            "NO_PROSPECTIVELY_FROZEN_AND_INDEPENDENTLY_QUALIFIED_STATISTICAL_ESTIMAND_OR_"
            "EXCHANGEABILITY_ARGUMENT_FOR_FULL_COUNT_TO_THINNED_G8_DECISION"
        ),
        "supersedes_v2_execution_status": "READY_FOR_OUTCOME_BLIND_G8_REFERENCE_GENERATION_ONLY",
        "authority": dict(NO_AUTHORITY),
    }
