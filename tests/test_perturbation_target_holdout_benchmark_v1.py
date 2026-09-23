"""Adversarial, synthetic-only qualification for the prospective Q2 benchmark.

All effects here are PLANTED TEST VALUES, not measured perturbation outcomes.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from sea_ad_jepa.perturbation.benchmark_target_holdout_v1 import (
    GuideDonorEffects, donor_matched_effects, freeze_target_partition,
    select_fold, training_baselines, evaluate_target_excluded_baselines,
)

SOURCE = "a" * 64
FEATURES = tuple(f"G{i:02d}" for i in range(16)) + ("DOWNSTREAM",)


def planted():
    gids, dids, tids, rows, controls = [], [], [], [], []
    for donor in ("D1", "D2"):
        # Two donor-matched, independently identified non-targeting guides.
        for k in (1, 2):
            gids.append(f"NT{k}")
            dids.append(donor)
            tids.append("NT")
            controls.append(True)
            rows.append(np.ones(len(FEATURES)) * 4.0)
        for j in range(16):
            gids.append(f"G{j:02d}_guide")
            dids.append(donor)
            tids.append(f"G{j:02d}")
            controls.append(False)
            x = np.ones(len(FEATURES)) * 4.6
            x[j] = 7.0
            rows.append(x)
    return donor_matched_effects(
        assay="SYNTHETIC_CRISPRi", source_sha256=SOURCE, feature_ids=FEATURES,
        guide_ids=gids, donor_ids=dids, target_ids=tids,
        is_control=controls, logcpm=np.array(rows, dtype=float),
        measured_features=[True] * len(FEATURES),
    )


def partition(data, seed="FROZEN_BEFORE_EFFECTS"):
    return freeze_target_partition(
        target_ids=data.target_ids, guide_ids=data.guide_ids,
        donor_ids=data.donor_ids, assay=data.assay,
        source_sha256=SOURCE, exposure="DEVELOPMENT",
        seed=seed, n_folds=4,
    )


def test_guide_donor_donor_matched_control_subtraction():
    data = planted()
    assert data.effects.shape == (32, 17)
    assert sorted(set(data.donor_ids)) == ["D1", "D2"]
    assert sorted(set(data.target_ids)) == sorted(FEATURES[:-1])
    assert np.allclose(data.effects[:, -1], 0.6)
    assert all(
        np.isclose(data.effects[i, FEATURES.index(t)], 3.0)
        for i, t in enumerate(data.target_ids)
    )


def test_partition_is_content_bound_and_row_order_invariant():
    data = planted()
    a = partition(data)
    b = freeze_target_partition(
        target_ids=tuple(reversed(data.target_ids)),
        guide_ids=tuple(reversed(data.guide_ids)),
        donor_ids=tuple(reversed(data.donor_ids)), assay=data.assay,
        source_sha256=SOURCE, exposure="DEVELOPMENT",
        seed="FROZEN_BEFORE_EFFECTS", n_folds=4,
    )
    assert a == b
    a.validate()
    assert {f for _, f in a.target_to_fold} == set(range(4))
    corrupt = replace(a, target_to_fold=a.target_to_fold[::-1])
    with pytest.raises(ValueError, match="sorted"):
        corrupt.validate()
    other = partition(data, seed="different")
    assert other.partition_sha256 != a.partition_sha256


def test_no_target_leakage_across_any_fold():
    data = planted()
    fixed = partition(data)
    for fold in range(4):
        train, test = select_fold(data, fixed, fold)
        assert set(np.array(data.target_ids)[train]).isdisjoint(
            set(np.array(data.target_ids)[test])
        )
        assert sum(test) % 2 == 0  # both donors kept with each held-out target


def test_downstream_baselines_macro_average_over_targets():
    data = planted()
    out = evaluate_target_excluded_baselines(data, partition(data), fold=0)
    assert out["status"] == "BASELINE_ONLY_NO_JEPA_TRAINING"
    assert out["jepa_training_authorized"] is False
    assert out["therapeutic_ranking_authorized"] is False
    assert out["n_test_targets"] == 4
    baselines = out["baselines"]
    assert baselines["train_target_equal_mean"]["macro_mae"] < baselines["no_change"]["macro_mae"]
    # Identity-only and no-change are mathematically identical after
    # excluding the perturbed target: never mistake engagement for recovery.
    assert baselines["no_change"]["macro_mae"] == baselines["target_identity_only"]["macro_mae"]
    assert baselines["no_change"]["macro_rmse"] == baselines["target_identity_only"]["macro_rmse"]
    assert all(r["n"] == 2 * (len(FEATURES) - 1)
               for r in baselines["no_change"]["per_target"])


def test_changing_held_out_outcomes_cannot_influence_fitted_baseline():
    data = planted()
    frozen = partition(data)
    train, test = select_fold(data, frozen, fold=0)
    before = training_baselines(data, train)
    x = data.effects.copy()
    x[test] += 1000
    attacked = replace(data, effects=x)
    after = training_baselines(attacked, train)
    assert np.array_equal(before[0], after[0])
    assert before[1] == after[1]


def test_changed_target_universe_or_assay_fails_closed():
    data = planted()
    frozen = partition(data)
    wrong_target = list(data.target_ids)
    wrong_target[0] = "UNSEEN"
    invalid = replace(data, target_ids=tuple(wrong_target))
    with pytest.raises(ValueError, match="same guide assigned conflicting targets"):
        select_fold(invalid, frozen, fold=0)
    other = replace(frozen, assay="DIFFERENT", partition_sha256=frozen.partition_sha256)
    with pytest.raises(ValueError, match="self-digest mismatch"):
        select_fold(data, other, fold=0)


def test_unmeasured_zero_and_duplicate_features_fail():
    data = planted()
    mask = data.measured.copy()
    mask[0, -1] = False
    with pytest.raises(ValueError, match="must be NaN"):
        replace(data, measured=mask).validate()
    x = data.effects.copy()
    x[0, -1] = np.nan
    valid_masked = replace(data, effects=x, measured=mask)
    valid_masked.validate()
    bad = replace(data, feature_ids=tuple(FEATURES[:-1]) + ("G00",))
    with pytest.raises(ValueError, match="duplicate feature"):
        bad.validate()


def test_missing_donor_controls_and_guide_identity_drift_fail():
    data = planted()
    with pytest.raises(ValueError, match="no matched non-targeting controls"):
        donor_matched_effects(
            assay="TEST", source_sha256=SOURCE, feature_ids=("A",),
            guide_ids=("G1", "NT1"), donor_ids=("D1", "D2"),
            target_ids=("A", "NT"), is_control=(False, True),
            logcpm=np.array([[6.], [2.]]), measured_features=(True,),
        )
    targets = list(data.target_ids)
    targets[16] = "DIFFERENT_TARGET"
    with pytest.raises(ValueError, match="same guide assigned conflicting targets"):
        replace(data, target_ids=tuple(targets)).validate()


def test_target_without_scored_features_reports_not_estimable():
    data = planted()
    frozen = partition(data)
    # One measured column remains and is each target gene only for this test.
    target_ids = sorted(set(data.target_ids))
    fold = 0
    held = [t for t, f in frozen.target_to_fold if f == fold]
    assert held
    masks = np.zeros_like(data.measured)
    newx = np.full_like(data.effects, np.nan)
    index = {g: i for i, g in enumerate(FEATURES)}
    for row, target in enumerate(data.target_ids):
        col = index[target]
        masks[row, col] = True
        newx[row, col] = data.effects[row, col]
    only_own = replace(data, effects=newx, measured=masks)
    out = evaluate_target_excluded_baselines(only_own, frozen, fold)
    assert out["baselines"]["no_change"]["n_estimable_targets"] == 0
    assert out["baselines"]["no_change"]["macro_mae"] is None


def test_partition_exposure_is_never_invented():
    data = planted()
    with pytest.raises(ValueError, match="assay, declared exposure"):
        freeze_target_partition(
            target_ids=data.target_ids, guide_ids=data.guide_ids,
            donor_ids=data.donor_ids, assay=data.assay,
            source_sha256=SOURCE, exposure="PROSPECTIVE_EXTERNAL_CONFIRMED",
            seed="seed", n_folds=4,
        )


def test_partition_rejects_changed_source_root_and_same_targets_different_units():
    data = planted()
    frozen = partition(data)
    bad_root = replace(data, source_sha256="b" * 64)
    with pytest.raises(ValueError, match="source root differs"):
        select_fold(bad_root, frozen, 0)
    guides = list(data.guide_ids)
    for i, guide in enumerate(guides):
        if guide == "G00_guide":
            guides[i] = "G00_relabelled_guide"
    changed = replace(data, guide_ids=tuple(guides))
    changed.validate()
    assert set(changed.target_ids) == set(data.target_ids)
    with pytest.raises(ValueError, match="row census differs"):
        select_fold(changed, frozen, 0)
