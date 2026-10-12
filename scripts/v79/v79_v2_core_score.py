#!/usr/bin/env python3
"""Controller-only V79 V2_CORE scoring boundary and frozen gate mathematics.

This module may consume controller truth only after a frozen qualification campaign.
No fit-side module imports it. Statistical gate functions implement Contract V2
verbatim and are outcome-agnostic.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
from scipy import stats

import v79_v2_core_launch as L


class ScoreRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise ScoreRefused(f"REFUSED V2_CORE scorer: {msg}")


def _finite_1d(values, *, name: str, min_n: int = 1) -> np.ndarray:
    a=np.asarray(values,dtype=float).reshape(-1)
    if a.size < min_n or np.any(~np.isfinite(a)):
        _refuse(f"{name} requires >= {min_n} finite values")
    return a


def _numerically_zero_sd(sd: float, mean: float) -> bool:
    tol=32.0*np.finfo(float).eps*max(1.0,abs(float(mean)))
    return abs(float(sd))<=tol


def gate_authority(contract: Mapping) -> dict:
    try: L.validate_launch_semantics(dict(contract))
    except Exception as exc: _refuse(f"contract is not frozen launch authority: {exc}")
    gates=list(contract["gates"]["list"])
    counts={"hard_statistical":sum(g["kind"]=="STAT" and g["verdict_class"]=="FAIL" for g in gates),
            "hard_rule":sum(g["kind"]=="RULE" and g["verdict_class"]=="FAIL" for g in gates),
            "limit_statistical":sum(g["kind"]=="STAT" and g["verdict_class"]=="LIMIT" for g in gates),
            "limit_rule":sum(g["kind"]=="RULE" and g["verdict_class"]=="LIMIT" for g in gates)}
    limits=[g for g in gates if g["verdict_class"]=="LIMIT"]
    if counts!={"hard_statistical":260,"hard_rule":28,"limit_statistical":4,"limit_rule":0}: _refuse(f"gate counts differ: {counts}")
    if len(limits)!=4 or any(g["verdict_class"]!="FAIL" for g in gates if g["world"]=="Q11_OMITTED_OPERATOR"): _refuse("LIMIT/Q11 authority differs")
    return {"gates":gates,"counts":counts,"limit_gates":limits,"alpha_per_gate":contract["gates"]["multiplicity"]["alpha_per_gate"]}


def require_complete_campaign(contract: Mapping, fit_receipts: list[Mapping]) -> list[Mapping]:
    want=int(contract.get("resources",{}).get("estimate",{}).get("n_fits",-1))
    if len(fit_receipts)!=want: _refuse(f"campaign has {len(fit_receipts)} fit receipts, requires {want}")
    ids=[]
    for r in fit_receipts:
        if r.get("schema")!="V79_V2_CORE_FIT_RECORD_V1" or r.get("execution_mode")!="QUALIFICATION": _refuse("non-qualification fit record in campaign")
        if r.get("contract_sha256")!=L.FINAL_CONTRACT_SHA256 or r.get("truth_accessed") is not False or r.get("scoring_run") is not False: _refuse("fit record authority/firewall mismatch")
        ids.append(r.get("fit_id"))
    if len(set(ids))!=want: _refuse("duplicate/missing fit identity")
    return fit_receipts


def one_sided_t_lower_across_genes(values, *, nominal: float, alpha: float) -> dict:
    x=_finite_1d(values,name="one_sided_t_lower_across_genes",min_n=2); nominal=float(nominal); alpha=float(alpha)
    if not (0.0<nominal<=1.0 and 0.0<alpha<1.0): _refuse("invalid nominal/alpha")
    mean=float(np.mean(x)); sd=float(np.std(x,ddof=1)); n=int(x.size)
    if _numerically_zero_sd(sd,mean):
        failed=mean < nominal-0.10
        return {"passed":not failed,"n":n,"mean":mean,"sd":sd,"t":None,"critical":None,"nominal":nominal,"alpha":alpha,"zero_sd_rule":True}
    t=(mean-nominal)/(sd/np.sqrt(n)); critical=float(stats.t.ppf(1.0-alpha,n-1)); failed=(mean<nominal) and (t < -critical)
    return {"passed":not failed,"n":n,"mean":mean,"sd":sd,"t":float(t),"critical":critical,"nominal":nominal,"alpha":alpha,"zero_sd_rule":False}


def two_sided_t_across_genes_and_materiality(values, *, alpha: float, materiality: float=0.50) -> dict:
    x=_finite_1d(values,name="two_sided_t_across_genes_and_materiality",min_n=2); alpha=float(alpha); materiality=float(materiality)
    if not (0.0<alpha<1.0 and materiality>=0): _refuse("invalid alpha/materiality")
    mean=float(np.mean(x)); sd=float(np.std(x,ddof=1)); n=int(x.size); material=abs(mean)>materiality; critical=float(stats.t.ppf(1.0-alpha/2.0,n-1))
    if _numerically_zero_sd(sd,mean): t=0.0 if mean==0.0 else float(np.copysign(np.inf,mean)); significant=(mean!=0.0)
    else: t=mean/(sd/np.sqrt(n)); significant=abs(t)>critical
    failed=bool(significant and material)
    return {"passed":not failed,"n":n,"mean":mean,"sd":sd,"t":float(t),"critical":critical,"materiality":materiality,"material":bool(material),"significant":bool(significant),"alpha":alpha}


def binomial_tail_gate(*, count: int, n: int, nominal: float, alpha: float) -> dict:
    count=int(count); n=int(n); nominal=float(nominal); alpha=float(alpha)
    if n<1 or count<0 or count>n or not (0.0<=nominal<=1.0) or not (0.0<alpha<1.0): _refuse("invalid binomial gate arguments")
    tail=float(stats.binom.sf(count-1,n,nominal)); return {"passed":not (tail<alpha),"count":count,"n":n,"nominal":nominal,"tail_probability":tail,"alpha":alpha}


def type_s_gate(*, wrong_sign_count: int, excluded_count: int, alpha: float) -> dict:
    wrong_sign_count=int(wrong_sign_count); excluded_count=int(excluded_count)
    if excluded_count<0 or wrong_sign_count<0 or wrong_sign_count>excluded_count: _refuse("invalid TYPE_S counts")
    if excluded_count==0: return {"passed":True,"wrong_sign_count":0,"excluded_count":0,"power":0.0,"nominal":0.05,"tail_probability":1.0,"alpha":float(alpha)}
    r=binomial_tail_gate(count=wrong_sign_count,n=excluded_count,nominal=0.05,alpha=alpha); r.update({"wrong_sign_count":wrong_sign_count,"excluded_count":excluded_count,"power":float(excluded_count)}); return r


def ppc_extreme_rate(p_values, *, alpha: float) -> dict:
    p=_finite_1d(p_values,name="PPC_EXTREME_RATE",min_n=1)
    if np.any((p<0.0)|(p>1.0)): _refuse("PPC p-values outside [0,1]")
    count=int(np.sum(p<0.01)); r=binomial_tail_gate(count=count,n=int(p.size),nominal=0.01,alpha=alpha); r.update({"extreme_count":count,"statistic_count":int(p.size),"threshold":0.01}); return r


def population_donor_sd_ratio(posterior_mean_sd, planted_sd, *, bounds: Sequence[float]) -> dict:
    post=_finite_1d(posterior_mean_sd,name="posterior donor SD",min_n=1); truth=_finite_1d(planted_sd,name="planted donor SD",min_n=1)
    if post.size!=truth.size: _refuse("posterior/truth donor-SD gene counts differ")
    lo,hi=(float(bounds[0]),float(bounds[1])); denom=float(np.mean(truth))
    if not (0.0<=lo<=hi): _refuse("invalid donor-SD ratio bounds")
    if denom<=0: _refuse("population donor-SD ratio undefined for nonpositive mean truth")
    ratio=float(np.mean(post)/denom); return {"passed":bool(lo<=ratio<=hi),"ratio":ratio,"bounds":[lo,hi],"posterior_mean":float(np.mean(post)),"planted_mean":denom,"n_genes":int(post.size)}


def convergence_all_fits_diagnosed(diagnoses) -> dict:
    d=list(diagnoses)
    if not d: _refuse("convergence gate requires fits")
    bad=sum(str(x)!="COMPLETE" for x in d); return {"passed":bad==0,"fit_count":len(d),"not_diagnosed_count":int(bad)}


def terminal_from_gate_results(contract: Mapping, gate_results: list[Mapping]) -> dict:
    post_label=contract.get("terminal_logic",{}).get("post_terminal_label")
    if post_label!=L.POST_TERMINAL_LABEL: _refuse("terminal post-fail label differs")
    first=next((i for i,r in enumerate(gate_results) if r.get("verdict_class")=="FAIL" and r.get("passed") is False),None)
    limits=sum(r.get("verdict_class")=="LIMIT" and r.get("passed") is False for r in gate_results)
    if first is None: return {"terminal":"V2_CORE_SYNTHETIC_QUALIFICATION_QUALIFIED","first_hard_fail_index":None,"post_terminal_count":0,"limit_failures":limits}
    return {"terminal":"V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED","first_hard_fail_index":first,"post_terminal_count":len(gate_results)-first-1,"post_terminal_label":post_label,"limit_failures":limits}


def bind_gate_evaluations(contract: Mapping, evaluations: list[Mapping]) -> dict:
    auth=gate_authority(contract); gates=auth["gates"]; key=lambda g:(g["world"],g["part"],g["gate"])
    expected={key(g):g for g in gates}; observed={key(e):e for e in evaluations}
    if set(observed)!=set(expected): _refuse("gate evaluation keys do not exactly match frozen gate list")
    rows=[]
    for g in gates:
        e=observed[key(g)]
        if not isinstance(e.get("passed"),bool): _refuse(f"gate {key(g)} lacks boolean passed")
        rows.append({"world":g["world"],"part":g["part"],"gate":g["gate"],"kind":g["kind"],"verdict_class":g["verdict_class"],"passed":e["passed"],"statistic":e.get("statistic"),"detail":e.get("detail"),"frozen_gate":g})
    return {"schema":"V79_V2_CORE_GATE_SCORE_TABLE_V1","rows":rows,"terminal":terminal_from_gate_results(contract,rows),"counts":auth["counts"],"alpha_per_gate":auth["alpha_per_gate"]}
