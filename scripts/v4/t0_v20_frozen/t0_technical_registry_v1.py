from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
from t0_package_integrity_v1 import verify_flat_package,is_hex64
SCHEMA='JEPA_T0_TECHNICAL_SENSITIVITY_REGISTRY_V1'
MEMBER='T0_TECHNICAL_SENSITIVITY_REGISTRY.json'

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def _hex64(x): return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)

def build_technical_registry(outdir,blocks:list[dict],source_authority_hashes:dict[str,str],audit_note:str):
    if not isinstance(blocks,list): raise ValueError('blocks must be list')
    seen=set(); norm=[]
    for b in blocks:
        if not isinstance(b,dict) or set(b)!={'name','columns'}: raise ValueError('each block requires name/columns only')
        name=b['name']; cols=b['columns']
        if not isinstance(name,str) or not name or name in seen or not isinstance(cols,list) or not cols or any(not isinstance(c,str) or not c for c in cols): raise ValueError('invalid technical block')
        if len(set(cols))!=len(cols): raise ValueError('duplicate column within technical block')
        seen.add(name); norm.append({'name':name,'columns':cols})
    for k,v in source_authority_hashes.items():
        if not isinstance(k,str) or not k or not _hex64(v): raise ValueError('invalid source authority hash')
    if not isinstance(audit_note,str) or not audit_note: raise ValueError('audit_note required')
    obj={'schema':SCHEMA,'audit_complete':True,'mandatory_direct_observation_block':['Q_DEPTH','Q_DETECT'],'additional_blocks':norm,'source_authority_hashes':dict(sorted(source_authority_hashes.items())),'audit_note':audit_note}
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('technical registry output must be absent or empty')
    out.mkdir(parents=True,exist_ok=True); (out/MEMBER).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
    with (out/'T0_TECHNICAL_REGISTRY_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); p=out/MEMBER; w.writerow(['filename','bytes','sha256']); w.writerow([MEMBER,p.stat().st_size,sha(p)])
    root=sha(out/'T0_TECHNICAL_REGISTRY_MANIFEST.csv'); (out/'T0_TECHNICAL_REGISTRY_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n'); return {'package_root_sha256':root,'registry':obj}

def load_technical_registry(outdir):
    out=Path(outdir); root=verify_flat_package(out,{MEMBER},'T0_TECHNICAL_REGISTRY_MANIFEST.csv','T0_TECHNICAL_REGISTRY_PACKAGE_ROOT_SHA256.txt',label='technical-registry package')
    obj=json.loads((out/MEMBER).read_text(encoding='utf-8'))
    keys={'schema','audit_complete','mandatory_direct_observation_block','additional_blocks','source_authority_hashes','audit_note'}
    if set(obj)!=keys or obj.get('schema')!=SCHEMA or obj.get('audit_complete') is not True or obj.get('mandatory_direct_observation_block')!=['Q_DEPTH','Q_DETECT'] or not isinstance(obj.get('audit_note'),str) or not obj['audit_note']:
        raise ValueError('technical registry metadata mismatch')
    names=set()
    blocks=obj.get('additional_blocks')
    if not isinstance(blocks,list): raise ValueError('technical registry blocks invalid')
    for b in blocks:
        if not isinstance(b,dict) or set(b)!={'name','columns'} or not isinstance(b['name'],str) or not b['name'] or b['name'] in names or not isinstance(b['columns'],list) or not b['columns'] or any(not isinstance(c,str) or not c for c in b['columns']) or len(set(b['columns']))!=len(b['columns']): raise ValueError('invalid stored technical block')
        names.add(b['name'])
    hashes=obj.get('source_authority_hashes')
    if not isinstance(hashes,dict) or any(not isinstance(k,str) or not k or not is_hex64(v) for k,v in hashes.items()): raise ValueError('invalid stored source hash')
    return {'package_root_sha256':root,'registry':obj,'blocks':{b['name']:b['columns'] for b in blocks}}
