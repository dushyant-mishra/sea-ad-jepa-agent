#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

OBS_SHA='852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
REC_SHA='8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da'
CORE_CSV_SHA='8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac'
EXPECTED_MANIFEST_SHA='4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660'

TD59_GENE_SHA={(0,'Z'):'f09455c4f5c120785608eda0c870bb299951814e895bbb7ff9d4dcf94b5680b2',(0,'X'):'a365be9aa9ccfc80adddfeb080f8fc6b0c0bc515554bace7076b5cf31a990ae5',(0,'Y'):'124246edc85f082477fb354f6f20c09752a08a1e079c509a6f94648658b31bd3',(1,'Z'):'2e1b171e833e248c9107b3f619df66f8ea33677bec7832aad58c6885ba4ae7be',(1,'X'):'8ef683be715f471f2a0f95531183416d75613eac43c745aa0ab10c7b59db6fa5',(1,'Y'):'e3dc6ad8c685155458c978d7c5127f26536098a88a10a5d87a6ac127b1689959'}
TD59_PAIR_SHA={(0,'Z'):'806553cdacc4d1e3214a2d61880b8795ca4a0637f3762280750cfb502dcd36ed',(0,'X'):'5d9f539d723117bffebfbcd57feefb9b880c50bc4c0aaab55dc9c9f9411a99fd',(0,'Y'):'eb6182759465df0e719bc793781ce0964e9a766761508ebe7bb192eda05defad',(1,'Z'):'960741f9b74118e8991cb859e3f044176afa8151eed3dace3f7b98102198db84',(1,'X'):'d28d1bd09181bbfd24ca3d737a95a6d911ace6906a5e94d6bbdf133bbc33e0da',(1,'Y'):'bc81c334afdcf169a0e4636ec5f76da51e248b4ac35821e26b2a71b8dbe4599f'}
RANGES=[(0,511,'TD56_TD57A_TD58','BASE','X'),(512,1023,'TD56_TD57A_TD58','BASE','Y'),(1024,1535,'TD57B','P0','X'),(1536,2047,'TD57B','P0','Y'),(2048,2559,'TD57B','P1','X'),(2560,3071,'TD57B','P1','Y'),(3072,3583,'TD57C','P0','Z'),(3584,4095,'TD57C','P0','X'),(4096,4607,'TD57C','P0','Y'),(4608,5119,'TD57C','P1','Z'),(5120,5631,'TD57C','P1','X'),(5632,6143,'TD57C','P1','Y'),(6144,6655,'TD59','P0','Z'),(6656,7167,'TD59','P0','X'),(7168,7679,'TD59','P0','Y'),(7680,8191,'TD59','P1','Z'),(8192,8703,'TD59','P1','X'),(8704,9215,'TD59','P1','Y')]
TD59_SLICES={(0,'Z'):(6144,6656),(0,'X'):(6656,7168),(0,'Y'):(7168,7680),(1,'Z'):(7680,8192),(1,'X'):(8192,8704),(1,'Y'):(8704,9216)}

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def digest(s:str)->bytes:return hashlib.sha256(s.encode()).digest()
def write_lf_bytes(path:Path,text:str)->None:Path(path).write_bytes(text.encode('utf-8'))
def pair_hash(genes:np.ndarray,prefix:str,panel:int,view:str)->str:
    rows=[]
    for a in range(511):
        ga=int(genes[a])
        for b in range(a+1,512):
            gb=int(genes[b]); g0,g1=sorted((ga,gb))
            pre=f'{prefix}|panel|{panel}|view|{view}|g0|{g0}|g1|{g1}'
            rows.append((digest(pre),g0,g1))
    rows.sort(key=lambda x:x[0])
    arr=np.array([[x[1],x[2]] for x in rows[:2048]],dtype=np.int32)
    return sha_bytes(arr.tobytes())

