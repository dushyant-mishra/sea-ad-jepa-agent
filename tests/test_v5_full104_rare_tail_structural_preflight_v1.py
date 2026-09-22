from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.full104_rare_tail_structural_preflight_v1 import (
    _tail_triplet_capacity,
    evaluate_rare_tail_structural_support_v1,
)


def _full104_like_case(*, weaken_nph_fold0: bool = False):
    # Preserve actual source donor counts: HVS 41, NPH52 17, SEA_AD 46.
    source = np.empty(104, dtype=np.int64)
    source[:41] = 0
    source[41:58] = 1
    source[58:] = 2

    fold = np.empty(104, dtype=np.int64)
    for s in range(3):
        donors = np.flatnonzero(source == s)
        fold[donors] = np.arange(donors.size, dtype=np.int64) % 4

    donor_rows = []
    operator_rows = []
    for d in range(104):
        n = 100
        if weaken_nph_fold0 and source[d] == 1 and fold[d] == 0:
            # Three retained cells cannot make a nearest-half relational triplet.
            n = 3
        donor_rows.extend([d] * n)
        # One operator per donor is enough for a structural unit test. Operator is
        # not assigned objective mass by the evaluator.
        operator_rows.extend([d % 42] * n)

    return (
        np.asarray(donor_rows, dtype=np.int64),
        np.asarray(operator_rows, dtype=np.int64),
        fold,
        source,
    )


def test_tail_capacity_respects_q95_and_nearest_half_geometry() -> None:
    assert _tail_triplet_capacity(0) == (0, 0, 0, 0)
    assert _tail_triplet_capacity(1) == (0, 0, 0, 0)
    assert _tail_triplet_capacity(2) == (1, 0, 0, 0)
    assert _tail_triplet_capacity(3) == (1, 0, 0, 0)

    # n=4 => one q95 anchor, nearest-half k=2 => one comparison.
    assert _tail_triplet_capacity(4) == (1, 1, 1, 1)

    # n=100 => q95 top 5 anchors; k=50 => C(50,2)=1225 each.
    # Population = 6125, but the inherited TD59 sample cap is 64/stratum.
    assert _tail_triplet_capacity(100) == (5, 5, 6125, 64)


def test_all_source_fold_cases_can_be_structurally_possible_without_claiming_biology() -> None:
    donor, operator, fold, source = _full104_like_case()
    out = evaluate_rare_tail_structural_support_v1(
        retained_donor_code=donor,
        retained_operator_code=operator,
        fold_by_donor=fold,
        source_by_donor=source,
    )
    assert out["status"] == "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN"
    assert out["structurally_possible_all_source_fold_cases"] is True
    assert len(out["source_fold_cases"]) == 12
    assert all(x["structurally_possible"] for x in out["source_fold_cases"])
    assert out["zxy_molecular_outcome_opened"] is False
    assert out["rare_tail_molecular_pass_claimed"] is False
    assert out["teacher_tail_evaluation_authorized"] is False
    assert out["training_authorized"] is False


def test_nph_source_fold_failure_stops_before_molecular_outcome() -> None:
    donor, operator, fold, source = _full104_like_case(weaken_nph_fold0=True)
    out = evaluate_rare_tail_structural_support_v1(
        retained_donor_code=donor,
        retained_operator_code=operator,
        fold_by_donor=fold,
        source_by_donor=source,
    )
    assert out["status"] == "STOP_STRUCTURAL_SUPPORT_INSUFFICIENT_BEFORE_MOLECULAR_OUTCOME"
    target = [
        x for x in out["source_fold_cases"]
        if x["source_code"] == 1 and x["fold_index"] == 0
    ]
    assert len(target) == 1
    assert target[0]["donors_structurally_eligible"] == 0
    assert target[0]["structurally_possible"] is False
    assert out["zxy_molecular_outcome_opened"] is False


def test_operator_fragmentation_can_reduce_triplet_capacity_without_equal_operator_weighting() -> None:
    donor, operator, fold, source = _full104_like_case()
    # Fragment donor 0's 100 cells into 34 tiny operator strata (within the
    # legal 0..41 operator registry). Most strata have only 2-3 cells and cannot
    # produce local comparison triplets.
    ix = np.flatnonzero(donor == 0)
    operator[ix] = np.arange(ix.size, dtype=np.int64) % 34

    out = evaluate_rare_tail_structural_support_v1(
        retained_donor_code=donor,
        retained_operator_code=operator,
        fold_by_donor=fold,
        source_by_donor=source,
    )
    d0 = [x for x in out["donor_capacity"] if x["donor_code"] == 0][0]
    assert d0["represented_operators"] == 34
    assert d0["triplet_capable_tail_anchor_upper_bound"] < d0["q95_tail_anchor_upper_bound"]
    # No operator is artificially reweighted; the diagnostic uses retained cell counts.
    assert sum(
        x["retained_cells"]
        for x in out["operator_capacity"]
        if x["donor_code"] == 0
    ) == 100


def test_invalid_or_incomplete_identity_geometry_fails_closed() -> None:
    donor, operator, fold, source = _full104_like_case()
    with pytest.raises(ValueError, match="invalid FULL104 operator"):
        bad = operator.copy()
        bad[0] = 42
        evaluate_rare_tail_structural_support_v1(
            retained_donor_code=donor,
            retained_operator_code=bad,
            fold_by_donor=fold,
            source_by_donor=source,
        )

    with pytest.raises(ValueError, match="every donor"):
        keep = donor != 103
        evaluate_rare_tail_structural_support_v1(
            retained_donor_code=donor[keep],
            retained_operator_code=operator[keep],
            fold_by_donor=fold,
            source_by_donor=source,
        )
