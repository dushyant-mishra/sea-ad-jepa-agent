from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .v79_rare_biology_generator_v1 import RareWorldConfig, _donor_latent, SOURCES, VISIBILITY, SOURCE_NOISE, SIGNS


def _auc(y, score):
    y=np.asarray(y,dtype=int); score=np.asarray(score,float); n1=int(y.sum()); n0=len(y)-n1
    if n1==0 or n0==0: return float('nan')
    ranks=pd.Series(score).rank(method='average').to_numpy()
    return float((ranks[y==1].sum()-n1*(n1+1)/2)/(n1*n0))

@dataclass(frozen=True)
class SpatialConfig:
    seed:int
    mode:str='conditioned'  # conditioned | intrinsic
    regime:str='central'
    n_donors:int=66
    cells_per_donor:int=20
    niche_fraction:float=0.35
    niche_multiplier:float=8.0
    rna_effect:float=1.0
    base_noise:float=0.35

@dataclass
class SpatialWorld:
    cells:pd.DataFrame
    rna:np.ndarray
    context_true:np.ndarray
    context_shuffled:np.ndarray
    context_distant:np.ndarray


def generate_spatial(cfg:SpatialConfig)->SpatialWorld:
    if cfg.mode not in {'conditioned','intrinsic'}: raise ValueError(cfg.mode)
    rng=np.random.default_rng(cfg.seed)
    base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='rna_only')
    active,prev=_donor_latent(rng,base)
    src=np.array([SOURCES[i%3] for i in rng.permutation(cfg.n_donors)])
    rows=[]; blocks=[]; true_blocks=[]; shuf_blocks=[]; dist_blocks=[]
    for d in range(cfg.n_donors):
        n=cfg.cells_per_donor; niche_n=max(2,int(round(n*cfg.niche_fraction))); start=int(rng.integers(0,n))
        niche=np.zeros(n,dtype=int); niche[(start+np.arange(niche_n))%n]=1
        if cfg.mode=='conditioned' and prev[d]>0:
            p_in=min(0.5,prev[d]*cfg.niche_multiplier)
            remaining=max(0.0,prev[d]*n-p_in*niche_n)
            p_out=min(0.5,remaining/max(1,n-niche_n))
            p=np.where(niche==1,p_in,p_out)
        else:
            p=np.full(n,prev[d])
        R=rng.binomial(1,p)
        source=src[d]; vis=VISIBILITY[source]; noise=cfg.base_noise*SOURCE_NOISE[source]
        latent=R[:,None]*cfg.rna_effect*SIGNS[None,:]
        x=latent+rng.normal(0,noise,(n,len(SIGNS)))
        observed=rng.binomial(1,np.clip(vis+0.25*R[:,None],0,1)); x=x*observed
        true=np.empty_like(x); distant=np.empty_like(x); shuffled=np.empty_like(x)
        for i in range(n):
            true[i]=(x[(i-1)%n]+x[(i+1)%n])/2
            distant[i]=(x[(i+n//2-1)%n]+x[(i+n//2+1)%n])/2
            # Matched within-donor shuffled context must never contain the focal
            # cell itself. Choosing j=i±1 would put x[i] directly into the
            # shuffled neighbor average and leak the answer.
            forbidden={i,(i-1)%n,(i+1)%n}
            candidates=np.array([j for j in range(n) if j not in forbidden],dtype=int)
            j=int(rng.choice(candidates))
            shuffled[i]=(x[(j-1)%n]+x[(j+1)%n])/2
            rows.append({'donor_id':f'D{d:04d}','source':source,'cell_index':i,'niche':int(niche[i]),'R':int(R[i]),'donor_active':int(active[d]),'donor_prevalence':float(prev[d])})
        blocks.append(x); true_blocks.append(true); shuf_blocks.append(shuffled); dist_blocks.append(distant)
    return SpatialWorld(pd.DataFrame(rows),np.vstack(blocks),np.vstack(true_blocks),np.vstack(shuf_blocks),np.vstack(dist_blocks))


def score_spatial(w:SpatialWorld)->dict:
    y=w.cells['R'].to_numpy(dtype=int)
    own=(w.rna*SIGNS).mean(1); t=(w.context_true*SIGNS).mean(1); s=(w.context_shuffled*SIGNS).mean(1); d=(w.context_distant*SIGNS).mean(1)
    return {
      'n_positive':int(y.sum()),'prevalence':float(y.mean()),'own_rna_auc':_auc(y,own),
      'true_context_auc':_auc(y,t),'shuffled_context_auc':_auc(y,s),'distant_context_auc':_auc(y,d),
      'true_minus_shuffled_auc':_auc(y,t)-_auc(y,s),'true_minus_distant_auc':_auc(y,t)-_auc(y,d),
      'niche_R_prevalence':float(w.cells.loc[w.cells.niche==1,'R'].mean()),
      'non_niche_R_prevalence':float(w.cells.loc[w.cells.niche==0,'R'].mean()),
    }

@dataclass(frozen=True)
class PerturbConfig:
    seed:int
    regime:str='central'
    n_donors:int=66
    cells_per_donor:int=30
    rna_effect:float=1.0
    response_delta:float=0.5
    base_noise:float=0.35

@dataclass
class PerturbWorld:
    cells:pd.DataFrame
    rna:np.ndarray


def generate_perturb(cfg:PerturbConfig)->PerturbWorld:
    rng=np.random.default_rng(cfg.seed)
    base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='rna_only')
    active,prev=_donor_latent(rng,base)
    src=np.array([SOURCES[i%3] for i in rng.permutation(cfg.n_donors)])
    rows=[]; blocks=[]
    for d in range(cfg.n_donors):
        n=cfg.cells_per_donor; R=rng.binomial(1,prev[d],n)
        arms=np.tile(np.array([0,1,2],dtype=int), int(np.ceil(n/3)))[:n]; rng.shuffle(arms)  # 0 control,1 actual,2 null
        source=src[d]; vis=VISIBILITY[source]; noise=cfg.base_noise*SOURCE_NOISE[source]
        amp=cfg.rna_effect + cfg.response_delta*(arms==1)
        latent=R[:,None]*amp[:,None]*SIGNS[None,:]
        x=latent+rng.normal(0,noise,(n,len(SIGNS)))
        observed=rng.binomial(1,np.clip(vis+0.25*R[:,None],0,1)); x=x*observed
        for i in range(n): rows.append({'donor_id':f'D{d:04d}','source':source,'arm':int(arms[i]),'R':int(R[i]),'donor_active':int(active[d]),'donor_prevalence':float(prev[d])})
        blocks.append(x)
    return PerturbWorld(pd.DataFrame(rows),np.vstack(blocks))


def score_perturb(w:PerturbWorld)->dict:
    score=(w.rna*SIGNS).mean(1); df=w.cells.copy(); df['score']=score
    rpos=df[df.R==1]
    means=rpos.groupby('arm')['score'].mean()
    prev=df.groupby('arm')['R'].mean()
    control=float(means.get(0,np.nan)); actual=float(means.get(1,np.nan)); null=float(means.get(2,np.nan))
    return {
      'n_positive':int(df.R.sum()),'prevalence':float(df.R.mean()),
      'actual_minus_control_Rpos':actual-control,
      'null_minus_control_Rpos':null-control,
      'arm_prevalence_gap':float(prev.max()-prev.min()),
      'control_Rpos_mean':control,'actual_Rpos_mean':actual,'null_Rpos_mean':null,
    }


def evaluate_spatial_gate(score:dict, mode:str)->tuple[bool,list[str]]:
    failures=[]
    if mode=='conditioned':
        if score['true_minus_shuffled_auc'] <= 0.03: failures.append('true_not_better_than_shuffled')
        if score['true_minus_distant_auc'] <= 0.05: failures.append('true_not_better_than_distant')
        if score['niche_R_prevalence'] - score['non_niche_R_prevalence'] <= 0.03: failures.append('niche_enrichment_weak')
    elif mode=='intrinsic':
        if abs(score['true_minus_shuffled_auc']) >= 0.12: failures.append('false_true_neighbor_advantage_vs_shuffled')
        if abs(score['true_minus_distant_auc']) >= 0.15: failures.append('false_true_neighbor_advantage_vs_distant')
    else:
        raise ValueError(mode)
    return (not failures), failures


def evaluate_perturb_gate(score:dict)->tuple[bool,list[str]]:
    failures=[]
    if score['actual_minus_control_Rpos'] <= 0.08: failures.append('actual_response_too_small')
    if abs(score['null_minus_control_Rpos']) >= 0.12: failures.append('null_response_too_large')
    if score['arm_prevalence_gap'] >= 0.10: failures.append('arm_prevalence_imbalance')
    return (not failures), failures
