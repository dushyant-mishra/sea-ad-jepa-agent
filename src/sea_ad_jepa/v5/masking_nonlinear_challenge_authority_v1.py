"""Prospective nonlinear challenge authority for FULL104 masking."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

CHALLENGE_ID = "NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1"
MODEL_FAMILY_ID = "HIST_GRADIENT_BOOSTING_REGRESSOR_EXPLICIT_V1"
SAMPLING_POLICY_ID = "DETERMINISTIC_HASH_BOTTOM_K_PER_DONOR_V1"
DONOR_WEIGHTING_POLICY_ID = "EQUAL_TOTAL_WEIGHT_PER_DONOR_V1"
RETUNING_POLICY_ID = "NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class NonlinearMaskingChallengeAuthorityV1:
    authority_id: str
    primary_parameters_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    challenge_id: str
    model_family_id: str
    sampling_policy_id: str
    donor_weighting_policy_id: str
    retuning_policy_id: str
    feature_count: int
    max_cells_per_donor: int
    learning_rate_numerator: int
    learning_rate_denominator: int
    max_iter: int
    max_leaf_nodes: int
    min_samples_leaf: int
    l2_regularization_numerator: int
    l2_regularization_denominator: int
    max_bins: int
    random_seed: int
    early_stopping: bool = False
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    @property
    def learning_rate(self) -> float:
        self.validate()
        return self.learning_rate_numerator / self.learning_rate_denominator

    @property
    def l2_regularization(self) -> float:
        self.validate()
        return self.l2_regularization_numerator / self.l2_regularization_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.primary_parameters_authority_sha256, "primary_parameters_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("nonlinear authority roots must be role-distinct")
        if self.challenge_id != CHALLENGE_ID:
            raise ValueError("challenge_id mismatch")
        if self.model_family_id != MODEL_FAMILY_ID:
            raise ValueError("model_family_id mismatch")
        if self.sampling_policy_id != SAMPLING_POLICY_ID:
            raise ValueError("sampling_policy_id mismatch")
        if self.donor_weighting_policy_id != DONOR_WEIGHTING_POLICY_ID:
            raise ValueError("donor_weighting_policy_id mismatch")
        if self.retuning_policy_id != RETUNING_POLICY_ID:
            raise ValueError("retuning_policy_id mismatch")

        for name in ("feature_count", "max_cells_per_donor", "learning_rate_numerator",
                     "learning_rate_denominator", "max_iter", "max_leaf_nodes",
                     "min_samples_leaf", "l2_regularization_denominator", "max_bins"):
            _positive_int(getattr(self, name), name)
        _nonnegative_int(self.l2_regularization_numerator, "l2_regularization_numerator")
        _nonnegative_int(self.random_seed, "random_seed")
        if self.max_bins > 255:
            raise ValueError("max_bins must be <= 255")
        if self.early_stopping is not False:
            raise ValueError("early stopping must be disabled")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("nonlinear challenge must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("nonlinear challenge cannot authorize training")

    def bind_primary_parameters(self, parameters: Any) -> None:
        self.validate()
        parameters.validate()
        if parameters.canonical_digest() != self.primary_parameters_authority_sha256:
            raise ValueError("primary parameter authority root mismatch")
        if int(parameters.ridge_score_feature_count) != int(self.feature_count):
            raise ValueError("nonlinear feature_count must equal frozen primary score feature count")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V1", **asdict(self)})
