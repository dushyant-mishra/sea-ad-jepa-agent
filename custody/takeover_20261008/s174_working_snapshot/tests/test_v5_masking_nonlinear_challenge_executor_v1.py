from __future__ import annotations

import hashlib
import sys
from pathlib import Path
import numpy as np

from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v1 import (
    CHALLENGE_ID, DONOR_WEIGHTING_POLICY_ID, MODEL_FAMILY_ID,
    RETUNING_POLICY_ID, SAMPLING_POLICY_ID, NonlinearMaskingChallengeAuthorityV1,
)
from sea_ad_jepa.v5.masking_nonlinear_challenge_executor_v1 import run_nonlinear_mask_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_v5_full104_masking_streaming_executor_v1 import _fixture, parameters


def h(name):
    return hashlib.sha256(name.encode()).hexdigest()


def nonlinear_authority(params):
    return NonlinearMaskingChallengeAuthorityV1(
        authority_id="TEST",
        primary_parameters_authority_sha256=params.canonical_digest(),
        outer_split_authority_sha256=h("split"),
        target_panel_authority_sha256=h("panel"),
        challenge_id=CHALLENGE_ID,
        model_family_id=MODEL_FAMILY_ID,
        sampling_policy_id=SAMPLING_POLICY_ID,
        donor_weighting_policy_id=DONOR_WEIGHTING_POLICY_ID,
        retuning_policy_id=RETUNING_POLICY_ID,
        feature_count=params.ridge_score_feature_count,
        max_cells_per_donor=3,
        learning_rate_numerator=1,
        learning_rate_denominator=10,
        max_iter=5,
        max_leaf_nodes=3,
        min_samples_leaf=2,
        l2_regularization_numerator=1,
        l2_regularization_denominator=1,
        max_bins=16,
        random_seed=7,
    )


def test_nonlinear_challenge_replays_and_scores_heldout_donors(tmp_path: Path):
    _, stream, _, _ = _fixture(tmp_path)
    params = parameters()
    auth = nonlinear_authority(params)
    kwargs = dict(
        stream=stream, fold_index=0, target_col=int(stream.target_cols[0]),
        target_id=stream.target_ids[0], mask={int(stream.target_cols[0]), 7},
        authority=auth, primary_parameters=params,
    )
    a = run_nonlinear_mask_score(**kwargs)
    b = run_nonlinear_mask_score(**kwargs)
    assert a == b
    assert np.isfinite(a["score"])
    assert a["heldout_donor_count"] == 4
    assert a["train_donor_count"] == 8


def test_nonlinear_accepts_current_within_donor_shuffled_override(tmp_path: Path):
    from sea_ad_jepa.v5.masking_control_executor_v1 import deterministic_within_donor_shuffle, materialize_stream_column
    _, stream, _, _ = _fixture(tmp_path)
    params = parameters()
    auth = nonlinear_authority(params)
    target = int(stream.target_cols[0])
    y, donor = materialize_stream_column(stream, column=target)
    shuffled = deterministic_within_donor_shuffle(y, donor, target_id=stream.target_ids[0], global_seed=17)
    out = run_nonlinear_mask_score(
        stream=stream, fold_index=0, target_col=target, target_id=stream.target_ids[0],
        mask={target, 7}, authority=auth, primary_parameters=params,
        y_override_by_selection=shuffled,
    )
    assert np.isfinite(out["score"])
    assert len(out["donor_scores"]) == 4


def test_nonlinear_source_contains_no_discovery_data_or_hidden_old_settings():
    source = Path("src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py").read_text(encoding="utf-8")
    forbidden = ("jepa_spike_work", "X_common6000", "outer5200", "burden=900", "20260917", "targets32", "univ[123]")
    assert [token for token in forbidden if token in source] == []
