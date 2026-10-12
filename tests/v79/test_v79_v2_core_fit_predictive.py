from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_fit_model as M  # noqa: E402
import v79_v2_core_fit_predictive as P  # noqa: E402


def _design():
    return {
        "src":np.array([0,0,0,0,1,1,1,1,2,2,2,2]),
        "donor":np.array([0,0,1,1,2,2,3,3,4,4,5,5]),
        "cls":np.array([0,1,2,0,1,2,0,1,2,0,1,2]),
        "log_lib":np.linspace(1.0,2.1,12),
    }


def _samples(part:str, draws=120):
    d=M.prepare_design(_design()); nb=d["donor_basis_by_donor"].shape[1]; shape=(2,draws)
    s={"alpha":np.zeros(shape),"class_contrasts":np.zeros(shape+(2,)),"source_contrasts":np.zeros(shape+(2,)),
       "donor_sd":np.zeros(shape),"donor_raw":np.zeros(shape+(nb,))}
    if part=="detection":
        s["beta_depth1"]=np.zeros(shape); s["beta_depth2"]=np.zeros(shape)
    else:
        s["gamma_depth1"]=np.zeros(shape); s["gamma_depth2"]=np.zeros(shape); s["sigma"]=np.ones(shape)
    return s


def test_evenly_spaced_projection_is_exactly_200_and_deterministic():
    s=_samples("detection",draws=120)
    a=P.select_posterior_draws(s,stored_draws=200); b=P.select_posterior_draws(s,stored_draws=200)
    assert all(v.shape[0]==200 for v in a.values())
    assert all(np.array_equal(a[k],b[k]) for k in a)


def test_detection_same_donor_zero_linear_predictor_is_half_probability_and_log2_loss():
    design=_design(); y=np.array([0,1]*6,dtype=int); mask=np.ones(12,dtype=bool)
    out=P.detection_heldout_metrics(_samples("detection"),design=design,detected=y,measured_mask=mask,
                                    new_donor=False,posterior_draws=200,calibration_bins=10,gh_nodes=40)
    assert out["schema"]=="V79_V2_CORE_DETECTION_HELDOUT_V1" and out["replicate_mode"]=="same_donor"
    assert abs(out["mean_log_loss"]-math.log(2.0))<1e-12
    assert abs(out["predicted_prevalence"]-.5)<1e-12 and abs(out["observed_prevalence"]-.5)<1e-12
    assert sum(x["n"] for x in out["calibration_bins"])==12
    assert all("oracle" not in str(k).lower() for k in out)


def test_detection_new_donor_uses_40_node_gh_and_zero_sd_reduces_to_half_probability():
    design=_design(); y=np.array([0,1]*6,dtype=int); mask=np.ones(12,dtype=bool)
    out=P.detection_heldout_metrics(_samples("detection"),design=design,detected=y,measured_mask=mask,
                                    new_donor=True,posterior_draws=200,calibration_bins=10,gh_nodes=40)
    assert out["replicate_mode"]=="new_donor" and out["gauss_hermite_nodes"]==40
    assert abs(out["mean_log_loss"]-math.log(2.0))<1e-12


def test_positive_same_donor_zero_mu_unit_sigma_matches_standard_normal_lpd():
    design=_design(); observed=np.ones(12,dtype=float); mask=np.ones(12,dtype=bool)
    out=P.positive_heldout_metrics(_samples("positive"),design=design,observed=observed,positive_mask=mask,
                                   new_donor=False,posterior_draws=200,gh_nodes=40)
    want=-0.5*math.log(2.0*math.pi)
    assert out["schema"]=="V79_V2_CORE_POSITIVE_HELDOUT_V1" and out["replicate_mode"]=="same_donor"
    assert abs(out["mean_lpd"]-want)<1e-12 and out["n_positive"]==12


def test_positive_new_donor_uses_exact_40_node_gh_and_zero_sd_matches_same_donor():
    design=_design(); observed=np.ones(12,dtype=float); mask=np.ones(12,dtype=bool)
    out=P.positive_heldout_metrics(_samples("positive"),design=design,observed=observed,positive_mask=mask,
                                   new_donor=True,posterior_draws=200,gh_nodes=40)
    want=-0.5*math.log(2.0*math.pi)
    assert out["replicate_mode"]=="new_donor" and out["gauss_hermite_nodes"]==40
    assert abs(out["mean_lpd"]-want)<1e-12


def test_heldout_output_contains_no_truth_q_or_operator_identity():
    design=_design(); y=np.array([0,1]*6,dtype=int); mask=np.ones(12,dtype=bool)
    out=P.detection_heldout_metrics(_samples("detection"),design=design,detected=y,measured_mask=mask,
                                    new_donor=False,posterior_draws=200,calibration_bins=10,gh_nodes=40)
    raw=str(out).lower()
    for forbidden in ("truth","oracle","q00","q11","operator","matrix"):
        assert forbidden not in raw
