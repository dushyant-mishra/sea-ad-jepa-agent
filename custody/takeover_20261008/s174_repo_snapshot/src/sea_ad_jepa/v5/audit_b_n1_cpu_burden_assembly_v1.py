"""Prospective N1 CPU assembly using frozen Audit-B planners and burden estimator.

This module is deliberately NOT a FULL104 execution command. It requires a
verified stream and independently authenticated donor-level RAW UMI statistics;
the current qualified heavy NPZ alone supplies donor_nnz, not donor_umi. The
heavy-data runtime/atomic commit must be separately qualified and source-bound
before opening any N1 result.

No terminal masking prediction outcomes, TD60, D_shared or training here.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Sequence

import numpy as np

from .audit_b_n1_cached_planner_v1 import plans_from_cached_partners
from .audit_b_n1_crossfold_planner_v1 import select_all_fold_partners_two_pass
from .audit_b_n1_result_contract_v1 import (
    EXPECTED_TENSOR_SHAPE,
    N_DONORS,
    N1_TARGET_COUNT,
    N_POLICIES,
    N_RUNGS,
    POLICY_ORDER,
    RUNG_ORDER,
    validate_n1_arrays,
)
from .audit_b_n1_runtime_rng_bridge_v1 import RNG_V3_GLOBAL_SEED
from .audit_b_production_burden_v1 import (
    BURDEN_RUNGS,
    POLICIES,
    measure_plan_burden,
)

SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
SOURCE_DONORS = (41, 17, 46)
FOLD_DONORS = (28, 26, 25, 25)
FULL104_CORE_SIZE = 17_186


def validate_donor_geometry(
    *,
    frozen_targets: Sequence[int],
    core_addresses: Sequence[int],
    donor_nnz: Any,
    donor_umi: Any,
    donor_source_code: Any,
    fold_by_donor: Any,
    stream: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fail closed on FULL104-only shape, identity and donor/fold coverage."""
    targets = np.asarray(frozen_targets)
    core = np.asarray(core_addresses)
    if (targets.ndim != 1 or targets.size != N1_TARGET_COUNT
            or not np.issubdtype(targets.dtype, np.integer)
            or np.unique(targets).size != targets.size
            or np.any(targets < 0)):
        raise ValueError("N1 must use exactly 256 frozen unique integer targets")
    if (core.ndim != 1 or core.size != FULL104_CORE_SIZE
            or not np.issubdtype(core.dtype, np.integer)
            or np.unique(core).size != core.size
            or np.any(core < 0)):
        raise ValueError("FULL104 strict core must have exactly 17186 unique addresses")
    if not set(map(int, targets)).issubset(set(map(int, core))):
        raise ValueError("frozen N1 targets must belong to the authenticated strict core")
    if not np.array_equal(stream.universe_cols, core):
        raise ValueError("stream universe must exactly match frozen strict-core order")
    if not np.array_equal(stream.target_cols, targets):
        raise ValueError("stream target order must exactly equal frozen N1 prefix")
    if (len(stream.target_ids) != N1_TARGET_COUNT
            or any(not isinstance(x, (int, np.integer)) for x in stream.target_ids)
            or not np.array_equal(np.asarray(stream.target_ids, dtype=np.int64), targets)):
        raise ValueError("runtime target IDs must be integer molecular address columns")

    source = np.asarray(donor_source_code)
    fold = np.asarray(fold_by_donor)
    if (source.shape != (N_DONORS,) or not np.issubdtype(source.dtype, np.integer)
            or not np.array_equal(np.bincount(source, minlength=3), SOURCE_DONORS)):
        raise ValueError("donor source codes/counts differ from authenticated FULL104")
    if (fold.shape != (N_DONORS,) or not np.issubdtype(fold.dtype, np.integer)
            or not np.array_equal(np.bincount(fold, minlength=4), FOLD_DONORS)):
        raise ValueError("outer folds must contain exactly 28/26/25/25 donors")
    if not np.array_equal(stream.fold_by_donor, fold):
        raise ValueError("stream donor-fold mapping differs from authenticated split")
    source_names = np.asarray([SOURCE_NAMES[int(x)] for x in source], dtype=object)
    if not np.array_equal(stream.source_by_donor, source_names):
        raise ValueError("stream donor-source names disagree with authenticated source codes")

    nnz = np.asarray(donor_nnz)
    umi = np.asarray(donor_umi)
    expected = (N_DONORS, FULL104_CORE_SIZE)
    if nnz.shape != expected or umi.shape != expected:
        raise ValueError("both donor burden arrays must be 104 x 17186 strict-core order")
    if (not np.issubdtype(nnz.dtype, np.integer)
            or not np.issubdtype(umi.dtype, np.integer)
            or np.any(nnz < 0) or np.any(umi < nnz)):
        raise ValueError("raw UMI and detected burden must be nonnegative integer counts with UMI >= nnz")
    return (
        targets.astype(np.int64, copy=False),
        core.astype(np.int64, copy=False),
        nnz.astype(np.float64, copy=False),
        umi.astype(np.float64, copy=False),
        source.astype(np.int64, copy=False),
        fold.astype(np.int64, copy=False),
    )


