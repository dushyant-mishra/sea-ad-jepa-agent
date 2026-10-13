from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np

PACKAGE_ID='JEPA_TD_RELATIONAL_SYNTHETIC_V1_20261013'
PACKAGE_SCHEMA='JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1'
N_NULL=64
CAPABILITIES=(
 ('REL_BROAD_MESO_POSITIVE','POSITIVE_TRUTH','PASS'),
 ('REL_FINE_RECURRENT_POSITIVE','POSITIVE_TRUTH','PASS'),
 ('REL_RARE_LOCAL_ISLAND_POSITIVE','POSITIVE_TRUTH','PASS'),
 ('REL_MULTI_ISLAND_POSITIVE','POSITIVE_TRUTH','PASS'),
 ('REL_DONOR_RESTRICTED_POSITIVE','POSITIVE_TRUTH','PASS'),
 ('REL_SOURCE_VISIBILITY_STRESS','STRESS_TRUTH','PASS'),
 ('REL_TECHNICAL_TWIN_NEGATIVE','NEGATIVE_TRUTH','FAIL'),
 ('REL_NULL_NEGATIVE','NEGATIVE_TRUTH','FAIL'),
 ('REL_UNDERPOWERED_POSITIVE','UNDERIDENTIFIED_TRUTH','NOT_ESTIMABLE'),
)
AUTHORITY={
 'synthetic_world_generation_authorized':False,'synthetic_world_regeneration_authorized':False,
 'qualification_model_fitting_authorized':False,'target_selection_authorized':False,
 'td60_authorized':False,'stage4_authorized':False,'training_authorized':False,
}

def canon(obj:Any)->bytes:
    return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def sha_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def sha_obj(x:Any)->str: return sha_bytes(canon(x))
def pairwise(feat:np.ndarray)->np.ndarray:
    feat=np.asarray(feat,float); dif=feat[:,None,:]-feat[None,:,:]
    return np.rint(np.sqrt(np.sum(dif*dif,axis=2))*10000.0).astype(np.int64)
def ids(n_donors:int,cells_per:int):
    donors=[]; within=[]
    for d in range(n_donors):
        for i in range(cells_per): donors.append(f'D{d:02d}'); within.append(i)
    return np.asarray(donors,object),np.asarray(within,int)
def base_common(n_donors=5,cells_per=35):
    donors,within=ids(n_donors,cells_per); n=len(donors)
    return donors,within,np.asarray(['OP0']*n,object),np.arange(n,dtype=int)
def null_maps(donors,operators,seed):
    rng=np.random.default_rng(seed); n=len(donors); out=[]
    for _ in range(N_NULL):
        m=np.arange(n)
        for d in sorted(set(donors.tolist())):
            for o in sorted(set(operators.tolist())):
                idx=np.where((donors==d)&(operators==o))[0]; p=idx[rng.permutation(len(idx))]
                if np.array_equal(p,idx) and len(idx)>1: p=np.roll(p,1)
                m[idx]=p
        out.append(m.tolist())
    return out
def opaque_id(capability:str,seed:int)->str:
    return hashlib.sha256(f'{PACKAGE_ID}|{capability}|{seed}'.encode()).hexdigest()[:16]

