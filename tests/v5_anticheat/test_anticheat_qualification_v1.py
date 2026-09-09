from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.anticheat_qualification_v1 import (
    AntiCheatQualificationError,
    BLOCKED,
    FAIL,
    PASS,
    balanced_accuracy,
    categorical_group_holdout_attack,
    categorical_purity,
    collapse_negative_control_report,
    cosine_centroid_memorization_attack,
    deterministic_group_folds,
    hardware_invariance_replay,
    latent_health_metrics,
    mask_row_sha256,
    proposal_p_over_q_audit,
    qualification_skeleton,
    quantile_scalar_group_holdout_attack,
    response_curve_against_full_evidence,
    split_manifest_for_entities,
    state_count_features,
)


def test_group_folds_are_row_order_invariant_by_identity():
    g = np.array(["a", "b", "a", "c", "b", "d"])
    f = deterministic_group_folds(g, n_folds=3, salt="x")
    assert f[0] == f[2]
    assert f[1] == f[4]
    mapping = {k: f[np.where(g == k)[0][0]] for k in np.unique(g)}
    rev = g[::-1]
    f2 = deterministic_group_folds(rev, n_folds=3, salt="x")
    mapping2 = {k: f2[np.where(rev == k)[0][0]] for k in np.unique(rev)}
    assert mapping == mapping2


def test_balanced_accuracy_not_raw_accuracy():
    y = np.array(["a"] * 9 + ["b"])
    p = np.array(["a"] * 10)
    assert balanced_accuracy(y, p) == pytest.approx(0.5)


def test_categorical_purity_and_group_attack_detect_shortcut():
    groups = np.array([f"d{i}" for i in range(20) for _ in range(4)])
    labels = np.array(["A", "A", "B", "B"] * 20)
    feature = labels.copy()
    assert categorical_purity(feature, labels)["weighted_purity"] == 1.0
    out = categorical_group_holdout_attack(feature, labels, groups, n_folds=5, salt="cat")
    assert out["balanced_accuracy"] == 1.0


def test_quantile_depth_attack_reports_grid_without_freezing_best():
    groups = np.array([f"d{i}" for i in range(40) for _ in range(5)])
    labels = np.array(["LOW" if i < 20 else "HIGH" for i in range(40) for _ in range(5)])
    values = np.array([float(i) for i in range(40) for _ in range(5)])
    out = quantile_scalar_group_holdout_attack(values, labels, groups, bin_grid=(4, 8), n_folds=5, salt="depth")
    assert [r["requested_bins"] for r in out["grid"]] == [4, 8]
    assert out["max_descriptive_balanced_accuracy"] > 0.7


def test_mask_hash_and_state_counts_are_exact():
    states = np.array([[0, 1, 1, 2], [0, 1, 1, 2], [1, 1, 1, 1]], dtype=np.uint8)
    h = mask_row_sha256(states)
    assert h[0] == h[1]
    assert h[0] != h[2]
    assert state_count_features(states).tolist() == [
        [1.0, 2.0, 1.0],
        [1.0, 2.0, 1.0],
        [0.0, 4.0, 0.0],
    ]


def test_donor_memorization_probe_detects_identity_geometry():
    rng = np.random.default_rng(1)
    labels = np.repeat(["d0", "d1", "d2"], 30)
    keys = np.arange(len(labels))
    centers = {
        "d0": np.array([1.0, 0.0, 0.0]),
        "d1": np.array([0.0, 1.0, 0.0]),
        "d2": np.array([0.0, 0.0, 1.0]),
    }
    z = np.stack([centers[x] + 0.01 * rng.normal(size=3) for x in labels])
    out = cosine_centroid_memorization_attack(z, labels, keys, test_modulus=4, test_bucket=0)
    assert out["balanced_accuracy"] > 0.95


def test_split_manifest_leaves_low_cardinality_source_out_exactly():
    out = split_manifest_for_entities({"source": np.array(["A", "A", "B", "C", "C"])}, leave_one_out_max_levels=8)
    assert out["source"]["mode"] == "leave_one_entity_out"
    assert out["source"]["fold_count"] == 3


def test_latent_health_detects_constant_and_rank1_controls():
    rng = np.random.default_rng(3)
    z = rng.normal(size=(200, 8))
    assert latent_health_metrics(z)["entropy_effective_rank"] > 5
    report = collapse_negative_control_report(z)
    assert report["status"] == PASS
    assert report["constant_control"]["entropy_effective_rank"] == 0.0
    assert report["rank1_control"]["entropy_effective_rank"] <= 1.000001


def test_proposal_p_over_q_identity_and_uniform_donor_mass():
    p = np.array([0.25, 0.25, 0.25, 0.25])
    q = np.array([0.1, 0.4, 0.2, 0.3])
    donors = np.array(["a", "a", "b", "b"])
    out = proposal_p_over_q_audit(p, q, donor_labels=donors)
    assert out["q_expectation_of_p_over_q"] == pytest.approx(1.0)
    assert out["max_abs_donor_mass_deviation_from_uniform"] == pytest.approx(0.0)
    assert out["importance_weight_ratio"] > 1.0


def test_proposal_support_gap_fails_closed():
    with pytest.raises(AntiCheatQualificationError, match="support gap"):
        proposal_p_over_q_audit(np.array([0.5, 0.5]), np.array([1.0, 0.0]))


def test_response_curve_reports_nonmonotone_behavior():
    full = np.array([[1.0, 0.0], [0.0, 1.0]])
    e20 = np.array([[0.7, 0.7], [0.7, 0.7]])
    e60 = np.array([[0.2, 0.98], [0.98, 0.2]])
    out = response_curve_against_full_evidence({0.2: e20, 0.6: e60, 1.0: full})
    assert out["cell_step_monotonicity_violation_rate"] > 0.0
    assert out["fractions"][-1]["mean_cosine_drift"] == pytest.approx(0.0)


def test_hardware_invariance_exact_and_failure():
    a = np.arange(12, dtype=np.int64).reshape(3, 4)
    assert hardware_invariance_replay(a, a.copy())["status"] == PASS
    b = a.copy()
    b[0, 0] += 1
    assert hardware_invariance_replay(a, b)["status"] == FAIL


def test_qualification_skeleton_is_fail_closed():
    q = qualification_skeleton(input_shortcut_atlas={"x": 1})
    assert q["cheat_qualified"] is False
    assert q["training_authorized"] is False
    assert all(v["status"] == BLOCKED for v in q["checkpoint_gates"].values())
