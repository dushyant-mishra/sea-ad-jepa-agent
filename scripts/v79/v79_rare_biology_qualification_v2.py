from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .v79_rare_biology_generator_v1 import RareWorldConfig, generate_world, SIGNS

KINDS=('rna_recoverable','teacher_private','separate_nucleus','technical_twin')
EVIDENCE_LEVELS=(0.2,0.4,0.6,0.8,1.0)
DEPTH_LEVELS=(0.25,0.5,0.75,1.0)

@dataclass(frozen=True)
class ChallengeConfig:
    seed: int
    kind: str
    regime: str='central'
    n_donors: int=66
    cells_per_donor: int=20


def build_challenge(cfg: ChallengeConfig):
    if cfg.kind not in KINDS: raise ValueError(cfg.kind)
    if cfg.kind=='rna_recoverable':
        base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='same_nucleus',rna_effect=1.0,atac_effect=1.35)
    elif cfg.kind=='teacher_private':
        base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='same_nucleus',rna_effect=0.15,atac_effect=1.35)
    elif cfg.kind=='separate_nucleus':
        base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='separate_nucleus',rna_effect=1.0,atac_effect=1.35)
    else:
        base=RareWorldConfig(seed=cfg.seed,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor,regime=cfg.regime,world='technical_twin',rna_effect=1.0,atac_effect=1.35)
    return generate_world(base)


def _auc(y, score):
    y=np.asarray(y,dtype=int); score=np.asarray(score,float); n1=int(y.sum()); n0=len(y)-n1
    if n1==0 or n0==0: return float('nan')
    ranks=pd.Series(score).rank(method='average').to_numpy()
    return float((ranks[y==1].sum()-n1*(n1+1)/2)/(n1*n0))


def evidence_score(rna, fraction: float, seed: int):
    k=max(1,round(rna.shape[1]*fraction)); rng=np.random.default_rng(seed); order=rng.permutation(rna.shape[1]); idx=np.sort(order[:k])
    return (rna[:,idx]*SIGNS[idx]).mean(axis=1)


def depth_score(rna, fraction: float, seed: int):
    rng=np.random.default_rng(seed); u=rng.random(rna.shape); keep=(u < fraction).astype(float)
    return (rna*keep*SIGNS[None,:]).mean(axis=1)


def score_challenge(cfg: ChallengeConfig):
    w=build_challenge(cfg); y=w.cells['R'].to_numpy(dtype=int); pseudo=w.cells['pseudo_rare'].to_numpy(dtype=int)
    rna=(w.rna*SIGNS[None,:]).mean(axis=1); atac=w.atac.mean(axis=1)
    donor=pd.DataFrame({'donor':w.cells['donor_id'],'rna':rna,'atac':atac}).groupby('donor').mean()
    source_prev=w.cells.groupby('source')['R'].mean()
    out={
      'kind':cfg.kind,'regime':cfg.regime,'n_positive':int(y.sum()),'prevalence':float(y.mean()),'pseudo_prevalence':float(pseudo.mean()),
      'zero_donor_fraction':float((w.cells.drop_duplicates('donor_id')['donor_active']==0).mean()),
      'source_prevalence_gap':float(source_prev.max()-source_prev.min()),
      'rna_auc_full':_auc(y,rna),'teacher_auc_full':_auc(y,rna+atac),'pseudo_auc_rna':_auc(pseudo,rna),
      'same_cell_rna_atac_corr':float(np.corrcoef(rna,atac)[0,1]) if np.std(rna)>0 and np.std(atac)>0 else float('nan'),
      'donor_rna_atac_corr':float(donor['rna'].corr(donor['atac'])) if donor['atac'].std()>0 else float('nan'),
    }
    for f in EVIDENCE_LEVELS: out[f'rna_auc_e{int(f*100)}']=_auc(y,evidence_score(w.rna,f,8100))
    for f in DEPTH_LEVELS: out[f'rna_auc_d{int(f*100)}']=_auc(y,depth_score(w.rna,f,9100))
    return out

