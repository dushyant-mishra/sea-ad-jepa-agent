#!/usr/bin/env python3
"""Audit S174->TD50->TD56/TD57B/TD59 custody join without granting authority.

Fail-closed custody script. It inventories physical archives, hashes extracted TD
artifacts, compares pre-S174 Stage81A3R NPZ member CRC/size against the S174 RAR
directory, and searches recovered text for explicit S174/new-shard bindings.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
try:
    import rarfile
except Exception:
    rarfile = None
TEXT_EXT={'.py','.json','.csv','.tsv','.txt','.out','.cpp','.md','.yaml','.yml'}
TERMINAL='TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED'
SEARCH_TERMS=['S174','s174','S174_REBUILD_BUILD_RECEIPT_V1','645df92bab23d274048c4d7fa15b55a13ec5c2f5daadde0531aa807d2712aade','60147fc84f0c39003d3ce4c6609b0f7ceba95eec0d4bca71404ecaf21220fa9a']
def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--td-dir', type=Path, required=True)
    ap.add_argument('--td-archive', type=Path, required=True)
    ap.add_argument('--stage81-zip', type=Path, required=True)
    ap.add_argument('--s174-rar', type=Path, required=True)
    ap.add_argument('--json-out', type=Path, required=True)
    args=ap.parse_args()
    result={'schema_version':'1.0','terminal':TERMINAL,'assets':{},'text_hits':[]}
    for label,p in [('td_archive',args.td_archive),('stage81_zip',args.stage81_zip),('s174_rar',args.s174_rar)]:
        result['assets'][label]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha256(p)}
    files=[]
    for p in sorted(args.td_dir.rglob('*')):
        if not p.is_file(): continue
        row={'path':str(p.relative_to(args.td_dir)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha256(p)}
        files.append(row)
        if p.suffix.lower() in TEXT_EXT:
            txt=p.read_text(encoding='utf-8',errors='replace')
            for term in SEARCH_TERMS:
                if term in txt: result['text_hits'].append({'path':row['path'],'term':term})
    result['td_extracted_files']=len(files)
    result['td_extracted_manifest']=files
    if rarfile is None:
        result['rar_directory_status']='RARFILE_MODULE_UNAVAILABLE'
    else:
        rr=[]
        with rarfile.RarFile(args.s174_rar) as rf:
            for i in rf.infolist():
                rr.append({'member':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'crc32':f'{i.CRC:08x}' if i.CRC is not None else '', 'is_dir':i.isdir()})
        result['rar_directory_status']='READ'
        result['s174_rar_members']=rr
        rmap={Path(r['member']).name:(r['bytes'],int(r['crc32'],16) if r['crc32'] else None) for r in rr if not r['is_dir']}
        zmap={}
        with zipfile.ZipFile(args.stage81_zip) as zf:
            for i in zf.infolist():
                n=Path(i.filename).name
                if n.endswith(('.counts.npz','.meta.npz')): zmap[n]=(i.file_size,i.CRC)
        names=sorted(set(zmap)|set(rmap)); same=sum(1 for n in names if n in zmap and n in rmap and zmap[n]==rmap[n])
        result['stage81_vs_s174_npz_comparison']={'members_compared':len(names),'same_size_and_crc':same,'different_or_missing':len(names)-same}
    result['adjudication']={'td56':'HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY','td57b':'HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY','td59':'TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY'}
    result['required_join']='S174 corrected shard hashes -> corrected 50K sparse matrix + corrected td50 source metadata/global_row receipt -> exact stage executor -> rerun stage result/root'
    args.json_out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'text_hits':len(result['text_hits']),'td_extracted_files':len(files),'terminal':TERMINAL},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