def find_name(z:zipfile.ZipFile,suffix:str)->str:
    hits=[n for n in z.namelist() if n.endswith(suffix)]
    if len(hits)!=1: raise RuntimeError(f'expected one {suffix}, got {hits}')
    return hits[0]

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--calibration-zip',type=Path,required=True); ap.add_argument('--td-artifacts-zip',type=Path,required=True); ap.add_argument('--manifest-out',type=Path,required=True); ap.add_argument('--receipt-out',type=Path,required=True); a=ap.parse_args()
    validation={}
    with zipfile.ZipFile(a.calibration_zip) as z:
        ob=z.read(find_name(z,'FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz')); rc=z.read(find_name(z,'FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv'))
    validation['observation_state_sha']=sha_bytes(ob)==OBS_SHA; validation['support_recurrence_sha']=sha_bytes(rc)==REC_SHA
    obs=np.load(io.BytesIO(ob),allow_pickle=False); states=obs['states']; common=np.where((states==1).all(axis=0))[0]
    recurrence=pd.read_csv(io.BytesIO(rc)); core=recurrence.loc[np.isin(recurrence.molecular_address_index.to_numpy(),common),['molecular_address_index','molecular_address_id','symbol']].copy()
    core=core.set_index('molecular_address_index').loc[common].reset_index()
    core_bytes=core.to_csv(index=False,lineterminator='\n').encode(); validation['common_core_csv_sha']=sha_bytes(core_bytes)==CORE_CSV_SHA; validation['common_core_count']=len(common)==17186
    ranked=np.array(sorted((int(x) for x in common),key=lambda g:digest(f'TD56S|gene|{g}')),dtype=np.int32)
    with zipfile.ZipFile(a.td_artifacts_zip) as z:
        b0=json.loads(z.read('td57b_p0_hvs.json')); b1=json.loads(z.read('td57b_p1_hvs.json')); c0=json.loads(z.read('td57c_p0_hvs.json'))
    validation['td57b_p0_X_exact']=np.array_equal(np.asarray(b0['gene_view_X'],dtype=np.int32),ranked[1024:1536]); validation['td57b_p0_Y_exact']=np.array_equal(np.asarray(b0['gene_view_Y'],dtype=np.int32),ranked[1536:2048])
    validation['td57b_p1_X_exact']=np.array_equal(np.asarray(b1['gene_view_X'],dtype=np.int32),ranked[2048:2560]); validation['td57b_p1_Y_exact']=np.array_equal(np.asarray(b1['gene_view_Y'],dtype=np.int32),ranked[2560:3072])
    for p,d in [(0,b0),(1,b1)]:
        sx=(1024,1536) if p==0 else (2048,2560); sy=(1536,2048) if p==0 else (2560,3072)
        validation[f'td57b_p{p}_X_pair_hash']=pair_hash(ranked[sx[0]:sx[1]],'TD57B',p,'X')==d['pair_addresses_X_sha256']; validation[f'td57b_p{p}_Y_pair_hash']=pair_hash(ranked[sy[0]:sy[1]],'TD57B',p,'Y')==d['pair_addresses_Y_sha256']
    c_slices={'Z':(3072,3584),'X':(3584,4096),'Y':(4096,4608)}
    for v,sl in c_slices.items():
        validation[f'td57c_p0_{v}_exact']=np.array_equal(np.asarray(c0['gene_views'][v],dtype=np.int32),ranked[sl[0]:sl[1]]); validation[f'td57c_p0_{v}_pair_hash']=pair_hash(ranked[sl[0]:sl[1]],'TD57C',0,v)==c0['pair_address_sha256'][v]
    for k,sl in TD59_SLICES.items():
        genes=ranked[sl[0]:sl[1]].astype(np.int32); validation[f'td59_p{k[0]}_{k[1]}_gene_hash']=sha_bytes(genes.tobytes())==TD59_GENE_SHA[k]; validation[f'td59_p{k[0]}_{k[1]}_pair_hash']=pair_hash(genes,'TD59',k[0],k[1])==TD59_PAIR_SHA[k]
    role={p:(stage,panel,view) for lo,hi,stage,panel,view in RANGES for p in range(lo,hi+1)}; idx=recurrence.set_index('molecular_address_index'); out=[]
    for p,g in enumerate(ranked[:9216]):
        rr=idx.loc[int(g)]; stage,panel,view=role[p]; out.append({'rank_position':p,'molecular_address_index':int(g),'molecular_address_id':str(rr['molecular_address_id']),'symbol':str(rr['symbol']),'historical_stage':stage,'panel':panel,'view':view})
    df=pd.DataFrame(out); a.manifest_out.parent.mkdir(parents=True,exist_ok=True); text=df.to_csv(index=False,lineterminator='\n'); write_lf_bytes(a.manifest_out,text); msha=sha_bytes(text.encode()); validation['manifest_sha']=msha==EXPECTED_MANIFEST_SHA
    status='PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST' if all(validation.values()) else 'FAIL_REPLAY_MANIFEST_VALIDATION'
    receipt={'schema':'JEPA_TD_RELATIONAL_REPLAY_MANIFEST_RECEIPT_V1','status':status,'common_core_rows':len(common),'common_core_csv_sha256':sha_bytes(core_bytes),'replay_addresses':len(df),'manifest_sha256':msha,'validation':validation,'scope':'metadata/provenance only; no expression values read; no target/training authority'}
    a.receipt_out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(receipt,sort_keys=True)); return 0 if status.startswith('PASS') else 2
if __name__=='__main__': raise SystemExit(main())
