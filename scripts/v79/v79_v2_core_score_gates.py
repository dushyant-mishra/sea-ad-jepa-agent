#!/usr/bin/env python3
"""Controller-only gate aggregation for V79 V2_CORE qualification.

Consumes per-gene identified score records and frozen gate definitions. Every verdict
is derived here; callers cannot supply pass/fail booleans. Unknown gate semantics
fail closed.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

import v79_v2_core_score as S


class GateEvaluationRefused(RuntimeError): pass

def _refuse(msg:str): raise GateEvaluationRefused(f"REFUSED V2_CORE gate evaluation: {msg}")

SUPPORTED_TESTS={
    "one_sided_t_lower_across_genes",
    "two_sided_t_across_genes_and_materiality",
    "binomial_lower",
    "interval_excludes_zero_rate",
    "binomial_upper",
    "binomial_upper_q05_above_floor",
    "TYPE_S",
}
SUPPORTED_RULE_GATES={"CONVERGENCE_ALL_FITS_DIAGNOSED","POPULATION_DONOR_SD_RATIO"}


def assert_gate_vocabulary_supported(contract:Mapping)->dict:
    unknown=[]
    for g in contract.get("gates",{}).get("list",[]):
        if g.get("kind")=="STAT":
            if g.get("test") not in SUPPORTED_TESTS: unknown.append((g.get("world"),g.get("part"),g.get("gate"),g.get("test")))
        elif g.get("kind")=="RULE":
            if g.get("gate") not in SUPPORTED_RULE_GATES: unknown.append((g.get("world"),g.get("part"),g.get("gate"),None))
        else: unknown.append((g.get("world"),g.get("part"),g.get("gate"),g.get("kind")))
    if unknown: _refuse(f"unsupported frozen gate vocabulary: {unknown[:3]}")
    return {"stat_tests":sorted(SUPPORTED_TESTS),"rule_gates":sorted(SUPPORTED_RULE_GATES)}


def _records(records:Sequence[Mapping],world:str,part:str)->list[Mapping]:
    rows=[r for r in records if r.get("world_name")==world and r.get("part")==part]
    rows.sort(key=lambda r:int(r.get("gene_index",-1)))
    if len(rows)!=44 or [int(r.get("gene_index",-1)) for r in rows]!=list(range(44)):
        _refuse(f"{world}/{part} requires exactly genes 0..43")
    return rows


def _q(row:Mapping,name:str)->Mapping:
    q=row.get("quantities",{}).get(name)
    if not isinstance(q,Mapping): _refuse(f"missing quantity {name}")
    return q


def _gene_fraction(row:Mapping,names:Sequence[str],field:str)->float:
    vals=[]
    for name in names:
        x=list(_q(row,name).get(field,[])); vals.extend(bool(v) for v in x)
    if not vals: _refuse(f"no scored quantities for {list(names)}")
    return float(np.mean(vals))


def _gene_mean(row:Mapping,name:str,field:str)->float|None:
    vals=np.asarray(_q(row,name).get(field,[]),dtype=float).reshape(-1)
    if vals.size==0: return None
    if np.any(~np.isfinite(vals)): _refuse(f"nonfinite {name}.{field}")
    return float(np.mean(vals))


def _coverage_single(rows:list[Mapping],name:str,field:str="covered90")->tuple[int,int]:
    flags=[]
    for r in rows:
        x=list(_q(r,name).get(field,[]))
        if len(x)!=1: _refuse(f"single-quantity coverage expected for {name}")
        flags.append(bool(x[0]))
    return int(sum(not x for x in flags)),len(flags)


def _exclusion_details(rows:list[Mapping],name:str)->dict:
    result={}
    for label,lo,hi in (("90","q05","q95"),("95","q025","q975"),("99","q005","q995")):
        per_gene=[]; total=0; excluded=0
        for r in rows:
            q=_q(r,name); lows=np.asarray(q.get(lo,[]),dtype=float); highs=np.asarray(q.get(hi,[]),dtype=float)
            if lows.shape!=highs.shape: _refuse(f"{name} {label}% interval shape differs")
            if np.any(~np.isfinite(lows)) or np.any(~np.isfinite(highs)): _refuse(f"{name} {label}% interval nonfinite")
            ex=(lows>0)|(highs<0); total+=int(ex.size); excluded+=int(np.sum(ex)); per_gene.append(float(np.mean(ex)) if ex.size else np.nan)
        result[label]={"excluded":excluded,"total":total,"rate":float(excluded/total) if total else None,"per_gene":per_gene}
    return result


def _interval_excludes_zero_gate(rows:list[Mapping],name:str,gate:Mapping,alpha:float)->dict:
    nominal_fp=float(gate["nominal"]); details=_exclusion_details(rows,name); per=details["90"]["per_gene"]
    usable=np.asarray([x for x in per if np.isfinite(x)],dtype=float)
    if usable.size==0: _refuse(f"no estimable {name} quantities for absent-effect gate")
    # Single scalar per gene -> binomial_lower on zero coverage; vector -> per-gene one-sided coverage.
    sizes=[len(_q(r,name).get("q05",[])) for r in rows]
    if all(n==1 for n in sizes):
        misses=int(details["90"]["excluded"]); stat=S.binomial_tail_gate(count=misses,n=len(rows),nominal=nominal_fp,alpha=alpha)
    else:
        zero_coverage=1.0-usable; stat=S.one_sided_t_lower_across_genes(zero_coverage,nominal=1.0-nominal_fp,alpha=alpha)
    stat["exclusion_rates"]={k:{kk:vv for kk,vv in v.items() if kk!="per_gene"} for k,v in details.items()}
    return stat


def _type_s(rows:list[Mapping],name:str,alpha:float)->dict:
    wrong=0; excluded=0
    for r in rows:
        q=_q(r,name); truth=np.asarray(q.get("truth",[]),dtype=float); mean=np.asarray(q.get("posterior_mean",[]),dtype=float)
        lo=np.asarray(q.get("q05",[]),dtype=float); hi=np.asarray(q.get("q95",[]),dtype=float)
        if not (truth.shape==mean.shape==lo.shape==hi.shape): _refuse("TYPE_S quantity shapes differ")
        ex=(lo>0)|(hi<0)
        for t,m,e in zip(truth,mean,ex):
            if not e: continue
            if t==0: _refuse("TYPE_S encountered zero planted source truth")
            excluded+=1; wrong+=int(np.sign(t)!=np.sign(m))
    return S.type_s_gate(wrong_sign_count=wrong,excluded_count=excluded,alpha=alpha)


def evaluate_gate(gate:Mapping,records:Sequence[Mapping],*,alpha:float,donor_sd_floor_by_part:Mapping[str,float])->dict:
    world=str(gate["world"]); part=str(gate["part"]); name=str(gate["gate"]); rows=_records(records,world,part)
    if gate["kind"]=="RULE":
        if name=="CONVERGENCE_ALL_FITS_DIAGNOSED": stat=S.convergence_all_fits_diagnosed([r.get("final_diagnosis") for r in rows])
        elif name=="POPULATION_DONOR_SD_RATIO":
            post=np.asarray([_q(r,"donor_sd")["posterior_mean"][0] for r in rows],dtype=float); truth=np.asarray([_q(r,"donor_sd")["truth"][0] for r in rows],dtype=float)
            stat=S.population_donor_sd_ratio(post,truth,bounds=gate["bounds"])
        else: _refuse(f"unsupported rule gate {name}")
        return {"world":world,"part":part,"gate":name,"passed":bool(stat["passed"]),"statistic":stat,"detail":None}
    test=str(gate.get("test")); qtype=gate.get("quantity_type")
    if test=="one_sided_t_lower_across_genes":
        names=gate.get("quantity_types") or [qtype]; vals=np.asarray([_gene_fraction(r,names,"covered90") for r in rows],dtype=float)
        stat=S.one_sided_t_lower_across_genes(vals,nominal=float(gate["nominal"]),alpha=alpha)
    elif test=="two_sided_t_across_genes_and_materiality":
        vals=np.asarray([x for r in rows if (x:=_gene_mean(r,str(qtype),"standardized_error")) is not None],dtype=float)
        stat=S.two_sided_t_across_genes_and_materiality(vals,alpha=alpha)
    elif test=="binomial_lower":
        misses,n=_coverage_single(rows,str(qtype)); stat=S.binomial_tail_gate(count=misses,n=n,nominal=1.0-float(gate["nominal"]),alpha=alpha)
    elif test=="interval_excludes_zero_rate": stat=_interval_excludes_zero_gate(rows,str(qtype),gate,alpha)
    elif test=="binomial_upper":
        if name!="PPC_EXTREME_RATE": _refuse(f"unrecognized binomial_upper gate {name}")
        p=[float(x["p_value"]) for r in rows for x in r.get("ppc",[])]
        stat=S.ppc_extreme_rate(p,alpha=alpha)
    elif test=="binomial_upper_q05_above_floor":
        floor=float(donor_sd_floor_by_part[part]); count=0
        for r in rows:
            q=_q(r,"donor_sd"); q05=np.asarray(q.get("q05",[]),dtype=float)
            if q05.size!=1: _refuse("donor-SD q05 gate requires one scalar per gene")
            count+=int(q05[0]>floor)
        stat=S.binomial_tail_gate(count=count,n=len(rows),nominal=float(gate["nominal"]),alpha=alpha); stat["floor"]=floor
    elif test=="TYPE_S": stat=_type_s(rows,str(qtype or "source"),alpha)
    else: _refuse(f"unsupported statistical test {test}")
    return {"world":world,"part":part,"gate":name,"passed":bool(stat["passed"]),"statistic":stat,"detail":None}


def evaluate_all_gates(contract:Mapping,records:Sequence[Mapping],*,donor_sd_floor_by_part:Mapping[str,float])->dict:
    assert_gate_vocabulary_supported(contract); alpha=float(contract["gates"]["multiplicity"]["alpha_per_gate"])
    expected_parts={(g["world"],g["part"]) for g in contract["gates"]["list"]}
    for world,part in expected_parts: _records(records,world,part)
    evals=[evaluate_gate(g,records,alpha=alpha,donor_sd_floor_by_part=donor_sd_floor_by_part) for g in contract["gates"]["list"]]
    return S.bind_gate_evaluations(contract,evals)
