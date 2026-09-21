"""Production-aligned Audit-B burden estimator primitives.

This module defines the estimator BEFORE the frozen N1 target sample is
executed. It consumes mask geometry and held-out donor x strict-core burden
statistics only; it never computes a masking prediction score.

Primary quantity
----------------
For each sampled target, donor, policy and burden rung:

    normalized_delta_B2 =
        [B2(addresses ADDED by policy) - B2(addresses DROPPED)]
        / B2(UNIFORM_RANDOM full mask at the same target/fold/rung)

where B2 is detected-token burden on that donor's held-out cells. The target
address is included in the uniform denominator because it is masked in every arm.

Per-target aggregation is source-balanced and donor-uniform within source across
all 104 donors, each evaluated only in its own held-out fold. Targets are then
weighted equally.

Precision primitives are implemented prospectively, but the scientific scope of
the escalation rule is intentionally UNRESOLVED. The original Phase-IV freeze did
not determine whether one predeclared policy x rung cell or all 18 non-uniform
policy x rung cells control sample-size escalation, nor how an undefined zero-mean
RSE should affect the ladder. Consequently this module may compute descriptive
precision summaries, but a zero-mean RSE causes escalation_decision() to STOP
rather than choose N2/N3. The preexecution V1 contract cannot authorize N1.

B3 raw-UMI burden is carried as a secondary descriptive metric and can never
drive escalation.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

POLICIES = (
    "UNIFORM_RANDOM",
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
)
NONUNIFORM_POLICIES = POLICIES[1:]
BURDEN_RUNGS = (
    Fraction(1, 20),
    Fraction(1, 10),
    Fraction(3, 20),
    Fraction(1, 5),
    Fraction(3, 10),
    Fraction(1, 2),
)
MAX_RELATIVE_STANDARD_ERROR = 0.05

PRIMARY_METRIC_ID = "B2_HELDOUT_DETECTED_TOKEN_BURDEN"
SECONDARY_METRIC_ID = "B3_HELDOUT_RAW_UMI_BURDEN__DESCRIPTIVE_ONLY"
NORMALIZATION_ID = "ADDED_MINUS_DROPPED_OVER_UNIFORM_FULL_MASK_WITH_TARGET_V1"
TARGET_AGGREGATION_ID = "SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1"
PRECISION_ID = "TARGET_SAMPLE_SD_OVER_SQRT_N__RELATIVE_TO_ABS_MEAN_V1"
ESCALATION_ID = "CANDIDATE_MAX_RSE_ACROSS_ALL_NONUNIFORM_POLICY_X_RUNG_CELLS_V1"
SCIENTIFIC_EXECUTION_SCOPE_STATE = "UNRESOLVED__PREEXECUTION_ONLY"


@dataclass(frozen=True)
class DonorBurdenObservationV1:
    target_col: int
    fold_index: int
    donor_code: int
    source_code: int
    policy_id: str
    rung_numerator: int
    rung_denominator: int
    uniform_detected_burden: float
    delta_detected_burden: float
    normalized_delta_detected: float
    uniform_umi_burden: float
    delta_umi_burden: float
    normalized_delta_umi: float


@dataclass(frozen=True)
class PrecisionSummaryV1:
    policy_id: str
    rung_numerator: int
    rung_denominator: int
    n_targets: int
    mean_normalized_delta_detected: float
    target_sample_sd: float
    standard_error: float
    relative_standard_error: float | None
    relative_standard_error_state: str
    precision_passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "rung_numerator": self.rung_numerator,
            "rung_denominator": self.rung_denominator,
            "n_targets": self.n_targets,
            "mean_normalized_delta_detected": self.mean_normalized_delta_detected,
            "target_sample_sd": self.target_sample_sd,
            "standard_error": self.standard_error,
            "relative_standard_error": self.relative_standard_error,
            "relative_standard_error_state": self.relative_standard_error_state,
            "precision_passed": self.precision_passed,
        }


def _as_burden_matrix(value: Any, name: str) -> np.ndarray:
    x = np.asarray(value, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 1 or x.shape[1] < 2:
        raise ValueError(f"{name} must be donor x address with >=1 donor and >=2 addresses")
    if not np.all(np.isfinite(x)) or np.any(x < 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return x


def _mask_positions(mask: Iterable[int], position_by_address: Mapping[int, int]) -> np.ndarray:
    cols = sorted({int(x) for x in mask})
    if not cols:
        raise ValueError("mask must be nonempty")
    missing = [c for c in cols if c not in position_by_address]
    if missing:
        raise ValueError(f"mask contains addresses outside strict core: {missing[:5]}")
    return np.asarray([position_by_address[c] for c in cols], dtype=np.int64)


def measure_plan_burden(
    *,
    target_col: int,
    fold_index: int,
    plans: Mapping[str, Mapping[str, Any]],
    heldout_donors: Sequence[int],
    fold_by_donor: Sequence[int],
    donor_source_code: Sequence[int],
    core_addresses: Sequence[int],
    donor_nnz: Any,
    donor_umi: Any,
    rung: Fraction,
) -> tuple[DonorBurdenObservationV1, ...]:
    """Measure exact held-out burden for one target x fold x rung plan."""
    nnz = _as_burden_matrix(donor_nnz, "donor_nnz")
    umi = _as_burden_matrix(donor_umi, "donor_umi")
    if umi.shape != nnz.shape:
        raise ValueError("donor_umi must align donor_nnz")
    core = np.asarray(core_addresses, dtype=np.int64)
    if core.ndim != 1 or core.size != nnz.shape[1] or np.unique(core).size != core.size:
        raise ValueError("core_addresses must uniquely align burden columns")
    source = np.asarray(donor_source_code, dtype=np.int64)
    if source.ndim != 1 or source.size != nnz.shape[0] or source.min() < 0:
        raise ValueError("donor_source_code must align burden donors")
    donors = np.asarray(heldout_donors, dtype=np.int64)
    if donors.ndim != 1 or donors.size == 0 or donors.min() < 0 or donors.max() >= nnz.shape[0]:
        raise ValueError("heldout_donors must be valid nonempty donor codes")
    if np.unique(donors).size != donors.size:
        raise ValueError("heldout_donors must not contain duplicates")
    folds = np.asarray(fold_by_donor, dtype=np.int64)
    if folds.ndim != 1 or folds.size != nnz.shape[0]:
        raise ValueError("fold_by_donor must align burden donors")
    if np.any(folds < 0) or np.any(folds >= 4):
        raise ValueError("fold_by_donor must contain only authenticated fold codes 0..3")
    if int(fold_index) < 0 or int(fold_index) >= 4:
        raise ValueError("fold_index must be one of the four authenticated folds: 0..3")
    expected_heldout = np.flatnonzero(folds == int(fold_index)).astype(np.int64)
    if expected_heldout.size == 0:
        raise ValueError(f"authenticated fold {int(fold_index)} has no held-out donors")
    if not np.array_equal(np.sort(donors), expected_heldout):
        raise ValueError(
            "heldout_donors do not exactly match authenticated fold membership: "
            f"fold={int(fold_index)} expected={expected_heldout.tolist()} "
            f"observed={np.sort(donors).tolist()}"
        )
    if set(POLICIES) - set(plans):
        raise ValueError("plans must contain every masking policy")
    if "_base_mask" not in plans:
        raise ValueError("plans must expose the common-random base mask")
    if rung not in BURDEN_RUNGS:
        raise ValueError("rung must be one of the six frozen burden rungs")

    pos = {int(c): i for i, c in enumerate(core)}
    base = set(map(int, plans["_base_mask"]["mask"]))
    base_pos = _mask_positions(base, pos)
    if int(target_col) not in base:
        raise ValueError("uniform base mask must contain the target")

    expected_co_mask_count = (
        (int(core.size) - 1) * int(rung.numerator)
    ) // int(rung.denominator)
    expected_mask_cardinality = 1 + expected_co_mask_count
    if len(base) != expected_mask_cardinality:
        raise ValueError(
            "uniform base-mask cardinality does not match frozen rung arithmetic: "
            f"rung={rung} expected={expected_mask_cardinality} observed={len(base)}"
        )
    declared_base_cardinality = plans["_base_mask"].get("mask_cardinality")
    if (
        declared_base_cardinality is not None
        and int(declared_base_cardinality) != len(base)
    ):
        raise ValueError("declared base mask_cardinality disagrees with mask bytes")

    # Validate every plan against the common-random base BEFORE reading burden.
    for policy in POLICIES:
        plan = plans[policy]
        if "mask" not in plan:
            raise ValueError(f"{policy} plan is missing its mask")
        mask = set(map(int, plan["mask"]))
        _mask_positions(mask, pos)
        if int(target_col) not in mask:
            raise ValueError(f"{policy} mask does not contain the target")
        if len(mask) != expected_mask_cardinality:
            raise ValueError(
                f"{policy} mask cardinality {len(mask)} does not match frozen rung "
                f"cardinality {expected_mask_cardinality}"
            )
        if policy == "UNIFORM_RANDOM" and mask != base:
            raise ValueError("UNIFORM_RANDOM mask must equal the common-random base mask")
        observed_added = mask - base
        observed_dropped = base - mask
        declared_added = set(map(int, plan.get("added_vs_base", ())))
        declared_dropped = set(map(int, plan.get("dropped_vs_base", ())))
        if declared_added != observed_added or declared_dropped != observed_dropped:
            raise ValueError(
                f"{policy} added_vs_base/dropped_vs_base do not match the actual mask"
            )
        if len(observed_added) != len(observed_dropped):
            raise ValueError(f"{policy} violates exact burden-preserving swap cardinality")
        if int(target_col) in observed_added or int(target_col) in observed_dropped:
            raise ValueError("target cannot enter added/dropped swap sets")
        declared_cardinality = plan.get("mask_cardinality")
        if declared_cardinality is not None and int(declared_cardinality) != len(mask):
            raise ValueError(f"{policy} declared mask_cardinality disagrees with mask bytes")

    rows: list[DonorBurdenObservationV1] = []
    for donor in donors:
        d = int(donor)
        uniform_nnz = float(nnz[d, base_pos].sum())
        uniform_umi = float(umi[d, base_pos].sum())
        if uniform_nnz <= 0:
            raise ValueError(
                f"uniform detected-token burden is zero for held-out donor {d}; "
                "relative burden is not estimable"
            )
        for policy in POLICIES:
            plan = plans[policy]
            added = set(map(int, plan["added_vs_base"]))
            dropped = set(map(int, plan["dropped_vs_base"]))
            if len(added) != len(dropped):
                raise ValueError("added/dropped address counts must match exactly")
            if int(target_col) in added or int(target_col) in dropped:
                raise ValueError("target cannot enter added/dropped swap sets")
            add_pos = _mask_positions(added, pos) if added else np.empty(0, dtype=np.int64)
            drop_pos = _mask_positions(dropped, pos) if dropped else np.empty(0, dtype=np.int64)
            delta_nnz = float(nnz[d, add_pos].sum() - nnz[d, drop_pos].sum())
            delta_umi = float(umi[d, add_pos].sum() - umi[d, drop_pos].sum())
            rows.append(
                DonorBurdenObservationV1(
                    target_col=int(target_col),
                    fold_index=int(fold_index),
                    donor_code=d,
                    source_code=int(source[d]),
                    policy_id=policy,
                    rung_numerator=int(rung.numerator),
                    rung_denominator=int(rung.denominator),
                    uniform_detected_burden=uniform_nnz,
                    delta_detected_burden=delta_nnz,
                    normalized_delta_detected=delta_nnz / uniform_nnz,
                    uniform_umi_burden=uniform_umi,
                    delta_umi_burden=delta_umi,
                    normalized_delta_umi=(delta_umi / uniform_umi) if uniform_umi > 0 else float("nan"),
                )
            )
    return tuple(rows)


def source_balanced_target_value(
    rows: Sequence[DonorBurdenObservationV1],
    *,
    expected_source_codes: Sequence[int],
    expected_donor_codes: Sequence[int],
    metric: str = "normalized_delta_detected",
) -> float:
    """Equal donors within source, then equal source weight for one target."""
    if not rows:
        raise ValueError("rows must be nonempty")
    targets = {r.target_col for r in rows}
    policies = {r.policy_id for r in rows}
    rungs = {(r.rung_numerator, r.rung_denominator) for r in rows}
    if len(targets) != 1 or len(policies) != 1 or len(rungs) != 1:
        raise ValueError("target aggregation requires one target, one policy, one rung")
    expected = tuple(int(x) for x in expected_source_codes)
    if len(expected) == 0 or len(set(expected)) != len(expected):
        raise ValueError("expected_source_codes must be unique and nonempty")
    donors_expected = tuple(int(x) for x in expected_donor_codes)
    if len(donors_expected) == 0 or len(set(donors_expected)) != len(donors_expected):
        raise ValueError("expected_donor_codes must be unique and nonempty")
    donors_observed = [int(r.donor_code) for r in rows]
    if len(set(donors_observed)) != len(donors_observed):
        raise ValueError("target aggregation contains duplicate donor observations")
    if set(donors_observed) != set(donors_expected):
        raise ValueError(
            "target aggregation donor set is incomplete or contains unexpected donors"
        )
    observed_sources = {int(r.source_code) for r in rows}
    if observed_sources != set(expected):
        raise ValueError(
            "target aggregation source set differs from expected_source_codes"
        )
    means: list[float] = []
    for source in expected:
        values = np.asarray(
            [float(getattr(r, metric)) for r in rows if r.source_code == source],
            dtype=np.float64,
        )
        if values.size == 0:
            raise ValueError(f"required source {source} has no held-out donor observations")
        if not np.all(np.isfinite(values)):
            raise ValueError(f"metric {metric!r} is nonfinite for source {source}")
        means.append(float(values.mean()))
    return float(np.mean(means))


def precision_summary(
    *,
    policy_id: str,
    rung: Fraction,
    target_values: Sequence[float],
    max_relative_standard_error: float = MAX_RELATIVE_STANDARD_ERROR,
) -> PrecisionSummaryV1:
    if policy_id not in NONUNIFORM_POLICIES:
        raise ValueError("precision summary is defined for non-uniform policies only")
    x = np.asarray(target_values, dtype=np.float64)
    if x.ndim != 1 or x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("target_values must contain >=2 finite target-level values")
    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    se = float(sd / np.sqrt(x.size))
    if mean == 0.0:
        rse = None
        state = "UNDEFINED_ZERO_MEAN__FAIL_CLOSED"
        passed = False
    else:
        rse = float(se / abs(mean))
        state = "FINITE"
        passed = bool(np.isfinite(rse) and rse <= float(max_relative_standard_error))
    return PrecisionSummaryV1(
        policy_id=policy_id,
        rung_numerator=int(rung.numerator),
        rung_denominator=int(rung.denominator),
        n_targets=int(x.size),
        mean_normalized_delta_detected=mean,
        target_sample_sd=sd,
        standard_error=se,
        relative_standard_error=rse,
        relative_standard_error_state=state,
        precision_passed=passed,
    )


def escalation_decision(
    summaries: Sequence[PrecisionSummaryV1],
    *,
    sample_level: str,
) -> dict[str, Any]:
    """Apply the frozen precision-only prefix rule across every required cell."""
    if sample_level not in {"N1", "N2", "N3"}:
        raise ValueError("sample_level must be N1, N2, or N3")
    required = {
        (policy, rung.numerator, rung.denominator)
        for policy in NONUNIFORM_POLICIES
        for rung in BURDEN_RUNGS
    }
    observed = {
        (s.policy_id, s.rung_numerator, s.rung_denominator)
        for s in summaries
    }
    if observed != required or len(summaries) != len(required):
        raise ValueError("precision summaries must cover every nonuniform policy x burden rung exactly once")
    unresolved_zero_mean = [
        s for s in summaries
        if s.relative_standard_error_state != "FINITE"
    ]
    if unresolved_zero_mean:
        raise ValueError(
            "STOP_ZERO_MEAN_RULE_UNRESOLVED: at least one policy x rung cell has "
            "undefined relative standard error because its target-level mean is zero. "
            "The original Phase-IV freeze did not specify whether this should stop, "
            "escalate, or use another precision estimand; no sample-size action is lawful "
            "until that rule is prospectively resolved."
        )

    failures = [s for s in summaries if not s.precision_passed]
    if not failures:
        return {
            "sample_level": sample_level,
            "precision_passed_all_policy_rung_cells": True,
            "next_sample_authorized": None,
            "state": "SUFFICIENT_PRECISION",
        }
    if sample_level == "N1":
        nxt = "N2"
        state = "ESCALATE_TO_N2"
    elif sample_level == "N2":
        nxt = "N3"
        state = "ESCALATE_TO_N3"
    else:
        nxt = None
        state = "INSUFFICIENT_PRECISION_AT_N3"
    return {
        "sample_level": sample_level,
        "precision_passed_all_policy_rung_cells": False,
        "next_sample_authorized": nxt,
        "state": state,
        "failed_cells": [
            {
                "policy_id": s.policy_id,
                "rung": [s.rung_numerator, s.rung_denominator],
                "relative_standard_error": s.relative_standard_error,
                "relative_standard_error_state": s.relative_standard_error_state,
            }
            for s in failures
        ],
    }
