#!/usr/bin/env python3
"""Materialize/replay the real-cell V5 multiplicity ledger from an optimum."""
from __future__ import annotations
import argparse, hashlib, json, math, sqlite3
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import numpy as np

from sea_ad_jepa.v5.full104_metadata_authority_v1 import (
    EXPECTED_METADATA_SQLITE_SHA256,
    validate_requested_metadata_authority,
)

GROUP_DOMAIN=b'SEA_AD_JEPA_V5_GROUP_FLOOR_ASSIGNMENT_V1\0'; ASSIGN_DOMAIN=b'SEA_AD_JEPA_V5_DONOR_FINAL_ASSIGNMENT_V1\0'; DOMAIN=b'SEA_AD_JEPA_V5_FULL_POPULATION_SCHEDULE_V1\0'

def rank(domain,donor,op,key): return hashlib.sha256(domain+donor.encode()+b'\0'+str(op).encode()+b'\0'+int(key).to_bytes(8,'little')).digest()

def sha256_file(path, chunk_size=1024*1024):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''): h.update(chunk)
    return h.hexdigest()

def main(argv=None, *, _expected_metadata_sha256_for_test: str | None = None):
    p=argparse.ArgumentParser(); p.add_argument('--metadata-sqlite',type=Path,required=True); p.add_argument('--expected-metadata-sha256',required=True); p.add_argument('--partition',required=True); p.add_argument('--optimum-json',type=Path,required=True); p.add_argument('--outdir',type=Path,required=True); a=p.parse_args(argv)
    try:
        expected_metadata_sha256=validate_requested_metadata_authority(a.expected_metadata_sha256,_expected_metadata_sha256_for_test=_expected_metadata_sha256_for_test)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    opt=json.loads(a.optimum_json.read_text()); observed=str(opt.get('metadata_sqlite_sha256',''))
    if observed.lower()!=expected_metadata_sha256 or opt.get('partition')!=a.partition: raise SystemExit('metadata/partition binding mismatch')
    st=a.metadata_sqlite.stat(); receipt=opt.get('metadata_file_receipt',{}); fp=(st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev); expected=(int(receipt.get('bytes',-1)),int(receipt.get('mtime_ns',-1)),int(receipt.get('inode',-1)),int(receipt.get('device',-1)))
    if fp!=expected: raise SystemExit('metadata file fingerprint changed since optimizer authentication; rerun optimizer')
    actual_metadata_sha256=sha256_file(a.metadata_sqlite)
    if actual_metadata_sha256.lower()!=observed.lower() or actual_metadata_sha256.lower()!=expected_metadata_sha256: raise SystemExit('metadata cryptographic digest changed since optimizer authentication; rerun optimizer')
    final=opt['final_optimum']; counts=final['donor_multiplicity_counts']; bounds=final['donor_ratio_bounds']; group_floor=int(opt['constraints']['minimum_group_presentations']); N=int(opt['population_cells']); H=int(final['total_presentations'])
    keys=np.empty(N,dtype=np.int64); mult=np.empty(N,dtype=np.uint8); off=0; source_pres=Counter(); group_pres=[]; donor_check={}
    con=sqlite3.connect(f'file:{a.metadata_sqlite}?mode=ro',uri=True); c=con.cursor(); donors=[str(x[0]) for x in c.execute('select distinct donor_id from cells where partition=? order by donor_id',(a.partition,))]
    if set(donors)!=set(counts): raise SystemExit('donor identity set moved')
    for d in donors:
        rows=c.execute('select stable_key,operator_index,source from cells where partition=? and donor_id=? order by operator_index,stable_key',(a.partition,d)).fetchall(); L=int(bounds[d]['min_multiplicity']); U=int(bounds[d]['max_multiplicity']); byop=defaultdict(list)
        for k,o,s in rows: byop[int(o)].append((int(k),str(s)))
        cells=[]
        for op,items in sorted(byop.items()):
            g=len(items); extra=max(0,group_floor-g*L); q,r=divmod(extra,g); base=L+q; chosen=set()
            if r: chosen={k for _,k in sorted((rank(GROUP_DOMAIN,d,op,k),k) for k,_ in items)[:r]}
            for k,s in items: cells.append((k,op,s,base+(k in chosen)))
        finals=[]
        for m,n in counts[d].items(): finals.extend([int(m)]*int(n))
        finals.sort(reverse=True); cells.sort(key=lambda x:(-x[3],rank(ASSIGN_DOMAIN,d,x[1],x[0])))
        if len(finals)!=len(cells): raise RuntimeError('donor multiplicity/cell mismatch')
        assigned=[]; bygroup=Counter(); dcnt=Counter()
        for cell,m in zip(cells,finals):
            if m<cell[3] or m>U: raise RuntimeError('final assignment violates group floor/cap construction')
            assigned.append((cell[0],m)); bygroup[cell[1]]+=m; source_pres[cell[2]]+=m; dcnt[m]+=1
        if {str(k):v for k,v in sorted(dcnt.items())}!={str(k):int(v) for k,v in counts[d].items()}: raise RuntimeError('donor multiplicity histogram changed')
        group_pres.extend(bygroup.values()); sl=slice(off,off+len(assigned)); keys[sl]=[x[0] for x in assigned]; mult[sl]=[x[1] for x in assigned]; off+=len(assigned); donor_check[d]=dcnt
    con.close()
    if sha256_file(a.metadata_sqlite).lower()!=actual_metadata_sha256.lower(): raise SystemExit('metadata cryptographic digest changed during materialization; rerun optimizer')
    if off!=N or int(mult.sum())!=H or min(group_pres)<group_floor: raise RuntimeError('materialized schedule invariant failed')
    order=np.argsort(keys,kind='stable'); sk=keys[order]; sm=mult[order]
    if not np.all(sk[1:]>sk[:-1]): raise RuntimeError('stable keys are not globally unique')
    rec=np.empty(N,dtype=np.dtype([('stable_key','<i8'),('multiplicity','u1')],align=False)); rec['stable_key']=sk; rec['multiplicity']=sm; data=rec.tobytes(order='C')
    raw=hashlib.sha256(data).hexdigest(); bound=hashlib.sha256(DOMAIN+b'LEDGER\0'+data).hexdigest(); a.outdir.mkdir(parents=True,exist_ok=True); ledger=a.outdir/'V5_FULL_POPULATION_MULTIPLICITY_LEDGER_V1.bin'; ledger.write_bytes(data)
    donor_n={d:int(bounds[d]['donor_cells']) for d in donors}; D=len(donors); A=Fraction(); lo=10**30; hi=0
    for d,cnt in donor_check.items():
        n=donor_n[d]
        for m,cnt_m in cnt.items(): A+=Fraction(cnt_m,D*D*n*n*m); lo=min(lo,n*m); hi=max(hi,n*m)
    P=Fraction(H)*A; seed=hashlib.sha256(DOMAIN+b'ORDER\0'+bytes.fromhex(bound)+H.to_bytes(8,'little')).digest(); aa=int.from_bytes(seed[:8],'little')%H or 1
    while math.gcd(aa,H)!=1: aa=(aa+1)%H or 1
    bb=int.from_bytes(seed[8:16],'little')%H
    out={'schema':'JEPA_V5_FULL_POPULATION_SCHEDULE_MATERIALIZATION_V4','status':'REAL_READER_FIT_CELL_MULTIPLICITY_LEDGER_REPLAYED__NO_TRAINING_AUTHORITY','parent_optimum_sha256':hashlib.sha256(a.optimum_json.read_bytes()).hexdigest(),'source_metadata_sha256':actual_metadata_sha256,'partition':a.partition,'unique_cells':N,'total_presentations':H,'minimum_group_presentations':min(group_pres),'maximum_cell_multiplicity':int(mult.max()),'importance_ess_fraction':float(Fraction(1,1)/P),'importance_weight_max_to_min_ratio':float(Fraction(hi,lo)),'source_presentations':dict(sorted(source_pres.items())),'source_presentation_fraction':{s:source_pres[s]/H for s in sorted(source_pres)},'canonical_multiplicity_ledger':{'records':N,'bytes':len(data),'encoding':'packed stable_key int64-le + multiplicity uint8, stable_key ascending','raw_sha256':raw,'domain_bound_sha256':bound,'digest_semantics':'raw_sha256 hashes exact ledger bytes; domain_bound_sha256 = SHA256(domain || LEDGER\\0 || raw bytes)','committed_as_large_binary':False,'reproducible_from_authority':True},'scientific_order_permutation':{'family':'AFFINE_BIJECTION_MOD_H','H':H,'a':aa,'b':bb,'gcd_a_H':math.gcd(aa,H),'formula':'canonical_slot_index=(a*scientific_presentation_index+b) mod H','seed_binding':'SHA256(domain || ORDER || domain_bound_ledger_sha256 || H)'},'pathology_used':False,'checkpoint_outcomes_used':False,'synthetic_data_used_for_authority':False,'training_authorized':False}
    report=a.outdir/'FULL_POPULATION_SCHEDULE_MATERIALIZATION_V4.json'; report.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