PREVALENCE_RANGES={
 'weak':(0.03,0.11),
 'central':(0.015,0.085),
 'strong':(0.005,0.055),
}
ZERO_DONOR_RANGES={
 'weak':(0.40,0.72),
 'central':(0.60,0.86),
 'strong':(0.70,0.94),
}
PSEUDO_RANGES={
 'weak':(0.03,0.11),
 'central':(0.015,0.08),
 'strong':(0.005,0.06),
}

def evaluate_geometry_gate(score: dict) -> tuple[bool,list[str]]:
    kind=score['kind']; regime=score['regime']; failures=[]
    if regime=='extreme':
        if kind=='technical_twin' and score['prevalence'] != 0: failures.append('technical_R_nonzero')
        if kind!='technical_twin' and score['n_positive'] < 1: failures.append('no_positive_cells')
        return (not failures), failures
    if kind!='technical_twin':
        lo,hi=PREVALENCE_RANGES[regime]
        if not (lo <= score['prevalence'] <= hi): failures.append('prevalence_range')
        lo,hi=ZERO_DONOR_RANGES[regime]
        if not (lo <= score['zero_donor_fraction'] <= hi): failures.append('zero_donor_range')
        if score['source_prevalence_gap'] > 0.12: failures.append('source_prevalence_gap')
    if kind=='rna_recoverable':
        if score['rna_auc_full'] < 0.95: failures.append('rna_full_weak')
        if not (0.70 <= score['rna_auc_e20'] <= 0.95): failures.append('e20_outside_challenge_band')
        if score['teacher_auc_full'] < 0.99: failures.append('teacher_weak')
        if score['same_cell_rna_atac_corr'] < 0.25: failures.append('same_cell_coupling_weak')
        if score['rna_auc_e100'] - score['rna_auc_e20'] < 0.03: failures.append('evidence_ladder_flat')
        if score['rna_auc_d100'] - score['rna_auc_d25'] < 0.03: failures.append('depth_ladder_flat')
    elif kind=='teacher_private':
        if score['teacher_auc_full'] < 0.99: failures.append('teacher_weak')
        if score['teacher_auc_full'] - score['rna_auc_full'] < 0.10: failures.append('privileged_increment_small')
        if regime in {'weak','central'}:
            if not (0.50 <= score['rna_auc_full'] <= 0.85): failures.append('rna_not_partially_informative')
            if not (0.40 <= score['rna_auc_e20'] <= 0.75): failures.append('e20_not_underidentified')
            if score['rna_auc_e100'] - score['rna_auc_e20'] < 0.01: failures.append('evidence_ladder_flat')
        else:
            if not (0.45 <= score['rna_auc_full'] <= 0.90): failures.append('rna_not_partially_informative_sparse')
            if score['rna_auc_e20'] > 0.80: failures.append('e20_too_informative_sparse')
    elif kind=='separate_nucleus':
        if score['rna_auc_full'] < 0.95: failures.append('rna_full_weak')
        if score['rna_auc_e20'] < 0.70: failures.append('e20_too_weak')
        if abs(score['same_cell_rna_atac_corr']) > 0.30: failures.append('false_same_cell_coupling')
        if score['donor_rna_atac_corr'] < 0.20: failures.append('donor_coupling_weak')
    elif kind=='technical_twin':
        if score['prevalence'] != 0: failures.append('technical_R_nonzero')
        if not (0.70 <= score['pseudo_auc_rna'] <= 0.95): failures.append('pseudo_rarity_not_tempting')
        lo,hi=PSEUDO_RANGES[regime]
        pseudo=score.get('pseudo_prevalence', score.get('pseudo_fraction', np.nan))
        if np.isnan(pseudo):
            pass
        elif not (lo <= pseudo <= hi): failures.append('pseudo_prevalence_range')
    return (not failures), failures
