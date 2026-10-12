from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_evaluate as E  # noqa: E402
import v79_v2_core_score as S  # noqa: E402


def _contract():
    return json.loads((ROOT/"results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text())


def _quantity(n=1, *, truth=1.0, mean=1.0, sd=1.0, cover=True, zero_exclude=False):
    t=np.full(n,truth,dtype=float); m=np.full(n,mean,dtype=float); s=np.full(n,sd,dtype=float)
    if cover:
        q05=t-0.5; q95=t+0.5
    else:
        q05=t+0.25; q95=t+0.75
    if zero_exclude:
        q05=np.full(n,0.1); q95=np.full(n,1.0)
    return {
        "labels":[f"q{i}" for i in range(n)],"truth":t.tolist(),"posterior_mean":m.tolist(),"posterior_sd":s.tolist(),
        "q005":(q05-0.5).tolist(),"q025":(q05-0.25).tolist(),"q05":q05.tolist(),"q50":m.tolist(),
        "q95":q95.tolist(),"q975":(q95+0.25).tolist(),"q995":(q95+0.5).tolist(),
        "covered90":((q05<=t)&(t<=q95)).tolist(),"covered95":np.ones(n,dtype=bool).tolist(),"covered99":np.ones(n,dtype=bool).tolist(),
        "standardized_error":((m-t)/s).tolist(),
    }


def _rows(world="Q00_BASELINE", part="detection", *, z=0.0):
    out=[]
    for g in range(44):
        qs={
            "intercept":_quantity(mean=1.0+z),"depth1":_quantity(mean=1.0+z),"depth2":_quantity(mean=1.0+z),
            "class":_quantity(2,mean=1.0+z),"source":_quantity(2,mean=1.0+z),
            "donor_sd":_quantity(truth=1.0,mean=1.0+z),"donor_effects":_quantity(4,mean=1.0+z),
        }
        if world=="Q04_SOURCE_ABSENT": qs["source"]=_quantity(2,truth=0.0,mean=0.0)
        if world=="Q05_CLASS_ABSENT": qs["class"]=_quantity(2,truth=0.0,mean=0.0)
        if world=="Q06_QUADRATIC_DEPTH_ABSENT": qs["depth2"]=_quantity(truth=0.0,mean=0.0)
        if world=="Q07_DONOR_ABSENT":
            qs["donor_sd"]=_quantity(truth=0.0,mean=0.0)
            qs["donor_effects"]=_quantity(4,truth=0.0,mean=0.0)
        if part=="positive": qs["sigma"]=_quantity(truth=1.0,mean=1.0+z)
        out.append({"world_name":world,"world_index":0,"opaque_world_id":"a"*12,"gene_index":g,"part":part,
                    "final_diagnosis":"COMPLETE","quantities":qs,"ppc":[{"name":"p","observed":0.0,"p_value":0.5}]})
    return out


def test_pooled_coverage_and_bias_dispatch_use_gene_as_independent_unit():
    c=_contract(); alpha=c["gates"]["multiplicity"]["alpha_per_gate"]; rows=_rows()
    cov={"world":"Q00_BASELINE","part":"detection","gate":"COVERAGE_FIXED_POOLED","kind":"STAT","verdict_class":"FAIL",
         "test":"one_sided_t_lower_across_genes","quantity_types":["intercept","depth1","depth2","class","source"],"nominal":0.9}
    r=E.evaluate_gate(c,cov,rows,alpha=alpha)
    assert r["passed"] is True and r["statistic"]["n"]==44
    biased=_rows(z=0.75)
    gate={"world":"Q00_BASELINE","part":"detection","gate":"BIAS_DEPTH1","kind":"STAT","verdict_class":"FAIL",
          "test":"two_sided_t_across_genes_and_materiality","quantity_type":"depth1"}
    b=E.evaluate_gate(c,gate,biased,alpha=alpha)
    assert b["passed"] is False and b["statistic"]["material"] is True


def test_absent_factor_gate_reports_90_95_99_exclusion_rates():
    c=_contract(); alpha=c["gates"]["multiplicity"]["alpha_per_gate"]; rows=_rows(world="Q04_SOURCE_ABSENT")
    gate={"world":"Q04_SOURCE_ABSENT","part":"detection","gate":"ABSENT_FALSE_POSITIVE_SOURCE","kind":"STAT","verdict_class":"FAIL",
          "test":"interval_excludes_zero_rate","quantity_type":"source","nominal":0.1}
    r=E.evaluate_gate(c,gate,rows,alpha=alpha)
    assert r["passed"] is True
    assert set(r["detail"]["interval_exclusion_rates"])=={"90","95","99"}


def test_type_s_uses_only_intervals_that_exclude_zero():
    c=_contract(); alpha=c["gates"]["multiplicity"]["alpha_per_gate"]; rows=_rows(world="Q03_WEAK_SOURCE")
    for row in rows:
        row["quantities"]["source"]=_quantity(2,truth=1.0,mean=1.0,zero_exclude=True)
    gate={"world":"Q03_WEAK_SOURCE","part":"detection","gate":"TYPE_S_SOURCE","kind":"STAT","verdict_class":"FAIL",
          "test":"binomial_upper","quantity_type":"source","nominal":0.05}
    r=E.evaluate_gate(c,gate,rows,alpha=alpha)
    assert r["passed"] is True and r["statistic"]["wrong_sign_count"]==0 and r["statistic"]["excluded_count"]==88


def test_donor_absent_floor_and_population_ratio_and_ppc_dispatch():
    c=_contract(); alpha=c["gates"]["multiplicity"]["alpha_per_gate"]
    rows=_rows(world="Q07_DONOR_ABSENT")
    gate={"world":"Q07_DONOR_ABSENT","part":"detection","gate":"ABSENT_FALSE_POSITIVE_DONOR_SD","kind":"STAT","verdict_class":"FAIL",
          "test":"binomial_upper_q05_above_floor","quantity_type":"donor_sd","nominal":0.05}
    r=E.evaluate_gate(c,gate,rows,alpha=alpha)
    assert "floor" in r["detail"] and r["statistic"]["n"]==44
    ratio={"world":"Q00_BASELINE","part":"detection","gate":"POPULATION_DONOR_SD_RATIO","kind":"RULE","verdict_class":"FAIL","bounds":[0.8,1.25]}
    rr=E.evaluate_gate(c,ratio,_rows(),alpha=alpha)
    assert rr["passed"] is True
    ppc={"world":"Q00_BASELINE","part":"detection","gate":"PPC_EXTREME_RATE","kind":"STAT","verdict_class":"FAIL",
         "test":"binomial_upper","nominal":0.01}
    rp=E.evaluate_gate(c,ppc,_rows(),alpha=alpha)
    assert rp["passed"] is True and rp["statistic"]["statistic_count"]==44


def test_group_rows_refuses_nonexact_44_gene_part():
    with pytest.raises(E.GateEvaluationRefused):
        E.validate_world_part_rows(_rows()[:-1],world="Q00_BASELINE",part="detection")


def test_full_contract_dispatch_evaluates_and_binds_all_292_frozen_gates():
    c=_contract(); rows=[]
    for w in c["worlds"]["world_list"]:
        for part in ("detection","positive"):
            rows.extend(_rows(world=w["name"],part=part))
    assert len(rows)==1056
    ev=E.build_gate_evaluations(c,rows)
    assert len(ev)==292
    table=S.bind_gate_evaluations(c,ev)
    assert len(table["rows"])==292
    assert table["counts"]=={"hard_statistical":260,"hard_rule":28,"limit_statistical":4,"limit_rule":0}
    assert table["terminal"]["terminal"] in {"V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED","V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED"}
