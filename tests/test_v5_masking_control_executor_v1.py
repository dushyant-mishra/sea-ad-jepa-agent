from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_control_executor_v1 import (
    deterministic_within_donor_shuffle,
    run_planted_proxy_control_fold,
    run_planted_proxy_matched_shuffle_control_fold,
    run_shuffled_negative_control_fold,
    run_planted_proxy_detection_fold,
    run_shuffled_null_detection_fold,
    select_planted_proxy,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_v5_full104_masking_streaming_executor_v1 import _fixture, budget, parameters


def test_proxy_selector_is_deterministic_outcome_blind_and_never_target() -> None:
    eligible = np.arange(20, dtype=np.int64)
    a = select_planted_proxy(eligible_cols=eligible, target_col=3, target_id="q3")
    b = select_planted_proxy(eligible_cols=eligible, target_col=3, target_id="q3")
    assert a == b
    assert a != 3
    assert a in set(eligible)


def test_within_donor_shuffle_preserves_each_donor_multiset_and_replays() -> None:
    values = np.arange(12, dtype=float)
    donor = np.repeat(np.arange(3), 4)
    a = deterministic_within_donor_shuffle(values, donor, target_id="q", global_seed=17)
    b = deterministic_within_donor_shuffle(values, donor, target_id="q", global_seed=17)
    assert np.array_equal(a, b)
    for d in range(3):
        ix = donor == d
        assert sorted(a[ix].tolist()) == sorted(values[ix].tolist())


def test_planted_proxy_control_detects_and_selects_exact_visible_proxy(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    result = run_planted_proxy_control_fold(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        eligible_proxy_cols=stream.universe_cols,
        global_seed=17,
    )
    assert result["control_id"] == "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1"
    assert result["proxy_selected"] is True
    assert result["detect_score"] >= result["after_mask_score"]
    assert result["mask_cardinality"] == result["uniform_mask_cardinality"]



def test_planted_matched_shuffle_control_is_same_mask_and_replays(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        eligible_proxy_cols=stream.universe_cols,
        global_seed=17,
    )
    first = run_planted_proxy_matched_shuffle_control_fold(**kwargs)
    second = run_planted_proxy_matched_shuffle_control_fold(**kwargs)
    assert first == second
    assert first["control_id"] == "PLANTED_SHORTCUT_MATCHED_SHUFFLE_CONTROL_V1"
    assert first["same_mask_shuffled_proxy"] is True
    assert first["proxy_selected"] is True
    assert first["mask_cardinality"] == first["uniform_mask_cardinality"]
    assert len(first["detect_donor_excess"]) == 4
    assert len(first["after_mask_donor_excess"]) == 4
    assert first["detect_excess"] == pytest.approx(
        first["detect_score"] - first["shuffled_detect_score"]
    )
    assert first["after_mask_excess"] == pytest.approx(
        first["after_mask_score"] - first["shuffled_after_mask_score"]
    )


def test_shuffled_negative_control_is_exactly_replayable(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        global_seed=17,
    )
    a = run_shuffled_negative_control_fold(**kwargs)
    b = run_shuffled_negative_control_fold(**kwargs)
    assert a == b
    assert a["control_id"] == "WITHIN_DONOR_SHUFFLED_NEGATIVE_CONTROL_V1"
    assert a["mask_cardinality"] == a["uniform_mask_cardinality"]


def test_control_source_contains_no_discovery_path_or_burden_constant() -> None:
    source = Path("src/sea_ad_jepa/v5/masking_control_executor_v1.py").read_text(encoding="utf-8")
    forbidden = (
        "jepa_spike_work",
        "X_common6000",
        "burden=900",
        "burden = 900",
        "0.15",
        "targets[0]",
        "univ[123]",
        "12345",
    )
    assert [token for token in forbidden if token in source] == []


def test_capacity_detection_controls_use_no_masking_burden(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    planted = run_planted_proxy_detection_fold(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        eligible_proxy_cols=stream.universe_cols,
    )
    shuffled = run_shuffled_null_detection_fold(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        global_seed=17,
    )
    assert planted["masking_burden_used"] is False
    assert shuffled["masking_burden_used"] is False
    assert planted["masking_policy_outcomes_inspected"] is False
    assert shuffled["masking_policy_outcomes_inspected"] is False
    assert planted["control_id"] == "PLANTED_SHORTCUT_CAPACITY_DETECTION_V1"
    assert shuffled["control_id"] == "WITHIN_DONOR_SHUFFLED_CAPACITY_NULL_V1"
    assert len(planted["donor_scores"]) == 4
    assert len(shuffled["donor_scores"]) == 4


def test_capacity_detection_replays_exactly(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        global_seed=17,
    )
    a = run_shuffled_null_detection_fold(**kwargs)
    b = run_shuffled_null_detection_fold(**kwargs)
    assert a == b
