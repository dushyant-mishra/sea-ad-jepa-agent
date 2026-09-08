#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

RECURRENCE_SHA='8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da'
OBSERVATION_SHA='852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
VOCAB=41_238
SOURCE_OPERATOR_COUNTS={'HVS':24,'NPH52':7,'SEA_AD':11}


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
    return h.hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--support-recurrence',type=Path,required=True)
    p.add_argument('--operator-observation-state',type=Path,required=True)
    p.add_argument('--out-json',type=Path,required=True)
    p.add_argument('--out-core-csv',type=Path,required=True)
    a=p.parse_args()
    sr=sha256(a.support_recurrence); os=sha256(a.operator_observation_state)
    if sr!=RECURRENCE_SHA: raise SystemExit(f'support recurrence authority mismatch: {sr}')
    if os!=OBSERVATION_SHA: raise SystemExit(f'operator observation authority mismatch: {os}')
    recurrence=pd.read_csv(a.support_recurrence)
    if len(recurrence)!=VOCAB or recurrence.molecular_address_index.tolist()!=list(range(VOCAB)):
        raise RuntimeError('support recurrence canonical ledger mismatch')
    z=np.load(a.operator_observation_state,allow_pickle=False)
    if tuple(z['states'].shape)!=(42,VOCAB): raise RuntimeError('operator observation tensor shape mismatch')
    names=[str(x) for x in z['state_names'].tolist()]
    if names!=['STRUCTURALLY_UNMEASURED','MEASURED_SCALAR','MEASURED_COLLISION_UNRESOLVED']:
        raise RuntimeError('operator observation state-name authority mismatch')
    measured=(z['states']==1)
    measured_count=measured.sum(axis=0)
    if not np.array_equal(measured_count,recurrence.operators_measured_scalar.to_numpy()):
        raise RuntimeError('recurrence/operator-state measured counts disagree')
    common_mask=measured.all(axis=0)
    if not np.array_equal(common_mask,recurrence.operators_measured_scalar.to_numpy()==42):
        raise RuntimeError('common-core authorities disagree')
    core=recurrence.loc[common_mask,['molecular_address_index','molecular_address_id','symbol']].copy()
    a.out_core_csv.parent.mkdir(parents=True,exist_ok=True)
    core.to_csv(a.out_core_csv,index=False,lineterminator='\n')
    source_support={}
    for src,nops in SOURCE_OPERATOR_COUNTS.items():
        col=f'{src}_operators_measured_scalar'
        all_count=int((recurrence[col]==nops).sum())
        any_count=int((recurrence[col]>0).sum())
        source_support[src]={
            'operators':nops,
            'measured_by_all_source_operators':all_count,
            'measured_by_any_source_operator':any_count,
            'common_core_fraction_of_source_all_support':float(len(core)/all_count),
        }
    out={
        'schema':'READER_FIT_SUPPORT_OVERLAP_PROFILE_V1',
        'vocabulary_size':VOCAB,
        'operators':42,
        'all_42_operators_measured_scalar':int(len(core)),
        'all_42_fraction_of_universe':float(len(core)/VOCAB),
        'source_support':source_support,
        'support_recurrence_sha256':sr,
        'operator_observation_state_sha256':os,
        'common_core_materialization':{
            'rows':int(len(core)),
            'csv_sha256':sha256(a.out_core_csv),
            'generator':'scripts/agent/profile_reader_fit_support_overlap_v1.py',
            'checked_in':False,
        },
        'interpretation':[
            'The all-42 common measured core is outcome-blind support geometry, not a training objective.',
            'Native-support views may retain all operator-specific measured addresses; a future reviewed common-core view may use this exact support to equalize molecular availability across operators.',
            'No mask fraction, visible-gene budget, block size, or loss weight is frozen here.',
        ],
        'candidate_use_only':True,
        'training_authorized':False,
    }
    a.out_json.parent.mkdir(parents=True,exist_ok=True)
    a.out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'json_sha256':sha256(a.out_json),'core_sha256':sha256(a.out_core_csv),'core_rows':len(core)},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
