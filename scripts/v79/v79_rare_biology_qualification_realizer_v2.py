from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from pathlib import Path
import numpy as np
from .v79_rare_biology_qualification_v2 import ChallengeConfig, build_challenge, KINDS
from .v79_rare_biology_production_v1 import _write_npz_deterministic, _sha256, _code_entities

@dataclass(frozen=True)
class QualificationRealizationConfig:
    seed_root: int
    n_donors: int = 66
    cells_per_donor: int = 20
    kinds: tuple[str, ...] = KINDS
    regimes: tuple[str, ...] = ('weak','central','strong','extreme')


def _derive_seed(root:int, challenge_id:str)->int:
    b=f'V79_RARE_QUALIFICATION_V2|{root}|{challenge_id}'.encode()
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big') % (2**32)


def realize_qualification(cfg:QualificationRealizationConfig,out_dir:str|Path)->dict:
    out=Path(out_dir)
    if out.exists() and any(out.iterdir()): raise FileExistsError(f'qualification output directory must be empty: {out}')
    (out/'fit_view').mkdir(parents=True,exist_ok=True); (out/'controller_truth').mkdir(parents=True,exist_ok=True)
    entries=[]; idx=0
    for kind in cfg.kinds:
        for regime in cfg.regimes:
            cid=f'RQ{idx:03d}'; idx+=1; seed=_derive_seed(cfg.seed_root,cid)
            w=build_challenge(ChallengeConfig(seed=seed,kind=kind,regime=regime,n_donors=cfg.n_donors,cells_per_donor=cfg.cells_per_donor))
            sc,dc,rc,ac=_code_entities(w.cells)
            fit_rel=f'fit_view/{cid}.npz'; truth_rel=f'controller_truth/{cid}.npz'
            _write_npz_deterministic(out/fit_rel,{
                'rna':w.rna.astype(np.float32),'atac':w.atac.astype(np.float32),
                'source_code':sc,'donor_code':dc,'rna_entity_code':rc,'atac_entity_code':ac,
            })
            _write_npz_deterministic(out/truth_rel,{
                'R':w.cells['R'].to_numpy(dtype=np.int8),
                'pseudo_rare':w.cells['pseudo_rare'].to_numpy(dtype=np.int8),
                'donor_active':w.cells['donor_active'].to_numpy(dtype=np.int8),
                'donor_prevalence':w.cells['donor_prevalence'].to_numpy(dtype=np.float32),
                'kind_code':np.full(len(w.cells),cfg.kinds.index(kind),dtype=np.int8),
                'regime_code':np.full(len(w.cells),cfg.regimes.index(regime),dtype=np.int8),
            })
            entries.append({'challenge_id':cid,'kind':kind,'regime':regime,'seed':seed,
                'fit_relpath':fit_rel,'truth_relpath':truth_rel,'fit_sha256':_sha256(out/fit_rel),'truth_sha256':_sha256(out/truth_rel),
                'n_cells':int(len(w.cells)),'n_positive':int(w.cells['R'].sum()),'n_pseudo_rare':int(w.cells['pseudo_rare'].sum())})
    mapping={'schema':'V79_RARE_QUALIFICATION_V2_CONTROLLER_MAP','kind_code':{str(i):k for i,k in enumerate(cfg.kinds)},
             'regime_code':{str(i):r for i,r in enumerate(cfg.regimes)},
             'challenges':[{k:e[k] for k in ('challenge_id','kind','regime','seed')} for e in entries]}
    mp=out/'controller_truth'/'CHALLENGE_MAP_V2.json'; mp.write_text(json.dumps(mapping,sort_keys=True,indent=2)+'\n')
    files=[]
    for p in sorted(x for x in out.rglob('*') if x.is_file()): files.append((p.relative_to(out).as_posix(),_sha256(p)))
    digest=hashlib.sha256('\n'.join(f'{r},{h}' for r,h in files).encode()).hexdigest()
    receipt={'schema':'V79_RARE_QUALIFICATION_V2_REALIZATION_RECEIPT','status':'REALIZED_ONCE__BLINDED__UNSCORED',
             'seed_root':cfg.seed_root,'n_donors':cfg.n_donors,'cells_per_donor':cfg.cells_per_donor,
             'kinds':list(cfg.kinds),'regimes':list(cfg.regimes),'challenge_count':len(entries),'challenges':entries,
             'controller_map_sha256':_sha256(mp),'directory_digest_sha256':digest}
    (out/'V79_RARE_QUALIFICATION_V2_REALIZATION_RECEIPT.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return receipt
