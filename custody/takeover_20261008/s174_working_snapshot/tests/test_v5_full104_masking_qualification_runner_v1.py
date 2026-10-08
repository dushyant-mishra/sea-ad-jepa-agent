from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

from sea_ad_jepa.v5.full104_masking_qualification_runner_v1 import (
    QualificationArrays,
    apply_burden_preserving_swaps,
    infer_strict_measured_scalar_common_core,
    run_primary_fold,
    source_balanced_donor_centered_prediction_correlation_squared,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import MaskingQualificationParametersAuthorityV1
from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import TargetEvidenceBudgetAuthorityV1


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def parameters() -> MaskingQualificationParametersAuthorityV1:
    return MaskingQualificationParametersAuthorityV1(
        authority_id="V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1",
        primary_attacker_id="RIDGE_EXPRESSION_PROXY_ATTACKER_V1",
        primary_score_id="SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1",
        targeted_partner_cap=2,
        ridge_candidate_pool_count=3,
        ridge_score_feature_count=2,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=3,
        prefix_floor_numerator=0,
        prefix_floor_denominator=1,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
    )


def budget() -> TargetEvidenceBudgetAuthorityV1:
    return TargetEvidenceBudgetAuthorityV1(
        authority_id="V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1",
        support_estimability_authority_sha256=h("support"),
        budget_semantics_id="MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=2,
        min_retained_non_target_rna_count=1,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )


def test_strict_common_core_infers_scalar_state_from_frozen_terminal_cardinality() -> None:
    obs = np.array(
        [
            [1, 1, 2, 0, 1],
            [1, 1, 2, 0, 2],
            [1, 1, 2, 0, 1],
        ],
        dtype=np.uint8,
    )
    code, indices = infer_strict_measured_scalar_common_core(obs, expected_size=2)
    assert code == 1
    assert indices.tolist() == [0, 1]
    # Ambiguous encodings fail closed rather than choosing an arbitrary state.
    with pytest.raises(ValueError, match="unique"):
        infer_strict_measured_scalar_common_core(np.array([[1, 2], [1, 2]], dtype=np.uint8), expected_size=1)


def test_burden_preserving_swap_is_exact_and_never_zip_truncates() -> None:
    base = {0, 2, 3}
    out = apply_burden_preserving_swaps(
        base_mask=base,
        target_col=0,
        targeted_cols=(4, 5),
        removable_order=(2, 3),
    )
    assert out == {0, 4, 5}
    assert len(out) == len(base)
    with pytest.raises(ValueError, match="removable"):
        apply_burden_preserving_swaps(
            base_mask={0, 2},
            target_col=0,
            targeted_cols=(3, 4),
            removable_order=(2,),
        )


def test_primary_score_matches_source_balanced_donor_centered_r_squared() -> None:
    y = np.array([0.0, 1.0, 0.0, 2.0, 1.0, 3.0, 1.0, 2.0])
    p = np.array([0.0, 2.0, 0.0, 4.0, 3.0, 1.0, 3.0, 2.0])
    donor = np.array([0, 0, 1, 1, 2, 2, 3, 3])
    source_by_donor = np.array(["A", "A", "B", "B"], dtype=object)
    # donors 0 and 1 are perfect; donors 2 and 3 are perfect negative -> r^2=1 throughout.
    score = source_balanced_donor_centered_prediction_correlation_squared(y, p, donor, source_by_donor)
    assert score == pytest.approx(1.0)


def synthetic_arrays() -> QualificationArrays:
    # 12 cells, 6 donors, 6 addresses. Donor 0/1 -> fold0, 2/3 -> fold1, 4/5 -> fold2.
    donor = np.repeat(np.arange(6), 2)
    source_by_donor = np.array(["A", "A", "A", "A", "B", "B"], dtype=object)
    fold_by_donor = np.array([0, 0, 1, 1, 2, 2])
    z = np.tile(np.array([0.0, 1.0]), 6)
    x = np.column_stack(
        [
            z,
            z + np.repeat(np.arange(6), 2) * 0.01,
            2.0 * z,
            np.array([0, 1, 1, 0] * 3, dtype=float),
            np.array([1, 0, 0, 1] * 3, dtype=float),
            np.ones(12),
        ]
    )
    return QualificationArrays(
        X=sp.csr_matrix(x),
        donor_code=donor,
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=np.arange(6, dtype=int),
        target_cols=np.array([0], dtype=int),
        target_ids=np.array(["q0"], dtype=object),
    )


def test_fold_runner_uses_same_ridge_attacker_for_every_arm_and_is_train_donor_only() -> None:
    arrays = synthetic_arrays()
    first = run_primary_fold(arrays=arrays, fold_index=0, parameters=parameters(), evidence_budget=budget(), global_seed=17)
    assert {row["method"] for row in first} == {
        "UNIFORM_RANDOM",
        "TOP8_CORRELATION",
        "RIDGE8_CONDITIONAL",
        "PREFIX3_SELECTIVE",
    }
    assert all(row["primary_attacker_id"] == "RIDGE_EXPRESSION_PROXY_ATTACKER_V1" for row in first)
    assert all(row["primary_score_id"] == "SOURCE_BALANCED_MEAN_DONOR_CENTERED_PREDICTION_CORRELATION_SQUARED_V1" for row in first)
    assert all(row["mask_cardinality"] == row["uniform_mask_cardinality"] for row in first)

    # Mutating heldout-fold expression cannot change train-only targeted partner selection.
    changed = synthetic_arrays()
    held_rows = np.isin(changed.donor_code, np.flatnonzero(changed.fold_by_donor == 0))
    altered = changed.X.toarray()
    altered[held_rows, :] += np.arange(6) * 1000.0
    changed = QualificationArrays(
        X=sp.csr_matrix(altered),
        donor_code=changed.donor_code,
        source_by_donor=changed.source_by_donor,
        fold_by_donor=changed.fold_by_donor,
        universe_cols=changed.universe_cols,
        target_cols=changed.target_cols,
        target_ids=changed.target_ids,
    )
    second = run_primary_fold(arrays=changed, fold_index=0, parameters=parameters(), evidence_budget=budget(), global_seed=17)
    by_method_first = {r["method"]: tuple(r["targeted_cols"]) for r in first}
    by_method_second = {r["method"]: tuple(r["targeted_cols"]) for r in second}
    assert by_method_first == by_method_second


def test_runner_source_contains_no_exploratory_hardcodes_or_training_switches() -> None:
    source = Path("src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "/mnt/data",
        "jepa_spike_work",
        "burden_frac=.15",
        "alpha=.01",
        "targets[:8]",
        "training_authorized=True",
        "protected_outcomes_authorized=True",
    )
    assert [token for token in forbidden if token in source] == []
