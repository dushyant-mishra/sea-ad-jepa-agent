"""Re-authorized nonlinear FULL104 challenge for independent confirmation."""
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
ORIGIN_POLICY_ID = "DISCOVERY_NONLINEAR_CAPACITY_REAUTHORIZED_FOR_FULL104_CONFIRMATION_V1"
SEED_NAMESPACE = "V5_FULL104_NONLINEAR_ROOT_DERIVED_V2"

FEATURE_COUNT = 32
MAX_CELLS_PER_DONOR = 256
LEARNING_RATE_NUMERATOR = 1
LEARNING_RATE_DENOMINATOR = 10
MAX_ITER = 50
MAX_LEAF_NODES = 15
MIN_SAMPLES_LEAF = 20
L2_NUMERATOR = 1
L2_DENOMINATOR = 1
MAX_BINS = 255


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class NonlinearMaskingChallengeAuthorityV2:
    authority_id: str
    primary_parameters_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    historical_nonlinear_script_sha256: str
    historical_nonlinear_summary_sha256: str
    challenge_id: str = CHALLENGE_ID
    model_family_id: str = MODEL_FAMILY_ID
    sampling_policy_id: str = SAMPLING_POLICY_ID
    donor_weighting_policy_id: str = DONOR_WEIGHTING_POLICY_ID
    retuning_policy_id: str = RETUNING_POLICY_ID
    parameter_origin_policy_id: str = ORIGIN_POLICY_ID
    feature_count: int = FEATURE_COUNT
    max_cells_per_donor: int = MAX_CELLS_PER_DONOR
    learning_rate_numerator: int = LEARNING_RATE_NUMERATOR
    learning_rate_denominator: int = LEARNING_RATE_DENOMINATOR
    max_iter: int = MAX_ITER
    max_leaf_nodes: int = MAX_LEAF_NODES
    min_samples_leaf: int = MIN_SAMPLES_LEAF
    l2_regularization_numerator: int = L2_NUMERATOR
    l2_regularization_denominator: int = L2_DENOMINATOR
    max_bins: int = MAX_BINS
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

    @property
    def random_seed(self) -> int:
        self.validate()
        payload = {
            "schema": "V5_FULL104_NONLINEAR_ROOT_DERIVED_SEED_V2",
            "namespace": SEED_NAMESPACE,
            "primary_parameters_authority_sha256": self.primary_parameters_authority_sha256,
            "outer_split_authority_sha256": self.outer_split_authority_sha256,
            "target_panel_authority_sha256": self.target_panel_authority_sha256,
        }
        return int.from_bytes(hashlib.sha256(_canonical(payload)).digest()[:8], "big")

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        roots = (
            _sha(self.primary_parameters_authority_sha256, "primary_parameters_authority_sha256"),
            _sha(self.outer_split_authority_sha256, "outer_split_authority_sha256"),
            _sha(self.target_panel_authority_sha256, "target_panel_authority_sha256"),
            _sha(self.historical_nonlinear_script_sha256, "historical_nonlinear_script_sha256"),
            _sha(self.historical_nonlinear_summary_sha256, "historical_nonlinear_summary_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("nonlinear V2 roots must be role-distinct")
        expected_strings = {
            "challenge_id": CHALLENGE_ID,
            "model_family_id": MODEL_FAMILY_ID,
            "sampling_policy_id": SAMPLING_POLICY_ID,
            "donor_weighting_policy_id": DONOR_WEIGHTING_POLICY_ID,
            "retuning_policy_id": RETUNING_POLICY_ID,
            "parameter_origin_policy_id": ORIGIN_POLICY_ID,
        }
        for name, expected in expected_strings.items():
            if getattr(self, name) != expected:
                raise ValueError(f"{name} mismatch")
        expected_numeric = {
            "feature_count": FEATURE_COUNT,
            "max_cells_per_donor": MAX_CELLS_PER_DONOR,
            "learning_rate_numerator": LEARNING_RATE_NUMERATOR,
            "learning_rate_denominator": LEARNING_RATE_DENOMINATOR,
            "max_iter": MAX_ITER,
            "max_leaf_nodes": MAX_LEAF_NODES,
            "min_samples_leaf": MIN_SAMPLES_LEAF,
            "l2_regularization_numerator": L2_NUMERATOR,
            "l2_regularization_denominator": L2_DENOMINATOR,
            "max_bins": MAX_BINS,
        }
        for name, expected in expected_numeric.items():
            if getattr(self, name) != expected:
                raise ValueError(f"{name} must remain prospectively frozen at {expected}")
        if self.early_stopping is not False:
            raise ValueError("early_stopping must remain False")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("nonlinear V2 must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("nonlinear challenge cannot authorize training")

    def bind_primary_parameters(self, parameters: Any) -> None:
        self.validate()
        parameters.validate()
        if parameters.canonical_digest() != self.primary_parameters_authority_sha256:
            raise ValueError("primary parameter authority root mismatch")
        if int(parameters.ridge_score_feature_count) != FEATURE_COUNT:
            raise ValueError("primary attacker feature count must equal frozen nonlinear feature count")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema": "V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V2", **asdict(self), "random_seed": self.random_seed})
