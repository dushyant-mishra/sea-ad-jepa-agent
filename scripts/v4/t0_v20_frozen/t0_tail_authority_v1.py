from __future__ import annotations
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_target_serializer_v2 import load_target_v2,sha256_file
from t0_discovery_fit_v2 import verify_target_v2_against_raw
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership
from t0_stable_cell_key_v1 import parse_stable_key_exact
from t0_weighted_quantile_v1 import equal_donor_cell_quantile
from t0_package_integrity_v1 import verify_flat_package,is_hex64

SCHEMA='JEPA_T0_RARE_TAIL_EXTENSION_V1'
TAIL_Q=.95
TAIL_MIN_CELLS=80
MIN_THRESHOLD_DONORS=10
MEMBERS={'T0_TAIL_THRESHOLD_F64LE.bin','T0_TAIL_METADATA.json','T0_TAIL_DISCOVERY_DONORS.csv'}


def _row_nonzero(counts,i):
    if sp is not None and sp.issparse(counts):
        row=counts.getrow(i); order=np.argsort(row.indices,kind='mergesort')
        return row.indices[order],np.asarray(row.data[order],dtype=np.float64)
    a=np.asarray(counts[i]); idx=np.flatnonzero(a); return idx,np.asarray(a[idx],dtype=np.float64)


def score_raw_counts(raw_counts,source_library,fit) -> np.ndarray:
    n,g=raw_counts.shape; lib=np.asarray(source_library,dtype=np.float64)
    if lib.shape!=(n,) or not np.isfinite(lib).all() or np.any(lib<=0): raise ValueError('invalid source_library')
    beta=np.asarray(fit['beta'],dtype=np.float64); mu=np.asarray(fit['mu'],dtype=np.float64); sigma=np.asarray(fit['sigma'],dtype=np.float64)
    if beta.shape!=(g,) or mu.shape!=(g,) or sigma.shape!=(g,) or np.any(sigma<=0): raise ValueError('target feature mismatch')
    w=beta/sigma; offset=float(np.dot(mu,w)); out=np.empty(n,dtype=np.float64)
    for i in range(n):
        idx,data=_row_nonzero(raw_counts,i)
        if not np.isfinite(data).all() or np.any(data<0) or np.any(np.floor(data)!=data): raise ValueError('invalid raw counts')
        if float(np.sum(data,dtype=np.float64))>lib[i]+1e-9: raise ValueError('scoring counts exceed source_library')
        norm=np.log1p(10000.0*data/lib[i])
        out[i]=float(np.dot(norm,w[idx])-offset)
    if not np.isfinite(out).all(): raise ValueError('nonfinite cell score')
    return out


def centered_scores_by_donor(scores,donor_id,stable_key) -> dict[str,np.ndarray]:
    s=np.asarray(scores,dtype=np.float64); d=np.asarray([str(x) for x in donor_id]); k=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64)
    if s.ndim!=1 or len(s)!=len(d) or len(s)!=len(k) or not np.isfinite(s).all(): raise ValueError('invalid scores/donors')
    out={}
    for donor in sorted(set(d),key=lambda x:x.encode('utf-8')):
        ix=np.flatnonzero(d==donor); ix=ix[np.argsort(k[ix],kind='mergesort')]
        vals=s[ix]; out[donor]=vals-float(np.sum(vals,dtype=np.float64)/len(vals))
    return out


def _compute_tail_threshold_from_loaded_target(target,*,raw_counts,donor_id,stable_key,source_library) -> dict:
    expected=list(map(str,target['fit']['canonical_donor_order'])); observed=sorted(set(map(str,donor_id)),key=lambda x:x.encode('utf-8'))
    if observed!=expected: raise ValueError('tail discovery donor universe must equal frozen target discovery donors')
    scores=score_raw_counts(raw_counts,source_library,target['fit']); centered=centered_scores_by_donor(scores,donor_id,stable_key)
    eligible=[d for d in expected if len(centered[d])>=TAIL_MIN_CELLS]
    if len(eligible)<MIN_THRESHOLD_DONORS: raise ValueError('too few tail-measurable discovery donors')
    threshold=equal_donor_cell_quantile([centered[d] for d in eligible],TAIL_Q)
    counts={d:len(centered[d]) for d in eligible}
    return {'threshold':float(threshold),'eligible_donors':eligible,'eligible_counts':counts,'target_package_root_sha256':target['package_root_sha256'],'target_discovery_provenance_root':target['provenance']['root_sha256']}


def compute_tail_threshold(target_dir,*,raw_counts,feature_ids,matrix_id,local_row,cell_id,donor_id,stable_key,source_library,donor_metadata,feature_split_csv,membership_csv) -> dict:
    kw=dict(raw_counts=raw_counts,feature_ids=feature_ids,matrix_id=matrix_id,local_row=local_row,cell_id=cell_id,donor_id=donor_id,stable_key=stable_key,source_library=source_library,donor_metadata=donor_metadata,feature_split_csv=feature_split_csv,membership_csv=membership_csv)
    verify_target_v2_against_raw(target_dir,**kw)
    target=load_target_v2(target_dir,feature_split_csv)
    return _compute_tail_threshold_from_loaded_target(target,raw_counts=raw_counts,donor_id=donor_id,stable_key=stable_key,source_library=source_library)


