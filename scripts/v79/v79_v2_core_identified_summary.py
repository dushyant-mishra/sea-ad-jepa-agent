#!/usr/bin/env python3
"""Truth-blind scoring-ready posterior summaries for V79 V2_CORE.

The qualification contract changes the scored parameterization when a class/source
level is not informative. Full chains are intentionally not retained, so these
derived quantities must be computed from the live joint posterior before disposal.
This module contains no truth, Q-label, gate or scoring logic.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np


class IdentifiedSummaryRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise IdentifiedSummaryRefused(f"REFUSED V2_CORE identified summary: {msg}")


def _flat(samples: Mapping[str,np.ndarray], name: str) -> np.ndarray:
    if name not in samples: _refuse(f"posterior site missing: {name}")
    a=np.asarray(samples[name],dtype=float)
    if a.ndim<2: _refuse(f"posterior site lacks chain/draw axes: {name}")
    return a.reshape((-1,)+a.shape[2:])


def _summary(draws: np.ndarray, labels: list[str]) -> dict:
    a=np.asarray(draws,dtype=float)
    if a.ndim==1: a=a[:,None]
    if a.ndim!=2 or a.shape[1]!=len(labels) or a.shape[0]<2: _refuse("summary draw/label shape mismatch")
    keys=("q005","q025","q05","q50","q95","q975","q995")
    probs=(.005,.025,.05,.50,.95,.975,.995)
    if len(labels)==0:
        return {"labels":[],"mean":[],"sd":[],**{k:[] for k in keys}}
    out={"labels":list(labels),"mean":np.mean(a,axis=0).tolist(),"sd":np.std(a,axis=0,ddof=1).tolist()}
    for key,p in zip(keys,probs): out[key]=np.quantile(a,p,axis=0).tolist()
    return out


def _factor_draws(samples: Mapping[str,np.ndarray], data: Mapping, *, site: str, basis_key: str, code_key: str):
    c=_flat(samples,site)
    basis=np.asarray(data[basis_key],dtype=float)
    codes=sorted(int(x) for x in np.unique(np.asarray(data[code_key],dtype=int)))
    if c.ndim!=2 or basis.shape!=(3,2) or any(x not in (0,1,2) for x in codes): _refuse(f"invalid factor geometry for {site}")
    effects=c@basis.T
    if codes==[0,1,2]:
        return c,["helmert_0","helmert_1"],{"mode":"helmert","observed_levels":codes,"reference_level":None},effects
    ref=codes[0]
    if len(codes)==1:
        scored=np.zeros((c.shape[0],0),dtype=float); labels=[]
    else:
        scored=np.stack([effects[:,lev]-effects[:,ref] for lev in codes[1:]],axis=1)
        labels=[f"level_{lev}_minus_{ref}" for lev in codes[1:]]
    return scored,labels,{"mode":"level_differences","observed_levels":codes,"reference_level":ref},effects


def scoring_ready_summary(samples_by_chain: Mapping[str,np.ndarray], data: Mapping, *, part: str) -> dict:
    if part not in {"detection","positive"}: _refuse("part must be detection or positive")
    alpha=_flat(samples_by_chain,"alpha").reshape(-1)
    class_scored,class_labels,class_id,class_effects=_factor_draws(samples_by_chain,data,site="class_contrasts",basis_key="class_basis",code_key="cls_code")
    source_scored,source_labels,source_id,source_effects=_factor_draws(samples_by_chain,data,site="source_contrasts",basis_key="source_basis",code_key="src_code")
    class_obs=class_id["observed_levels"]; source_obs=source_id["observed_levels"]
    intercept=alpha+class_effects[:,class_obs].mean(axis=1)+source_effects[:,source_obs].mean(axis=1)
    depth1=_flat(samples_by_chain,"beta_depth1" if part=="detection" else "gamma_depth1").reshape(-1)
    depth2=_flat(samples_by_chain,"beta_depth2" if part=="detection" else "gamma_depth2").reshape(-1)
    donor_sd=_flat(samples_by_chain,"donor_sd").reshape(-1)
    raw=_flat(samples_by_chain,"donor_raw"); W=np.asarray(data["donor_basis_by_donor"],dtype=float)
    if raw.ndim!=2 or raw.shape[1]!=W.shape[1] or len(raw)!=len(donor_sd): _refuse("donor posterior geometry differs")
    donor_effects=(raw*donor_sd[:,None])@W.T
    donor_codes=sorted(int(x) for x in np.unique(np.asarray(data["donor_code"],dtype=int)))
    if any(d<0 or d>=W.shape[0] for d in donor_codes): _refuse("informative donor code out of range")
    quantities={
        "intercept":_summary(intercept,["intercept"]),
        "depth1":_summary(depth1,["depth1"]),
        "depth2":_summary(depth2,["depth2"]),
        "class":_summary(class_scored,class_labels),
        "source":_summary(source_scored,source_labels),
        "donor_sd":_summary(donor_sd,["donor_sd"]),
        "donor_effects":_summary(donor_effects[:,donor_codes],[f"donor_{d}" for d in donor_codes]),
    }
    if part=="positive": quantities["sigma"]=_summary(_flat(samples_by_chain,"sigma").reshape(-1),["sigma"])
    return {"schema":"V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1","part":part,
            "identification":{"class":class_id,"source":source_id,"donor_codes":donor_codes},
            "quantities":quantities}
