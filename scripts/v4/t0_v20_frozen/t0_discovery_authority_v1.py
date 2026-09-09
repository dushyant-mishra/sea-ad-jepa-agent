from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
from t0_target_serializer_v2 import load_target_v2
from t0_donor_role_authority_v2 import load_role_authority
from t0_package_integrity_v1 import verify_flat_package

SCHEMA='JEPA_T0_DISCOVERY_AUTHORITY_LINK_V1'
MEMBER='T0_DISCOVERY_AUTHORITY_LINK.json'
MANIFEST='T0_DISCOVERY_AUTHORITY_MANIFEST.csv'
ROOT_FILE='T0_DISCOVERY_AUTHORITY_PACKAGE_ROOT_SHA256.txt'
EXPECTED_FILES={MEMBER,MANIFEST,ROOT_FILE}


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()


def _hex64(x):
    return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)


def _read_manifest_strict(path: Path):
    with path.open('r',encoding='utf-8',newline='') as f:
        rows=list(csv.reader(f))
    if rows!=[] and rows[0]!=['filename','bytes','sha256']:
        raise ValueError('discovery authority manifest columns mismatch')
    if len(rows)!=2:
        raise ValueError('discovery authority manifest row count mismatch')
    filename,byte_text,digest=rows[1]
    if filename!=MEMBER:
        raise ValueError('discovery authority manifest member mismatch')
    try:
        nbytes=int(byte_text)
    except Exception as e:
        raise ValueError('discovery authority manifest bytes invalid') from e
    if nbytes<0 or str(nbytes)!=byte_text:
        raise ValueError('discovery authority manifest bytes not canonical integer')
    if not _hex64(digest):
        raise ValueError('discovery authority manifest sha256 invalid')
    return nbytes,digest


def build_discovery_authority(outdir,target_dir,role_dir,feature_split_csv):
    target=load_target_v2(target_dir,feature_split_csv); role=load_role_authority(role_dir)
    donors=list(map(str,target['fit']['canonical_donor_order']))
    if donors!=role['discovery_donors']: raise ValueError('target discovery donors do not equal frozen role authority')
    obj={'schema':SCHEMA,'target_package_root_sha256':target['package_root_sha256'],'donor_role_package_root_sha256':role['package_root_sha256'],'discovery_provenance_root_sha256':target['provenance']['root_sha256'],'discovery_donors':donors}
    out=Path(outdir)
    if out.exists() and any(out.iterdir()): raise ValueError('discovery authority output must be absent or empty')
    out.mkdir(parents=True,exist_ok=True)
    (out/MEMBER).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    with (out/MANIFEST).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n'); p=out/MEMBER
        w.writerow(['filename','bytes','sha256']); w.writerow([p.name,p.stat().st_size,sha(p)])
    root=sha(out/MANIFEST); (out/ROOT_FILE).write_text(root+'\n',encoding='utf-8')
    return {'package_root_sha256':root,**obj}


def load_discovery_authority(outdir,target_dir,role_dir,feature_split_csv):
    out=Path(outdir)
    root=verify_flat_package(out,{MEMBER},MANIFEST,ROOT_FILE,label='discovery-authority package')
    member_path=out/MEMBER
    try:
        obj=json.loads(member_path.read_text(encoding='utf-8'))
    except Exception as e:
        raise ValueError('discovery authority JSON invalid') from e
    expected_obj_keys={'schema','target_package_root_sha256','donor_role_package_root_sha256','discovery_provenance_root_sha256','discovery_donors'}
    if set(obj)!=expected_obj_keys: raise ValueError('discovery authority JSON keys mismatch')
    target=load_target_v2(target_dir,feature_split_csv); role=load_role_authority(role_dir)
    if (obj.get('schema')!=SCHEMA
        or not _hex64(obj.get('target_package_root_sha256'))
        or not _hex64(obj.get('donor_role_package_root_sha256'))
        or not _hex64(obj.get('discovery_provenance_root_sha256'))
        or obj['target_package_root_sha256']!=target['package_root_sha256']
        or obj['donor_role_package_root_sha256']!=role['package_root_sha256']
        or obj['discovery_provenance_root_sha256']!=target['provenance']['root_sha256']
        or obj['discovery_donors']!=role['discovery_donors']):
        raise ValueError('discovery authority linkage mismatch')
    return {'package_root_sha256':root,**obj,'confirmation_donors':role['confirmation_donors']}
