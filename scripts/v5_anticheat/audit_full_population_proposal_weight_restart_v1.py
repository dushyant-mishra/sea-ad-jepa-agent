#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, sqlite3
from collections import Counter
from pathlib import Path
import numpy as np

from sea_ad_jepa.v5.full104_metadata_authority_v1 import (
    EXPECTED_METADATA_SQLITE_SHA256,
    validate_requested_metadata_authority,
)

DOMAIN=b'SEA_AD_JEPA_V5_FULL_POPULATION_SCHEDULE_V1\0'
LEDGER_DTYPE=np.dtype([('stable_key','<i8'),('multiplicity','u1')],align=False)
PRES_DTYPE=np.dtype([('presentation_index','<u8'),('stable_key','<i8'),('weight_denominator','<u8')],align=False)


def sha256_file(path: Path, chunk=8<<20):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(chunk),b''): h.update(b)
    return h.hexdigest()
def bound_ledger_digest(data: bytes): return hashlib.sha256(DOMAIN+b'LEDGER\0'+data).hexdigest()
def affine_from(bound_hex: str,H:int):
    seed=hashlib.sha256(DOMAIN+b'ORDER\0'+bytes.fromhex(bound_hex)+H.to_bytes(8,'little')).digest()
    a=int.from_bytes(seed[:8],'little')%H or 1
    while math.gcd(a,H)!=1: a=(a+1)%H or 1
    b=int.from_bytes(seed[8:16],'little')%H
    return a,b

def load_metadata(metadata_sqlite: Path, partition: str):
    con=sqlite3.connect(f'file:{metadata_sqlite}?mode=ro&immutable=1',uri=True)
    donor_n={str(d):int(n) for d,n in con.execute('select donor_id,count(*) from cells where partition=? group by donor_id',(partition,))}
    rows=con.execute('select stable_key,donor_id from cells where partition=? order by stable_key',(partition,)).fetchall()
    con.close()
    keys=np.asarray([int(r[0]) for r in rows],dtype=np.int64)
    if len(keys)>1 and not np.all(keys[1:]>keys[:-1]): raise RuntimeError('STOP_PROPOSAL_METADATA_STABLE_KEY_NOT_UNIQUE_SORTED')
    dn=np.asarray([donor_n[str(r[1])] for r in rows],dtype=np.uint32)
    did=np.asarray([str(r[1]) for r in rows],dtype=object)
    return keys,dn,did,donor_n

def presentation_records(start,end,*,H,a,b,prefix,keys,mult,donor_n,D):
    t=np.arange(start,end,dtype=np.uint64)
    slot=(np.uint64(a)*t+np.uint64(b))%np.uint64(H)
    idx=np.searchsorted(prefix,slot,side='right')
    den=(np.uint64(D)*donor_n[idx].astype(np.uint64)*mult[idx].astype(np.uint64))
    out=np.empty(len(t),dtype=PRES_DTYPE)
    out['presentation_index']=t; out['stable_key']=keys[idx]; out['weight_denominator']=den
    return out

def stream_digest(*,H,a,b,prefix,keys,mult,donor_n,D,chunk_size,packing_mode=False):
    h=hashlib.sha256()
    for start in range(0,H,chunk_size):
        end=min(H,start+chunk_size)
        rec=presentation_records(start,end,H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=donor_n,D=D)
        if packing_mode and len(rec)>1:
            packed=rec[::-1].copy()
            rec=packed[np.argsort(packed['presentation_index'],kind='stable')]
        if len(rec) and (int(rec['presentation_index'][0])!=start or int(rec['presentation_index'][-1])!=end-1):
            raise RuntimeError('STOP_PROPOSAL_PACKING_PRESENTATION_INDEX_MISMATCH')
        h.update(rec.tobytes(order='C'))
    return h.hexdigest()


