from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.masking_control_executor_v1 import (
    deterministic_within_donor_shuffle,
    run_planted_proxy_control_fold,
    run_shuffled_negative_control_fold,
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
        method="RIDGE8_CONDITIONAL",
        global_seed=17,
    )
    assert result["control_id"] == "PLANTED_SHORTCUT_POSITIVE_CONTROL_V1"
    assert result["method"] == "RIDGE8_CONDITIONAL"
    assert result["proxy_selected"] is True
    assert result["detect_score"] >= result["after_mask_score"]
    assert result["detect_excess"] == pytest.approx(
        result["detect_score"] - result["shuffled_detect_score"]
    )
    assert result["after_mask_excess"] == pytest.approx(
        result["after_mask_score"] - result["shuffled_after_mask_score"]
    )
    assert result["mask_cardinality"] == result["uniform_mask_cardinality"]


def test_shuffled_negative_control_is_exactly_replayable(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    kwargs = dict(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        method="RIDGE8_CONDITIONAL",
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


@pytest.mark.parametrize(
    "method",
    ["UNIFORM_RANDOM", "TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE"],
)
def test_shuffled_control_runs_each_declared_policy_without_hidden_ridge_default(
    tmp_path: Path, method: str
) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    out = run_shuffled_negative_control_fold(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        method=method,
        global_seed=17,
    )
    assert out["method"] == method
    assert out["mask_cardinality"] == out["uniform_mask_cardinality"]


def test_uniform_planted_control_does_not_pretend_to_target_proxy(tmp_path: Path) -> None:
    _, stream, _, _ = _fixture(tmp_path)
    out = run_planted_proxy_control_fold(
        stream=stream,
        fold_index=0,
        parameters=parameters(),
        evidence_budget=budget(),
        target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0],
        eligible_proxy_cols=stream.universe_cols,
        method="UNIFORM_RANDOM",
        global_seed=17,
    )
    assert out["method"] == "UNIFORM_RANDOM"
    assert out["targeted_cols"] == ()
