#!/usr/bin/env python3
"""Controller-only automatic evaluation of frozen V79 V2_CORE qualification gates.

Consumes only controller-scored per-gene rows (truth already transformed into the
same identified parameterization as the posterior) and the immutable Contract V2.
No fitter imports this module. No threshold is inferred from outcomes.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np

import v79_v2_core_score as S


class GateEvaluationRefused(RuntimeError): pass

def _refuse(msg:str): raise GateEvaluationRefused(f"REFUSED V2_CORE gate evaluation: {msg}")


def _finite(values, *, name:str, allow_empty:bool=False)->np.ndarray:
    a=np.asarray(values,dtype=float).reshape(-1)
    if (a.size==0 and not allow_empty) or np.any(~np.isfinite(a)): _refuse(f"{name} requires finite values")
    return a


def validate_world_part_rows(rows:Sequence[Mapping], *, world:str, part:str)->list[Mapping]:
    r=list(rows)
    if len(r)!=44: _refuse(f"{world}/{part} has {len(r)} gene rows, expected 44")
    genes=[]; opaque=set()
    for x in r:
        if x.get("world_name")!=world or x.get("part")!=part: _refuse("world/part row identity differs")
        g=x.get("gene_index")
        if not isinstance(g,int) or not (0<=g<44): _refuse("gene index outside frozen 44-gene panel")
        if not isinstance(x.get("quantities"),Mapping): _refuse("gene quantities missing")
        genes.append(g); opaque.add(str(x.get("opaque_world_id")))
    if sorted(genes)!=list(range(44)) or len(set(genes))!=44: _refuse("gene rows are not one-to-one 0..43")
    if len(opaque)!=1: _refuse("world/part rows mix opaque world IDs")
    return sorted(r,key=lambda x:int(x["gene_index"]))


def _q(row:Mapping,name:str)->Mapping:
    q=row.get("quantities",{}).get(name)
    if not isinstance(q,Mapping): _refuse(f"quantity missing: {name}")
    labels=q.get("labels")
    if not isinstance(labels,list): _refuse(f"quantity labels missing: {name}")
    n=len(labels)
    required=("truth","posterior_mean","posterior_sd","q005","q025","q05","q50","q95","q975","q995","covered90","covered95","covered99","standardized_error")
    for k in required:
        v=q.get(k)
        if not isinstance(v,list) or len(v)!=n: _refuse(f"quantity {name}.{k} length differs")
    for k in ("truth","posterior_mean","posterior_sd","q005","q025","q05","q50","q95","q975","q995","standardized_error"):
        if np.any(~np.isfinite(np.asarray(q[k],dtype=float))): _refuse(f"quantity {name}.{k} nonfinite")
    return q


def _per_gene_fraction(rows:Sequence[Mapping], names:Sequence[str], field:str)->np.ndarray:
    out=[]
    for row in rows:
        vals=[]
        for name in names:
            q=_q(row,name)
            vals.extend(bool(x) for x in q[field])
        if not vals: _refuse(f"gene {row.get('gene_index')} has no scored quantities for {list(names)}")
        out.append(float(np.mean(vals)))
    return np.asarray(out,dtype=float)


def _per_gene_mean(rows:Sequence[Mapping], name:str, field:str)->np.ndarray:
    out=[]
    for row in rows:
        q=_q(row,name); a=_finite(q[field],name=f"{name}.{field}",allow_empty=True)
        if a.size: out.append(float(np.mean(a)))
    if len(out)<2: _refuse(f"{name}.{field} has fewer than two evaluable genes")
    return np.asarray(out,dtype=float)


def _flatten(rows:Sequence[Mapping], name:str, field:str)->np.ndarray:
    vals=[]
    for row in rows: vals.extend(_q(row,name)[field])
    return _finite(vals,name=f"{name}.{field}")


def _interval_exclusion_rates(rows:Sequence[Mapping], name:str)->dict[str,float]:
    counts={"90":["q05","q95"],"95":["q025","q975"],"99":["q005","q995"]}
    out={}
    for label,(lo,hi) in counts.items():
        flags=[]
        for row in rows:
            q=_q(row,name); a=_finite(q[lo],name=f"{name}.{lo}",allow_empty=True); b=_finite(q[hi],name=f"{name}.{hi}",allow_empty=True)
            if a.size!=b.size: _refuse("interval endpoint count differs")
            flags.extend(((a>0.0)|(b<0.0)).tolist())
        if not flags: _refuse(f"no evaluable intervals for {name}")
        out[label]=float(np.mean(flags))
    return out


def _base_result(gate:Mapping, statistic:Mapping, detail:Mapping|None=None)->dict:
    return {"world":gate["world"],"part":gate["part"],"gate":gate["gate"],
            "passed":bool(statistic["passed"]),"statistic":dict(statistic),"detail":dict(detail or {})}


def evaluate_gate(contract:Mapping, gate:Mapping, rows:Sequence[Mapping], *, alpha:float)->dict:
    world=str(gate.get("world")); part=str(gate.get("part")); name=str(gate.get("gate"))
    rows=validate_world_part_rows(rows,world=world,part=part)

    if name=="CONVERGENCE_ALL_FITS_DIAGNOSED":
        return _base_result(gate,S.convergence_all_fits_diagnosed([r.get("final_diagnosis") for r in rows]))

    if name=="POPULATION_DONOR_SD_RATIO":
        post=_flatten(rows,"donor_sd","posterior_mean"); truth=_flatten(rows,"donor_sd","truth")
        return _base_result(gate,S.population_donor_sd_ratio(post,truth,bounds=gate["bounds"]))

    if name=="PPC_EXTREME_RATE":
        p=[]
        for row in rows:
            table=row.get("ppc")
            if not isinstance(table,list) or not table: _refuse("PPC table missing")
            for rec in table:
                if not isinstance(rec,Mapping) or "p_value" not in rec: _refuse("PPC record schema differs")
                p.append(float(rec["p_value"]))
        return _base_result(gate,S.ppc_extreme_rate(p,alpha=alpha))

    if name=="TYPE_S_SOURCE":
        wrong=0; excluded=0
        for row in rows:
            q=_q(row,"source")
            truth=_finite(q["truth"],name="source.truth",allow_empty=True)
            mean=_finite(q["posterior_mean"],name="source.posterior_mean",allow_empty=True)
            lo=_finite(q["q05"],name="source.q05",allow_empty=True); hi=_finite(q["q95"],name="source.q95",allow_empty=True)
            if not (truth.size==mean.size==lo.size==hi.size): _refuse("TYPE_S source scalar count differs")
            exc=(lo>0.0)|(hi<0.0)
            excluded+=int(np.sum(exc)); wrong+=int(np.sum(exc & ((mean*truth)<0.0)))
        return _base_result(gate,S.type_s_gate(wrong_sign_count=wrong,excluded_count=excluded,alpha=alpha))

    test=str(gate.get("test",""))
    if test=="one_sided_t_lower_across_genes":
        names=gate.get("quantity_types")
        if names is None: names=[str(gate.get("quantity_type"))]
        if not isinstance(names,list) or not names or any(not isinstance(x,str) for x in names): _refuse("coverage quantity list differs")
        values=_per_gene_fraction(rows,names,"covered90")
        stat=S.one_sided_t_lower_across_genes(values,nominal=float(gate["nominal"]),alpha=alpha)
        return _base_result(gate,stat,{"quantity_types":list(names)})

    if test=="two_sided_t_across_genes_and_materiality":
        qname=str(gate.get("quantity_type")); values=_per_gene_mean(rows,qname,"standardized_error")
        stat=S.two_sided_t_across_genes_and_materiality(values,alpha=alpha,materiality=0.50)
        return _base_result(gate,stat,{"quantity_type":qname})

    if test=="binomial_lower":
        qname=str(gate.get("quantity_type")); covered=_flatten(rows,qname,"covered90").astype(bool)
        misses=int(np.sum(~covered)); nominal=float(gate["nominal"])
        stat=S.binomial_tail_gate(count=misses,n=int(covered.size),nominal=1.0-nominal,alpha=alpha)
        return _base_result(gate,stat,{"quantity_type":qname,"misses":misses,"coverage_nominal":nominal})

    if test=="interval_excludes_zero_rate":
        qname=str(gate.get("quantity_type")); rates=_interval_exclusion_rates(rows,qname); exclusion_nominal=float(gate["nominal"])
        if qname in {"class","source"}:
            cover0=[]
            for row in rows:
                q=_q(row,qname); lo=_finite(q["q05"],name=f"{qname}.q05",allow_empty=True); hi=_finite(q["q95"],name=f"{qname}.q95",allow_empty=True)
                if lo.size!=hi.size: _refuse("zero-coverage endpoint count differs")
                if lo.size: cover0.append(float(np.mean((lo<=0.0)&(0.0<=hi))))
            stat=S.one_sided_t_lower_across_genes(cover0,nominal=1.0-exclusion_nominal,alpha=alpha)
        else:
            lo=_flatten(rows,qname,"q05"); hi=_flatten(rows,qname,"q95"); exclusions=int(np.sum((lo>0.0)|(hi<0.0)))
            stat=S.binomial_tail_gate(count=exclusions,n=int(lo.size),nominal=exclusion_nominal,alpha=alpha)
        return _base_result(gate,stat,{"quantity_type":qname,"interval_exclusion_rates":rates})

    if test=="binomial_upper_q05_above_floor":
        qname=str(gate.get("quantity_type"))
        try: floor=float(contract["worlds"]["planting_magnitudes"]["fixed_magnitudes"]["donor_absent_floor"][part])
        except Exception as exc: _refuse(f"donor absent floor missing: {exc}")
        q05=_flatten(rows,qname,"q05"); count=int(np.sum(q05>floor))
        stat=S.binomial_tail_gate(count=count,n=int(q05.size),nominal=float(gate["nominal"]),alpha=alpha)
        return _base_result(gate,stat,{"quantity_type":qname,"floor":floor,"q05_above_floor_count":count})

    if test=="binomial_upper":
        _refuse(f"unrecognized binomial_upper gate {name}; TYPE_S/PPC must use their frozen named dispatch")

    _refuse(f"unsupported frozen gate/test {name}/{test}")


def build_gate_evaluations(contract:Mapping, scored_gene_rows:Sequence[Mapping])->list[dict]:
    rows=list(scored_gene_rows)
    if len(rows)!=1056: _refuse(f"scored campaign has {len(rows)} gene-part rows, expected 1056")
    grouped=defaultdict(list)
    for row in rows: grouped[(row.get("world_name"),row.get("part"))].append(row)
    expected={(str(w.get("name")),p) for w in contract.get("worlds",{}).get("world_list",[]) for p in ("detection","positive")}
    if set(grouped)!=expected: _refuse("scored world/part groups differ from frozen 12x2 authority")
    for (world,part),grp in grouped.items(): validate_world_part_rows(grp,world=world,part=part)
    alpha=float(contract["gates"]["multiplicity"]["alpha_per_gate"])
    out=[]
    for gate in contract["gates"]["list"]:
        out.append(evaluate_gate(contract,gate,grouped[(gate["world"],gate["part"])],alpha=alpha))
    if len(out)!=292: _refuse(f"evaluated {len(out)} gates, expected 292")
    return out
