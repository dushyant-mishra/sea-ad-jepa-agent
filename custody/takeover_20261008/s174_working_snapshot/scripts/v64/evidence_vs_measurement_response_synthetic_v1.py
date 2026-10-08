#!/usr/bin/env python3
"""Synthetic separation of biological-evidence and measurement-quality response curves.

Software semantics only. Evidence fraction changes WHICH distinct biological features are
available. Measurement depth holds feature identity fixed and changes only measurement
noise. No real data, no production thresholds, no biological calibration.
"""
from __future__ import annotations
import json
import numpy as np

SEED=6703
N_DONORS=80
CELLS_PER_DONOR=30
K=4
P=40
EVIDENCE_FRACTIONS=(0.20,0.40,0.60,0.80,1.00)
DEPTH_FRACTIONS=(0.25,0.50,0.75,1.00)

def add_bias(x):
    return np.column_stack([np.ones(len(x)),np.asarray(x,float)])

def fit(x,y):
    b,*_=np.linalg.lstsq(add_bias(x),np.asarray(y,float),rcond=None)
    return b

def pred(x,b):
    return add_bias(x)@b

def mse(y,p):
    return float(np.mean(np.square(np.asarray(y)-np.asarray(p))))

def fixture():
    rng=np.random.default_rng(SEED)
    donor=np.repeat(np.arange(N_DONORS),CELLS_PER_DONOR)
    donor_state=rng.normal(scale=.45,size=(N_DONORS,K))
    z=rng.normal(size=(len(donor),K))+donor_state[donor]
    w=rng.normal(size=(K,P))
    signal=z@w
    base_noise=rng.normal(size=signal.shape)
    feature_order=rng.permutation(P)
    train=donor<60
    val=~train
    return dict(donor=donor,z=z,signal=signal,base_noise=base_noise,
                feature_order=feature_order,train=train,val=val)

def _curve_errors(d, evidence_override_same_subset=False, depth_override_fixed_noise=False):
    tr,va=d["train"],d["val"]
    evidence=[]
    n20=max(1,int(round(P*EVIDENCE_FRACTIONS[0])))
    for f in EVIDENCE_FRACTIONS:
        n=max(1,int(round(P*f)))
        idx=d["feature_order"][:(n20 if evidence_override_same_subset else n)]
        x=d["signal"][:,idx]+0.30*d["base_noise"][:,idx]
        b=fit(x[tr],d["z"][tr])
        evidence.append({"fraction":float(f),"n_features":int(len(idx)),
                         "mse_to_true_state":mse(d["z"][va],pred(x[va],b))})

    depth=[]
    idx=np.arange(P)
    for dep in DEPTH_FRACTIONS:
        effective=DEPTH_FRACTIONS[0] if depth_override_fixed_noise else dep
        # Same biological evidence; higher depth means lower measurement noise.
        x=d["signal"][:,idx]+(0.50/np.sqrt(effective))*d["base_noise"][:,idx]
        b=fit(x[tr],d["z"][tr])
        depth.append({"depth_fraction":float(dep),"n_features":P,
                      "mse_to_true_state":mse(d["z"][va],pred(x[va],b))})
    return evidence,depth

def strictly_improves(curve,key,minimum_relative_gain):
    vals=np.array([x[key] for x in curve],float)
    nonincreasing=bool(np.all(np.diff(vals)<=1e-12))
    gain=float((vals[0]-vals[-1])/vals[0]) if vals[0]>0 else 0.0
    return nonincreasing and gain>minimum_relative_gain,nonincreasing,gain

def run_smoke(evidence_override_same_subset=False, depth_override_fixed_noise=False):
    d=fixture()
    evidence,depth=_curve_errors(d,evidence_override_same_subset,depth_override_fixed_noise)
    ev_ok,ev_mono,ev_gain=strictly_improves(evidence,"mse_to_true_state",0.25)
    dp_ok,dp_mono,dp_gain=strictly_improves(depth,"mse_to_true_state",0.10)
    gates={
        "evidence_curve_converges_as_distinct_features_are_added":ev_ok,
        "measurement_curve_converges_as_noise_falls_at_fixed_features":dp_ok,
        "evidence_feature_count_reaches_full_panel":evidence[-1]["n_features"]==P,
        "measurement_feature_identity_is_fixed":all(x["n_features"]==P for x in depth),
    }
    return {
      "schema":"V67_EVIDENCE_VS_MEASUREMENT_RESPONSE_SYNTHETIC_V1",
      "status":"SYNTHETIC_SOFTWARE_SEMANTICS_ONLY",
      "fixture":{"seed":SEED,"donors":N_DONORS,"cells_per_donor":CELLS_PER_DONOR,
                 "latent_rank":K,"features":P},
      "evidence_response":{"meaning":"add distinct biological evidence at fixed measurement noise",
                           "curve":evidence,"monotonic_nonincreasing":ev_mono,
                           "relative_error_reduction":ev_gain},
      "measurement_response":{"meaning":"same biological evidence at improving measurement precision",
                              "curve":depth,"monotonic_nonincreasing":dp_mono,
                              "relative_error_reduction":dp_gain},
      "counterfactual_flags":{"same_evidence_subset_at_all_fractions":bool(evidence_override_same_subset),
                              "fixed_noise_at_all_depths":bool(depth_override_fixed_noise)},
      "gates":gates,
      "pass":bool(all(gates.values())),
      "interpretation":{
        "qualified":"software distinction between biological-evidence response and measurement-quality response",
        "not_qualified":"real biological uncertainty calibration, real depth calibration, production evidence fractions, or training authority"
      },
      "governance":{"real_data_used":False,"training":"OFF","stage4":"NOT_AUTHORIZED",
                    "Morabito":"PROTECTED","TD60":"BLOCKED"}
    }

def main():
    o=run_smoke()
    print(json.dumps(o,indent=2,sort_keys=True))
    return 0 if o["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
