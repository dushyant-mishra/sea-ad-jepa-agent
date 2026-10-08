"""Independent synthetic red-team: guide imbalance must not impersonate donors.

This test plants numbers solely to challenge weighting. NOT biological evidence.
"""
import numpy as np

from sea_ad_jepa.perturbation.benchmark_target_holdout_v1 import (
    GuideDonorEffects, evaluate_target_excluded_baselines,
    freeze_target_partition, training_baselines,
)


def fixture_unequal_guides():
    # G00: D1 has 8 guides with +10 response, D2 has 1 guide with 0.
    # G01: one guide in each donor, both zero. All units are synthetic.
    guide_ids = tuple(
        [f"G00_D1_{i}" for i in range(8)]
        + ["G00_D2_0", "G01_D1_0", "G01_D2_0"]
    )
    donor_ids = tuple(["D1"] * 8 + ["D2", "D1", "D2"])
    target_ids = tuple(["G00"] * 9 + ["G01", "G01"])
    effect = np.zeros((11, 3), dtype=float)
    effect[:8, -1] = 10.0  # intentionally extreme planted downstream signal
    return GuideDonorEffects(
        assay="SYNTHETIC_ONLY_CRISPRI",
        source_sha256="a" * 64,
        feature_ids=("G00", "G01", "DOWNSTREAM"),
        guide_ids=guide_ids, donor_ids=donor_ids, target_ids=target_ids,
        effects=effect, measured=np.ones(effect.shape, dtype=bool),
    )


def partition(data):
    return freeze_target_partition(
        target_ids=data.target_ids, guide_ids=data.guide_ids,
        donor_ids=data.donor_ids, feature_ids=data.feature_ids,
        assay=data.assay, source_sha256=data.source_sha256,
        exposure="DEVELOPMENT", seed="BEFORE_FAKE_OUTCOMES", n_folds=2,
    )


def test_train_baseline_is_equal_target_then_equal_donor_not_equal_guide():
    data = fixture_unequal_guides()
    mean, _ = training_baselines(data, np.ones(11, dtype=bool))
    # G00 donor-uniform mean (10+0)/2=5; G01 donor-uniform mean 0.
    # Both targets get equal weight => 2.5.
    assert mean[-1] == 2.5
    assert mean[-1] != 8 * 10 / 11  # pooled-row estimate would be wrong


def test_heldout_target_score_is_donor_uniform_despite_8_to_1_guides():
    data = fixture_unequal_guides()
    frozen = partition(data)
    fold = dict(frozen.target_to_fold)["G00"]
    report = evaluate_target_excluded_baselines(data, frozen, fold)
    row = report["baselines"]["no_change"]["per_target"][0]
    assert row["target"] == "G00"
    assert row["status"] == "ESTIMABLE"
    # Exclude G00; score zero G01 and measured DOWNSTREAM.
    # D1 MAE 5, D2 MAE 0 => target MAE (5+0)/2 = 2.5.
    assert row["mae"] == 2.5
    assert row["n_donors"] == 2
    assert row["n_guides"] == 9
    assert row["n"] == 18
    assert {x["donor"] for x in row["per_donor"]} == {"D1", "D2"}
    assert report["scoring_geometry"].startswith("EQUAL_TARGET_THEN_EQUAL_DONOR")
    # Pooled-row MAE would be 8*5/9; tested geometry must not yield that.
    assert row["mae"] != 8 * 5 / 9


def test_duplicating_one_donor_guides_does_not_shift_target_or_macro_estimate():
    data = fixture_unequal_guides()
    frozen = partition(data)
    fold = dict(frozen.target_to_fold)["G00"]
    original = evaluate_target_excluded_baselines(data, frozen, fold)
    original_score = original["baselines"]["no_change"]["macro_mae"]
    # Duplicate an arbitrary D1 guide's measurement with a new guide ID.
    from dataclasses import replace
    new = replace(
        data,
        guide_ids=data.guide_ids + ("G00_D1_extra",),
        donor_ids=data.donor_ids + ("D1",),
        target_ids=data.target_ids + ("G00",),
        effects=np.vstack([data.effects, data.effects[0]]),
        measured=np.vstack([data.measured, data.measured[0]]),
    )
    changed = evaluate_target_excluded_baselines(
        new, partition(new), dict(partition(new).target_to_fold)["G00"],
    )
    assert changed["baselines"]["no_change"]["macro_mae"] == original_score
