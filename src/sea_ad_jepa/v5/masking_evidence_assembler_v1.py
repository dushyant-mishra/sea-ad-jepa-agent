"""Assemble final masking decision evidence from raw donor-level artifacts.

No decision interval can be hand-entered through this module.  Every interval is
reconstructed from donor-level primary/control/nonlinear rows and evaluated by
the bound precision authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .masking_qualification_decision_v1 import (
    IntervalEvidenceV1,
    MaskingPolicyDecisionEvidenceV1,
    POLICIES,
)
from .masking_nonlinear_challenge_receipt_v1 import (
    NonlinearChallengeEvidenceV1,
    NonlinearChallengeReceiptV1,
    evaluate_nonlinear_challenge,
)
from .masking_structural_controls_v1 import (
    StructuralControlReceiptV1,
    build_structural_control_receipt,
)
from .precision_authority_v2 import source_balanced_mean


NONLINEAR_MODES = (
    "REAL",
    "SHUFFLED",
    "PLANTED_DETECT",
    "PLANTED_AFTER",
    "PLANTED_SHUFFLED_DETECT",
    "PLANTED_SHUFFLED_AFTER",
)


@dataclass(frozen=True)
class AssembledMaskingEvidenceV1:
    policy_evidence: Mapping[str, MaskingPolicyDecisionEvidenceV1]
    nonlinear_receipts: Mapping[str, NonlinearChallengeReceiptV1]
    structural_receipt: StructuralControlReceiptV1

    def validate(self) -> None:
        if set(self.policy_evidence) != set(POLICIES):
            raise ValueError("assembled primary evidence must cover every policy")
        if set(self.nonlinear_receipts) != set(POLICIES):
            raise ValueError("assembled nonlinear receipts must cover every policy")
        self.structural_receipt.validate()
        for policy in POLICIES:
            self.policy_evidence[policy].validate()
            self.nonlinear_receipts[policy].validate()


def _key(row: Mapping[str, Any]) -> tuple[int, str]:
    return (int(row["target_col"]), str(row["target_id"]))


def _target_order(primary_rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[int, str], ...]:
    pairs = sorted(
        {
            (int(row["target_index"]), _key(row))
            for row in primary_rows
            if row.get("method") == "UNIFORM_RANDOM"
        },
        key=lambda x: x[0],
    )
    if not pairs or [index for index, _ in pairs] != list(range(len(pairs))):
        raise ValueError("primary rows must contain contiguous target_index values")
    keys = tuple(key for _, key in pairs)
    if len(set(keys)) != len(keys):
        raise ValueError("target identity is not one-to-one")
    return keys


def _matrix_from_donor_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    target_order: Sequence[tuple[int, str]],
    donor_count: int,
    policy: str,
    donor_field: str,
    mode: str | None = None,
) -> np.ndarray:
    target_index = {key: i for i, key in enumerate(target_order)}
    matrix = np.full((len(target_order), donor_count), np.nan, dtype=np.float64)
    seen = np.zeros(matrix.shape, dtype=np.bool_)
    for row in rows:
        if str(row.get("method")) != policy:
            continue
        if mode is not None and str(row.get("mode")) != mode:
            continue
        key = _key(row)
        if key not in target_index:
            raise ValueError("control/nonlinear row references target outside primary panel")
        ti = target_index[key]
        for donor, value in row[donor_field]:
            d = int(donor)
            if d < 0 or d >= donor_count:
                raise ValueError("donor evidence is outside donor registry")
            if seen[ti, d]:
                raise ValueError(
                    f"duplicate donor evidence for policy={policy} target={key} donor={d}"
                )
            matrix[ti, d] = float(value)
            seen[ti, d] = True
    if not np.all(seen):
        missing = int((~seen).sum())
        raise ValueError(
            f"incomplete donor matrix for policy={policy} field={donor_field} mode={mode}: "
            f"{missing} target-donor units missing"
        )
    if np.any(~np.isfinite(matrix)):
        raise ValueError("donor matrix contains nonfinite values")
    return matrix


def _interval(precision: Any, matrix: np.ndarray, donor_source_code: np.ndarray, label: str) -> IntervalEvidenceV1:
    out = precision.interval(matrix, donor_source_code)
    precision.assert_interval_precise(out, label=label)
    return IntervalEvidenceV1(
        mean=float(out.mean),
        lower_two_sided=float(out.lower_two_sided),
        upper_two_sided=float(out.upper_two_sided),
        lower_one_sided=float(out.lower_one_sided),
        upper_one_sided=float(out.upper_one_sided),
    )


def _per_source_upper_bounds(
    precision: Any,
    matrix: np.ndarray,
    donor_source_code: np.ndarray,
    *,
    label: str,
) -> dict[str, float]:
    source = np.asarray(donor_source_code)
    out: dict[str, float] = {}
    for code in sorted(set(map(int, source))):
        ix = np.flatnonzero(source == code)
        local = precision.interval(matrix[:, ix], np.zeros(ix.size, dtype=np.int64))
        precision.assert_interval_precise(local, label=f"{label}:source={code}")
        out[str(code)] = float(local.upper_one_sided)
    return out


def _target_source_balanced_values(matrix: np.ndarray, donor_source_code: np.ndarray) -> np.ndarray:
    return np.asarray(
        [
            source_balanced_mean(matrix[index : index + 1], donor_source_code)
            for index in range(matrix.shape[0])
        ],
        dtype=np.float64,
    )


def _assert_roots(*values: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError("raw evidence artifact roots must be role-distinct")
    for value in values:
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("raw evidence artifact roots must be SHA-256 digests")


def assemble_masking_evidence(
    *,
    primary_rows: Sequence[Mapping[str, Any]],
    replay_primary_rows: Sequence[Mapping[str, Any]],
    negative_control_rows: Sequence[Mapping[str, Any]],
    planted_control_rows: Sequence[Mapping[str, Any]],
    nonlinear_rows: Sequence[Mapping[str, Any]],
    donor_source_code: np.ndarray,
    precision_authority: Any,
    nonlinear_authority_sha256: str,
    primary_artifact_sha256: str,
    control_artifact_sha256: str,
    nonlinear_artifact_sha256: str,
) -> AssembledMaskingEvidenceV1:
    precision_authority.validate()
    _assert_roots(
        nonlinear_authority_sha256,
        primary_artifact_sha256,
        control_artifact_sha256,
        nonlinear_artifact_sha256,
        precision_authority.canonical_digest(),
    )
    source = np.asarray(donor_source_code)
    if source.ndim != 1 or source.size == 0:
        raise ValueError("donor_source_code must be a nonempty vector")

    targets = _target_order(primary_rows)
    donor_count = int(source.size)
    precision_authority.assert_sufficient(
        target_count=len(targets),
        donor_count=donor_count,
        outer_fold_count=4,
    )
    structural = build_structural_control_receipt(primary_rows, replay_primary_rows)

    uniform_real = _matrix_from_donor_rows(
        primary_rows,
        target_order=targets,
        donor_count=donor_count,
        policy="UNIFORM_RANDOM",
        donor_field="heldout_donor_scores",
    )

    policy_evidence: dict[str, MaskingPolicyDecisionEvidenceV1] = {}
    nonlinear_receipts: dict[str, NonlinearChallengeReceiptV1] = {}

    for policy in POLICIES:
        real = _matrix_from_donor_rows(
            primary_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="heldout_donor_scores",
        )
        shuffled_uniform = _matrix_from_donor_rows(
            negative_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="uniform_donor_scores",
        )
        shuffled_policy = _matrix_from_donor_rows(
            negative_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="targeted_donor_scores",
        )
        planted_detect = _matrix_from_donor_rows(
            planted_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="detect_donor_scores",
        )
        planted_after = _matrix_from_donor_rows(
            planted_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="after_mask_donor_scores",
        )
        planted_shuffled_detect = _matrix_from_donor_rows(
            planted_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="shuffled_detect_donor_scores",
        )
        planted_shuffled_after = _matrix_from_donor_rows(
            planted_control_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="shuffled_after_mask_donor_scores",
        )

        delta = uniform_real - real
        residual = real - shuffled_policy
        negative_delta = shuffled_uniform - shuffled_policy
        planted_detect_excess = planted_detect - planted_shuffled_detect
        planted_after_excess = planted_after - planted_shuffled_after

        delta_interval = _interval(precision_authority, delta, source, f"{policy}:delta_vs_uniform")
        residual_interval = _interval(precision_authority, residual, source, f"{policy}:residual_vs_shuffled")
        negative_interval = _interval(precision_authority, negative_delta, source, f"{policy}:negative_delta")
        planted_detect_interval = _interval(
            precision_authority, planted_detect_excess, source, f"{policy}:planted_detect"
        )
        planted_after_interval = _interval(
            precision_authority, planted_after_excess, source, f"{policy}:planted_after"
        )

        nl_real = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="REAL",
        )
        nl_shuffled = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="SHUFFLED",
        )
        nl_plant_detect = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="PLANTED_DETECT",
        )
        nl_plant_after = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="PLANTED_AFTER",
        )
        nl_plant_shuf_detect = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="PLANTED_SHUFFLED_DETECT",
        )
        nl_plant_shuf_after = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy=policy,
            donor_field="donor_scores",
            mode="PLANTED_SHUFFLED_AFTER",
        )
        nl_uniform_shuffled = _matrix_from_donor_rows(
            nonlinear_rows,
            target_order=targets,
            donor_count=donor_count,
            policy="UNIFORM_RANDOM",
            donor_field="donor_scores",
            mode="SHUFFLED",
        )
        nl_negative = nl_uniform_shuffled - nl_shuffled
        nl_residual = nl_real - nl_shuffled
        nl_detect = nl_plant_detect - nl_plant_shuf_detect
        nl_after = nl_plant_after - nl_plant_shuf_after

        nl_negative_interval = _interval(
            precision_authority, nl_negative, source, f"{policy}:nonlinear_negative"
        )
        nl_residual_interval = _interval(
            precision_authority, nl_residual, source, f"{policy}:nonlinear_residual"
        )
        nl_detect_interval = _interval(
            precision_authority, nl_detect, source, f"{policy}:nonlinear_planted_detect"
        )
        nl_after_interval = _interval(
            precision_authority, nl_after, source, f"{policy}:nonlinear_planted_after"
        )

        nonlinear_receipt = evaluate_nonlinear_challenge(
            NonlinearChallengeEvidenceV1(
                policy_id=policy,
                burden_numerator=int(primary_rows[0]["burden_numerator"]),
                burden_denominator=int(primary_rows[0]["burden_denominator"]),
                nonlinear_authority_sha256=nonlinear_authority_sha256,
                raw_real_evidence_sha256=nonlinear_artifact_sha256,
                raw_shuffled_evidence_sha256=control_artifact_sha256,
                raw_planted_evidence_sha256=primary_artifact_sha256,
                negative_control_delta=nl_negative_interval,
                planted_detect_excess=nl_detect_interval,
                planted_after_mask_excess=nl_after_interval,
                real_excess_over_shuffled_null=nl_residual_interval,
            )
        )
        nonlinear_receipts[policy] = nonlinear_receipt

        target_delta = _target_source_balanced_values(delta, source)
        effective_values = [
            float(row["effective_targeted_n"])
            for row in primary_rows
            if row.get("method") == policy
        ]
        if not effective_values:
            raise ValueError(f"no primary rows found for policy {policy}")

        policy_evidence[policy] = MaskingPolicyDecisionEvidenceV1(
            policy_id=policy,
            burden_numerator=int(primary_rows[0]["burden_numerator"]),
            burden_denominator=int(primary_rows[0]["burden_denominator"]),
            raw_primary_evidence_sha256=primary_artifact_sha256,
            raw_control_evidence_sha256=control_artifact_sha256,
            raw_nonlinear_evidence_sha256=nonlinear_artifact_sha256,
            precision_authority_sha256=precision_authority.canonical_digest(),
            delta_vs_uniform=delta_interval,
            excess_over_shuffled_null=residual_interval,
            source_excess_upper_one_sided=_per_source_upper_bounds(
                precision_authority, residual, source, label=f"{policy}:residual"
            ),
            target_delta_median=float(np.median(target_delta)),
            worst_target_delta=float(np.min(target_delta)),
            mean_effective_targeted_n=float(np.mean(effective_values)),
            negative_control_delta=negative_interval,
            planted_detect_excess=planted_detect_interval,
            planted_after_mask_excess=planted_after_interval,
            nonlinear_excess_over_shuffled_null=nl_residual_interval,
            replay_exact=structural.replay_exact,
            untreated_identity_exact=structural.untreated_identity_exact,
            no_privileged_metadata=structural.no_privileged_metadata,
            precision_requirements_met=True,
        )

    result = AssembledMaskingEvidenceV1(
        policy_evidence=policy_evidence,
        nonlinear_receipts=nonlinear_receipts,
        structural_receipt=structural,
    )
    result.validate()
    return result
