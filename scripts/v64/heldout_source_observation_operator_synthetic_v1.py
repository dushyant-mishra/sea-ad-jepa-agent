#!/usr/bin/env python3
"""Synthetic observation-operator calibration under leave-one-source-out transfer.

Software semantics only. The held-out source's observation descriptor is ESTIMATED from
an independent technical calibration channel; the planted source scale is used only to
generate data and is never supplied to the transfer model.
"""
from __future__ import annotations
import json
import numpy as np

SEED=6702
N_DONORS=90
CELLS_PER_DONOR=30
N_SOURCES=3
K=4
P=24
TRUE_CAPTURE=np.array([0.55,1.00,1.55],float)
CAL_REF=np.array([0.75,0.90,1.05,1.20,1.35,1.50],float)

def ridge(x,y,a=1e-6):
    x=np.asarray(x,float); y=np.asarray(y,float)
    xm=x.mean(0); ym=y.mean(0); xc=x-xm; yc=y-ym
    b=np.linalg.solve(xc.T@xc+a*np.eye(x.shape[1]),xc.T@y- xc.T@np.repeat(ym[None,:],len(xc),axis=0))
    return xm,ym,b

def predict(m,x):
    xm,ym,b=m
    return (np.asarray(x,float)-xm)@b+ym

def r2(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    return float(1-np.square(y-p).sum()/np.square(y-y.mean(0,keepdims=True)).sum())

def fixture():
    rng=np.random.default_rng(SEED)
    donor=np.repeat(np.arange(N_DONORS),CELLS_PER_DONOR)
    source=donor%N_SOURCES
    donor_state=rng.normal(scale=.5,size=(N_DONORS,K))
    z=rng.normal(size=(len(donor),K))+donor_state[donor]
    w=rng.normal(size=(K,P))
    x=TRUE_CAPTURE[source,None]*(z@w)+.15*rng.normal(size=(len(donor),P))
    # Technical controls measure acquisition scale but carry no z information.
    calibrator=TRUE_CAPTURE[source,None]*CAL_REF[None,:]+.06*rng.normal(
        size=(len(donor),len(CAL_REF)))
    return dict(donor=donor,source=source,z=z,x=x,calibrator=calibrator)

def estimate_capture(calibrator,source):
    est=np.zeros(N_SOURCES,float)
    for s in range(N_SOURCES):
        ratios=calibrator[source==s]/CAL_REF[None,:]
        est[s]=float(np.median(ratios))
    return est

def run_smoke(misspecify_heldout=1.0):
    d=fixture()
    estimated=estimate_capture(d["calibrator"],d["source"])
    per_source=[]
    for s in range(N_SOURCES):
        tr=d["source"]!=s; te=d["source"]==s
        raw=ridge(d["x"][tr],d["z"][tr])
        raw_r2=r2(d["z"][te],predict(raw,d["x"][te]))

        use=estimated.copy()
        use[s]*=float(misspecify_heldout)
        x_norm=d["x"]/use[d["source"],None]
        aware=ridge(x_norm[tr],d["z"][tr])
        aware_r2=r2(d["z"][te],predict(aware,x_norm[te]))

        per_source.append({
            "heldout_source":int(s),
            "heldout_source_absent_from_train":bool(s not in set(d["source"][tr].tolist())),
            "donor_overlap":len(set(d["donor"][tr].tolist())&set(d["donor"][te].tolist())),
            "true_capture_for_diagnostic_only":float(TRUE_CAPTURE[s]),
            "estimated_capture_from_technical_controls":float(estimated[s]),
            "relative_estimation_error":float(abs(estimated[s]-TRUE_CAPTURE[s])/TRUE_CAPTURE[s]),
            "raw_shared_r2":raw_r2,
            "operator_aware_shared_r2":aware_r2,
        })
    raw=float(np.mean([x["raw_shared_r2"] for x in per_source]))
    aware=float(np.mean([x["operator_aware_shared_r2"] for x in per_source]))
    maxerr=float(max(x["relative_estimation_error"] for x in per_source))
    gates={
        "every_source_is_truly_held_out":all(x["heldout_source_absent_from_train"] for x in per_source),
        "technical_calibrator_estimates_descriptor":maxerr<0.10,
        "operator_aware_transfer_is_strong":all(x["operator_aware_shared_r2"]>0.95 for x in per_source),
        "operator_aware_beats_raw_on_mean":aware>raw+0.10,
    }
    return {
        "schema":"V67_HELDOUT_SOURCE_OBSERVATION_OPERATOR_SYNTHETIC_V2",
        "status":"SYNTHETIC_SOFTWARE_SEMANTICS_ONLY",
        "fixture":{"donors":N_DONORS,"sources":N_SOURCES,"cells_per_donor":CELLS_PER_DONOR,
                   "seed":SEED,"calibration_channels":len(CAL_REF)},
        "descriptor_source":"INDEPENDENT_TECHNICAL_CALIBRATION_CHANNEL",
        "heldout_descriptor_misspecification_factor":float(misspecify_heldout),
        "per_source":per_source,
        "means":{"raw_shared_r2":raw,"operator_aware_shared_r2":aware},
        "gates":gates,
        "pass":bool(all(gates.values())),
        "structural_diagnostics":{
            "donor_disjointness_is_a_split_property_not_a_scientific_gate":True,
            "all_donor_overlaps":[x["donor_overlap"] for x in per_source],
        },
        "interpretation":{
            "qualified":"synthetic mechanics for estimating a measurement-scale descriptor from technical controls and using it for leave-one-source-out normalization",
            "not_qualified":"real technology transfer, identification of real observation operators, real calibration channels, or biological authority"
        },
        "governance":{"real_data_used":False,"training":"OFF","stage4":"NOT_AUTHORIZED",
                      "Morabito":"PROTECTED","TD60":"BLOCKED"}
    }

def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
