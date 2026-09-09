from __future__ import annotations
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from t0_discovery_confirmation_split_v1 import _digest,NAMESPACE,TAIL_MIN_CELLS,N_CONFIRM
from t0_metadata_coding_v1 import encode_binary_utf8
from t0_target_learner_v1 import nuisance_design

SCHEMA='JEPA_T0_DONOR_ROLE_AUTHORITY_V1'
REGISTRY='T0_DONOR_ROLE_REGISTRY.csv'; META='T0_DONOR_ROLE_METADATA.json'
MEMBERS={REGISTRY,META}

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def _hex64(x): return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)

def build_role_authority(outdir,support:pd.DataFrame,metadata:pd.DataFrame,input_authority_hashes:dict[str,str]) -> dict:
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('role output must be absent or empty')
    reqs={'source','donor_id','operator_index','cells'}
    if not reqs.issubset(support.columns): raise ValueError('support schema missing fields')
    s=support[(support.source=='SEA_AD')&(support.operator_index==31)][['donor_id','cells']].copy()
    if s.empty or s.donor_id.duplicated().any(): raise ValueError('SEA_AD op31 support invalid')
    s['donor_id']=s.donor_id.astype(str)
    raw_cells=pd.to_numeric(s.cells,errors='raise').to_numpy(dtype=np.float64)
    if not np.isfinite(raw_cells).all() or np.any(raw_cells<0) or np.any(np.floor(raw_cells)!=raw_cells): raise ValueError('cells must be finite nonnegative integers')
    s['cells']=raw_cells.astype(np.int64)
    req=['donor_id','AT8_available','age','sex','technical_complete']
    if list(metadata.columns)!=req: raise ValueError(f'metadata schema must be exactly {req}')
    m=metadata.copy(); m['donor_id']=m.donor_id.astype(str)
    if m.donor_id.duplicated().any() or (m.donor_id=='').any(): raise ValueError('metadata donor IDs invalid')
    if set(m.donor_id)!=set(s.donor_id): raise ValueError('support/metadata donor sets differ')
    if m.AT8_available.dtype!=bool or m.technical_complete.dtype!=bool: raise ValueError('availability flags must be boolean')
    age=pd.to_numeric(m.age,errors='coerce'); complete=m.AT8_available & m.technical_complete & np.isfinite(age) & m.sex.notna() & m.sex.astype(str).ne('')
    x=s.merge(m.loc[complete,['donor_id','age','sex']],on='donor_id',how='inner',validate='one_to_one')
    if len(x)<N_CONFIRM+18: raise ValueError('too few complete donors for 18 confirmation + >=18 discovery')
    sex_code,mapping=encode_binary_utf8(x.sex.tolist()); x['sex_code']=sex_code; x['split_hash']=x.donor_id.map(_digest); x['tail_measurable']=x.cells.ge(TAIL_MIN_CELLS)
    elig=x[x.tail_measurable].sort_values(['split_hash','donor_id'])
    if len(elig)<N_CONFIRM: raise ValueError('too few tail-measurable complete donors')
    confirm=set(elig.head(N_CONFIRM).donor_id); x['role']=x.donor_id.map(lambda d:'CONFIRMATION' if d in confirm else 'DISCOVERY')
    if int((x.role=='DISCOVERY').sum())<18: raise ValueError('fewer than 18 discovery donors')
    # Exact rank preflight for full discovery/confirmation and every discovery LOODO training set.
    for role in ['DISCOVERY','CONFIRMATION']:
        q=x[x.role.eq(role)].sort_values('donor_id',key=lambda z:z.map(lambda v:v.encode('utf-8')))
        nuisance_design(q.age.to_numpy(float),q.sex_code.to_numpy(float))
    disc=x[x.role.eq('DISCOVERY')].sort_values('donor_id',key=lambda z:z.map(lambda v:v.encode('utf-8'))).reset_index(drop=True)
    for i in range(len(disc)):
        q=disc.drop(index=i); nuisance_design(q.age.to_numpy(float),q.sex_code.to_numpy(float))
    for k,v in input_authority_hashes.items():
        if not isinstance(k,str) or not k or not _hex64(v): raise ValueError('input authority hashes must be named lowercase hex SHA256')
    reg=x[['donor_id','cells','split_hash','role','tail_measurable']].copy(); reg['namespace']=NAMESPACE
    reg=reg.sort_values(['role','split_hash','donor_id']).reset_index(drop=True)
    out.mkdir(parents=True,exist_ok=True); reg.to_csv(out/REGISTRY,index=False,lineterminator='\n')
    meta={'schema':SCHEMA,'finalized':True,'namespace':NAMESPACE,'tail_min_cells':TAIL_MIN_CELLS,'confirmation_donors':N_CONFIRM,'discovery_donors':int((reg.role=='DISCOVERY').sum()),'complete_donors':len(reg),'sex_utf8_mapping':mapping,'input_authority_hashes':dict(sorted(input_authority_hashes.items())),'rank_checks':'discovery + confirmation + every discovery LOODO full rank'}
    (out/META).write_text(json.dumps(meta,sort_keys=True,separators=(',',':'))+'\n')
    with (out/'T0_DONOR_ROLE_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['filename','bytes','sha256'])
        for name in sorted(MEMBERS,key=lambda x:x.encode()):
            p=out/name; w.writerow([name,p.stat().st_size,sha256_file(p)])
    root=sha256_file(out/'T0_DONOR_ROLE_MANIFEST.csv'); (out/'T0_DONOR_ROLE_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n')
    return {'package_root_sha256':root,'registry':reg,'metadata':meta}

def load_role_authority(outdir) -> dict:
    out=Path(outdir); expected=MEMBERS|{'T0_DONOR_ROLE_MANIFEST.csv','T0_DONOR_ROLE_PACKAGE_ROOT_SHA256.txt'}
    if not out.is_dir(): raise ValueError('role package directory missing')
    got={p.name for p in out.iterdir() if p.is_file()}
    if got!=expected or any(p.is_dir() for p in out.iterdir()): raise ValueError('role package member set mismatch')
    root_text=(out/'T0_DONOR_ROLE_PACKAGE_ROOT_SHA256.txt').read_text(encoding='utf-8')
    if not root_text.endswith('\n') or root_text.count('\n')!=1: raise ValueError('role root-file format mismatch')
    root=root_text[:-1]
    if not _hex64(root) or sha256_file(out/'T0_DONOR_ROLE_MANIFEST.csv')!=root: raise ValueError('role package root mismatch')
    man=pd.read_csv(out/'T0_DONOR_ROLE_MANIFEST.csv',dtype={'filename':str,'bytes':str,'sha256':str})
    if list(man.columns)!=['filename','bytes','sha256'] or len(man)!=len(MEMBERS) or set(man.filename)!=MEMBERS or man.filename.duplicated().any(): raise ValueError('role manifest mismatch')
    for r in man.itertuples(index=False):
        if not isinstance(r.bytes,str) or not r.bytes.isdigit() or str(int(r.bytes))!=r.bytes or not _hex64(r.sha256): raise ValueError('role manifest row invalid')
        p=out/r.filename
        if p.stat().st_size!=int(r.bytes) or sha256_file(p)!=r.sha256: raise ValueError('role member mismatch')
    meta=json.loads((out/META).read_text(encoding='utf-8')); reg=pd.read_csv(out/REGISTRY,dtype={'donor_id':str,'cells':str,'split_hash':str,'role':str,'tail_measurable':str,'namespace':str})
    expected_meta_keys={'schema','finalized','namespace','tail_min_cells','confirmation_donors','discovery_donors','complete_donors','sex_utf8_mapping','input_authority_hashes','rank_checks'}
    if set(meta)!=expected_meta_keys or meta.get('schema')!=SCHEMA or meta.get('finalized') is not True or meta.get('namespace')!=NAMESPACE or meta.get('tail_min_cells')!=TAIL_MIN_CELLS or meta.get('confirmation_donors')!=N_CONFIRM: raise ValueError('role metadata mismatch')
    if not isinstance(meta.get('sex_utf8_mapping'),dict) or sorted(meta['sex_utf8_mapping'].values())!=[0,1] or len(meta['sex_utf8_mapping'])!=2: raise ValueError('role sex mapping invalid')
    if not isinstance(meta.get('input_authority_hashes'),dict) or any(not isinstance(k,str) or not k or not _hex64(v) for k,v in meta['input_authority_hashes'].items()): raise ValueError('role input hashes invalid')
    cols=['donor_id','cells','split_hash','role','tail_measurable','namespace']
    if list(reg.columns)!=cols or reg.donor_id.duplicated().any() or reg.donor_id.isna().any() or reg.donor_id.eq('').any(): raise ValueError('role registry invalid')
    try:
        cells=np.asarray([int(x) if x.isdigit() else (_ for _ in ()).throw(ValueError()) for x in reg.cells],dtype=np.int64)
    except Exception as e:
        raise ValueError('role cells must be canonical nonnegative integers') from e
    if np.any(cells<0): raise ValueError('role cells negative')
    reg['cells']=cells
    if not reg.split_hash.map(_hex64).all(): raise ValueError('role split hashes invalid')
    if not reg.role.isin(['DISCOVERY','CONFIRMATION']).all() or set(reg.role)!={'DISCOVERY','CONFIRMATION'}: raise ValueError('role labels invalid')
    if not reg.tail_measurable.isin(['True','False']).all(): raise ValueError('role tail-measurable encoding invalid')
    reg['tail_measurable']=reg.tail_measurable.eq('True')
    if not reg.namespace.eq(NAMESPACE).all() or not reg.split_hash.eq(reg.donor_id.map(_digest)).all(): raise ValueError('role deterministic hashes mismatch')
    if not reg.tail_measurable.eq(reg.cells.ge(TAIL_MIN_CELLS)).all(): raise ValueError('role tail support mismatch')
    # Recompute the frozen assignment from registry contents: confirmation is exactly the first 18 tail-measurable donors by split_hash, donor_id.
    elig=reg.loc[reg.tail_measurable].sort_values(['split_hash','donor_id'])
    if len(elig)<N_CONFIRM: raise ValueError('role too few eligible confirmation donors')
    expected_confirm=set(elig.head(N_CONFIRM).donor_id)
    expected_role=reg.donor_id.map(lambda d:'CONFIRMATION' if d in expected_confirm else 'DISCOVERY')
    if not reg.role.eq(expected_role).all(): raise ValueError('role assignment does not match frozen deterministic rule')
    if int((reg.role=='CONFIRMATION').sum())!=N_CONFIRM or int((reg.role=='DISCOVERY').sum())<18: raise ValueError('role counts invalid')
    canonical=reg.sort_values(['role','split_hash','donor_id']).reset_index(drop=True)
    if not reg.reset_index(drop=True).equals(canonical): raise ValueError('role registry row order not canonical')
    if meta.get('discovery_donors')!=int((reg.role=='DISCOVERY').sum()) or meta.get('complete_donors')!=len(reg) or meta.get('rank_checks')!='discovery + confirmation + every discovery LOODO full rank': raise ValueError('role metadata counts/rank declaration mismatch')
    return {'package_root_sha256':root,'registry':reg,'metadata':meta,'discovery_donors':sorted(reg.loc[reg.role.eq('DISCOVERY'),'donor_id'],key=lambda x:x.encode()),'confirmation_donors':sorted(reg.loc[reg.role.eq('CONFIRMATION'),'donor_id'],key=lambda x:x.encode())}


def verify_role_authority_against_inputs(outdir, support:pd.DataFrame, metadata:pd.DataFrame, input_authority_hashes:dict[str,str]) -> dict:
    """Independently rebuild a frozen donor-role package from its metadata-only source inputs.

    Conclusion-bearing use requires this recomputation before pathology values are opened.
    The stored package is accepted only when every rebuilt member and package root is byte-identical.
    """
    import tempfile
    frozen=load_role_authority(outdir)
    with tempfile.TemporaryDirectory(prefix='t0-role-recompute-') as td:
        rebuilt=build_role_authority(Path(td)/'role',support,metadata,input_authority_hashes)
        if rebuilt['package_root_sha256']!=frozen['package_root_sha256']:
            raise ValueError('frozen donor-role package does not match canonical source-input recomputation')
        src=Path(td)/'role'; dst=Path(outdir)
        expected=MEMBERS|{'T0_DONOR_ROLE_MANIFEST.csv','T0_DONOR_ROLE_PACKAGE_ROOT_SHA256.txt'}
        for name in expected:
            if (src/name).read_bytes()!=(dst/name).read_bytes():
                raise ValueError(f'frozen donor-role member mismatch canonical recomputation: {name}')
    return frozen