class N1DonorTensorAccumulator:
    """Exact-once 256 x policy x rung x donor receipt assembly, no early zeros."""

    def __init__(
        self,
        *,
        frozen_targets: Sequence[int],
        donor_source_code: Sequence[int],
        fold_by_donor: Sequence[int],
    ) -> None:
        targets = np.asarray(frozen_targets)
        source = np.asarray(donor_source_code)
        folds = np.asarray(fold_by_donor)
        if (targets.shape != (N1_TARGET_COUNT,)
                or not np.issubdtype(targets.dtype, np.integer)
                or np.any(targets < 0)
                or np.unique(targets).size != N1_TARGET_COUNT):
            raise ValueError("invalid frozen 256-target N1 order")
        if (source.shape != (N_DONORS,)
                or not np.issubdtype(source.dtype, np.integer)
                or not np.array_equal(np.bincount(source, minlength=3), SOURCE_DONORS)):
            raise ValueError("invalid FULL104 source counts")
        if (folds.shape != (N_DONORS,)
                or not np.issubdtype(folds.dtype, np.integer)
                or not np.array_equal(np.bincount(folds, minlength=4), FOLD_DONORS)):
            raise ValueError("invalid FULL104 outer fold counts")
        self.targets = targets.astype(np.int64, copy=True)
        self.source = source.astype(np.int64, copy=True)
        self.folds = folds.astype(np.int64, copy=True)
        self.detected = np.full(EXPECTED_TENSOR_SHAPE, np.nan, dtype=np.float64)
        self.umi = np.full(EXPECTED_TENSOR_SHAPE, np.nan, dtype=np.float64)
        self.seen = np.zeros(EXPECTED_TENSOR_SHAPE, dtype=np.bool_)

    def ingest(
        self,
        *,
        target_index: int,
        fold_index: int,
        rung_index: int,
        observations: Sequence[Any],
    ) -> None:
        if not (0 <= target_index < N1_TARGET_COUNT
                and 0 <= fold_index < 4 and 0 <= rung_index < N_RUNGS):
            raise ValueError("target/fold/rung index is outside frozen N1 geometry")
        expected_donors = np.flatnonzero(self.folds == fold_index)
        expected_pairs = {
            (str(policy), int(donor))
            for donor in expected_donors
            for policy in POLICIES
        }
        by_pair: dict[tuple[str, int], Any] = {}
        rung = BURDEN_RUNGS[rung_index]
        for row in observations:
            donor = int(row.donor_code)
            key = (str(row.policy_id), donor)
            if key not in expected_pairs or key in by_pair:
                raise ValueError("missing/duplicate/extra policy-donor row or held-out donor leakage")
            if (int(row.target_col) != int(self.targets[target_index])
                    or int(row.fold_index) != fold_index
                    or (int(row.rung_numerator), int(row.rung_denominator))
                    != (rung.numerator, rung.denominator)
                    or int(row.source_code) != int(self.source[donor])):
                raise ValueError("observation target/fold/rung/source identity drift")
            if (not np.isfinite(row.normalized_delta_detected)
                    or not np.isfinite(row.normalized_delta_umi)):
                raise ValueError("nonfinite donor burden: relative burden is not estimable")
            by_pair[key] = row
        if set(by_pair) != expected_pairs:
            raise ValueError("incomplete policy x held-out-donor observations")

        # Validate the entire incoming cell before mutating the accumulator.
        for donor in expected_donors:
            if self.seen[target_index, :, rung_index, donor].any():
                raise ValueError("duplicate target/fold/rung/donor result consumption")
            uniform = by_pair[("UNIFORM_RANDOM", int(donor))]
            if (uniform.normalized_delta_detected != 0
                    or uniform.normalized_delta_umi != 0):
                raise ValueError("uniform base must have exactly zero delta")
        for policy_index, policy in enumerate(POLICY_ORDER):
            for donor in expected_donors:
                d = int(donor)
                row = by_pair[(policy, d)]
                self.detected[target_index, policy_index, rung_index, d] = row.normalized_delta_detected
                self.umi[target_index, policy_index, rung_index, d] = row.normalized_delta_umi
                self.seen[target_index, policy_index, rung_index, d] = True

    def finalize(self) -> dict[str, np.ndarray]:
        if not np.all(self.seen):
            missing = int(np.count_nonzero(~self.seen))
            raise ValueError(f"not all N1 target/policy/rung/donor cells were consumed: missing {missing}")
        return validate_n1_arrays(
            target_cols=self.targets,
            expected_target_cols=self.targets,
            donor_normalized_delta_detected=self.detected,
            donor_normalized_delta_umi=self.umi,
            donor_source_code=self.source,
        )