def freeze_tail_authority(outdir,target_dir,**kwargs) -> dict:
    r=compute_tail_threshold(target_dir,**kwargs); out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('tail output directory must be absent or empty')
    out.mkdir(parents=True,exist_ok=True)
    (out/'T0_TAIL_THRESHOLD_F64LE.bin').write_bytes(np.asarray([r['threshold']],dtype='<f8').tobytes())
    pd.DataFrame({'donor_id':r['eligible_donors'],'cells':[r['eligible_counts'][d] for d in r['eligible_donors']]}).to_csv(out/'T0_TAIL_DISCOVERY_DONORS.csv',index=False,lineterminator='\n')
    meta={'schema':SCHEMA,'q':TAIL_Q,'comparison':'centered_cell_score > frozen_threshold','tail_min_cells':TAIL_MIN_CELLS,'min_threshold_donors':MIN_THRESHOLD_DONORS,'target_package_root_sha256':r['target_package_root_sha256'],'target_discovery_provenance_root':r['target_discovery_provenance_root']}
    (out/'T0_TAIL_METADATA.json').write_text(json.dumps(meta,sort_keys=True,separators=(',',':'))+'\n')
    with (out/'T0_TAIL_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['filename','bytes','sha256'])
        for name in sorted(MEMBERS,key=lambda x:x.encode()):
            p=out/name; w.writerow([name,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/'T0_TAIL_MANIFEST.csv'); (out/'T0_TAIL_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n')
    return {'schema':SCHEMA,'package_root_sha256':root,**r}


def load_tail_authority(outdir,target_package_root_sha256=None) -> dict:
    out=Path(outdir); root=verify_flat_package(out,MEMBERS,'T0_TAIL_MANIFEST.csv','T0_TAIL_PACKAGE_ROOT_SHA256.txt',label='tail package')
    meta=json.loads((out/'T0_TAIL_METADATA.json').read_text(encoding='utf-8'))
    meta_keys={'schema','q','comparison','tail_min_cells','min_threshold_donors','target_package_root_sha256','target_discovery_provenance_root'}
    if set(meta)!=meta_keys or meta.get('schema')!=SCHEMA or meta.get('q')!=TAIL_Q or meta.get('comparison')!='centered_cell_score > frozen_threshold' or meta.get('tail_min_cells')!=TAIL_MIN_CELLS or meta.get('min_threshold_donors')!=MIN_THRESHOLD_DONORS or not is_hex64(meta.get('target_package_root_sha256')) or not is_hex64(meta.get('target_discovery_provenance_root')): raise ValueError('tail metadata mismatch')
    th=np.fromfile(out/'T0_TAIL_THRESHOLD_F64LE.bin',dtype='<f8')
    if th.shape!=(1,) or not np.isfinite(th[0]): raise ValueError('invalid tail threshold')
    donors=pd.read_csv(out/'T0_TAIL_DISCOVERY_DONORS.csv',dtype={'donor_id':str,'cells':str})
    if list(donors.columns)!=['donor_id','cells'] or len(donors)<MIN_THRESHOLD_DONORS or donors.donor_id.duplicated().any() or donors.donor_id.isna().any() or donors.donor_id.eq('').any(): raise ValueError('invalid tail donor support')
    try: cells=np.asarray([int(x) if isinstance(x,str) and x.isdigit() else (_ for _ in ()).throw(ValueError()) for x in donors.cells],dtype=np.int64)
    except Exception as e: raise ValueError('tail donor cells must be canonical nonnegative integers') from e
    donors['cells']=cells
    if (donors.cells<TAIL_MIN_CELLS).any(): raise ValueError('invalid tail donor support')
    expected_order=sorted(donors.donor_id.astype(str),key=lambda x:x.encode('utf-8'))
    if donors.donor_id.astype(str).tolist()!=expected_order: raise ValueError('tail donor order not canonical')
    if target_package_root_sha256 is not None and meta['target_package_root_sha256']!=str(target_package_root_sha256):
        raise ValueError('tail target-root linkage mismatch')
    return {'package_root_sha256':root,'threshold':float(th[0]),'metadata':meta,'donors':donors}

def _compare_tail_recomputation(frozen,rec) -> dict:
    if frozen['threshold']!=rec['threshold']: raise ValueError('frozen tail threshold mismatch canonical recomputation')
    fd=frozen['donors']; expected=pd.DataFrame({'donor_id':rec['eligible_donors'],'cells':[rec['eligible_counts'][d] for d in rec['eligible_donors']]})
    if not fd.equals(expected): raise ValueError('frozen tail donor support mismatch canonical recomputation')
    if frozen['metadata']['target_discovery_provenance_root']!=rec['target_discovery_provenance_root']: raise ValueError('tail provenance linkage mismatch')
    return {'verified':True,'package_root_sha256':frozen['package_root_sha256'],'threshold':frozen['threshold']}


def verify_tail_authority_against_loaded_target(tail_dir,target,*,raw_counts,donor_id,stable_key,source_library) -> dict:
    """Use only after the caller has independently verified target against these raw discovery inputs."""
    frozen=load_tail_authority(tail_dir,target['package_root_sha256'])
    rec=_compute_tail_threshold_from_loaded_target(target,raw_counts=raw_counts,donor_id=donor_id,stable_key=stable_key,source_library=source_library)
    return _compare_tail_recomputation(frozen,rec)


def verify_tail_authority_against_raw(tail_dir,target_dir,**kwargs) -> dict:
    verify_target_v2_against_raw(target_dir,**kwargs)
    target=load_target_v2(target_dir,kwargs['feature_split_csv'])
    return verify_tail_authority_against_loaded_target(tail_dir,target,raw_counts=kwargs['raw_counts'],donor_id=kwargs['donor_id'],stable_key=kwargs['stable_key'],source_library=kwargs['source_library'])
