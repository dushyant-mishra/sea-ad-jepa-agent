from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_fit_surface as F  # noqa: E402
import v79_v2_core_score_oracle as O  # noqa: E402


def _design():
    return {
        "src":np.array([0,0,1,1,2,2],dtype=np.int64),
        "donor":np.array([0,1,2,3,4,5],dtype=np.int64),
        "cls":np.array([0,1,2,0,1,2],dtype=np.int64),
        "log_lib":np.array([-2.,-1.,0.,1.,2.,3.],dtype=float),
    }


def _world(*,oid="a"*12,detected=None,observed=None):
    support=np.ones((6,1),dtype=bool)
    if detected is None: detected=np.array([0,1,0,1,0,1],dtype=np.int8)
    if observed is None: observed=np.ones(6,dtype=float)
    obs={}
    for rep in ("train","same_donor","new_donor"):
        obs[rep]={"detected":np.asarray(detected).reshape(6,1),"observed":np.asarray(observed).reshape(6,1)}
    return F.BlindedWorld(Path("."),"QUALIFICATION_TRUTH_FREEZE",oid,"b"*64,{},_design(),support,obs)


class _Truth:
    def __init__(self,*,oid="a"*12,name="Q00_BASELINE",operator=False,prevalence=0.031,sigma=1.0):
        self.opaque_world_id=oid; self.world_name=name; self.world_index=11 if operator else 0
        z=np.zeros(1); c=np.zeros((1,2)); donor=np.zeros((6,1))
        self.arrays={
            "support.npy":np.ones((6,1),dtype=bool),
            "design/op.npy":np.arange(6,dtype=np.int64),
            "truth/detection/intercept.npy":z.copy(),"truth/detection/depth1.npy":z.copy(),"truth/detection/depth2.npy":z.copy(),
            "truth/detection/class_contrasts.npy":c.copy(),"truth/detection/source_contrasts.npy":c.copy(),
            "truth/detection/donor_sd.npy":z.copy(),"truth/detection/donor_effects.npy":donor.copy(),
            "truth/detection/prevalence.npy":np.array([prevalence],dtype=float),
            "truth/positive/intercept.npy":z.copy(),"truth/positive/depth1.npy":z.copy(),"truth/positive/depth2.npy":z.copy(),
            "truth/positive/class_contrasts.npy":c.copy(),"truth/positive/source_contrasts.npy":c.copy(),
            "truth/positive/donor_sd.npy":z.copy(),"truth/positive/donor_effects.npy":donor.copy(),
            "truth/positive/sigma.npy":np.array([sigma],dtype=float),
        }
        if operator:
            self.arrays["truth/operator_offsets/detection.npy"]=np.ones((6,1),dtype=float)
            self.arrays["truth/operator_offsets/positive.npy"]=np.ones((6,1),dtype=float)
        self.manifest={"generated_outputs":{k:"0"*64 for k in self.arrays}}
    def load(self,rel):
        if rel not in self.arrays: raise KeyError(rel)
        return np.asarray(self.arrays[rel])


def test_detection_zero_truth_gives_half_probability_log2_and_exact_planted_prevalence():
    truth=_Truth(prevalence=0.031); world=_world()
    out=O.heldout_oracle(truth,world,gene_index=0,part="detection")
    assert out["gating"] is False
    assert math.isclose(out["planted_prevalence"],0.031)
    for mode in ("same_donor","new_donor"):
        rec=out[mode]
        assert rec["schema"]=="V79_V2_CORE_DETECTION_ORACLE_V1"
        assert rec["replicate_mode"]==mode
        assert rec["gauss_hermite_nodes"]==(None if mode=="same_donor" else 40)
        assert math.isclose(rec["mean_log_loss"],math.log(2.0),rel_tol=1e-12)
        assert math.isclose(rec["predicted_prevalence"],0.5,rel_tol=1e-12)
        assert len(rec["calibration_bins"])==10


def test_positive_zero_mu_unit_sigma_matches_standard_normal_and_new_donor_zero_sd():
    truth=_Truth(sigma=1.0); world=_world(observed=np.ones(6,dtype=float))
    out=O.heldout_oracle(truth,world,gene_index=0,part="positive")
    expected=-0.5*math.log(2.0*math.pi)
    assert out["gating"] is False
    assert "planted_prevalence" not in out
    assert math.isclose(out["same_donor"]["mean_lpd"],expected,rel_tol=1e-12)
    assert math.isclose(out["new_donor"]["mean_lpd"],expected,rel_tol=1e-12)
    assert out["new_donor"]["gauss_hermite_nodes"]==40


def test_q11_operator_offsets_shift_oracle_and_are_required_if_manifest_declares_them():
    base=O.heldout_oracle(_Truth(),_world(),gene_index=0,part="detection")
    q11_truth=_Truth(name="Q11_OMITTED_OPERATOR",operator=True)
    shifted=O.heldout_oracle(q11_truth,_world(),gene_index=0,part="detection")
    assert shifted["same_donor"]["predicted_prevalence"]>base["same_donor"]["predicted_prevalence"]
    q11_truth.arrays.pop("truth/operator_offsets/detection.npy")
    with pytest.raises(O.OracleRefused): O.heldout_oracle(q11_truth,_world(),gene_index=0,part="detection")


def test_oracle_refuses_truth_blinded_world_identity_or_support_mismatch():
    with pytest.raises(O.OracleRefused): O.heldout_oracle(_Truth(oid="b"*12),_world(oid="a"*12),gene_index=0,part="detection")
    t=_Truth(); t.arrays["support.npy"][0,0]=False
    with pytest.raises(O.OracleRefused): O.heldout_oracle(t,_world(),gene_index=0,part="detection")


def test_oracle_output_is_descriptive_only_and_contains_no_gate_decision_fields():
    out=O.heldout_oracle(_Truth(),_world(),gene_index=0,part="detection")
    text=str(out).lower()
    assert "qualified" not in text and "hard_fail" not in text and "gate_status" not in text
