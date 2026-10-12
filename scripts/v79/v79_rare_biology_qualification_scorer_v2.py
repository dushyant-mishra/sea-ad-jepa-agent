from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .v79_rare_biology_generator_v1 import SIGNS
from .v79_rare_biology_production_v1 import _sha256
from .v79_rare_biology_qualification_v2 import evidence_score, depth_score, evaluate_geometry_gate


def _auc(y, score):
    y=np.asarray(y,dtype=int); score=np.asarray(score,float); n1=int(y.sum()); n0=len(y)-n1
    if n1==0 or n0==0: return float('nan')
    ranks=pd.Series(score).rank(method='average').to_numpy()
    return float((ranks[y==1].sum()-n1*(n1+1)/2)/(n1*n0))


def _score_one(fit, truth, kind, regime):
    y=truth['R'].astype(int); pseudo=truth['pseudo_rare'].astype(int)
    rna=(fit['rna']*SIGNS[None,:]).mean(axis=1); atac=fit['atac'].mean(axis=1)
    donor_code=fit['donor_code'].astype(int); source_code=fit['source_code'].astype(int)
    by_donor=pd.DataFrame({'donor':donor_code,'rna':rna,'atac':atac}).groupby('donor').mean()
    source_prev=pd.DataFrame({'source':source_code,'R':y}).groupby('source')['R'].mean()
    donor_first=pd.DataFrame({'donor':donor_code,'active':truth['donor_active'].astype(int)}).drop_duplicates('donor')
    row={
      'kind':kind,'regime':regime,'n_positive':int(y.sum()),'prevalence':float(y.mean()),'pseudo_prevalence':float(pseudo.mean()),
      'zero_donor_fraction':float((donor_first['active']==0).mean()),
      'source_prevalence_gap':float(source_prev.max()-source_prev.min()),
      'rna_auc_full':_auc(y,rna),'teacher_auc_full':_auc(y,rna+atac),'pseudo_auc_rna':_auc(pseudo,rna),
      'same_cell_rna_atac_corr':float(np.corrcoef(rna,atac)[0,1]) if np.std(rna)>0 and np.std(atac)>0 else float('nan'),
      'donor_rna_atac_corr':float(by_donor['rna'].corr(by_donor['atac'])) if by_donor['atac'].std()>0 else float('nan'),
    }
    for f in (0.2,0.4,0.6,0.8,1.0): row[f'rna_auc_e{int(f*100)}']=_auc(y,evidence_score(fit['rna'],f,8100))
    for f in (0.25,0.5,0.75,1.0): row[f'rna_auc_d{int(f*100)}']=_auc(y,depth_score(fit['rna'],f,9100))
    return row


def score_package(root_dir: str|Path) -> dict:
    root=Path(root_dir)
    receipt=json.loads((root/'V79_RARE_QUALIFICATION_V2_REALIZATION_RECEIPT.json').read_text())
    map_path=root/'controller_truth'/'CHALLENGE_MAP_V2.json'
    if _sha256(map_path) != receipt['controller_map_sha256']: raise ValueError('controller map hash mismatch')
    cmap=json.loads(map_path.read_text())
    by_id={x['challenge_id']:x for x in cmap['challenges']}
    rows=[]; gating_failures=0; structural_failures=0
    for e in receipt['challenges']:
        fp=root/e['fit_relpath']; tp=root/e['truth_relpath']
        if _sha256(fp)!=e['fit_sha256']: raise ValueError(f"fit hash mismatch {e['challenge_id']}")
        if _sha256(tp)!=e['truth_sha256']: raise ValueError(f"truth hash mismatch {e['challenge_id']}")
        m=by_id[e['challenge_id']]
        with np.load(fp,allow_pickle=False) as fit, np.load(tp,allow_pickle=False) as truth:
            row=_score_one(fit,truth,m['kind'],m['regime'])
        ok,why=evaluate_geometry_gate(row)
        row['challenge_id']=e['challenge_id']; row['gate_failures']=';'.join(why)
        if m['regime']=='extreme':
            row['gate_status']='REPORT_ONLY_STRUCTURAL_PASS' if ok else 'REPORT_ONLY_STRUCTURAL_FAIL'
            if not ok: structural_failures += 1
        else:
            row['gate_status']='PASS' if ok else 'FAIL'
            if not ok: gating_failures += 1
        rows.append(row)
    terminal='QUALIFICATION_GEOMETRY_PASS' if gating_failures==0 and structural_failures==0 else 'QUALIFICATION_GEOMETRY_FAIL'
    return {
      'schema':'V79_RARE_QUALIFICATION_V2_CONTROLLER_SCORE',
      'terminal':terminal,
      'directory_digest_sha256':receipt['directory_digest_sha256'],
      'gating_challenge_count':sum(r['regime']!='extreme' for r in rows),
      'extreme_report_only_count':sum(r['regime']=='extreme' for r in rows),
      'gating_failures':gating_failures,'structural_failures':structural_failures,'rows':rows,
    }
