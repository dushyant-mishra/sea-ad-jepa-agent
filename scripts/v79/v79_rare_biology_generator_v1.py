from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

TARGETS = [
    'AIF1','APOE','B2M','BSG','C1QB','CD74','CTSB','FCER1G','GPX4',
    'HLA-DPA1','LAPTM5','NFKBIA','NPC2','PRDX1','TXNIP'
]
SIGNS = np.array([1,1,1,1,1,1,1,1,-1,1,1,1,1,1,1], dtype=float)
SOURCES = ('HVS','NPH52','SEA_AD')
# Detection fractions measured in the authenticated 665-cell TRAIN microglia subset.
VISIBILITY = {
    'HVS': np.array([.984375,0,.234375,.023438,.046875,.109375,.015625,.039062,0,0,0,.226562,.015625,0,0]),
    'NPH52': np.array([.427632,.549342,.832237,.125,.723684,.927632,.753289,.394737,.276316,.588816,.615132,.223684,.263158,.101974,.368421]),
    'SEA_AD': np.array([.167382,.137339,.017167,.004292,.094421,.004292,.012876,0,.012876,0,.030043,.004292,.004292,.171674,0]),
}
# Empirical donor-active fractions and positive-donor prevalence beta moments from
# the source-specific detection-residual STAT1 TRAIN calibration.
REGIMES = {
    'weak': dict(active_prob=28/66, alpha=1.2670743912, beta=6.7275855147, tail_fraction=0.0661654135),
    'central': dict(active_prob=17/66, alpha=1.2449148260, beta=5.5522387114, tail_fraction=0.0406015038),
    'strong': dict(active_prob=11/66, alpha=2.9310863813, beta=16.3274095698, tail_fraction=0.0270676692),
    'extreme': dict(active_prob=7/66, alpha=2.4078043575, beta=13.5442026597, tail_fraction=0.0165413534),
}
# Relative source residual SDs after detected-gene residualization; HVS normalized to 1.
SOURCE_NOISE = {'HVS':1.0, 'NPH52':0.4496662782/0.1837290780, 'SEA_AD':0.2218350492/0.1837290780}

@dataclass(frozen=True)
class RareWorldConfig:
    seed: int
    n_donors: int = 66
    cells_per_donor: int = 20
    regime: str = 'central'
    world: str = 'same_nucleus'  # same_nucleus | separate_nucleus | technical_twin | rna_only
    rna_effect: float = 1.0
    atac_effect: float = 1.35
    base_noise: float = 0.35

@dataclass
class RareWorld:
    cells: pd.DataFrame
    rna: np.ndarray
    atac: np.ndarray
    genes: tuple[str, ...] = tuple(TARGETS)


def _donor_latent(rng: np.random.Generator, cfg: RareWorldConfig):
    reg = REGIMES[cfg.regime]
    active = rng.binomial(1, reg['active_prob'], cfg.n_donors)
    prev = np.zeros(cfg.n_donors, dtype=float)
    n = int(active.sum())
    if n:
        p = rng.beta(reg['alpha'], reg['beta'], n)
        prev[active == 1] = np.clip(p, 0.01, 0.50)
    return active, prev


def generate_world(cfg: RareWorldConfig) -> RareWorld:
    if cfg.regime not in REGIMES:
        raise ValueError(f'unknown regime {cfg.regime}')
    if cfg.world not in {'same_nucleus','separate_nucleus','technical_twin','rna_only'}:
        raise ValueError(f'unknown world {cfg.world}')
    rng = np.random.default_rng(cfg.seed)
    active, prev = _donor_latent(rng, cfg)
    # Assign source after latent biology so source cannot cause donor activation.
    src = np.array([SOURCES[i % 3] for i in rng.permutation(cfg.n_donors)])
    rows=[]
    rna=[]
    atac=[]
    for d in range(cfg.n_donors):
        donor_id=f'D{d:04d}'
        if cfg.world == 'technical_twin':
            R = np.zeros(cfg.cells_per_donor, dtype=int)
            pseudo = rng.binomial(1, REGIMES[cfg.regime]['tail_fraction'], cfg.cells_per_donor)
        else:
            R = rng.binomial(1, prev[d], cfg.cells_per_donor)
            pseudo = np.zeros(cfg.cells_per_donor, dtype=int)
        source=src[d]
        vis=VISIBILITY[source]
        noise_scale=cfg.base_noise*SOURCE_NOISE[source]
        # Shared latent program plus gene-specific noise; observation visibility is source-specific.
        shared = R[:,None] * cfg.rna_effect * SIGNS[None,:]
        x = shared + rng.normal(0, noise_scale, (cfg.cells_per_donor, len(TARGETS)))
        observed = rng.binomial(1, np.clip(vis + 0.25*R[:,None], 0, 1))
        x = x * observed
        if cfg.world == 'technical_twin':
            # Pseudo-rarity is observation-driven, with no biological R.
            x += pseudo[:,None] * rng.normal(0.8, 0.15, (cfg.cells_per_donor, len(TARGETS))) * observed
        if cfg.world == 'rna_only':
            y=np.zeros_like(x)
        elif cfg.world == 'same_nucleus':
            y = R[:,None] * cfg.atac_effect * np.abs(SIGNS)[None,:] + rng.normal(0, cfg.base_noise, x.shape)
        elif cfg.world == 'separate_nucleus':
            # Independent nuclei share donor-level latent prevalence but not cell identity.
            R_atac = rng.binomial(1, prev[d], cfg.cells_per_donor)
            y = R_atac[:,None] * cfg.atac_effect * np.abs(SIGNS)[None,:] + rng.normal(0, cfg.base_noise, x.shape)
        else:  # technical twin
            y = pseudo[:,None] * rng.normal(0.8, 0.15, x.shape) + rng.normal(0, cfg.base_noise, x.shape)
        for i in range(cfg.cells_per_donor):
            rows.append({
                'donor_id': donor_id,
                'source': source,
                'donor_active': int(active[d]),
                'donor_prevalence': float(prev[d]),
                'R': int(R[i]),
                'pseudo_rare': int(pseudo[i]),
                'rna_entity_id': f'{donor_id}:RNA:{i:04d}',
                'atac_entity_id': (f'{donor_id}:RNA:{i:04d}' if cfg.world=='same_nucleus' else f'{donor_id}:ATAC:{i:04d}'),
            })
        rna.append(x); atac.append(y)
    return RareWorld(pd.DataFrame(rows), np.vstack(rna), np.vstack(atac))
