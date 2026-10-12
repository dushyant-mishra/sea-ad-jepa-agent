#!/usr/bin/env python3
"""Truth-blind compact output primitives for V79 V2_CORE qualification fits.

These functions implement only predeclared Contract V2 output/statistic mechanics
plus controller-frozen prospective implementation conventions. They never read
controller truth and never score qualification gates.
"""
from __future__ import annotations

import hashlib
import re
from typing import Mapping

import numpy as np

PPC_DOMAIN = b"V79_V2_CORE_PPC_V1\0"


class FitOutputRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise FitOutputRefused(f"REFUSED V2_CORE fit output: {msg}")


def ppc_seed(fit_id: str) -> int:
    if not re.fullmatch(r"[0-9a-f]{64}",str(fit_id)): _refuse("PPC seed requires opaque 64-hex fit_id")
    digest=hashlib.sha256(PPC_DOMAIN+str(fit_id).encode("ascii")).digest()
    return int.from_bytes(digest[:4],"little",signed=False)


def two_sided_mid_p(observed: float, replicated: np.ndarray) -> float:
    r=np.asarray(replicated,dtype=float).reshape(-1)
    if r.size==0 or not np.isfinite(float(observed)) or np.any(~np.isfinite(r)):
        _refuse("mid-p requires finite observed value and nonempty finite replicates")
    gt=float(np.mean(r>observed)); lt=float(np.mean(r<observed)); eq=float(np.mean(r==observed))
    return float(min(1.0,2.0*min(gt+0.5*eq,lt+0.5*eq)))


def _decile_codes(z: np.ndarray, n_bins: int=10) -> np.ndarray:
    z=np.asarray(z,dtype=float).reshape(-1)
    if z.size==0 or np.any(~np.isfinite(z)) or n_bins<1: _refuse("invalid z for deciles")
    edges=np.quantile(z,np.linspace(0.0,1.0,n_bins+1))
    return np.clip(np.searchsorted(edges[1:-1],z,side="right"),0,n_bins-1).astype(np.int16)


def world_z_decile_codes(log_lib: np.ndarray, mask: np.ndarray, *, n_bins: int=10) -> np.ndarray:
    x=np.asarray(log_lib,dtype=float).reshape(-1); mask=np.asarray(mask,dtype=bool).reshape(-1)
    if len(x)==0 or len(mask)!=len(x) or np.any(~np.isfinite(x)): _refuse("invalid world log_lib/mask")
    sd=float(np.std(x,ddof=0))
    if not np.isfinite(sd) or sd<=0: _refuse("world log_lib has zero/nonfinite population SD")
    z=(x-float(np.mean(x)))/sd; edges=np.quantile(z,np.linspace(0.0,1.0,n_bins+1)); masked=z[mask]
    return np.clip(np.searchsorted(edges[1:-1],masked,side="right"),0,n_bins-1).astype(np.int16)


def _rec(name: str, value: float) -> dict:
    return {"name":str(name),"value":float(value)}


def detection_statistics(y: np.ndarray, *, z: np.ndarray, cls: np.ndarray, src: np.ndarray,
                         donor: np.ndarray, z_bin_count: int=10, z_bins: np.ndarray|None=None) -> list[dict]:
    y=np.asarray(y).reshape(-1); z=np.asarray(z).reshape(-1); cls=np.asarray(cls).reshape(-1); src=np.asarray(src).reshape(-1); donor=np.asarray(donor).reshape(-1)
    n=len(y)
    if n==0 or any(len(x)!=n for x in (z,cls,src,donor)): _refuse("unaligned detection PPC inputs")
    if np.any((y!=0)&(y!=1)): _refuse("detection PPC y must be binary")
    bins=_decile_codes(z,z_bin_count) if z_bins is None else np.asarray(z_bins,dtype=np.int16).reshape(-1)
    if len(bins)!=n or np.any((bins<0)|(bins>=z_bin_count)): _refuse("invalid detection z-decile codes")
    out=[_rec("zero_fraction_overall",np.mean(y==0))]
    for b in range(z_bin_count):
        m=bins==b
        if np.any(m): out.append(_rec(f"zero_fraction_zdecile_{b}",np.mean(y[m]==0)))
    for c in sorted(np.unique(cls).tolist()):
        m=cls==c; out.append(_rec(f"zero_fraction_class_{int(c)}",np.mean(y[m]==0)))
    for s in sorted(np.unique(src).tolist()):
        m=src==s; out.append(_rec(f"zero_fraction_source_{int(s)}",np.mean(y[m]==0)))
    donor_rates=[]
    for d in sorted(np.unique(donor).tolist()):
        m=donor==d
        if int(np.sum(m))>=5: donor_rates.append(float(np.mean(y[m])))
    if donor_rates: out.append(_rec("sd_donor_detection_fraction",np.std(np.asarray(donor_rates),ddof=0)))
    return out


