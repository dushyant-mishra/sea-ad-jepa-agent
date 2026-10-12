from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_descriptive as D  # noqa: E402


def _calibration(predicted: float, observed: float):
    rows=[]
    for b in range(10):
        rows.append({"bin_index":b,"lower":b/10,"upper":(b+1)/10,"n":0,"mean_predicted":None,"observed_rate":None})
    rows[2]={"bin_index":2,"lower":0.2,"upper":0.3,"n":10,"mean_predicted":predicted,"observed_rate":observed}
    return rows


def test_detection_heldout_preserves_frozen_calibration_and_prevalence_reporting():
    fid="a"*64
    receipts=[{
        "fit_id":fid,"part":"detection",
        "heldout_predictive":{
            "same_donor":{"schema":"V79_V2_CORE_DETECTION_HELDOUT_V1","replicate_mode":"same_donor","posterior_draws":200,
                "gauss_hermite_nodes":None,"n_measured":10,"mean_log_loss":0.7,"predicted_prevalence":0.25,
                "observed_prevalence":0.20,"calibration_bins":_calibration(0.25,0.20)},
            "new_donor":{"schema":"V79_V2_CORE_DETECTION_HELDOUT_V1","replicate_mode":"new_donor","posterior_draws":200,
                "gauss_hermite_nodes":40,"n_measured":10,"mean_log_loss":0.8,"predicted_prevalence":0.35,
                "observed_prevalence":0.30,"calibration_bins":_calibration(0.35,0.30)},
        },
    }]
    oracle={fid:{"planted_prevalence":0.03,
                 "same_donor":{"mean_log_loss":0.5},"new_donor":{"mean_log_loss":0.6}}}
    out=D.detection_heldout(receipts,oracle)
    assert out["gating"] is False
    assert math.isclose(out["same_donor"]["mean_model_minus_oracle_log_loss"],0.2)
    assert math.isclose(out["same_donor"]["mean_predicted_prevalence"],0.25)
    assert math.isclose(out["same_donor"]["mean_observed_prevalence"],0.20)
    assert math.isclose(out["same_donor"]["mean_predicted_minus_observed_prevalence"],0.05)
    assert len(out["same_donor"]["calibration_bins"])==10
    b=out["same_donor"]["calibration_bins"][2]
    assert b["n"]==10 and math.isclose(b["mean_predicted"],0.25) and math.isclose(b["observed_rate"],0.20)
    assert out["low_prevalence_lt_0_05"]["n_fits"]==1


def test_detection_heldout_refuses_non_frozen_calibration_schema():
    fid="b"*64
    receipts=[{"fit_id":fid,"part":"detection","heldout_predictive":{
        "same_donor":{"mean_log_loss":0.7,"predicted_prevalence":0.25,"observed_prevalence":0.20,"calibration_bins":[]},
        "new_donor":{"mean_log_loss":0.8,"predicted_prevalence":0.35,"observed_prevalence":0.30,"calibration_bins":[]},
    }}]
    oracle={fid:{"planted_prevalence":0.2,"same_donor":{"mean_log_loss":0.5},"new_donor":{"mean_log_loss":0.6}}}
    try:
        D.detection_heldout(receipts,oracle)
    except D.DescriptiveRefused:
        return
    raise AssertionError("empty/non-10-bin calibration must be refused")
