#!/usr/bin/env python3
"""Controller-only non-gating descriptive summaries for V79 V2_CORE.

All aggregation conventions were frozen prospectively before qualification outcomes.
This module consumes controller-scored identified quantity rows plus truth-blind fit-side
held-out metrics and controller-computed oracle references. It never changes gate logic.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import rankdata

SCHEMA="V79_V2_CORE_DESCRIPTIVE_METRICS_V1"
FAMILIES={"parameter_recovery","donor_recovery","detection_heldout","positive_heldout","ppc_q10_q11_second_stage"}

class DescriptiveRefused(RuntimeError): pass

def _refuse(msg:str): raise DescriptiveRefused(f"REFUSED V2_CORE descriptive aggregation: {msg}")

def _finite(values, name:str, *, allow_empty:bool=False)->np.ndarray:
    a=np.asarray(values,dtype=float).reshape(-1)
    if (a.size==0 and not allow_empty) or np.any(~np.isfinite(a)): _refuse(f"{name} requires finite values")
    return a

def _pearson(x,y):
    x=_finite(x,"pearson x",allow_empty=True); y=_finite(y,"pearson y",allow_empty=True)
    if x.size!=y.size or x.size<2: return None
    sx=float(np.std(x)); sy=float(np.std(y))
    if sx==0.0 or sy==0.0:
        return 1.0 if np.array_equal(x,y) else None
    return float(np.corrcoef(x,y)[0,1])

def _rmse(x,y):
    x=_finite(x,"rmse x"); y=_finite(y,"rmse y")
    if x.size!=y.size: _refuse("RMSE lengths differ")
    return float(np.sqrt(np.mean((x-y)**2)))

def _median_iqr(values):
    a=_finite(values,"summary values",allow_empty=True)
    if a.size==0: return {"n_defined":0,"median":None,"q25":None,"q75":None}
    return {"n_defined":int(a.size),"median":float(np.median(a)),"q25":float(np.quantile(a,.25)),"q75":float(np.quantile(a,.75))}

def _quantity(row:Mapping,name:str)->Mapping:
    q=row.get("quantities",{}).get(name)
    if not isinstance(q,Mapping): _refuse(f"quantity missing: {name}")
    labels=q.get("labels"); truth=q.get("truth"); mean=q.get("posterior_mean")
    if not isinstance(labels,list) or not isinstance(truth,list) or not isinstance(mean,list) or len(labels)!=len(truth) or len(labels)!=len(mean):
        _refuse(f"quantity schema differs: {name}")
    _finite(truth,f"{name}.truth",allow_empty=True); _finite(mean,f"{name}.posterior_mean",allow_empty=True)
    return q


def _pair_metrics(truth,mean)->dict:
    t=_finite(truth,"truth"); m=_finite(mean,"posterior mean")
    if t.size!=m.size: _refuse("truth/posterior count differs")
    nz=t!=0
    sign=None if not np.any(nz) else float(np.mean(np.sign(t[nz])==np.sign(m[nz])))
    return {"n_scalars":int(t.size),"pearson":_pearson(t,m),"rmse":_rmse(t,m),"sign_agreement_nonzero_truth":sign}


def parameter_recovery(scored_rows:Sequence[Mapping])->dict:
    pooled=defaultdict(lambda:{"truth":[],"mean":[],"by_label":defaultdict(lambda:{"truth":[],"mean":[]})})
    for row in scored_rows:
        world=str(row.get("world_name")); part=str(row.get("part")); quantities=row.get("quantities")
        if not world or part not in {"detection","positive"} or not isinstance(quantities,Mapping): _refuse("scored row identity differs")
        for name,q in quantities.items():
            if name=="donor_effects": continue
            q=_quantity(row,name); key=f"{world}|{part}|{name}"
            for label,t,m in zip(q["labels"],q["truth"],q["posterior_mean"]):
                pooled[key]["truth"].append(float(t)); pooled[key]["mean"].append(float(m))
                pooled[key]["by_label"][str(label)]["truth"].append(float(t)); pooled[key]["by_label"][str(label)]["mean"].append(float(m))
    groups={}
    for key,rec in sorted(pooled.items()):
        out=_pair_metrics(rec["truth"],rec["mean"]); out["by_label"]={}
        for label,x in sorted(rec["by_label"].items()):
            out["by_label"][label]=_pair_metrics(x["truth"],x["mean"])
        groups[key]=out
    return {"gating":False,"groups":groups}


def _spearman(x,y):
    x=_finite(x,"spearman x",allow_empty=True); y=_finite(y,"spearman y",allow_empty=True)
    if x.size!=y.size or x.size<3 or np.std(x)==0 or np.std(y)==0: return None
    return _pearson(rankdata(x,method="average"),rankdata(y,method="average"))

def _calibration_slope(posterior,truth):
    x=_finite(posterior,"calibration posterior",allow_empty=True); y=_finite(truth,"calibration truth",allow_empty=True)
    if x.size!=y.size or x.size<3 or np.var(x)==0: return None
    return float(np.mean((x-x.mean())*(y-y.mean()))/np.var(x))

def donor_recovery(scored_rows:Sequence[Mapping])->dict:
    per=[]
    for row in scored_rows:
        q=_quantity(row,"donor_effects"); t=_finite(q["truth"],"donor truth",allow_empty=True); m=_finite(q["posterior_mean"],"donor posterior",allow_empty=True)
        if t.size!=m.size: _refuse("donor truth/posterior count differs")
        if t.size<3 or np.std(t)==0 or np.std(m)==0:
            spearman=slope=shrink=None
        else:
            spearman=_spearman(m,t); slope=_calibration_slope(m,t); shrink=float(np.std(m,ddof=0)/np.std(t,ddof=0))
        per.append({"world_name":row.get("world_name"),"part":row.get("part"),"gene_index":int(row.get("gene_index")),
                    "n_informative_donors":int(t.size),"spearman":spearman,"calibration_slope":slope,"shrinkage_factor":shrink})
    summary={}
    for metric in ("spearman","calibration_slope","shrinkage_factor"):
        summary[metric]=_median_iqr([r[metric] for r in per if r[metric] is not None])
    return {"gating":False,"per_gene":per,"summary":summary}


def _heldout_records(receipts:Sequence[Mapping],oracle_by_fit_id:Mapping,*,part:str,metric:str,delta_name:str)->dict:
    rows={"same_donor":[],"new_donor":[]}; low=[]
    for rec in receipts:
        if rec.get("part")!=part: continue
        fid=str(rec.get("fit_id")); held=rec.get("heldout_predictive"); oracle=oracle_by_fit_id.get(fid)
        if not isinstance(held,Mapping) or not isinstance(oracle,Mapping): _refuse(f"heldout/oracle record missing for fit {fid}")
        for mode in ("same_donor","new_donor"):
            model=held.get(mode); ref=oracle.get(mode)
            if not isinstance(model,Mapping) or not isinstance(ref,Mapping): _refuse(f"heldout/oracle mode missing for fit {fid}")
            mv=float(model[metric]); ov=float(ref[metric])
            if not np.isfinite(mv) or not np.isfinite(ov): _refuse("heldout/oracle metric nonfinite")
            rows[mode].append(mv-ov)
        if part=="detection" and float(oracle.get("planted_prevalence",np.nan))<0.05: low.append(rows["same_donor"][-1])
    out={"gating":False}
    for mode,vals in rows.items():
        a=_finite(vals,f"{part} {mode}",allow_empty=True)
        out[mode]={"n_fits":int(a.size),delta_name:None if a.size==0 else float(np.mean(a)),"median_delta":None if a.size==0 else float(np.median(a))}
    if part=="detection":
        a=_finite(low,"low prevalence deltas",allow_empty=True)
        out["low_prevalence_lt_0_05"]={"n_fits":int(a.size),delta_name:None if a.size==0 else float(np.mean(a))}
    return out

def detection_heldout(receipts:Sequence[Mapping],oracle_by_fit_id:Mapping)->dict:
    return _heldout_records(receipts,oracle_by_fit_id,part="detection",metric="mean_log_loss",delta_name="mean_model_minus_oracle_log_loss")
def positive_heldout(receipts:Sequence[Mapping],oracle_by_fit_id:Mapping)->dict:
    return _heldout_records(receipts,oracle_by_fit_id,part="positive",metric="mean_lpd",delta_name="mean_model_minus_oracle_mean_lpd")


def _row_abs_z(row):
    vals=[]
    for q in row.get("quantities",{}).values(): vals.extend(np.abs(_finite(q.get("standardized_error",[]),"standardized error",allow_empty=True)).tolist())
    return None if not vals else float(np.mean(vals))
def _row_donor_rmse(row):
    q=_quantity(row,"donor_effects"); return _rmse(q["truth"],q["posterior_mean"])
def _row_ppc_extreme(row):
    p=row.get("ppc")
    if not isinstance(p,list) or not p: _refuse("PPC rows missing")
    vals=[]
    for rec in p:
        if not isinstance(rec,Mapping) or "p_value" not in rec: _refuse("PPC record differs")
        v=float(rec["p_value"])
        if not 0<=v<=1: _refuse("PPC p-value outside [0,1]")
        vals.append(v<0.01)
    return float(np.mean(vals))

def _pc1_fraction(matrix):
    x=np.asarray(matrix,dtype=float)
    if x.ndim!=2 or x.shape[0]<2 or x.shape[1]<2: return None
    x=x-x.mean(axis=1,keepdims=True)
    s=np.linalg.svd(x,compute_uv=False)
    total=float(np.sum(s*s))
    return None if total<=0 else float((s[0]*s[0])/total)
def _second_stage_group(rows):
    if len(rows)<3: return {"n_genes":len(rows),"n_common_donors":0,"gene_correlation_upper_triangle_pearson":None,"gene_correlation_upper_triangle_rmse":None,"truth_pc1_variance_fraction":None,"posterior_pc1_variance_fraction":None}
    label_sets=[set(_quantity(r,"donor_effects")["labels"]) for r in rows]
    common=sorted(set.intersection(*label_sets)) if label_sets else []
    if len(common)<2: return {"n_genes":len(rows),"n_common_donors":len(common),"gene_correlation_upper_triangle_pearson":None,"gene_correlation_upper_triangle_rmse":None,"truth_pc1_variance_fraction":None,"posterior_pc1_variance_fraction":None}
    truth=[]; post=[]
    for r in sorted(rows,key=lambda x:int(x["gene_index"])):
        q=_quantity(r,"donor_effects"); idx={label:i for i,label in enumerate(q["labels"])}
        truth.append([q["truth"][idx[x]] for x in common]); post.append([q["posterior_mean"][idx[x]] for x in common])
    t=np.asarray(truth,dtype=float); m=np.asarray(post,dtype=float)
    tc=np.corrcoef(t); mc=np.corrcoef(m); iu=np.triu_indices(len(rows),1)
    tv=np.asarray(tc[iu],dtype=float); mv=np.asarray(mc[iu],dtype=float); finite=np.isfinite(tv)&np.isfinite(mv)
    corr=None; rmse=None
    if np.any(finite): corr=_pearson(tv[finite],mv[finite]); rmse=_rmse(tv[finite],mv[finite])
    return {"n_genes":len(rows),"n_common_donors":len(common),"gene_correlation_upper_triangle_pearson":corr,
            "gene_correlation_upper_triangle_rmse":rmse,"truth_pc1_variance_fraction":_pc1_fraction(t),"posterior_pc1_variance_fraction":_pc1_fraction(m)}


def ppc_q10_q11_second_stage(scored_rows:Sequence[Mapping],*,heldout_model_metric:Mapping|None=None)->dict:
    rows=list(scored_rows); heldout_model_metric=heldout_model_metric or {}
    ppc_summary={}; grouped=defaultdict(list)
    for row in rows:
        key=f"{row.get('world_name')}|{row.get('part')}"; grouped[key].append(row)
    for key,grp in sorted(grouped.items()):
        by_name=defaultdict(list)
        for r in grp:
            for rec in r.get("ppc",[]): by_name[str(rec.get("name"))].append(float(rec.get("p_value")))
        ppc_summary[key]={name:{"n":len(vals),"extreme_lt_0_01_count":int(np.sum(np.asarray(vals)<.01)),"extreme_fraction":float(np.mean(np.asarray(vals)<.01))} for name,vals in sorted(by_name.items())}
    pairs={}
    for r in rows:
        world=str(r.get("world_name"))
        if world in {"Q10_S174_DESIGN_IMBALANCE","Q11_OMITTED_OPERATOR"}: pairs[(world,str(r.get("part")),int(r.get("gene_index")))]=r
    contrast={}
    for part in ("detection","positive"):
        deltas_z=[]; deltas_donor=[]; deltas_ppc=[]; deltas_held=[]; n=0
        for g in sorted({k[2] for k in pairs if k[1]==part}):
            a=pairs.get(("Q10_S174_DESIGN_IMBALANCE",part,g)); b=pairs.get(("Q11_OMITTED_OPERATOR",part,g))
            if a is None or b is None: continue
            za=_row_abs_z(a); zb=_row_abs_z(b)
            if za is not None and zb is not None: deltas_z.append(zb-za)
            deltas_donor.append(_row_donor_rmse(b)-_row_donor_rmse(a)); deltas_ppc.append(_row_ppc_extreme(b)-_row_ppc_extreme(a))
            ka=("Q10_S174_DESIGN_IMBALANCE",part,g); kb=("Q11_OMITTED_OPERATOR",part,g)
            if ka in heldout_model_metric and kb in heldout_model_metric: deltas_held.append(float(heldout_model_metric[kb])-float(heldout_model_metric[ka]))
            n+=1
        contrast[part]={"paired_genes":n,"mean_abs_standardized_error_delta":None if not deltas_z else float(np.mean(deltas_z)),
                        "donor_effect_rmse_delta":None if not deltas_donor else float(np.mean(deltas_donor)),
                        "ppc_extreme_fraction_delta":None if not deltas_ppc else float(np.mean(deltas_ppc)),
                        "heldout_model_metric_delta":None if not deltas_held else float(np.mean(deltas_held))}
    second={key:_second_stage_group(grp) for key,grp in sorted(grouped.items())}
    return {"gating":False,"ppc_by_world_part_statistic":ppc_summary,"q11_minus_q10":contrast,"second_stage":second}


def build_descriptive_metrics(scored_rows:Sequence[Mapping],fit_receipts:Sequence[Mapping],oracle_by_fit_id:Mapping,*,heldout_model_metric:Mapping|None=None)->dict:
    families={
        "parameter_recovery":parameter_recovery(scored_rows),
        "donor_recovery":donor_recovery(scored_rows),
        "detection_heldout":detection_heldout(fit_receipts,oracle_by_fit_id),
        "positive_heldout":positive_heldout(fit_receipts,oracle_by_fit_id),
        "ppc_q10_q11_second_stage":ppc_q10_q11_second_stage(scored_rows,heldout_model_metric=heldout_model_metric),
    }
    if set(families)!=FAMILIES: _refuse("descriptive family set differs")
    return {"schema":SCHEMA,"gating":False,"families":families}