def positive_statistics(y_log: np.ndarray, *, z: np.ndarray, donor: np.ndarray, z_bin_count: int=10,
                        z_bins: np.ndarray|None=None) -> list[dict]:
    y=np.asarray(y_log,dtype=float).reshape(-1); z=np.asarray(z,dtype=float).reshape(-1); donor=np.asarray(donor).reshape(-1)
    n=len(y)
    if n==0 or len(z)!=n or len(donor)!=n or np.any(~np.isfinite(y)): _refuse("unaligned/nonfinite positive PPC inputs")
    bins=_decile_codes(z,z_bin_count) if z_bins is None else np.asarray(z_bins,dtype=np.int16).reshape(-1)
    if len(bins)!=n or np.any((bins<0)|(bins>=z_bin_count)): _refuse("invalid positive z-decile codes")
    out=[_rec("mean_log_positive",np.mean(y)),_rec("variance_log_positive",np.var(y,ddof=0)),
         _rec("q01_log_positive",np.quantile(y,0.01)),_rec("q99_log_positive",np.quantile(y,0.99))]
    for b in range(z_bin_count):
        m=bins==b
        if int(np.sum(m))>=5: out.append(_rec(f"mean_log_positive_zdecile_{b}",np.mean(y[m])))
    donor_means=[]
    for d in sorted(np.unique(donor).tolist()):
        m=donor==d
        if int(np.sum(m))>=3: donor_means.append(float(np.mean(y[m])))
    if donor_means: out.append(_rec("sd_donor_mean_log_positive",np.std(np.asarray(donor_means),ddof=0)))
    return out


def _selected_indices(samples_by_chain: Mapping[str,np.ndarray], n_draws: int) -> np.ndarray:
    shapes=[]
    for v in samples_by_chain.values():
        a=np.asarray(v)
        if a.ndim<2: _refuse("posterior sites must retain chain and draw axes")
        shapes.append(a.shape[:2])
    if not shapes or len(set(shapes))!=1: _refuse("posterior chain/draw axes differ across sites")
    total=int(shapes[0][0]*shapes[0][1])
    if total<n_draws or n_draws<=0: _refuse("insufficient posterior draws")
    return np.linspace(0,total-1,int(n_draws),dtype=np.int64)


def _flat_selected(samples_by_chain: Mapping[str,np.ndarray], name: str, idx: np.ndarray) -> np.ndarray:
    if name not in samples_by_chain: _refuse(f"posterior site missing: {name}")
    a=np.asarray(samples_by_chain[name],dtype=float); flat=a.reshape((-1,)+a.shape[2:]); return flat[idx]


def _eta_draws(samples: Mapping[str,np.ndarray], data: Mapping, *, part: str, idx: np.ndarray) -> np.ndarray:
    alpha=_flat_selected(samples,"alpha",idx)
    b1=_flat_selected(samples,"beta_depth1" if part=="detection" else "gamma_depth1",idx)
    b2=_flat_selected(samples,"beta_depth2" if part=="detection" else "gamma_depth2",idx)
    cc=_flat_selected(samples,"class_contrasts",idx); sc=_flat_selected(samples,"source_contrasts",idx)
    ds=_flat_selected(samples,"donor_sd",idx); dr=_flat_selected(samples,"donor_raw",idx)
    z=np.asarray(data["z"],dtype=float); q=np.asarray(data["q"],dtype=float)
    cr=np.asarray(data["class_rows"],dtype=float); sr=np.asarray(data["source_rows"],dtype=float); wr=np.asarray(data["donor_rows"],dtype=float)
    eta=alpha[:,None]+b1[:,None]*z[None,:]+b2[:,None]*q[None,:]
    eta += cc@cr.T + sc@sr.T
    if wr.shape[1]: eta += (dr*ds[:,None])@wr.T
    return eta


def posterior_predictive_detection(samples_by_chain: Mapping[str,np.ndarray], data: Mapping, *, fit_id: str,
                                   world_log_lib: np.ndarray, measured_mask: np.ndarray, draws: int=1000) -> list[dict]:
    idx=_selected_indices(samples_by_chain,draws); eta=_eta_draws(samples_by_chain,data,part="detection",idx=idx)
    rng=np.random.default_rng(ppc_seed(fit_id)); p=1.0/(1.0+np.exp(-eta)); reps=(rng.random(p.shape)<p).astype(np.int8)
    zb=world_z_decile_codes(world_log_lib,measured_mask,n_bins=10)
    obs=detection_statistics(data["y"],z=data["z"],cls=data["cls_code"],src=data["src_code"],donor=data["donor_code"],z_bins=zb)
    rep_by={x["name"]:[] for x in obs}
    for row in reps:
        vals={x["name"]:x["value"] for x in detection_statistics(row,z=data["z"],cls=data["cls_code"],src=data["src_code"],donor=data["donor_code"],z_bins=zb)}
        if set(vals)!=set(rep_by): _refuse("detection replicated statistic set changed")
        for k in rep_by: rep_by[k].append(vals[k])
    return ppc_table(obs,{k:np.asarray(v) for k,v in rep_by.items()})


