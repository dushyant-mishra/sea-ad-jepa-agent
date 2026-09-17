"""Fail-closed remaining-RNA necessity rule for current V5 query-local state.

This module does not choose a production numerical threshold. Thresholds are explicit
inputs to the authority and therefore must be frozen prospectively elsewhere before a
production decision is made.

The decisive intervention keeps query identity and lawful global biological context
available while ablating the remaining RNA evidence. This permits legitimate global
context but rejects a target that can be solved from query identity/global context alone.
Expression reconstruction metrics are deliberately absent from the approved vocabulary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from statistics import median
from typing import Any, Mapping, Sequence, Tuple


APPROVED_PROTOCOL_IDS: Tuple[str, ...] = (
    "KEEP_QUERY_IDENTITY_AND_LAWFUL_GLOBAL_CONTEXT_FIXED__ABLATE_REMAINING_RNA_V1",
)
APPROVED_METRIC_IDS: Tuple[str, ...] = (
    "QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1",
    "QUERY_LOCAL_LATENT_STATE_COSINE_ERROR_V1",
)
APPROVED_IDENTITY_ONLY_COMPARATOR_IDS: Tuple[str, ...] = (
    "QUERY_IDENTITY_ONLY_V1",
)
APPROVED_GLOBAL_CONTEXT_NO_RNA_COMPARATOR_IDS: Tuple[str, ...] = (
    "QUERY_IDENTITY_PLUS_LAWFUL_GLOBAL_CONTEXT_NO_REMAINING_RNA_V1",
)
APPROVED_FAILURE_SEMANTICS_IDS: Tuple[str, ...] = (
    "FAIL_CLOSED_IF_REMAINING_RNA_NOT_NECESSARY_V1",
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


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RemainingRnaNecessityAuthorityV1:
    authority_id: str
    representation_authority_sha256: str
    support_estimability_authority_sha256: str
    target_address_provider_authority_sha256: str
    masking_authority_sha256: str
    precision_authority_sha256: str
    protocol_id: str
    metric_id: str
    min_median_advantage_numerator: int
    min_median_advantage_denominator: int
    min_win_fraction_numerator: int
    min_win_fraction_denominator: int
    identity_only_comparator_id: str
    global_context_no_rna_comparator_id: str
    failure_semantics_id: str
    training_authorized: bool = False

    @property
    def min_median_advantage(self) -> float:
        return self.min_median_advantage_numerator / self.min_median_advantage_denominator

    @property
    def min_win_fraction(self) -> float:
        return self.min_win_fraction_numerator / self.min_win_fraction_denominator

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        _sha(self.representation_authority_sha256, "representation_authority_sha256")
        _sha(self.support_estimability_authority_sha256, "support_estimability_authority_sha256")
        _sha(self.target_address_provider_authority_sha256, "target_address_provider_authority_sha256")
        _sha(self.masking_authority_sha256, "masking_authority_sha256")
        _sha(self.precision_authority_sha256, "precision_authority_sha256")

        _enum(self.protocol_id, APPROVED_PROTOCOL_IDS, "protocol_id")
        _enum(self.metric_id, APPROVED_METRIC_IDS, "metric_id")
        _enum(
            self.identity_only_comparator_id,
            APPROVED_IDENTITY_ONLY_COMPARATOR_IDS,
            "identity_only_comparator_id",
        )
        _enum(
            self.global_context_no_rna_comparator_id,
            APPROVED_GLOBAL_CONTEXT_NO_RNA_COMPARATOR_IDS,
            "global_context_no_rna_comparator_id",
        )
        _enum(self.failure_semantics_id, APPROVED_FAILURE_SEMANTICS_IDS, "failure_semantics_id")

        _nonnegative_int(
            self.min_median_advantage_numerator,
            "min_median_advantage_numerator",
        )
        _positive_int(
            self.min_median_advantage_denominator,
            "min_median_advantage_denominator",
        )
        win_num = _nonnegative_int(
            self.min_win_fraction_numerator,
            "min_win_fraction_numerator",
        )
        win_den = _positive_int(
            self.min_win_fraction_denominator,
            "min_win_fraction_denominator",
        )
        if win_num > win_den:
            raise ValueError("min_win_fraction must lie in the closed unit interval")

        if self.training_authorized is not False:
            raise ValueError("remaining-RNA necessity authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_sha(
            {
                "schema": "V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1",
                **asdict(self),
                "training_authorized": False,
            }
        )


def _finite_scores(values: Sequence[float], name: str) -> tuple[float, ...]:
    out: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must contain finite real numbers")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{name} must contain finite real numbers")
        out.append(numeric)
    return tuple(out)


def evaluate_remaining_rna_necessity_v1(
    authority: RemainingRnaNecessityAuthorityV1,
    *,
    full_remaining_rna_scores: Sequence[float],
    identity_only_scores: Sequence[float],
    global_context_no_rna_scores: Sequence[float],
) -> dict[str, Any]:
    """Evaluate paired query-local state evidence under a frozen decision rule.

    Inputs must be aligned evaluation units. Positive advantage is oriented to mean
    "remaining RNA helps" for both approved latent-state metric directions.
    Precision/sample-size sufficiency is intentionally delegated to the bound precision
    authority; this function only returns the observed unit count and the paired rule.
    """

    authority.validate()
    full = _finite_scores(full_remaining_rna_scores, "full_remaining_rna_scores")
    identity = _finite_scores(identity_only_scores, "identity_only_scores")
    global_no_rna = _finite_scores(
        global_context_no_rna_scores,
        "global_context_no_rna_scores",
    )

    if not full or len(full) != len(identity) or len(full) != len(global_no_rna):
        raise ValueError("score inputs must have the same nonzero length")

    if authority.metric_id == "QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1":
        identity_delta = tuple(a - b for a, b in zip(full, identity))
        global_delta = tuple(a - b for a, b in zip(full, global_no_rna))
    elif authority.metric_id == "QUERY_LOCAL_LATENT_STATE_COSINE_ERROR_V1":
        identity_delta = tuple(b - a for a, b in zip(full, identity))
        global_delta = tuple(b - a for a, b in zip(full, global_no_rna))
    else:  # validate() makes this unreachable; retain explicit fail-closed behavior.
        raise ValueError("metric_id has no approved direction")

    n = len(full)
    identity_median = float(median(identity_delta))
    global_median = float(median(global_delta))
    identity_win = sum(delta > 0 for delta in identity_delta) / n
    global_win = sum(delta > 0 for delta in global_delta) / n

    passed = (
        identity_median >= authority.min_median_advantage
        and global_median >= authority.min_median_advantage
        and identity_win >= authority.min_win_fraction
        and global_win >= authority.min_win_fraction
    )

    return {
        "schema": "V5_REMAINING_RNA_NECESSITY_EVALUATION_V1",
        "authority_sha256": authority.canonical_digest(),
        "metric_id": authority.metric_id,
        "n_units": n,
        "identity_only_median_advantage": identity_median,
        "global_context_no_rna_median_advantage": global_median,
        "identity_only_win_fraction": identity_win,
        "global_context_no_rna_win_fraction": global_win,
        "min_median_advantage": authority.min_median_advantage,
        "min_win_fraction": authority.min_win_fraction,
        "passed": passed,
        "training_authorized": False,
    }
