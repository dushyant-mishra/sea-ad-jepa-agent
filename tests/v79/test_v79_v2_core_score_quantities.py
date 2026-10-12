from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_quantities as Q  # noqa: E402
import v79_v2_core_score_truth as T  # noqa: E402


def _contract(): return json.loads((ROOT/"results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text())
def _world(): return T.load_truth_set(ROOT/"results/v79/v2_core_realization_audit_freeze_v1/package/controller_truth",_contract())["Q00_BASELINE"]

def _q(labels,mean=None):
    n=len(labels); m=np.zeros(n) if mean is None else np.asarray(mean,dtype=float)
    return {"labels":list(labels),"mean":m.tolist(),"sd":np.ones(n).tolist(),
            "q005":(m-2.5).tolist(),"q025":(m-2.0).tolist(),"q05":(m-1.0).tolist(),"q50":m.tolist(),
            "q95":(m+1.0).tolist(),"q975":(m+2.0).tolist(),"q995":(m+2.5).tolist()}

def _summary(part="detection",*,class_ident=None,source_ident=None,donors=(0,1)):
    ci=class_ident or {"mode":"helmert","observed_levels":[0,1,2],"reference_level":None}
    si=source_ident or {"mode":"helmert","observed_levels":[0,1,2],"reference_level":None}
    clabels=["helmert_0","helmert_1"] if ci["mode"]=="helmert" else [f"level_{x}_minus_{ci['reference_level']}" for x in ci["observed_levels"][1:]]
    slabels=["helmert_0","helmert_1"] if si["mode"]=="helmert" else [f"level_{x}_minus_{si['reference_level']}" for x in si["observed_levels"][1:]]
    qs={"intercept":_q(["intercept"]),"depth1":_q(["depth1"]),"depth2":_q(["depth2"]),
        "class":_q(clabels),"source":_q(slabels),"donor_sd":_q(["donor_sd"]),
        "donor_effects":_q([f"donor_{d}" for d in donors])}
    if part=="positive": qs["sigma"]=_q(["sigma"])
    return {"schema":"V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1","part":part,
            "identification":{"class":ci,"source":si,"donor_codes":list(donors)},"quantities":qs}


def test_all_level_identification_matches_raw_frozen_helmert_truth():
    w=_world(); s=_summary("detection")
    truth=Q.identified_truth_for_summary(w,"detection",0,s)
    assert np.allclose(truth["class"],w.load("truth/detection/class_contrasts.npy")[0])
    assert np.allclose(truth["source"],w.load("truth/detection/source_contrasts.npy")[0])
    assert np.isclose(truth["intercept"][0],w.load("truth/detection/intercept.npy")[0])
    assert np.allclose(truth["donor_effects"],w.load("truth/detection/donor_effects.npy")[:2,0])


def test_missing_levels_transform_truth_to_level_differences_and_identified_intercept():
    ci={"mode":"level_differences","observed_levels":[0,2],"reference_level":0}
    si={"mode":"level_differences","observed_levels":[1,2],"reference_level":1}
    w=_world(); s=_summary("detection",class_ident=ci,source_ident=si)
    truth=Q.identified_truth_for_summary(w,"detection",0,s)
    B=Q._helmert3(); c=w.load("truth/detection/class_contrasts.npy")[0]; src=w.load("truth/detection/source_contrasts.npy")[0]
    ce=B@c; se=B@src
    assert np.allclose(truth["class"],[ce[2]-ce[0]])
    assert np.allclose(truth["source"],[se[2]-se[1]])
    expected=w.load("truth/detection/intercept.npy")[0]+np.mean(ce[[0,2]])+np.mean(se[[1,2]])
    assert np.isclose(truth["intercept"][0],expected)


def test_gene_score_computes_90_95_99_coverage_and_standardized_error_in_identified_space():
    w=_world(); s=_summary("positive")
    truth=Q.identified_truth_for_summary(w,"positive",3,s)
    for name,t in truth.items():
        labels=s["quantities"][name]["labels"]; a=np.asarray(t,dtype=float)
        s["quantities"][name]={"labels":labels,"mean":a.tolist(),"sd":np.ones(len(a)).tolist(),
                               "q005":(a-1.5).tolist(),"q025":(a-1.0).tolist(),"q05":(a-0.5).tolist(),"q50":a.tolist(),
                               "q95":(a+0.5).tolist(),"q975":(a+1.0).tolist(),"q995":(a+1.5).tolist()}
    receipt={"schema":"V79_V2_CORE_FIT_RECORD_V1","execution_mode":"QUALIFICATION","opaque_world_id":w.opaque_world_id,
             "gene_index":3,"part":"positive","final_diagnosis":"COMPLETE","scoring_summary":s,"ppc":[{"name":"x","observed":0.0,"p_value":0.5}]}
    r=Q.score_gene_quantities(w,receipt)
    for x in r["quantities"].values():
        assert all(x["covered90"]) and all(x["covered95"]) and all(x["covered99"])
        assert np.allclose(x["standardized_error"],0.0)
        assert {"q005","q025","q05","q95","q975","q995"} <= set(x)
