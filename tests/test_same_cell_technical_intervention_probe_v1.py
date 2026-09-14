import copy

import numpy as np
import pytest

from sea_ad_jepa.v5.same_cell_technical_intervention_probe_v1 import (
    SameCellInterventionThresholdAuthorityV1,
    _cosine_rows,
    qualify_same_cell_intervention,
    seal_same_cell_intervention_receipt_v1,
    summarize_same_cell_intervention,
    validate_same_cell_intervention_receipt_v1,
)


def data():
    rng=np.random.default_rng(7)
    bio=rng.normal(size=(64,8))
    obs=rng.normal(size=(64,4))
    bio2=bio + 0.001*rng.normal(size=bio.shape)
    obs2=obs + 0.5*rng.normal(size=obs.shape)
    return bio,bio2,obs,obs2


def summary():
    bio,bio2,obs,obs2=data()
    return summarize_same_cell_intervention(
        stable_cell_keys=[f"c{i}" for i in range(64)],
        intervention="MEASUREMENT_DEPTH",
        z_bio_baseline=bio,z_bio_perturbed=bio2,
        z_obs_baseline=obs,z_obs_perturbed=obs2,
    )


def test_same_cell_summary_separates_stable_biology_from_responsive_observation():
    s=summary()
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


def test_cosine_rows_distinguishes_asymmetric_zero_from_both_zero():
    nonzero=np.array([[1.0,0.0],[0.0,2.0]],dtype=np.float64)
    zeros=np.zeros_like(nonzero)
    assert np.array_equal(_cosine_rows(nonzero,zeros),np.array([0.0,0.0]))
    assert np.array_equal(_cosine_rows(zeros,nonzero),np.array([0.0,0.0]))
    assert np.array_equal(_cosine_rows(zeros,zeros),np.array([1.0,1.0]))


def test_cosine_rows_is_stable_for_finite_extreme_and_near_zero_scales():
    a=np.array([[1e308,1e308],[1e-308,0.0]],dtype=np.float64)
    b=a.copy()
    result=_cosine_rows(a,b)
    assert np.isfinite(result).all()
    assert np.allclose(result,np.ones(2),rtol=0.0,atol=1e-15)


def test_same_cell_receipt_binds_parent_plan_strength_and_identity_preservation():
    env=seal_same_cell_intervention_receipt_v1(
        summary=summary(),
        parent_sha256="a"*64,
        intervention_plan_sha256="b"*64,
        intervention_strength=0.20,
        intervention_strength_frozen_before_execution=True,
        stable_row_identity_preserved=True,
        donor_identity_preserved=True,
        operator_identity_preserved=True,
        source_identity_preserved=True,
    )
    out=validate_same_cell_intervention_receipt_v1(
        env,parent_sha256="a"*64,intervention_plan_sha256="b"*64,
    )
    assert out["authority_classification"] == "MEASUREMENT_ROBUSTNESS_ONLY__NOT_D_SHARED_AUTHORITY"
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["training_authorized"] is False


def test_same_cell_receipt_rejects_parent_substitution():
    env=seal_same_cell_intervention_receipt_v1(
        summary=summary(),parent_sha256="a"*64,intervention_plan_sha256="b"*64,
        intervention_strength=0.20,intervention_strength_frozen_before_execution=True,
        stable_row_identity_preserved=True,donor_identity_preserved=True,
        operator_identity_preserved=True,source_identity_preserved=True,
    )
    with pytest.raises(RuntimeError,match="STOP_V5_ARTIFACT_PARENT_MISMATCH"):
        validate_same_cell_intervention_receipt_v1(
            env,parent_sha256="c"*64,intervention_plan_sha256="b"*64,
        )


def test_same_cell_receipt_rejects_adaptive_strength_or_identity_change():
    base=dict(
        summary=summary(),parent_sha256="a"*64,intervention_plan_sha256="b"*64,
        intervention_strength=0.20,intervention_strength_frozen_before_execution=True,
        stable_row_identity_preserved=True,donor_identity_preserved=True,
        operator_identity_preserved=True,source_identity_preserved=True,
    )
    for field in (
        "intervention_strength_frozen_before_execution",
        "stable_row_identity_preserved",
        "donor_identity_preserved",
        "operator_identity_preserved",
        "source_identity_preserved",
    ):
        bad=base.copy(); bad[field]=False
        with pytest.raises(RuntimeError,match="STOP_SAME_CELL_RECEIPT"):
            seal_same_cell_intervention_receipt_v1(**bad)


def test_same_cell_receipt_rejects_outcome_feedback_and_authority_escalation():
    base=dict(
        summary=summary(),parent_sha256="a"*64,intervention_plan_sha256="b"*64,
        intervention_strength=0.20,intervention_strength_frozen_before_execution=True,
        stable_row_identity_preserved=True,donor_identity_preserved=True,
        operator_identity_preserved=True,source_identity_preserved=True,
    )
    for field in ("d_shared_outcomes_used","protected_data_used","pathology_used","training_authorized"):
        bad=base.copy(); bad[field]=True
        with pytest.raises(RuntimeError,match="STOP_SAME_CELL_RECEIPT_FORBIDDEN"):
            seal_same_cell_intervention_receipt_v1(**bad)


def test_same_cell_receipt_requires_explicit_positive_finite_strength():
    base=dict(
        summary=summary(),parent_sha256="a"*64,intervention_plan_sha256="b"*64,
        intervention_strength_frozen_before_execution=True,
        stable_row_identity_preserved=True,donor_identity_preserved=True,
        operator_identity_preserved=True,source_identity_preserved=True,
    )
    for value in (0.0,-0.1,float("nan"),True):
        with pytest.raises(ValueError):
            seal_same_cell_intervention_receipt_v1(**base,intervention_strength=value)
