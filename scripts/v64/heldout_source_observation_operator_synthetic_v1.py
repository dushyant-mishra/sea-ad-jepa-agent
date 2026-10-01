#!/usr/bin/env python3
"""Synthetic held-out-source observation-operator qualification.

Software semantics only. No real biology, no production threshold, no training authority.
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
CAPTURE=np.array([0.55,1.00,1.55],float)

def ridge(x,y,a=1e-6):
    x=np.asarray(x,float); y=np.asarray(y,float)
    xm=x.mean(0); ym=y.mean(0); xc=x-xm; yc=y-ym
    b=np.linalg.solve(xc.T@xc+a*np.eye(x.shape[1]),xc.T@yc)
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
    latent_measurement=z@w
    x=CAPTURE[source,None]*latent_measurement+.15*rng.normal(size=(len(donor),P))
    return dict(donor=donor,source=source,z=z,x=x)

def run_smoke():
    d=fixture()
    per_source=[]
    for s in range(N_SOURCES):
        tr=d["source"]!=s
        te=d["source"]==s
        # Raw observation model: measurement scale is mixed into the evidence.
        raw=ridge(d["x"][tr],d["z"][tr])
        raw_r2=r2(d["z"][te],predict(raw,d["x"][te]))

        # Observation-operator-aware path: use a lawful physical acquisition
        # descriptor (capture/sensitivity), not dataset identity, to map observed
        # evidence onto a comparable measurement scale.
        x_norm=d["x"]/CAPTURE[d["source"],None]
        aware=ridge(x_norm[tr],d["z"][tr])
        aware_r2=r2(d["z"][te],predict(aware,x_norm[te]))

        # Measurement descriptor alone must not predict biology.
        capture_only=CAPTURE[d["source"],None]
        cb=ridge(capture_only[tr],d["z"][tr])
        capture_r2=r2(d["z"][te],predict(cb,capture_only[te]))

        train_donors=set(d["donor"][tr].tolist())
        test_donors=set(d["donor"][te].tolist())
        per_source.append({
            "heldout_source":int(s),
            "capture_descriptor":float(CAPTURE[s]),
            "train_sources":sorted(set(d["source"][tr].tolist())),
            "heldout_source_absent_from_train":bool(s not in set(d["source"][tr].tolist())),
            "donor_overlap":len(train_donors&test_donors),
            "raw_shared_r2":raw_r2,
            "operator_aware_shared_r2":aware_r2,
            "capture_only_shared_r2":capture_r2,
        })
    raw=np.mean([x["raw_shared_r2"] for x in per_source])
    aware=np.mean([x["operator_aware_shared_r2"] for x in per_source])
    cap=np.mean([x["capture_only_shared_r2"] for x in per_source])
    gates={
        "every_source_is_truly_held_out":all(x["heldout_source_absent_from_train"] for x in per_source),
        "donors_are_disjoint":all(x["donor_overlap"]==0 for x in per_source),
        "operator_aware_transfer_is_strong":all(x["operator_aware_shared_r2"]>0.95 for x in per_source),
        "operator_aware_beats_raw_on_mean":bool(aware>raw+0.10),
        "capture_descriptor_alone_is_not_biology":bool(cap<0.03),
    }
    return {
        "schema":"V67_HELDOUT_SOURCE_OBSERVATION_OPERATOR_SYNTHETIC_V1",
        "status":"SYNTHETIC_SOFTWARE_SEMANTICS_ONLY",
        "fixture":{"donors":N_DONORS,"sources":N_SOURCES,"cells_per_donor":CELLS_PER_DONOR,
                   "capture_descriptors":CAPTURE.tolist(),"seed":SEED},
        "per_source":per_source,
        "means":{"raw_shared_r2":float(raw),"operator_aware_shared_r2":float(aware),
                 "capture_only_shared_r2":float(cap)},
        "gates":gates,
        "pass":bool(all(gates.values())),
        "interpretation":{
            "qualified":"synthetic held-out-source observation-operator transfer mechanics",
            "not_qualified":"real technology transfer, real acquisition descriptors, production preprocessing, or biological authority",
            "forbidden_reading":"source identity is not a biological state feature; the successful descriptor represents how evidence was measured"
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
