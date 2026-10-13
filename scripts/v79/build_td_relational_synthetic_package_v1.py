from __future__ import annotations
import hashlib, json, math
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
AUTHORITY={'synthetic_world_generation_authorized':False,'synthetic_world_regeneration_authorized':False,
 'qualification_model_fitting_authorized':False,'target_selection_authorized':False,
 'td60_authorized':False,'stage4_authorized':False,'training_authorized':False}

def canon(x:Any)->bytes:
    return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def sha_bytes(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def sha_obj(x:Any)->str:return sha_bytes(canon(x))
def pairwise(f):
    a=np.asarray(f,float); d=a[:,None,:]-a[None,:,:]
    return np.rint(np.sqrt(np.sum(d*d,axis=2))*10000).astype(np.int64)
def ids(nd:int,nc:int=35):
    return np.asarray([f'D{d:02d}' for d in range(nd) for _ in range(nc)],object),np.tile(np.arange(nc),nd)
def common(nd=5,nc=35):
    d,w=ids(nd,nc); n=len(d); return d,w,np.asarray(['OP0']*n,object),np.arange(n,dtype=int)
def permuted_unit(w,mul,shift):
    n=int(w.max())+1; return ((w*mul+shift)%n)/(n-1)
def null_maps(donors,ops,seed):
    n=len(donors); out=[]; allowed=[2,3,4,6,8,9,11,12,13,16,17,18,19,22,23,24,26,27,29,31,32,33,34]
    for q in range(N_NULL):
        m=np.arange(n)
        for dn in sorted(set(donors.tolist())):
            for op in sorted(set(ops.tolist())):
                idx=np.where((donors==dn)&(ops==op))[0]; k=len(idx)
                choices=[a for a in allowed if math.gcd(a,k)==1] or [1]
                a=choices[(q+seed)%len(choices)]; b=(q*7+seed)%k
                local=(a*np.arange(k)+b)%k
                if np.array_equal(local,np.arange(k)): local=np.roll(local,1)
                m[idx]=idx[local]
        out.append(m.tolist())
    return out
def opaque(cap,seed):return hashlib.sha256(f'{PACKAGE_ID}|{cap}|{seed}'.encode()).hexdigest()[:16]

def coarse(seed,visibility=1.0):
    d,w,o,r=common(); c=(w//7).astype(float); fine=(w%7)/7
    latent=np.c_[c,fine]; z=np.c_[c*8,fine*.1]
    x=np.c_[c*8,permuted_unit(w,3,1)]; y=np.c_[c*8,permuted_unit(w,11,2)/visibility]
    t={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'coarse_mesoscale','rare_state':[0]*len(r),'island_id':[-1]*len(r)}
    return d,o,r,z,x,y,np.ones(len(r),bool),np.ones(len(r),bool),t

def fine(seed,nd=5):
    d,w,o,r=common(nd); u=w/34; latent=np.c_[u,np.sin(2*np.pi*u)]
    z=latent; x=latent+np.c_[((w%3)-1)*.002,((w%5)-2)*.001]; y=latent+np.c_[((w%5)-2)*.001,((w%3)-1)*.002]
    t={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'fine_recurrent','rare_state':[0]*len(r),'island_id':[-1]*len(r)}
    return d,o,r,z,x,y,np.ones(len(r),bool),np.ones(len(r),bool),t

def rare(seed,multi=False,restricted=False):
    nd=6 if restricted else 5; d,w,o,r=common(nd); n=len(r); active=set(range(5)) if restricted else set(range(nd))
    rare=np.zeros(n,bool); island=np.full(n,-1,int)
    z=np.c_[10+w/3,np.zeros(n)]; x=np.c_[10+permuted_unit(w,3,1)*8,np.zeros(n)]; y=np.c_[10+permuted_unit(w,11,2)*8,np.ones(n)]; latent=np.c_[10+w/3,np.zeros(n)]
    for k in range(nd):
        idx=np.where(d==f'D{k:02d}')[0]
        if k not in active:continue
        groups=[idx[:6],idx[20:26]] if multi else [idx[13:21]]; centers=[-4.,4.] if multi else [0.]
        for gi,(g,c) in enumerate(zip(groups,centers)):
            rare[g]=True; island[g]=gi; local=np.linspace(-.4,.4,len(g)); lat=np.c_[np.full(len(g),c),local]
            latent[g]=lat; z[g]=lat; x[g]=lat+np.c_[np.zeros(len(g)),((np.arange(len(g))%2)*2-1)*.001]; y[g]=lat+np.c_[np.zeros(len(g)),((np.arange(len(g))%3)-1)*.001]
    t={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'rare_local_islands','rare_state':rare.astype(int).tolist(),'island_id':island.tolist(),'active_donors':sorted(f'D{k:02d}' for k in active),'zero_prevalence_donors':sorted(set(d.tolist())-set(f'D{k:02d}' for k in active))}
    return d,o,r,z,x,y,rare,np.ones(n,bool),t

def technical(seed):
    d,w,o,r=common(); n=len(r); pseudo=np.zeros(n,bool)
    z=np.c_[permuted_unit(w,17,3)*10,np.zeros(n)]; x=np.c_[permuted_unit(w,3,1)*10,np.zeros(n)]; y=np.c_[permuted_unit(w,11,2)*10,np.ones(n)]
    for k in range(5):
        idx=np.where(d==f'D{k:02d}')[0]; g=idx[13:21]; pseudo[g]=True; z[g]=np.c_[np.zeros(len(g)),np.linspace(-.4,.4,len(g))]
    latent=np.c_[permuted_unit(w,19,4),np.zeros(n)]
    t={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'none_target','rare_state':[0]*n,'pseudo_rare':pseudo.astype(int).tolist(),'technical_twin':True}
    return d,o,r,z,x,y,pseudo,np.ones(n,bool),t

def null(seed):
    d,w,o,r=common(); n=len(r); z=np.c_[permuted_unit(w,17,3)*10,np.zeros(n)]; x=np.c_[permuted_unit(w,3,1)*10,np.zeros(n)]; y=np.c_[permuted_unit(w,11,2)*10,np.ones(n)]; latent=np.c_[permuted_unit(w,19,4),np.zeros(n)]
    t={'latent_coordinates':latent.tolist(),'relation_metric':'euclidean_on_latent_coordinates','relation_scope':'none_target','rare_state':[0]*n}
    return d,o,r,z,x,y,np.ones(n,bool),np.ones(n,bool),t

def underpowered(seed):return fine(seed,nd=4)

def make(cap,seed):
    if cap=='REL_BROAD_MESO_POSITIVE': data=coarse(seed,1.0); source='SYN_A'
    elif cap=='REL_SOURCE_VISIBILITY_STRESS': data=coarse(10101,.55); source='SYN_B'
    elif cap=='REL_FINE_RECURRENT_POSITIVE': data=fine(seed); source='SYN_A'
    elif cap=='REL_RARE_LOCAL_ISLAND_POSITIVE': data=rare(seed); source='SYN_A'
    elif cap=='REL_MULTI_ISLAND_POSITIVE': data=rare(seed,multi=True); source='SYN_A'
    elif cap=='REL_DONOR_RESTRICTED_POSITIVE': data=rare(seed,restricted=True); source='SYN_A'
    elif cap=='REL_TECHNICAL_TWIN_NEGATIVE': data=technical(seed); source='SYN_A'
    elif cap=='REL_NULL_NEGATIVE': data=null(seed); source='SYN_A'
    elif cap=='REL_UNDERPOWERED_POSITIVE': data=underpowered(seed); source='SYN_A'
    else:raise KeyError(cap)
    d,o,r,z,x,y,focal,pool,t=data
    fit={'source':source,'panel_id':'P0','z_distances':pairwise(z).tolist(),'x_distances':pairwise(x).tolist(),'y_distances':pairwise(y).tolist(),'donor_ids':d.tolist(),'operator_ids':o.tolist(),'global_rows':r.tolist(),'focal_mask':focal.astype(bool).tolist(),'neighbor_pool_mask':pool.astype(bool).tolist(),'null_y_identity_maps':null_maps(d,o,seed+9000),'min_focal_anchors_per_donor':1}
    lat=np.asarray(t['latent_coordinates'],float); t['biological_distance_matrix_sha256']=sha_obj(pairwise(lat).tolist()); t['entity_count']=len(r); rr=np.asarray(t.get('rare_state',[0]*len(r))); t['donor_prevalence']={dn:float(np.mean(rr[d==dn])) for dn in sorted(set(d.tolist()))}
    return fit,t

def main(out_dir:str):
    root=Path(out_dir); root.mkdir(parents=True,exist_ok=True); fd=root/'fit_views'; fd.mkdir(exist_ok=True)
    truth={}; fits=[]; caps=[]; fm=[]; ledger=[]; seeds={cap:316100+i*1009 for i,(cap,_,_) in enumerate(CAPABILITIES)}; seeds['REL_BROAD_MESO_POSITIVE']=10101; seeds['REL_SOURCE_VISIBILITY_STRESS']=10101
    for cap,semantic,expected in CAPABILITIES:
        cid=opaque(cap,seeds[cap]); fit,t=make(cap,seeds[cap]); raw=canon(fit); fsha=sha_bytes(raw); (fd/f'{cid}.json').write_bytes(raw)
        fits.append({'challenge_id':cid,'sha256':fsha}); caps.append({'capability_id':cap,'challenge_id':cid,'semantic_class':semantic})
        fm.append({'challenge_id':cid,'payload_path':f'fit_views/{cid}.json','sha256':fsha,'row_count':len(fit['donor_ids']),'feature_count':3,'available_metadata_fields':['source','panel_id','donor_ids','operator_ids','global_rows','focal_mask','neighbor_pool_mask'],'donor_count':len(set(fit['donor_ids'])),'source_count':1,'operator_count':len(set(fit['operator_ids'])),'support_summary':{'focal_count':int(sum(fit['focal_mask'])),'neighbor_pool_count':int(sum(fit['neighbor_pool_mask']))}})
        t['biological_relational_truth_present']=semantic in {'POSITIVE_TRUTH','STRESS_TRUTH','UNDERIDENTIFIED_TRUTH'}
        if cap=='REL_UNDERPOWERED_POSITIVE':t['underpowered_reason']='only_4_recurring_donors_below_frozen_minimum_5'
        truth[cid]={'capability_id':cap,'semantic_class':semantic,'expected_status':expected,'fit_view_sha256':fsha,'planted_truth':t,'source_visibility':'reduced_observation_quality_same_latent_truth' if cap=='REL_SOURCE_VISIBILITY_STRESS' else 'nominal','technical_or_null_designation':'technical_twin' if cap=='REL_TECHNICAL_TWIN_NEGATIVE' else ('null' if cap=='REL_NULL_NEGATIVE' else 'biological'),'underpowered':cap=='REL_UNDERPOWERED_POSITIVE'}
        ledger.append({'capability_id':cap,'coverage_status':'SATISFIED_NEW_PROSPECTIVE_WORLD','challenge_id':cid,'basis':'historical Stage81A3 broad/fine latent-factor mechanics' if cap in {'REL_BROAD_MESO_POSITIVE','REL_FINE_RECURRENT_POSITIVE'} else ('PR311 rare-biology semantics plus explicit new relational truth' if cap not in {'REL_NULL_NEGATIVE','REL_UNDERPOWERED_POSITIVE'} else 'prospective relational falsifier/support control'),'why_not_existing_world':'Existing frozen assets do not expose an explicit controller-separated C2 relational truth object in the exact PR316 blinded distance interface.'})
    cm={r['capability_id']:r['challenge_id'] for r in caps}; broad=cm['REL_BROAD_MESO_POSITIVE']; stress=cm['REL_SOURCE_VISIBILITY_STRESS']; shared=sha_obj(truth[broad]['planted_truth']['latent_coordinates']); truth[broad]['paired_latent_truth_sha256']=shared; truth[stress]['paired_latent_truth_sha256']=shared
    controller={'schema':'JEPA_TD_RELATIONAL_SYNTHETIC_CONTROLLER_TRUTH_V1','package_id':PACKAGE_ID,'truth':truth}; cb=canon(controller); csha=sha_bytes(cb); (root/'controller_truth.json').write_bytes(cb)
    manifest={'schema':'JEPA_TD_RELATIONAL_SYNTHETIC_CONTENT_MANIFEST_V1','package_id':PACKAGE_ID,'realization_id':sha_obj({'package':PACKAGE_ID,'seeds':seeds})[:24],'generator_contract':{'seed_ledger':seeds,'n_null':N_NULL,'td_outcomes_used_for_tuning':False},'fit_views':fits,'controller_truth_sha256':csha,'capabilities':caps,'capability_ledger':ledger}; mb=canon(manifest); psha=sha_bytes(mb); (root/'content_manifest.json').write_bytes(mb)
    binding={'schema':PACKAGE_SCHEMA,'package_id':PACKAGE_ID,'package_sha256':psha,'controller_truth_sha256':csha,'authority':AUTHORITY,'fit_view_fields':['source','panel_id','z_distances','x_distances','y_distances','donor_ids','operator_ids','global_rows','focal_mask','neighbor_pool_mask','null_y_identity_maps','min_focal_anchors_per_donor'],'fit_views':fits,'capabilities':caps}; (root/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json').write_bytes(canon(binding))
    (root/'fit_view_manifest.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_FIT_VIEW_MANIFEST_V1','package_id':PACKAGE_ID,'challenges':fm})); (root/'capability_ledger.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_CAPABILITY_LEDGER_V1','package_id':PACKAGE_ID,'capabilities':ledger})); adapter={r['challenge_id']:{'authenticated_fit_view_sha256':r['sha256'],'payload_path':f"fit_views/{r['challenge_id']}.json"} for r in fits}; (root/'TD_RELATIONAL_ADAPTER_PAYLOAD_INDEX_V1.json').write_bytes(canon({'schema':'JEPA_TD_RELATIONAL_ADAPTER_PAYLOAD_INDEX_V1','package_id':PACKAGE_ID,'payloads':adapter})); return root

if __name__=='__main__':
    import sys
    main(sys.argv[1])
