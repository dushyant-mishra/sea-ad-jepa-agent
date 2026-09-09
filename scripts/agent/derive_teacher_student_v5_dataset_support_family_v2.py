#!/usr/bin/env python3
"""Reconstruct V5 support-family geometry from exact reader-fit support bytes.

Outcome-blind.  Reads only the frozen operator observation-state matrix, the
materialized all-42 common core, and the operator support summary.  Produces no
training/execution authority.
"""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sea_ad_jepa.v5.support_family_policy_v3 import SUPPORT_FAMILIES, support_family_counts

STATE_SHA='852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
CORE_SHA='8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac'
OP_SHA='1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--state-npz',required=True,type=Path)
    ap.add_argument('--common-core-csv',required=True,type=Path)
    ap.add_argument('--support-by-operator-csv',required=True,type=Path)
    ap.add_argument('--output-csv',required=True,type=Path)
    a=ap.parse_args()
    if sha(a.state_npz)!=STATE_SHA: raise RuntimeError('operator observation-state NPZ SHA drift')
    if sha(a.common_core_csv)!=CORE_SHA: raise RuntimeError('common-core CSV SHA drift')
    if sha(a.support_by_operator_csv)!=OP_SHA: raise RuntimeError('support-by-operator CSV SHA drift')
    z=np.load(a.state_npz,allow_pickle=False)
    if set(z.files)!={'states','matrix_id','operator_index','molecular_address_index','state_names'}: raise RuntimeError('state NPZ key drift')
    states=z['states']; matrix=z['matrix_id']; operators=z['operator_index']; addresses=z['molecular_address_index']; names=z['state_names'].tolist()
    if states.shape!=(42,41_238) or operators.tolist()!=list(range(42)) or addresses.tolist()!=list(range(41_238)): raise RuntimeError('state geometry drift')
    if names!=['STRUCTURALLY_UNMEASURED','MEASURED_SCALAR','MEASURED_COLLISION_UNRESOLVED']: raise RuntimeError('state-name drift')
    measured_code=names.index('MEASURED_SCALAR')
    common=pd.read_csv(a.common_core_csv)
    if list(common.columns)!=['molecular_address_index','molecular_address_id','symbol']: raise RuntimeError('common-core schema drift')
    common_ids=common.molecular_address_index.astype(int).tolist()
    derived=addresses[(states==measured_code).all(0)].astype(int).tolist()
    if common_ids!=derived or len(common_ids)!=17_186: raise RuntimeError('common core != exact all-42 measured intersection')
    op=pd.read_csv(a.support_by_operator_csv)
    if len(op)!=42 or op.operator_index.astype(int).tolist()!=list(range(42)): raise RuntimeError('operator support summary drift')
    rows=[]
    for oi in range(42):
        measured=int((states[oi]==measured_code).sum())
        r=op.iloc[oi]
        if int(r.operator_index)!=oi or str(r.matrix_id)!=str(matrix[oi]) or int(r.measured_scalar_addresses)!=measured: raise RuntimeError(f'operator {oi} detached support summary')
        fam=support_family_counts(measured_count=measured,common_core_count=17_186,vocabulary_size=41_238)
        if sum(x['family_loss_weight'] for x in fam.values())!=1: raise RuntimeError('family weight sum drift')
        for family in SUPPORT_FAMILIES:
            x=fam[family]; w=x['family_loss_weight']
            rows.append({
                'operator_index':oi,'matrix_id':str(matrix[oi]),'source':str(r.source),'operator_measured':measured,
                'family':family,'family_support_count':int(x['family_support_count']),
                'family_loss_weight_num':w.numerator,'family_loss_weight_den':w.denominator,'family_loss_weight':float(w),
                'target_count':int(x['target_count']),'student_visible_count':int(x['student_visible_count']),
                'teacher_support_count':int(x['teacher_support_count']),
                'target_fraction_within_family':int(x['target_count'])/int(x['family_support_count']),
                'student_visible_fraction_of_universe':int(x['student_visible_count'])/41_238,
                'per_address_expected_loss_mass':1/measured,
            })
    df=pd.DataFrame(rows)
    if len(df)!=84 or not bool((df.teacher_support_count==df.operator_measured).all()): raise RuntimeError('teacher full-support invariant failed')
    for oi,g in df.groupby('operator_index'):
        if len(g)!=2 or abs(float(g.family_loss_weight.sum())-1)>1e-15: raise RuntimeError(f'operator {oi} family mass drift')
    a.output_csv.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(a.output_csv,index=False,lineterminator='\n')
    print(f'PASS_DATASET_SUPPORT_FAMILY_V2 {sha(a.output_csv)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