def restart_stream_digest(*,H,a,b,prefix,keys,mult,donor_n,D,restart_boundaries,max_chunk=200_000):
    h=hashlib.sha256()
    bounds=sorted(set([0,H,*[int(x) for x in restart_boundaries if 0<=int(x)<=H]]))
    if bounds[0]!=0 or bounds[-1]!=H:
        raise RuntimeError('STOP_PROPOSAL_RESTART_BOUNDARY_CLOSURE')
    for seg_start,seg_end in zip(bounds[:-1],bounds[1:]):
        for start in range(seg_start,seg_end,max_chunk):
            end=min(seg_end,start+max_chunk)
            rec=presentation_records(start,end,H=H,a=a,b,prefix=prefix,keys=keys,mult=mult,donor_n=donor_n,D=D)
            h.update(rec.tobytes(order='C'))
    return h.hexdigest(),bounds

def audit(*,metadata_sqlite:Path,expected_metadata_sha256:str,partition:str,schedule_report:Path,ledger:Path,chunk_size:int=200_000,_expected_metadata_sha256_for_test:str|None=None):
    try:
        active_expected_metadata_sha256=validate_requested_metadata_authority(expected_metadata_sha256,_expected_metadata_sha256_for_test=_expected_metadata_sha256_for_test)
    except ValueError as exc:
        raise RuntimeError(f'STOP_PROPOSAL_METADATA_AUTHORITY_MISMATCH: {exc}') from exc
    if sha256_file(metadata_sqlite)!=active_expected_metadata_sha256: raise RuntimeError('STOP_PROPOSAL_METADATA_SHA_MISMATCH')
    report=json.loads(schedule_report.read_text())
    if report.get('source_metadata_sha256')!=active_expected_metadata_sha256 or report.get('partition')!=partition: raise RuntimeError('STOP_PROPOSAL_SCHEDULE_PARENT_MISMATCH')
    raw=ledger.read_bytes(); observed_raw=hashlib.sha256(raw).hexdigest(); info=report['canonical_multiplicity_ledger']
    if observed_raw!=info['raw_sha256']: raise RuntimeError('STOP_PROPOSAL_LEDGER_RAW_SHA_MISMATCH')
    observed_bound=bound_ledger_digest(raw)
    if observed_bound!=info['domain_bound_sha256']: raise RuntimeError('STOP_PROPOSAL_LEDGER_DOMAIN_SHA_MISMATCH')
    if len(raw)%LEDGER_DTYPE.itemsize: raise RuntimeError('STOP_PROPOSAL_LEDGER_RECORD_ALIGNMENT')
    rec=np.frombuffer(raw,dtype=LEDGER_DTYPE)
    keys=rec['stable_key']; mult=rec['multiplicity']
    if np.any(mult==0): raise RuntimeError('STOP_PROPOSAL_ZERO_MULTIPLICITY')
    if len(keys)>1 and not np.all(keys[1:]>keys[:-1]): raise RuntimeError('STOP_PROPOSAL_LEDGER_KEYS_NOT_UNIQUE_SORTED')
    H=int(mult.astype(np.uint64).sum()); N=len(rec)
    if H!=int(report['total_presentations']) or N!=int(report['unique_cells']): raise RuntimeError('STOP_PROPOSAL_LEDGER_GEOMETRY_MISMATCH')
    a,b=affine_from(observed_bound,H); order=report['scientific_order_permutation']
    if (a,b,H)!=(int(order['a']),int(order['b']),int(order['H'])) or math.gcd(a,H)!=1: raise RuntimeError('STOP_PROPOSAL_AFFINE_REPLAY_MISMATCH')
    mkeys,dn,dids,donor_counts=load_metadata(metadata_sqlite,partition)
    if N!=len(mkeys) or not np.array_equal(keys,mkeys): raise RuntimeError('STOP_PROPOSAL_LEDGER_METADATA_KEY_MISMATCH')
    D=len(donor_counts)
    observed_donor_cells=Counter(map(str,dids.tolist()))
    if observed_donor_cells != Counter(donor_counts): raise RuntimeError('STOP_PROPOSAL_DONOR_TARGET_MASS_MISMATCH')
    donor_presentations=Counter()
    for d,m_i in zip(dids,mult): donor_presentations[str(d)] += int(m_i)
    if set(donor_presentations) != set(donor_counts): raise RuntimeError('STOP_PROPOSAL_DONOR_PRESENTATION_SET_MISMATCH')
    prefix=np.cumsum(mult,dtype=np.uint64)
    direct=stream_digest(H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D,chunk_size=chunk_size,packing_mode=False)
    packed128=stream_digest(H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D,chunk_size=128,packing_mode=True)
    packed576=stream_digest(H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D,chunk_size=576,packing_mode=True)
    if len({direct,packed128,packed576})!=1: raise RuntimeError('STOP_PROPOSAL_PACKING_REPLAY_MISMATCH')
    full_restart_digest,restart_boundaries=restart_stream_digest(H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D,restart_boundaries=[1,128,576,H//2,max(0,H-129),H-1],max_chunk=chunk_size)
    if full_restart_digest!=direct: raise RuntimeError('STOP_PROPOSAL_FULL_HORIZON_RESTART_REPLAY_MISMATCH')
    cursors=sorted(c for c in set([0,1,127,128,575,576,H//2,max(0,H-577),max(0,H-129),H-1,H]) if 0<=c<=H)
    restart=[]
    for c in cursors:
        lo=max(0,c-17); hi=min(H,c+17)
        baseline=presentation_records(lo,hi,H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D)
        left=presentation_records(lo,c,H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D)
        right=presentation_records(c,hi,H=H,a=a,b=b,prefix=prefix,keys=keys,mult=mult,donor_n=dn,D=D)
        resumed=np.concatenate([left,right]) if len(left)+len(right) else baseline
        ok=baseline.tobytes()==resumed.tobytes()
        if not ok: raise RuntimeError(f'STOP_PROPOSAL_RESTART_REPLAY_MISMATCH:{c}')
        restart.append({'cursor':c,'window_start':lo,'window_end':hi,'replay_exact':True})
    return {
      'schema':'JEPA_V5_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_V1',
      'status':'PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY',
      'source_metadata_sha256':active_expected_metadata_sha256,'partition':partition,'unique_cells':N,'donors':D,'total_presentations':H,
      'ledger_raw_sha256':observed_raw,'ledger_domain_bound_sha256':observed_bound,
      'affine_order':{'H':H,'a':a,'b':b,'gcd_a_H':math.gcd(a,H)},
      'proposal_definition':'q_i=m_i/H','target_definition':'p_i=1/(D*n_d)','exact_weight_definition':'w_i=H/(D*n_d*m_i)',
      'exact_donor_target_mass':'1/D for every donor','donor_presentation_min':min(donor_presentations.values()),'donor_presentation_max':max(donor_presentations.values()),'presentation_stream_digest_sha256':direct,
      'packing_replays':[{'physical_batch_size':128,'digest_sha256':packed128,'exact':True},{'physical_batch_size':576,'digest_sha256':packed576,'exact':True}],
      'full_horizon_restart_replay':{'restart_boundaries':restart_boundaries,'digest_sha256':full_restart_digest,'exact':True},
      'restart_probes':restart,
      'full104_expression_binding_required':True,'full104_expression_binding_closed':False,
      'update_local_conditioning_authority_created':False,'gpu_authority_created':False,'production_dimensions_created':False,
      'pathology_used':False,'checkpoint_outcomes_used':False,'training_authorized':False,
    }

def main():
 p=argparse.ArgumentParser(); p.add_argument('--metadata-sqlite',type=Path,required=True); p.add_argument('--expected-metadata-sha256',required=True); p.add_argument('--partition',default='reader_fit'); p.add_argument('--schedule-report',type=Path,required=True); p.add_argument('--ledger',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--chunk-size',type=int,default=200000); a=p.parse_args(); r=audit(metadata_sqlite=a.metadata_sqlite,expected_metadata_sha256=a.expected_metadata_sha256,partition=a.partition,schedule_report=a.schedule_report,ledger=a.ledger,chunk_size=a.chunk_size); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
