"""Synthetic tests for retrospective target-profile baselines (NO new biology)."""
from dataclasses import replace
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.perturbation.benchmark_screen_profile_baselines_v1 import (
    ScreenBaselineError, ScreenProfiles, fixed_target_folds,
    load_verified_screen_gzip, score_retrospective_baselines,
)


def profiles():
    targets = tuple("T%d" % i for i in range(10))
    genes = targets + ("SHARED",)
    x = np.zeros((10, len(genes)), dtype=float)
    x[:, -1] = 2.0
    for i in range(10):
        x[i, i] = -100.0  # massive self-engagement must never count as downstream
    return ScreenProfiles("SYNTHETIC_SAME_SCREEN", "a" * 64, targets, genes, x)


def test_target_heldout_macro_and_all_self_gene_excluded():
    p = profiles()
    r = score_retrospective_baselines(p, seed="FIXED", n_folds=5)
    assert r["targets"] == r["targets_estimable"] == 10
    assert r["biological_uncertainty_estimable"] is False
    assert r["independent_confirmation_authorized"] is False
    assert r["jepa_training_authorized"] is False
    assert r["exposure"] == "DEVELOPMENT_RETROSPECTIVE_ALREADY_INSPECTED"
    assert all(x["scored_genes"] == 10 for x in r["per_target"])
    # For a target's own row the -100 own-gene signal is excluded;
    # no-change error therefore comes only from the common downstream +2.
    assert r["macro"]["no_change_mae"] == pytest.approx(0.2)


def test_split_reproducible_without_outcome_dependency():
    p = profiles()
    f = fixed_target_folds(p, seed="FIXED")
    assert f == fixed_target_folds(replace(p, effects=p.effects * 1000), seed="FIXED")
    assert f != fixed_target_folds(p, seed="DIFFERENT")
    assert set(f.values()) == set(range(5))


def test_holdout_outcomes_do_not_influence_training_mean():
    p = profiles()
    fold = fixed_target_folds(p, seed="FIXED")
    target = next(t for t in p.targets if fold[t] == 0)
    i = p.targets.index(target)
    x = p.effects.copy()
    x[i, :] = 5000
    # Modifying one target in the fold being evaluated cannot change its
    # competitors' training fit for that fold; other folds remain development.
    before = score_retrospective_baselines(p, seed="FIXED")
    after = score_retrospective_baselines(replace(p, effects=x), seed="FIXED")
    b = {r["target"]: r for r in before["per_target"]}
    a = {r["target"]: r for r in after["per_target"]}
    other_same_fold = next(t for t in p.targets if t != target and fold[t] == 0)
    assert a[other_same_fold] == b[other_same_fold]


def test_training_only_responsive_selection_ignores_heldout_outcomes():
    p = profiles()
    before = score_retrospective_baselines(p, seed="FIXED")
    folds = fixed_target_folds(p, seed="FIXED")
    heldout = [p.targets.index(t) for t, fold in folds.items() if fold == 0]
    x = p.effects.copy()
    x[heldout, :] += 10_000
    after = score_retrospective_baselines(replace(p, effects=x), seed="FIXED")
    assert (
        before["responsive_subset"]["selection_digest_by_fold"]["0"]
        == after["responsive_subset"]["selection_digest_by_fold"]["0"]
    )
    assert before["responsive_subset"]["scope"] == "SECONDARY_DEVELOPMENT_DIAGNOSTIC"
    assert before["responsive_subset"]["macro_no_change_mae"] is not None


def test_missing_feature_is_not_silently_zero_filled():
    p = profiles()
    x = p.effects.copy()
    x[:, -1] = np.nan
    r = score_retrospective_baselines(replace(p, effects=x), seed="FIXED")
    assert r["targets_estimable"] == 10
    assert all(row["scored_genes"] == 9 for row in r["per_target"])


def test_duplicate_gene_and_infinite_result_fail_closed():
    p = profiles()
    with pytest.raises(ScreenBaselineError, match="duplicate"):
        replace(p, genes=p.genes[:-1] + (p.genes[0],)).validate()
    x = p.effects.copy()
    x[0, 0] = np.inf
    with pytest.raises(ScreenBaselineError, match="infinite"):
        replace(p, effects=x).validate()


def test_realistic_verified_gzip_fixture_and_tampering(tmp_path):
    csv_text = "name,Gene,Log2FC\nT1,T1,-1\nT1,A,0.5\nT2,T2,-2\nT2,A,0\n"
    path = tmp_path / "data.csv.gz"
    with gzip.open(path, "wt") as fh:
        fh.write(csv_text)
    digest = hashlib.sha256(csv_text.encode()).hexdigest()
    loaded = load_verified_screen_gzip(path, screen="SYNTHETIC", expected_csv_sha256=digest)
    assert loaded.targets == ("T1", "T2")
    assert loaded.effects.shape == (2, 3)
    assert np.isnan(loaded.effects[0, loaded.genes.index("T2")])
    assert loaded.effects[1, loaded.genes.index("A")] == 0.0
    with pytest.raises(ScreenBaselineError, match="SHA256 mismatch"):
        load_verified_screen_gzip(path, screen="SYNTHETIC", expected_csv_sha256="f" * 64)


def test_duplicate_original_source_rows_fail(tmp_path):
    text = "name,Gene,Log2FC\nT1,A,0.2\nT1,A,0.3\n"
    path = tmp_path / "duplicate.csv.gz"
    with gzip.open(path, "wt") as fh:
        fh.write(text)
    with pytest.raises(ScreenBaselineError, match="duplicate original"):
        load_verified_screen_gzip(
            path, screen="SYNTHETIC",
            expected_csv_sha256=hashlib.sha256(text.encode()).hexdigest(),
        )


def test_no_same_screen_external_replication_claim():
    r = score_retrospective_baselines(profiles(), seed="FIXED")
    assert "SAME_EXPERIMENT" in r["split_kind"]
    assert r["brain_causal_generalization_authorized"] is False
    assert r["therapeutic_ranking_authorized"] is False
