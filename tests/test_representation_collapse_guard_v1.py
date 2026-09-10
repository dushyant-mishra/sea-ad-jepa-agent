import pathlib
import sys
import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v5.representation_collapse_guard_v1 import (
    RepresentationCollapseThresholdAuthorityV1,
    qualify_representation_against_collapse,
    summarize_representation_geometry,
)


def authority(**kw):
    base = dict(
        minimum_centered_rms=0.1,
        minimum_active_dimension_fraction=0.5,
        minimum_effective_rank_fraction=0.3,
        maximum_top_variance_fraction=0.8,
        calibration_authority_id="cal-v1",
        thresholds_frozen_before_candidate_model_outcome=True,
        threshold_provenance="PROSPECTIVE_PREMODEL",
    )
    base.update(kw)
    return RepresentationCollapseThresholdAuthorityV1(**base)


def healthy():
    rng = np.random.default_rng(7)
    return rng.normal(size=(128, 8))


def test_summary_has_no_threshold_decision():
    s = summarize_representation_geometry(healthy())
    assert s["thresholds_applied"] is False
    assert 0 < s["effective_rank_fraction"] <= 1


def test_healthy_geometry_can_pass_but_never_authorizes_training():
    s = summarize_representation_geometry(healthy())
    out = qualify_representation_against_collapse(s, authority=authority(), representation_id="z_bio")
    assert out["passed"] is True
    assert out["training_authorized"] is False


def test_exact_constant_embedding_stops():
    s = summarize_representation_geometry(np.ones((64, 8)))
    with pytest.raises(RuntimeError, match="REPRESENTATION_COLLAPSE"):
        qualify_representation_against_collapse(s, authority=authority(), representation_id="z_bio")


def test_rank_one_embedding_stops_on_effective_rank_or_top_share():
    v = np.linspace(-1, 1, 128)[:, None]
    x = v @ np.arange(1, 9, dtype=float)[None, :]
    s = summarize_representation_geometry(x)
    assert s["active_dimension_fraction"] == 1.0
    with pytest.raises(RuntimeError, match="REPRESENTATION_COLLAPSE"):
        qualify_representation_against_collapse(s, authority=authority(), representation_id="z_bio")


def test_dead_coordinates_can_be_caught_even_when_total_variance_is_large():
    rng = np.random.default_rng(4)
    x = np.zeros((128, 8)); x[:, :2] = rng.normal(size=(128, 2)) * 100
    s = summarize_representation_geometry(x)
    assert s["centered_rms"] > 1
    with pytest.raises(RuntimeError, match="active_dimension_fraction"):
        qualify_representation_against_collapse(s, authority=authority(minimum_effective_rank_fraction=0.0, maximum_top_variance_fraction=1.0), representation_id="z_bio")


def test_near_constant_requires_external_scale_threshold():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(64, 8)) * 1e-14
    s = summarize_representation_geometry(x)
    with pytest.raises(RuntimeError, match="centered_rms"):
        qualify_representation_against_collapse(s, authority=authority(), representation_id="z_bio")


def test_checkpoint_derived_thresholds_rejected():
    s = summarize_representation_geometry(healthy())
    with pytest.raises(ValueError, match="prospective"):
        qualify_representation_against_collapse(s, authority=authority(threshold_provenance="CHECKPOINT_DERIVED"), representation_id="z_bio")


def test_thresholds_must_be_frozen_before_model_outcome():
    s = summarize_representation_geometry(healthy())
    with pytest.raises(ValueError, match="before candidate-model outcome"):
        qualify_representation_against_collapse(s, authority=authority(thresholds_frozen_before_candidate_model_outcome=False), representation_id="z_bio")


def test_nonfinite_embedding_rejected():
    x = healthy(); x[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        summarize_representation_geometry(x)


def test_boolean_threshold_is_not_accepted_as_numeric():
    s = summarize_representation_geometry(healthy())
    with pytest.raises(ValueError, match="explicit numeric"):
        qualify_representation_against_collapse(s, authority=authority(minimum_centered_rms=True), representation_id="z_bio")
