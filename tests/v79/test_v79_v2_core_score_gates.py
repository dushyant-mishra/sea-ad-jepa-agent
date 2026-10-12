from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_gates as G  # noqa: E402


def _contract(): return json.loads((ROOT/"results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text())

def _q(truth=(1.0,),mean=(1.0,),covered=True):
    truth=np.asarray(truth,dtype=float); mean=np.asarray(mean,dtype=float); n=len(truth)
    return {"labels":[f"x{i}" for i in range(n)],"truth":truth.tolist(),"posterior_mean":mean.tolist(),"posterior_sd":np.ones(n).tolist(),
            "q005":(mean-3).tolist(),"q025":(mean-2).tolist(),"q05":(mean-1).tolist(),"q50":mean.tolist(),
            "q95":(mean+1).tolist(),"q975":(mean+2).tolist(),"q995":(mean+3).tolist(),
            "covered90":[covered]*n,"covered95":[covered]*n,"covered99":[covered]*n,
            "standardized_error":(mean-truth).tolist()}

def _rows(world="Q00_BASELINE",part="detection"):
    rows=[]
    for g in range(44):
        qs={"intercept":_q(),"depth1":_q(),"depth2":_q(),"class":_q((1.,-1.),(1.,-1.)),"source":_q((1.,-1.),(1.,-1.)),
            "donor_sd":_q((1.,),(1.,)),"donor_effects":_q((1.,-1.),(1.,-1.))}
        if part=="positive": qs["sigma"]=_q((1.,),(1.,))
        rows.append({"world_name":world,"part":part,"gene_index":g,"final_diagnosis":"COMPLETE","quantities":qs,
                     "ppc":[{"name":"s","observed":0.0,"p_value":0.5}]})
    return rows


def test_every_frozen_gate_family_has_an_explicit_dispatcher():
    r=G.assert_gate_vocabulary_supported(_contract())
    assert set(r["stat_tests"])==G.SUPPORTED_TESTS
    assert set(r["rule_gates"])==G.SUPPORTED_RULE_GATES


def test_fixed_pooled_coverage_and_bias_dispatch_from_gene_records():
    c=_contract(); rows=_rows()
    cov=next(g for g in c["gates"]["list"] if g["world"]=="Q00_BASELINE" and g["part"]=="detection" and g["gate"]=="COVERAGE_FIXED_POOLED")
    bias=next(g for g in c["gates"]["list"] if g["world"]=="Q00_BASELINE" and g["part"]=="detection" and g["gate"]=="BIAS_INTERCEPT")
    a=G.evaluate_gate(cov,rows,alpha=c["gates"]["multiplicity"]["alpha_per_gate"],donor_sd_floor_by_part={"detection":.1,"positive":.1})
    b=G.evaluate_gate(bias,rows,alpha=c["gates"]["multiplicity"]["alpha_per_gate"],donor_sd_floor_by_part={"detection":.1,"positive":.1})
    assert a["passed"] is True and b["passed"] is True


def test_absent_effect_reports_90_95_99_rates_and_can_fail():
    c=_contract(); rows=_rows("Q06_QUADRATIC_DEPTH_ABSENT","detection")
    for r in rows:
        r["quantities"]["depth2"]=_q((0.,),(2.,),covered=False)
        q=r["quantities"]["depth2"]; q["q05"]=[1.]; q["q025"]=[.5]; q["q005"]=[.1]; q["q95"]=[3.]; q["q975"]=[3.5]; q["q995"]=[4.]
    gate=next(g for g in c["gates"]["list"] if g["world"]=="Q06_QUADRATIC_DEPTH_ABSENT" and g["part"]=="detection" and g["gate"].startswith("ABSENT_FALSE_POSITIVE"))
    out=G.evaluate_gate(gate,rows,alpha=c["gates"]["multiplicity"]["alpha_per_gate"],donor_sd_floor_by_part={"detection":.1,"positive":.1})
    assert out["passed"] is False
    assert out["statistic"]["exclusion_rates"]["90"]["rate"]==1.0
    assert out["statistic"]["exclusion_rates"]["95"]["rate"]==1.0
    assert out["statistic"]["exclusion_rates"]["99"]["rate"]==1.0


def test_q07_donor_sd_floor_gate_uses_supplied_frozen_floor():
    c=_contract(); rows=_rows("Q07_DONOR_ABSENT","detection")
    floor=.03818885859309774
    for r in rows:
        q=r["quantities"]["donor_sd"]; q["q05"]=[floor+0.1]
    gate=next(g for g in c["gates"]["list"] if g["world"]=="Q07_DONOR_ABSENT" and g["part"]=="detection" and g["gate"]=="ABSENT_FALSE_POSITIVE_DONOR_SD")
    out=G.evaluate_gate(gate,rows,alpha=c["gates"]["multiplicity"]["alpha_per_gate"],donor_sd_floor_by_part={"detection":floor,"positive":.008759977409129621})
    assert out["passed"] is False and out["statistic"]["floor"]==floor


def test_ppc_and_convergence_rules_are_derived_not_injected():
    c=_contract(); rows=_rows()
    ppc=next(g for g in c["gates"]["list"] if g["world"]=="Q00_BASELINE" and g["part"]=="detection" and g["gate"]=="PPC_EXTREME_RATE")
    conv=next(g for g in c["gates"]["list"] if g["world"]=="Q00_BASELINE" and g["part"]=="detection" and g["gate"]=="CONVERGENCE_ALL_FITS_DIAGNOSED")
    alpha=c["gates"]["multiplicity"]["alpha_per_gate"]
    assert G.evaluate_gate(ppc,rows,alpha=alpha,donor_sd_floor_by_part={"detection":.1,"positive":.1})["passed"] is True
    rows[-1]["final_diagnosis"]="NOT_DIAGNOSED"
    assert G.evaluate_gate(conv,rows,alpha=alpha,donor_sd_floor_by_part={"detection":.1,"positive":.1})["passed"] is False