def coarse_geometry(seed:int,visibility:float=1.0):
    donors,within,ops,rows=base_common(); rng=np.random.default_rng(seed)
    coarse=(within//8).astype(float); fine=(within%8)/8.0
    latent=np.c_[coarse,fine]; z=np.c_[coarse*5.0,fine*.2]
    x=np.c_[coarse*5.0,rng.normal(0,1.2,len(rows))]
    y=np.c_[coarse*5.0,rng.normal(0,1.2/visibility,len(rows))]
    truth={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'coarse_mesoscale','rare_state':[0]*len(rows),'island_id':[-1]*len(rows)}
    return donors,ops,rows,z,x,y,np.ones(len(rows),bool),np.ones(len(rows),bool),truth

def fine_geometry(seed:int,n_donors=5,cells_per=35):
    donors,within=ids(n_donors,cells_per); n=len(donors); ops=np.asarray(['OP0']*n,object); rows=np.arange(n); rng=np.random.default_rng(seed)
    t=within/(cells_per-1); latent=np.c_[t,np.sin(2*np.pi*t)]
    z=latent+rng.normal(0,.004,latent.shape); x=latent+rng.normal(0,.025,latent.shape); y=latent+rng.normal(0,.025,latent.shape)
    truth={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'fine_recurrent','rare_state':[0]*n,'island_id':[-1]*n}
    return donors,ops,rows,z,x,y,np.ones(n,bool),np.ones(n,bool),truth

def rare_geometry(seed:int,multi=False,donor_restricted=False):
    n_donors=6 if donor_restricted else 5
    donors,within=ids(n_donors,35); n=len(donors); ops=np.asarray(['OP0']*n,object); rows=np.arange(n); rng=np.random.default_rng(seed)
    active=set(range(5)) if donor_restricted else set(range(n_donors)); rare=np.zeros(n,bool); island=np.full(n,-1,int)
    z=np.zeros((n,2)); x=np.zeros((n,2)); y=np.zeros((n,2)); latent=np.zeros((n,2))
    for d in range(n_donors):
        idx=np.where(donors==f'D{d:02d}')[0]; wi=within[idx]
        z[idx]=np.c_[10+wi/4,np.zeros(len(idx))]
        x[idx]=rng.normal([10,0],[2,2],(len(idx),2)); y[idx]=rng.normal([10,0],[2,2],(len(idx),2)); latent[idx]=np.c_[10+wi/4,np.zeros(len(idx))]
        if d not in active: continue
        groups=[idx[0:6],idx[20:26]] if multi else [idx[13:21]]; centers=[-4.0,4.0] if multi else [0.0]
        for gi,(g,c) in enumerate(zip(groups,centers)):
            rare[g]=True; island[g]=gi; local=np.linspace(-.4,.4,len(g)); lat=np.c_[np.full(len(g),c),local]
            latent[g]=lat; z[g]=lat+rng.normal(0,.003,lat.shape); x[g]=lat+rng.normal(0,.018,lat.shape); y[g]=lat+rng.normal(0,.018,lat.shape)
    truth={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'rare_local_islands','rare_state':rare.astype(int).tolist(),'island_id':island.tolist(),'active_donors':sorted(f'D{d:02d}' for d in active),'zero_prevalence_donors':sorted(set(donors.tolist())-set(f'D{d:02d}' for d in active))}
    return donors,ops,rows,z,x,y,rare,np.ones(n,bool),truth

def technical_twin(seed:int):
    donors,within,ops,rows=base_common(); n=len(rows); rng=np.random.default_rng(seed); pseudo=np.zeros(n,bool)
    z=rng.normal(0,2,(n,2)); x=rng.normal(0,2,(n,2)); y=rng.normal(0,2,(n,2))
    for d in range(5):
        idx=np.where(donors==f'D{d:02d}')[0]; g=idx[13:21]; pseudo[g]=True; local=np.linspace(-.4,.4,len(g)); z[g]=np.c_[np.zeros(len(g)),local]+rng.normal(0,.003,(len(g),2))
    truth={'latent_coordinates':rng.normal(0,1,(n,2)).tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'none_target','rare_state':[0]*n,'pseudo_rare':pseudo.astype(int).tolist(),'technical_twin':True}
    return donors,ops,rows,z,x,y,pseudo,np.ones(n,bool),truth

def null_geometry(seed:int):
    donors,within,ops,rows=base_common(); n=len(rows); rng=np.random.default_rng(seed)
    z=rng.normal(0,1,(n,3)); x=rng.normal(0,1,(n,3)); y=rng.normal(0,1,(n,3))
    truth={'latent_coordinates':rng.normal(0,1,(n,2)).tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'none_target','rare_state':[0]*n}
    return donors,ops,rows,z,x,y,np.ones(n,bool),np.ones(n,bool),truth

def underpowered(seed:int):
    donors,within=ids(4,35); n=len(donors); ops=np.asarray(['OP0']*n,object); rows=np.arange(n); rng=np.random.default_rng(seed); t=within/34
    latent=np.c_[t,np.sin(2*np.pi*t)]; z=latent+rng.normal(0,.003,latent.shape); x=latent+rng.normal(0,.02,latent.shape); y=latent+rng.normal(0,.02,latent.shape)
    truth={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'genuine_but_underpowered','rare_state':[0]*n,'underpowered_reason':'only_4_recurring_donors_below_frozen_minimum_5'}
    return donors,ops,rows,z,x,y,np.ones(n,bool),np.ones(n,bool),truth

def challenge(cap:str,seed:int):
    if cap=='REL_BROAD_MESO_POSITIVE': data=coarse_geometry(seed,1.0); source='SYN_A'
    elif cap=='REL_SOURCE_VISIBILITY_STRESS': data=coarse_geometry(10101,.55); source='SYN_B'
    elif cap=='REL_FINE_RECURRENT_POSITIVE': data=fine_geometry(seed); source='SYN_A'
    elif cap=='REL_RARE_LOCAL_ISLAND_POSITIVE': data=rare_geometry(seed); source='SYN_A'
    elif cap=='REL_MULTI_ISLAND_POSITIVE': data=rare_geometry(seed,multi=True); source='SYN_A'
    elif cap=='REL_DONOR_RESTRICTED_POSITIVE': data=rare_geometry(seed,donor_restricted=True); source='SYN_A'
    elif cap=='REL_TECHNICAL_TWIN_NEGATIVE': data=technical_twin(seed); source='SYN_A'
    elif cap=='REL_NULL_NEGATIVE': data=null_geometry(seed); source='SYN_A'
    elif cap=='REL_UNDERPOWERED_POSITIVE': data=underpowered(seed); source='SYN_A'
    else: raise KeyError(cap)
    donors,ops,rows,zf,xf,yf,focal,pool,truth=data
    fit={'source':source,'panel_id':'P0','z_distances':pairwise(zf).tolist(),'x_distances':pairwise(xf).tolist(),'y_distances':pairwise(yf).tolist(),'donor_ids':donors.tolist(),'operator_ids':ops.tolist(),'global_rows':rows.tolist(),'focal_mask':focal.astype(bool).tolist(),'neighbor_pool_mask':pool.astype(bool).tolist(),'null_y_identity_maps':null_maps(donors,ops,seed+9000),'min_focal_anchors_per_donor':1}
    latent=np.asarray(truth['latent_coordinates'],float); truth['biological_distance_matrix_sha256']=sha_obj(pairwise(latent).tolist()); truth['entity_count']=len(rows)
    rare=np.asarray(truth.get('rare_state',[0]*len(rows))); truth['donor_prevalence']={d:float(np.mean(rare[donors==d])) for d in sorted(set(donors.tolist()))}
    return fit,truth

def main(out_dir:str):
    root=Path(out_dir); root.mkdir(parents=True,exist_ok=True); fit_dir=root/'fit_views'; fit_dir.mkdir(exist_ok=True)
    truth={}; fit_records=[]; caps=[]; fit_manifest=[]; capability_ledger=[]
    seeds={cap:316100+i*1009 for i,(cap,_,_) in enumerate(CAPABILITIES)}; seeds['REL_BROAD_MESO_POSITIVE']=10101; seeds['REL_SOURCE_VISIBILITY_STRESS']=10101
    for cap,semantic,expected in CAPABILITIES:
        cid=opaque_id(cap,seeds[cap]); fit,t=challenge(cap,seeds[cap]); fb=canon(fit); fsha=sha_bytes(fb); (fit_dir/f'{cid}.json').write_bytes(fb)
        fit_records.append({'challenge_id':cid,'sha256':fsha}); caps.append({'capability_id':cap,'challenge_id':cid,'semantic_class':semantic})
        fit_manifest.append({'challenge_id':cid,'payload_path':f'fit_views/{cid}.json','sha256':fsha,'row_count':len(fit['donor_ids']),'feature_count':3,'available_metadata_fields':['source','panel_id','donor_ids','operator_ids','global_rows','focal_mask','neighbor_pool_mask'],'donor_count':len(set(fit['donor_ids'])),'source_count':1,'operator_count':len(set(fit['operator_ids'])),'support_summary':{'focal_count':int(sum(fit['focal_mask'])),'neighbor_pool_count':int(sum(fit['neighbor_pool_mask']))}})
        t['biological_relational_truth_present']=semantic in {'POSITIVE_TRUTH','STRESS_TRUTH','UNDERIDENTIFIED_TRUTH'}
        truth[cid]={'capability_id':cap,'semantic_class':semantic,'expected_status':expected,'fit_view_sha256':fsha,'planted_truth':t,'source_visibility':'reduced_observation_quality_same_latent_truth' if cap=='REL_SOURCE_VISIBILITY_STRESS' else 'nominal','technical_or_null_designation':'technical_twin' if cap=='REL_TECHNICAL_TWIN_NEGATIVE' else ('null' if cap=='REL_NULL_NEGATIVE' else 'biological'),'underpowered':cap=='REL_UNDERPOWERED_POSITIVE'}
        capability_ledger.append({'capability_id':cap,'coverage_status':'SATISFIED_NEW_PROSPECTIVE_WORLD','challenge_id':cid,'basis':'historical Stage81A3 broad/fine latent-factor mechanics' if cap in {'REL_BROAD_MESO_POSITIVE','REL_FINE_RECURRENT_POSITIVE'} else ('PR311 rare-biology semantics plus explicit new relational truth' if cap not in {'REL_NULL_NEGATIVE','REL_UNDERPOWERED_POSITIVE'} else 'prospective relational falsifier/support control'),'why_not_existing_world':'Existing frozen assets do not expose an explicit controller-separated C2 relational truth object in the exact PR316 blinded distance interface.'})
    capmap={r['capability_id']:r['challenge_id'] for r in caps}; broad=capmap['REL_BROAD_MESO_POSITIVE']; stress=capmap['REL_SOURCE_VISIBILITY_STRESS']; shared=sha_obj(truth[broad]['planted_truth']['latent_coordinates']); truth[broad]['paired_latent_truth_sha256']=shared; truth[stress]['paired_latent_truth_sha256']=shared
    controller={'schema':'JEPA_TD_RELATIONAL_SYNTHETIC_CONTROLLER_TRUTH_V1','package_id':PACKAGE_ID,'truth':truth}; cb=canon(controller); csha=sha_bytes(cb); (root/'controller_truth.json').write_bytes(cb)
    manifest={'schema':'JEPA_TD_RELATIONAL_SYNTHETIC_CONTENT_MANIFEST_V1','package_id':PACKAGE_ID,'realization_id':sha_obj({'package':PACKAGE_ID,'seeds':seeds})[:24],'generator_contract':{'seed_ledger':seeds,'n_null':N_NULL,'td_outcomes_used_for_tuning':False},'fit_views':fit_records,'controller_truth_sha256':csha,'capabilities':caps,'capability_ledger':capability_ledger}; mb=canon(manifest); package_sha=sha_bytes(mb); (root/'content_manifest.json').write_bytes(mb)
    binding={'schema':PACKAGE_SCHEMA,'package_id':PACKAGE_ID,'package_sha256':package_sha,'controller_truth_sha256':csha,'authority':AUTHORITY,'fit_view_fields':['source','panel_id','z_distances','x_distances','y_distances','donor_ids','operator_ids','global_rows','focal_mask','neighbor_pool_mask','null_y_identity_maps','min_focal_anchors_per_donor'],'fit_views':fit_records,'capabilities':caps}; (root/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json').write_bytes(canon(binding))
    (root/'fit_view_manifest.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_FIT_VIEW_MANIFEST_V1','package_id':PACKAGE_ID,'challenges':fit_manifest})); (root/'capability_ledger.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_CAPABILITY_LEDGER_V1','package_id':PACKAGE_ID,'capabilities':capability_ledger}))
    adapter={r['challenge_id']:{'authenticated_fit_view_sha256':r['sha256'],'payload_path':f"fit_views/{r['challenge_id']}.json"} for r in fit_records}; (root/'TD_RELATIONAL_ADAPTER_PAYLOAD_INDEX_V1.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_ADAPTER_PAYLOAD_INDEX_V1','package_id':PACKAGE_ID,'payloads':adapter}))
    return root

if __name__=='__main__':
    import sys
    main(sys.argv[1])
