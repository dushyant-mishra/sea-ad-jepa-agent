#!/usr/bin/env python3
"""Controller-only identified truth/posterior quantity matching for V79 V2_CORE."""
from __future__ import annotations

import re
from typing import Mapping

import numpy as np

import v79_v2_core_score_truth as T


class QuantityScoreRefused(RuntimeError): pass

def _refuse(msg:str): raise QuantityScoreRefused(f"REFUSED V2_CORE quantity score: {msg}")

def _helmert3()->np.ndarray:
    h=np.zeros((3,2),dtype=float)
    for j in range(2):
        den=np.sqrt((j+1)*(j+2)); h[:j+1,j]=1.0/den; h[j+1,j]=-(j+1)/den
    return h


def _raw_gene_truth(world:T.TruthWorld,part:str,gene_index:int)->dict[str,np.ndarray]:
    if part not in {"detection","positive"}: _refuse("unknown part")
    if not isinstance(gene_index,int) or not (0<=gene_index<44): _refuse("gene index outside frozen 44-gene panel")
    out={}
    for name in ("intercept","depth1","depth2","class_contrasts","source_contrasts","donor_sd"):
        a=world.load(f"truth/{part}/{name}.npy")
        if a.shape[0]!=44: _refuse(f"truth {name} gene dimension differs")
        out[name]=np.asarray(a[gene_index],dtype=float)
    donor=world.load(f"truth/{part}/donor_effects.npy")
    if donor.ndim!=2 or donor.shape[1]!=44: _refuse("truth donor_effects must be donor x 44 genes")
    out["donor_effects"]=np.asarray(donor[:,gene_index],dtype=float)
    if part=="positive":
        a=world.load("truth/positive/sigma.npy")
        if a.shape!=(44,): _refuse("positive sigma truth shape differs")
        out["sigma"]=np.asarray(a[gene_index],dtype=float)
    return out


def _identified_factor_truth(raw_contrasts:np.ndarray, ident:Mapping, labels:list[str], *, factor:str)->tuple[np.ndarray,np.ndarray]:
    c=np.asarray(raw_contrasts,dtype=float).reshape(-1)
    if c.shape!=(2,): _refuse(f"{factor} truth contrast shape differs")
    B=_helmert3(); effects=B@c
    levels=ident.get("observed_levels")
    if not isinstance(levels,list) or not levels or any(not isinstance(x,int) or x not in (0,1,2) for x in levels) or levels!=sorted(set(levels)):
        _refuse(f"{factor} observed levels differ")
    mode=ident.get("mode")
    if mode=="helmert":
        if levels!=[0,1,2] or ident.get("reference_level") is not None or labels!=["helmert_0","helmert_1"]:
            _refuse(f"{factor} helmert identification differs")
        return c,effects
    if mode!="level_differences": _refuse(f"unknown {factor} identification mode")
    ref=ident.get("reference_level")
    if ref!=levels[0]: _refuse(f"{factor} reference level differs")
    expected_labels=[f"level_{lev}_minus_{ref}" for lev in levels[1:]]
    if labels!=expected_labels: _refuse(f"{factor} level-difference labels differ")
    vals=np.asarray([effects[lev]-effects[ref] for lev in levels[1:]],dtype=float)
    return vals,effects


SUMMARY_KEYS={"labels","mean","sd","q005","q025","q05","q50","q95","q975","q995"}

def _posterior_quantity(rec:Mapping,name:str)->dict:
    q=rec.get("quantities",{}).get(name)
    if not isinstance(q,Mapping) or set(q)!=SUMMARY_KEYS: _refuse(f"posterior quantity schema differs: {name}")
    labels=q["labels"]
    if not isinstance(labels,list) or any(not isinstance(x,str) for x in labels): _refuse(f"posterior labels differ: {name}")
    n=len(labels); out={"labels":list(labels)}
    for k in ("mean","sd","q005","q025","q05","q50","q95","q975","q995"):
        a=np.asarray(q[k],dtype=float).reshape(-1)
        if a.size!=n or np.any(~np.isfinite(a)): _refuse(f"posterior {name}.{k} differs")
        out[k]=a
    if np.any(out["sd"]<=0): _refuse(f"posterior {name} has nonpositive SD")
    if np.any(out["q005"]>out["q025"]) or np.any(out["q025"]>out["q05"]) or np.any(out["q05"]>out["q50"]) or np.any(out["q50"]>out["q95"]) or np.any(out["q95"]>out["q975"]) or np.any(out["q975"]>out["q995"]):
        _refuse(f"posterior quantiles not ordered: {name}")
    return out


