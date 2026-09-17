"""Prospective FULL104 masking-qualification design authority for current V5.

This schema binds *how masking candidates are to be qualified* before the
qualification outcomes are inspected. It does not select a production winner,
does not choose a numerical mask burden, and cannot authorize training or
protected-outcome access.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence, Tuple


APPROVED_SCIENTIFIC_SEMANTICS_IDS: Tuple[str, ...] = (
    "BIOLOGICAL_QUERY_LOCAL_STATE_NOT_SCALAR_EXPRESSION_V1",
)
APPROVED_EXPRESSION_ATTACKER_ROLE_IDS: Tuple[str, ...] = (
    "ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_JEPA_LOSS_V1",
)
APPROVED_POLICY_ARMS: Tuple[str, ...] = (
    "UNIFORM_RANDOM",
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
)
APPROVED_PRIMARY_ATTACKER_IDS: Tuple[str, ...] = (
    "RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
)
APPROVED_SECONDARY_ATTACKER_IDS: Tuple[str, ...] = (
    "NONLINEAR_TREE_ENSEMBLE_EXPRESSION_PROXY_CHALLENGE_V1",
)
APPROVED_PRIMARY_SCORE_IDS: Tuple[str, ...] = (
    "SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
)
APPROVED_PAIRED_ESTIMAND_IDS: Tuple[str, ...] = (
    "UNIFORM_MINUS_TARGETED_SCORE_AT_TARGET_X_OUTER_FOLD_V1",
)
REQUIRED_CONTROLS: Tuple[str, ...] = (
    "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1",
    "WITHIN_DONOR_SHUFFLED_NEGATIVE_CONTROL_V1",
    "UNTREATED_MASK_IDENTITY_CONTROL_V1",
    "DETERMINISTIC_REPLAY_CONTROL_V1",
    "NO_PRIVILEGED_METADATA_CONTROL_V1",
)
APPROVED_NONLINEAR_RETUNING_POLICY_IDS: Tuple[str, ...] = (
    "NONLINEAR_REPORTED_WITHOUT_POLICY_RETUNING_V1",
)
APPROVED_POOLED_MEAN_GUARDRAIL_IDS: Tuple[str, ...] = (
    "NO_HARMFUL_SIGN_REVERSAL_HIDDEN_BY_POOLED_MEAN_V1",
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _enum(value: object, approved: Tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in approved:
        raise ValueError(f"{name} must be one of the approved current values {approved!r}, got {value!r}")
    return value


def _exact_sequence(value: object, expected: Tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must exactly equal {expected!r}")
    normalized = tuple(value)
    if normalized != expected:
        raise ValueError(f"{name} must exactly equal {expected!r}")
    return normalized


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _live_digest(obj: Any, name: str) -> str:
    if getattr(obj, "training_authorized", False) is not False:
        raise ValueError(f"{name} unexpectedly authorizes training")
    obj.validate()
    return _sha(obj.canonical_digest(), f"{name} canonical digest")


@dataclass(frozen=True)
class MaskingQualificationDesignAuthorityV1:
    authority_id: str
    full104_substrate_sha256: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    canonical_registry_authority_sha256: str
    teacher_target_semantics_authority_sha256: str
    target_evidence_budget_authority_sha256: str
    precision_authority_sha256: str
    outer_split_authority_sha256: str
    target_panel_authority_sha256: str
    address_universe_ladder_authority_sha256: str
    rng_replay_authority_sha256: str
    qualification_runner_source_sha256: str
    scientific_semantics_id: str
    expression_attacker_role_id: str
    policy_arms: Sequence[str]
    primary_attacker_id: str
    secondary_attacker_id: str
    primary_score_id: str
    paired_estimand_id: str
    controls: Sequence[str]
    nonlinear_retuning_policy_id: str
    pooled_mean_guardrail_id: str
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        root_names = (
            "full104_substrate_sha256",
            "representation_authority_sha256",
            "support_estimability_authority_sha256",
            "canonical_registry_authority_sha256",
            "teacher_target_semantics_authority_sha256",
            "target_evidence_budget_authority_sha256",
            "precision_authority_sha256",
            "outer_split_authority_sha256",
            "target_panel_authority_sha256",
            "address_universe_ladder_authority_sha256",
            "rng_replay_authority_sha256",
            "qualification_runner_source_sha256",
        )
        roots = tuple(_sha(getattr(self, name), name) for name in root_names)
        if len(set(roots)) != len(roots):
            raise ValueError("masking qualification authority role roots must be distinct")

        _enum(self.scientific_semantics_id, APPROVED_SCIENTIFIC_SEMANTICS_IDS, "scientific_semantics_id")
        _enum(
            self.expression_attacker_role_id,
            APPROVED_EXPRESSION_ATTACKER_ROLE_IDS,
            "expression_attacker_role_id",
        )
        _exact_sequence(self.policy_arms, APPROVED_POLICY_ARMS, "policy_arms")
        _enum(self.primary_attacker_id, APPROVED_PRIMARY_ATTACKER_IDS, "primary_attacker_id")
        _enum(self.secondary_attacker_id, APPROVED_SECONDARY_ATTACKER_IDS, "secondary_attacker_id")
        _enum(self.primary_score_id, APPROVED_PRIMARY_SCORE_IDS, "primary_score_id")
        _enum(self.paired_estimand_id, APPROVED_PAIRED_ESTIMAND_IDS, "paired_estimand_id")
        _exact_sequence(self.controls, REQUIRED_CONTROLS, "controls")
        _enum(
            self.nonlinear_retuning_policy_id,
            APPROVED_NONLINEAR_RETUNING_POLICY_IDS,
            "nonlinear_retuning_policy_id",
        )
        _enum(
            self.pooled_mean_guardrail_id,
            APPROVED_POOLED_MEAN_GUARDRAIL_IDS,
            "pooled_mean_guardrail_id",
        )
        if self.protected_outcomes_authorized is not False:
            raise ValueError("masking qualification design cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("masking qualification design authority cannot authorize training")

    def bind_live_authorities(
        self,
        *,
        target_evidence_budget: Any,
        precision: Any,
        outer_split: Any,
        target_panel: Any,
        address_universe_ladder: Any,
        rng_replay: Any,
    ) -> None:
        """Require live authority objects to match their declared semantic roles."""
        self.validate()
        expected = {
            "target_evidence_budget": self.target_evidence_budget_authority_sha256,
            "precision": self.precision_authority_sha256,
            "outer_split": self.outer_split_authority_sha256,
            "target_panel": self.target_panel_authority_sha256,
            "address_universe_ladder": self.address_universe_ladder_authority_sha256,
            "rng_replay": self.rng_replay_authority_sha256,
        }
        observed = {
            "target_evidence_budget": _live_digest(target_evidence_budget, "target evidence budget"),
            "precision": _live_digest(precision, "precision"),
            "outer_split": _live_digest(outer_split, "outer split"),
            "target_panel": _live_digest(target_panel, "target panel"),
            "address_universe_ladder": _live_digest(address_universe_ladder, "address universe ladder"),
            "rng_replay": _live_digest(rng_replay, "rng replay"),
        }
        for role, expected_digest in expected.items():
            if observed[role] != expected_digest:
                label = role.replace("_", " ")
                raise ValueError(f"{label} authority root mismatch")

    def canonical_digest(self) -> str:
        self.validate()
        payload = {
            "schema": "V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1",
            **asdict(self),
            "policy_arms": list(_exact_sequence(self.policy_arms, APPROVED_POLICY_ARMS, "policy_arms")),
            "controls": list(_exact_sequence(self.controls, REQUIRED_CONTROLS, "controls")),
            "protected_outcomes_authorized": False,
            "training_authorized": False,
        }
        return _digest(payload)
