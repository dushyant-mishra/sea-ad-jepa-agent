from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_identified_summary as I  # noqa: E402


def _helmert3():
    return np.array([[1/np.sqrt(2),1/np.sqrt(6)],[-1/np.sqrt(2),1/np.sqrt(6)],[0,-2/np.sqrt(6)]],dtype=float)


def _fixture(part="detection",missing_source=False):
    shape=(2,5); n=shape[0]*shape[1]
    s={"alpha":np.arange(n,dtype=float).reshape(shape)/10,
       "class_contrasts":np.zeros(shape+(2,)),"source_contrasts":np.zeros(shape+(2,)),
       "donor_sd":np.ones(shape)*0.5,"donor_raw":np.ones(shape+(2,))}
    if part=="detection": s.update(beta_depth1=np.ones(shape)*.2,beta_depth2=np.ones(shape)*-.1)
    else: s.update(gamma_depth1=np.ones(shape)*.2,gamma_depth2=np.ones(shape)*-.1,sigma=np.ones(shape)*.7)
    # make source contrasts nonzero/correlated with alpha so derived-intercept summary must use joint draws
    s["source_contrasts"][...,0]=np.arange(n).reshape(shape)/20
    src=np.array([0,1,0,1] if missing_source else [0,1,2,0])
    data={"class_basis":_helmert3(),"source_basis":_helmert3(),
          "donor_basis_by_donor":np.array([[1/np.sqrt(2),0],[-1/np.sqrt(2),0],[0,1.],]),
          "cls_code":np.array([0,1,2,0]),"src_code":src,"donor_code":np.array([0,1,2,0])}
    return s,data


def test_all_factor_levels_score_frozen_helmert_contrasts():
    s,d=_fixture("detection",missing_source=False)
    out=I.scoring_ready_summary(s,d,part="detection")
    assert out["identification"]["class"]["mode"]=="helmert"
    assert out["identification"]["source"]["mode"]=="helmert"
    assert out["quantities"]["class"]["labels"]==["helmert_0","helmert_1"]
    assert out["quantities"]["source"]["labels"]==["helmert_0","helmert_1"]
    assert out["quantities"]["depth1"]["mean"]==[0.2]


def test_missing_factor_level_scores_differences_and_joint_identified_intercept():
    s,d=_fixture("detection",missing_source=True)
    out=I.scoring_ready_summary(s,d,part="detection")
    assert out["identification"]["source"]=={"mode":"level_differences","observed_levels":[0,1],"reference_level":0}
    assert out["quantities"]["source"]["labels"]==["level_1_minus_0"]
    # direct joint-draw calculation for the identified intercept
    alpha=s["alpha"].reshape(-1); sc=s["source_contrasts"].reshape(-1,2); effects=sc@d["source_basis"].T
    direct=alpha+effects[:,[0,1]].mean(axis=1)  # class effects are zero
    assert np.isclose(out["quantities"]["intercept"]["mean"][0],direct.mean())
    assert np.isclose(out["quantities"]["intercept"]["sd"][0],direct.std(ddof=1))


def test_donor_effects_include_only_informative_donors_and_positive_sigma():
    s,d=_fixture("positive",missing_source=False)
    d["donor_code"]=np.array([0,0,2,2])
    out=I.scoring_ready_summary(s,d,part="positive")
    assert out["quantities"]["donor_effects"]["labels"]==["donor_0","donor_2"]
    assert out["quantities"]["sigma"]["mean"]==[0.7]
    assert out["identification"]["donor_codes"]==[0,2]