def identified_truth_for_summary(world:T.TruthWorld,part:str,gene_index:int,summary:Mapping)->dict[str,np.ndarray]:
    if summary.get("schema")!="V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1" or summary.get("part")!=part: _refuse("identified summary schema/part differs")
    ident=summary.get("identification"); qs=summary.get("quantities")
    if not isinstance(ident,Mapping) or not isinstance(qs,Mapping): _refuse("identified summary sections missing")
    raw=_raw_gene_truth(world,part,gene_index)
    class_post=_posterior_quantity(summary,"class"); source_post=_posterior_quantity(summary,"source")
    class_truth,class_effects=_identified_factor_truth(raw["class_contrasts"],ident.get("class",{}),class_post["labels"],factor="class")
    source_truth,source_effects=_identified_factor_truth(raw["source_contrasts"],ident.get("source",{}),source_post["labels"],factor="source")
    class_levels=ident["class"]["observed_levels"]; source_levels=ident["source"]["observed_levels"]
    intercept=float(np.asarray(raw["intercept"]).reshape(()))+float(np.mean(class_effects[class_levels]))+float(np.mean(source_effects[source_levels]))
    out={"intercept":np.asarray([intercept]),"depth1":np.asarray([float(np.asarray(raw["depth1"]).reshape(()))]),
         "depth2":np.asarray([float(np.asarray(raw["depth2"]).reshape(()))]),"class":class_truth,"source":source_truth,
         "donor_sd":np.asarray([float(np.asarray(raw["donor_sd"]).reshape(()))])}
    donor_post=_posterior_quantity(summary,"donor_effects"); donor_raw=np.asarray(raw["donor_effects"],dtype=float).reshape(-1); donor_vals=[]
    for label in donor_post["labels"]:
        m=re.fullmatch(r"donor_(\d+)",label)
        if not m: _refuse("donor label differs")
        d=int(m.group(1))
        if d>=len(donor_raw): _refuse("donor truth index out of range")
        donor_vals.append(donor_raw[d])
    codes=ident.get("donor_codes")
    if codes!=[int(x.split("_")[1]) for x in donor_post["labels"]]: _refuse("donor identification labels/codes differ")
    out["donor_effects"]=np.asarray(donor_vals,dtype=float)
    if part=="positive": out["sigma"]=np.asarray([float(np.asarray(raw["sigma"]).reshape(()))])
    if set(qs)!=set(out): _refuse(f"posterior quantity set differs: {set(qs)^set(out)}")
    for name,truth in out.items():
        post=_posterior_quantity(summary,name)
        if len(truth)!=len(post["labels"]): _refuse(f"truth/posterior scalar count differs: {name}")
    return out


def score_gene_quantities(world:T.TruthWorld,fit_receipt:Mapping)->dict:
    if fit_receipt.get("schema")!="V79_V2_CORE_FIT_RECORD_V1" or fit_receipt.get("execution_mode")!="QUALIFICATION": _refuse("qualification fit receipt required")
    if fit_receipt.get("opaque_world_id")!=world.opaque_world_id: _refuse("fit/truth opaque world mismatch")
    part=str(fit_receipt.get("part")); gene=int(fit_receipt.get("gene_index",-1)); summary=fit_receipt.get("scoring_summary")
    truth=identified_truth_for_summary(world,part,gene,summary); rows={}
    for name,t in truth.items():
        p=_posterior_quantity(summary,name); t=np.asarray(t,dtype=float).reshape(-1)
        covered90=(p["q05"]<=t)&(t<=p["q95"]); covered95=(p["q025"]<=t)&(t<=p["q975"]); covered99=(p["q005"]<=t)&(t<=p["q995"]); z=(p["mean"]-t)/p["sd"]
        rows[name]={"labels":p["labels"],"truth":t.tolist(),"posterior_mean":p["mean"].tolist(),"posterior_sd":p["sd"].tolist(),
                    "q005":p["q005"].tolist(),"q025":p["q025"].tolist(),"q05":p["q05"].tolist(),"q50":p["q50"].tolist(),
                    "q95":p["q95"].tolist(),"q975":p["q975"].tolist(),"q995":p["q995"].tolist(),
                    "covered90":covered90.astype(bool).tolist(),"covered95":covered95.astype(bool).tolist(),"covered99":covered99.astype(bool).tolist(),"standardized_error":z.tolist()}
    return {"opaque_world_id":world.opaque_world_id,"world_name":world.world_name,"world_index":world.world_index,"gene_index":gene,"part":part,
            "final_diagnosis":fit_receipt.get("final_diagnosis"),"quantities":rows,"ppc":fit_receipt.get("ppc")}