def posterior_predictive_positive(samples_by_chain: Mapping[str,np.ndarray], data: Mapping, *, fit_id: str,
                                  world_log_lib: np.ndarray, positive_mask: np.ndarray, draws: int=1000) -> list[dict]:
    idx=_selected_indices(samples_by_chain,draws); mu=_eta_draws(samples_by_chain,data,part="positive",idx=idx)
    sigma=_flat_selected(samples_by_chain,"sigma",idx)
    rng=np.random.default_rng(ppc_seed(fit_id)); reps=rng.normal(loc=mu,scale=sigma[:,None])
    zb=world_z_decile_codes(world_log_lib,positive_mask,n_bins=10)
    obs=positive_statistics(data["y_log"],z=data["z"],donor=data["donor_code"],z_bins=zb)
    rep_by={x["name"]:[] for x in obs}
    for row in reps:
        vals={x["name"]:x["value"] for x in positive_statistics(row,z=data["z"],donor=data["donor_code"],z_bins=zb)}
        if set(vals)!=set(rep_by): _refuse("positive replicated statistic set changed")
        for k in rep_by: rep_by[k].append(vals[k])
    return ppc_table(obs,{k:np.asarray(v) for k,v in rep_by.items()})


def full_donor_effect_summary(samples_by_chain: Mapping[str,np.ndarray], donor_basis_by_donor: np.ndarray) -> dict:
    """Full-posterior donor-effect summary; compact draw artifact is separate."""
    if set(("donor_raw","donor_sd"))-set(samples_by_chain): _refuse("donor posterior sites missing")
    raw=np.asarray(samples_by_chain["donor_raw"],dtype=float); sd=np.asarray(samples_by_chain["donor_sd"],dtype=float); W=np.asarray(donor_basis_by_donor,dtype=float)
    if raw.ndim!=3 or sd.ndim!=2 or raw.shape[:2]!=sd.shape or W.ndim!=2 or raw.shape[2]!=W.shape[1]: _refuse("donor posterior/basis shapes differ")
    flat=(raw.reshape(-1,raw.shape[-1])*sd.reshape(-1)[:,None])@W.T
    return {"mean":np.mean(flat,axis=0).tolist(),"sd":np.std(flat,axis=0,ddof=1).tolist(),
            "q05":np.quantile(flat,.05,axis=0).tolist(),"q50":np.quantile(flat,.50,axis=0).tolist(),
            "q95":np.quantile(flat,.95,axis=0).tolist()}


def compact_donor_effect_draws(samples_by_chain: Mapping[str,np.ndarray], donor_basis_by_donor: np.ndarray,
                                *, stored_draws: int=200) -> np.ndarray:
    if set(("donor_raw","donor_sd")) - set(samples_by_chain): _refuse("donor posterior sites missing")
    raw=np.asarray(samples_by_chain["donor_raw"],dtype=float); sd=np.asarray(samples_by_chain["donor_sd"],dtype=float); W=np.asarray(donor_basis_by_donor,dtype=float)
    if raw.ndim!=3 or sd.ndim!=2 or raw.shape[:2]!=sd.shape or W.ndim!=2 or raw.shape[2]!=W.shape[1]: _refuse("donor posterior/basis shapes differ")
    idx=_selected_indices({"donor_raw":raw,"donor_sd":sd},stored_draws)
    flat_raw=raw.reshape(-1,raw.shape[-1]); flat_sd=sd.reshape(-1)
    return np.asarray((flat_raw[idx]*flat_sd[idx,None])@W.T,dtype=np.float32)


def ppc_table(observed_stats: list[Mapping], replicated_stat_matrix: Mapping[str,np.ndarray]) -> list[dict]:
    out=[]
    for rec in observed_stats:
        name=str(rec.get("name")); value=float(rec.get("value"))
        if name not in replicated_stat_matrix: _refuse(f"missing replicated statistic {name}")
        out.append({"name":name,"observed":value,"p_value":two_sided_mid_p(value,np.asarray(replicated_stat_matrix[name],dtype=float))})
    if set(replicated_stat_matrix)!={x["name"] for x in observed_stats}: _refuse("replicated statistic set differs")
    return out