def assemble_n1_from_authenticated_stream(
    *,
    stream: Any,
    frozen_targets: Sequence[int],
    core_addresses: Sequence[int],
    donor_nnz: Any,
    donor_umi: Any,
    donor_source_code: Sequence[int],
    fold_by_donor: Sequence[int],
    parameters: Any,
    global_seed: int = RNG_V3_GLOBAL_SEED,
) -> dict[str, np.ndarray]:
    """Full CPU computation, requiring caller-certified physical inputs.

    This function has NO heavy-production CLI, output writer or resume authority.
    It must not be used on physical FULL104 until those independent gates close.
    """
    if type(global_seed) is not int or global_seed != RNG_V3_GLOBAL_SEED:
        raise ValueError("N1 global seed drifted from frozen RNG-V3")
    parameters.validate()
    (targets, core, nnz, umi, source, folds) = validate_donor_geometry(
        frozen_targets=frozen_targets, core_addresses=core_addresses,
        donor_nnz=donor_nnz, donor_umi=donor_umi,
        donor_source_code=donor_source_code, fold_by_donor=fold_by_donor,
        stream=stream,
    )
    for rung in BURDEN_RUNGS:
        co_count = ((core.size - 1) * rung.numerator) // rung.denominator
        if co_count < int(parameters.targeted_partner_cap):
            raise ValueError("frozen masking partner cap exceeds N1 rung co-mask count")

    # Authentication of 8915 block hashes / 4553407 row identities is the
    # stream's job, never silently delegated to an undersized fixture.
    stream.validate_layout()
    acc = N1DonorTensorAccumulator(
        frozen_targets=targets, donor_source_code=source, fold_by_donor=folds,
    )
    for target_index, target_col in enumerate(targets):
        all_fold_partners = select_all_fold_partners_two_pass(
            stream=stream, target_col=int(target_col),
            parameters=parameters, global_seed=global_seed,
        )
        if (len(all_fold_partners) != 4
                or [int(p.fold_index) for p in all_fold_partners] != list(range(4))
                or any(int(p.target_col) != int(target_col) for p in all_fold_partners)):
            raise ValueError("crossfold planner omitted or duplicated a target/fold")
        for partners in all_fold_partners:
            fold_index = int(partners.fold_index)
            heldout = np.flatnonzero(folds == fold_index)
            for rung_index, rung in enumerate(BURDEN_RUNGS):
                count = ((core.size - 1) * rung.numerator) // rung.denominator
                plans = plans_from_cached_partners(
                    stream=stream, partners=partners,
                    target_id=int(target_col), co_mask_count=count,
                    global_seed=global_seed,
                )
                observations = measure_plan_burden(
                    target_col=int(target_col), fold_index=fold_index,
                    plans=plans, heldout_donors=heldout,
                    fold_by_donor=folds, donor_source_code=source,
                    core_addresses=core, donor_nnz=nnz, donor_umi=umi, rung=rung,
                )
                acc.ingest(
                    target_index=target_index, fold_index=fold_index,
                    rung_index=rung_index, observations=observations,
                )
    return acc.finalize()
