import numpy as np
import pytest

from sea_ad_jepa.v5.same_cell_technical_intervention_probe_v1 import (
    SameCellInterventionThresholdAuthorityV1,
    qualify_same_cell_intervention,
    summarize_same_cell_intervention,
)

def data():
    rng=np.random.default_rng(7)
    bio=rng.normal(size=(64,8))
    obs=rng.normal(size=(64,4))
    bio2=bio + 0.001*rng.normal(size=bio.shape)
    obs2=obs + 0.5*rng.normal(size=obs.shape)
    return bio,bio2,obs,obs2

def test_same_cell_summary_separates_stable_biology_from_responsive_observation():
    bio,bio2,obs,obs2=data()
    s=summarize_same_cell_intervention(
        stable_cell_keys=[f"c{i}" for i in range(64)],
        intervention="MEASUREMENT_DEPTH",
        z_bio_baseline=bio,z_bio_perturbed=bio2,
        z_obs_baseline=obs,z_obs_perturbed=obs2,
    )
    assert s["bio_median_relative_l2"] < 0.01
    assert s["obs_median_relative_l2"] > 0.1
    assert s["thresholds_applied"] is False

def test_qualification_requires_explicit_threshold_authority_and_passes_good_case():
    bio,bio2,obs,obs2=data()
    s=summarize_same_cell_intervention(
        stable_cell_keys=[f"c{i}" for i in range(64)],
        intervention="MASK_IDENTITY",
        z_bio_baseline=bio,z_bio_perturbed=bio2,
        z_obs_baseline=obs,z_obs_perturbed=obs2,
    )
    t=SameCellInterventionThresholdAuthorityV1(
        max_bio_median_relative_l2=0.01,
        max_bio_p95_relative_l2=0.02,
        min_bio_median_cosine=0.999,
        min_obs_median_relative_l2=0.1,
        max_bio_to_obs_median_delta_ratio=0.1,
        calibration_authority_id="CALIBRATION_ONLY",
    )
    assert qualify_same_cell_intervention(s,thresholds=t)["passed"]

def test_bad_biology_drift_stops_even_when_observation_moves():
    bio,bio2,obs,obs2=data(); bio2=bio+0.5
    s=summarize_same_cell_intervention(
        stable_cell_keys=[f"c{i}" for i in range(64)],intervention="SUPPORT_FAMILY",
        z_bio_baseline=bio,z_bio_perturbed=bio2,z_obs_baseline=obs,z_obs_perturbed=obs2,
    )
    t=SameCellInterventionThresholdAuthorityV1(0.01,0.02,0.99,0.1,0.1,"CAL")
    with pytest.raises(RuntimeError,match="STOP_SAME_CELL"):
        qualify_same_cell_intervention(s,thresholds=t)

def test_unknown_intervention_and_misaligned_keys_are_rejected():
    bio,bio2,obs,obs2=data()
    with pytest.raises(ValueError,match="unsupported"):
        summarize_same_cell_intervention(stable_cell_keys=[f"c{i}" for i in range(64)],intervention="SOURCE",
            z_bio_baseline=bio,z_bio_perturbed=bio2,z_obs_baseline=obs,z_obs_perturbed=obs2)
    with pytest.raises(ValueError,match="stable_cell_keys"):
        summarize_same_cell_intervention(stable_cell_keys=["x"]*64,intervention="MASK_IDENTITY",
            z_bio_baseline=bio,z_bio_perturbed=bio2,z_obs_baseline=obs,z_obs_perturbed=obs2)

def test_threshold_authority_has_no_defaults():
    import inspect
    sig=inspect.signature(SameCellInterventionThresholdAuthorityV1)
    assert all(p.default is inspect._empty for p in sig.parameters.values())
