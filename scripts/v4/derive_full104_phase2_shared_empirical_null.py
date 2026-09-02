#!/usr/bin/env python3
"""Deterministic empirical matched-null qualification for a FULL104 shared level.

The expensive view-shuffle statistic is evaluated exactly on the observed-basis
coordinates using FFT circular correlations.  Compact order+offset maps reproduce
every expanded cell/view permutation without storing redundant giant tables.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, time
from pathlib import Path
import numpy as np
import pandas as pd

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def atomic_json(p:Path,v)->None:
 t=p.with_suffix(p.suffix+'.tmp'); t.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8'); os.replace(t,p)
def seed_from(key:str,*parts)->int:
 text='|'.join([key,*map(str,parts)]).encode(); return int.from_bytes(hashlib.sha256(text).digest()[:8],'little')
def paired_prefix_overlap(order_a,order_b,rank):
 a=np.empty(rank,np.int32); b=np.empty(rank,np.int32); a[order_a]=np.arange(rank); b[order_b]=np.arange(rank)
 return np.asarray([np.count_nonzero((a<d)&(b<d))/d for d in range(1,rank+1)],np.float64)
def coordinate_diagonals(mean_rows,within_rows,basis):
 mu=basis['mean']; w=basis['components']; centered=mean_rows-mu
 out=np.empty((len(mean_rows),w.shape[1]),np.float64)
 for d in range(len(mean_rows)):
  m=mean_rows[d]; correction=within_rows[d]-np.outer(m,mu)-np.outer(mu,m)+np.outer(mu,mu)
  out[d]=np.einsum('ik,ij,jk->k',w,correction,w,optimize=True)
 return centered@w,out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--amendment',required=True); ap.add_argument('--matrix',required=True); ap.add_argument('--analytic',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 started=time.time(); amendment=Path(a.amendment).resolve(); matrix=Path(a.matrix).resolve(); analytic=Path(a.analytic).resolve(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
 procedure=json.loads((amendment/'PHASE2_SHARED_PROCEDURE_AMENDMENT_V2.json').read_text()); ma=json.loads((matrix/'PHASE2_FEATURE_MATRIX_AUDIT.json').read_text())
 level=int(ma.get('sample_level',0)); reps=int(procedure['empirical_matched_null']['replicates'])
 if procedure['status']!='FROZEN_PROSPECTIVELY_BEFORE_LEVEL1_SHARED_GEOMETRY' or ma['status']!='PASS_PHASE2_FEATURE_MATRIX_ASSEMBLED': raise RuntimeError('input gate missing')
 base=matrix.parent; aa=base/f'SHARED_LEVEL{level}_ANALYTIC_DIAGNOSTIC_MANIFEST_SHA256.txt'; am=analytic/f'SHARED_LEVEL{level}_ANALYTIC_DIAGNOSTIC_MANIFEST.csv'
 if not aa.is_file() or sha(am)!=aa.read_text().strip(): raise RuntimeError('analytic diagnostic anchor mismatch')
 rows=pd.read_csv(matrix/'PHASE2_FEATURE_ROWS.csv',dtype={'donor_id':str}); donors=sorted(rows.donor_id.unique()); donor_ix={x:i for i,x in enumerate(donors)}
 fold_path=base/'preexpression_freeze/PHASE2_DONOR_FOLDS.csv'; folds=pd.read_csv(fold_path,dtype={'donor_id':str}).set_index('donor_id'); donor_folds=np.asarray([int(folds.loc[d,'outer_fold']) for d in donors]); donor_sources=np.asarray([rows.loc[rows.donor_id.eq(d),'source'].iloc[0] for d in donors])
 rng=json.loads((base/'preexpression_freeze/PHASE2_RNG_KEYS.json').read_text())['keys']; null_key=rng['matched_null']; boot_key=rng['donor_bootstrap']
 rank=np.load(analytic/'SHARED_OVERCOMPLETE_BASIS_A.npz')['components'].shape[1]; dims=np.arange(1,rank+1)
 groups=[]
 for (donor,op),g in rows.groupby(['donor_id','operator_index'],sort=True): groups.append((donor_ix[donor],int(op),g.index.to_numpy(np.int64)))
 strata=pd.DataFrame([{'stratum_index':i,'donor_index':d,'donor_id':donors[d],'operator_index':op,'cells':len(ix),'permutation_role':'UNSHUFFLABLE_SINGLETON' if len(ix)==1 else ('LIMITED_N_LT_4' if len(ix)<4 else 'FULL_PAIRWISE_DISTINCT')} for i,(d,op,ix) in enumerate(groups)])
 strata.to_csv(out/'SHARED_EMPIRICAL_NULL_STRATA.csv',index=False,lineterminator='\n')
 cell_counts=np.bincount(rows.donor_id.map(donor_ix),minlength=len(donors)).astype(np.float64)
 singleton_cells=np.zeros(len(donors)); limited_cells=np.zeros(len(donors))
 for d,op,ix in groups:
  if len(ix)==1: singleton_cells[d]+=1
  if len(ix)<4: limited_cells[d]+=len(ix)
 map_payload={}
 null_store={}; calibration=[]; held_tables=[]
 for sketch_i,label in enumerate('AB'):
  basis_file=np.load(analytic/f'SHARED_OVERCOMPLETE_BASIS_{label}.npz'); basis={k:basis_file[k] for k in ('mean','scale','components','eigenvalues')}
  views=np.load(matrix/f'{label}_views.npy',mmap_mode='r'); means=np.load(analytic/f'sufficient_statistics/{label}_mean.npy',mmap_mode='r'); within=np.load(analytic/f'sufficient_statistics/{label}_within.npy',mmap_mode='r')
  donor_mean,donor_within_diag=coordinate_diagonals(means,within,basis)
  null_cross_sum=np.zeros((reps,len(donors),rank),np.float64); orders=[]; order_indptr=[0]; offsets=np.zeros((reps,len(groups),4),np.uint32)
  for s,(d,op,ix) in enumerate(groups):
   n=len(ix); order=np.random.default_rng(seed_from(null_key,level,label,s,'order')).permutation(n).astype(np.int32); orders.append(order); order_indptr.append(order_indptr[-1]+n)
   for r in range(reps):
    gen=np.random.default_rng(seed_from(null_key,level,label,s,r,'offset'))
    if n==1: off=np.zeros(4,np.uint32)
    elif n>=4: off=gen.choice(n,size=4,replace=False).astype(np.uint32)
    else:
     start=int(gen.integers(n)); off=((start+np.arange(4))%n).astype(np.uint32)
    offsets[r,s]=off
   score=np.empty((n,4,rank),np.float64)
   for v in range(4): score[:,v]=(np.asarray(views[ix,v],np.float64)-basis['mean'])@basis['components']
   score=score[order]
   fft=[np.fft.rfft(score[:,v,:],axis=0) for v in range(4)]
   for v in range(4):
    for w in range(v+1,4):
     corr=np.fft.irfft(np.conj(fft[v])*fft[w],n=n,axis=0)
     delta=(offsets[:,s,w].astype(np.int64)-offsets[:,s,v].astype(np.int64))%n
     null_cross_sum[:,d,:]+=2.0*corr[delta]
   if (s+1)%100==0: print(f'empirical-null sketch={label} strata={s+1}/{len(groups)}',flush=True)
  null_between=null_cross_sum/(cell_counts[None,:,None]*12.0)
  empirical_signal=np.sort(null_between.mean(axis=1),axis=1)[:,::-1]
  null_stability=np.empty((reps,rank),np.float64)
  for r in range(reps):
   full_order=np.argsort(null_between[r].mean(axis=0))[::-1]
   sampled=np.concatenate([np.random.default_rng(seed_from(boot_key,level,label,r,src)).choice(np.flatnonzero(donor_sources==src),size=np.count_nonzero(donor_sources==src),replace=True) for src in sorted(set(donor_sources))])
   sample_order=np.argsort(null_between[r,sampled].mean(axis=0))[::-1]
   null_stability[r]=paired_prefix_overlap(full_order,sample_order,rank)
  null_held=np.empty((reps,len(donors),rank),np.float32)
  for r in range(reps):
   for fold in sorted(set(donor_folds)):
    tr=np.flatnonzero(donor_folds!=fold); he=np.flatnonzero(donor_folds==fold)
    t2=donor_within_diag[tr].mean(axis=0); pt=null_between[r,tr].mean(axis=0); p2=(t2+2*pt)/3; slope=pt/np.maximum(p2,np.finfo(float).eps)
    ht2=donor_within_diag[he]; hpt=null_between[r,he]; hp2=(ht2+2*hpt)/3
    sse=ht2-2*slope*hpt+slope*slope*hp2; var=np.maximum(ht2-donor_mean[he]**2,0)
    null_held[r,he]=1-np.cumsum(sse,axis=1)/np.maximum(np.cumsum(var,axis=1),np.finfo(float).eps)
  order_concat=np.concatenate(orders).astype(np.int32); order_indptr=np.asarray(order_indptr,np.int64)
  map_payload[f'{label}_order_concat']=order_concat; map_payload[f'{label}_order_indptr']=order_indptr; map_payload[f'{label}_offsets']=offsets
  np.savez_compressed(out/f'SHARED_EMPIRICAL_NULL_{label}.npz',signal=empirical_signal,subspace_stability=null_stability,held_donor_predictability=null_held,donor_between_diagonal=null_between.astype(np.float32),dimensions=dims)
  null_store[label]={'signal':empirical_signal,'stability':null_stability,'held':null_held}
  held_tables.append(pd.DataFrame({'sketch':label,'donor_id':np.repeat(donors,rank),'dimension':np.tile(dims,len(donors)),'empirical_null_predictability_mean':null_held.mean(axis=0).ravel(),'empirical_null_predictability_se':(null_held.std(axis=0,ddof=1)/math.sqrt(reps)).ravel()}))
 np.savez_compressed(out/'SHARED_EMPIRICAL_NULL_MAPS.npz',**map_payload)
 held_null=pd.concat(held_tables,ignore_index=True); held_null.to_csv(out/'SHARED_EMPIRICAL_NULL_HELDOUT.csv',index=False,lineterminator='\n')
 observed_held=pd.read_csv(analytic/'SHARED_DONOR_HELDOUT_PREDICTABILITY.csv'); observed_held=observed_held[observed_held.dimension.le(rank)]
 analytic_calibration=pd.read_csv(analytic/'TEACHER_DIMENSION_CALIBRATION_SHARED.csv')
 sketch_agreement=analytic_calibration.groupby('dimension').independent_sketch_subspace_agreement.first().to_dict()
 observed_by={(x.sketch,int(x.dimension)):x for x in observed_held.groupby(['sketch','dimension']).heldout_predictability.agg(['mean','std','count']).reset_index().itertuples(index=False)}
 for label in 'AB':
  boot=np.load(analytic/f'SHARED_BOOTSTRAP_{label}.npz'); oe=boot['observed_eigenvalues']; ost=boot['observed_stability']; ns=null_store[label]
  for j,d in enumerate(dims):
   om=oe[:,:d].mean(axis=0); ose=oe[:,:d].std(axis=0,ddof=1)/math.sqrt(len(oe)); nm=ns['signal'][:,:d].mean(axis=0); nse=ns['signal'][:,:d].std(axis=0,ddof=1)/math.sqrt(reps)
   signal=bool(np.all(om-ose>nm+nse)); osm=float(ost[:,j].mean()); osse=float(ost[:,j].std(ddof=1)/math.sqrt(len(ost))); nsm=float(ns['stability'][:,j].mean()); nsse=float(ns['stability'][:,j].std(ddof=1)/math.sqrt(reps)); stability=osm-osse>nsm+nsse
   ob=observed_by[(label,int(d))]; opm=float(ob.mean); opse=float(ob.std/math.sqrt(ob.count)); npm=float(ns['held'][:,:,j].mean()); donor_rep=ns['held'][:,:,j].mean(axis=0); npse=float(donor_rep.std(ddof=1)/math.sqrt(len(donor_rep))); predict=opm-opse>npm+npse
   calibration.append({'sample_level':level,'sketch':label,'dimension':int(d),'observed_cumulative_generalized_signal':float(om.sum()),'empirical_null_cumulative_signal_mean':float(nm.sum()),'empirical_null_cumulative_signal_se':float(np.sqrt(np.square(nse).sum())),'observed_signal_minimum_margin':float(np.min((om-ose)-(nm+nse))),'empirical_null_signal_supported':signal,'observed_subspace_stability_mean':osm,'observed_subspace_stability_se':osse,'empirical_null_subspace_stability_mean':nsm,'empirical_null_subspace_stability_se':nsse,'empirical_null_stability_supported':bool(stability),'held_donor_predictability_mean':opm,'held_donor_predictability_se':opse,'empirical_null_predictability_mean':npm,'empirical_null_predictability_donor_se':npse,'independent_sketch_A_B_subspace_agreement':float(sketch_agreement[int(d)]),'empirical_null_predictability_supported':bool(predict),'jointly_supported':bool(signal and stability and predict),'authority_tag':'DERIVE_ON_104_FIT'})
 cal=pd.DataFrame(calibration); cal.to_csv(out/'TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL.csv',index=False,lineterminator='\n')
 common=cal.groupby('dimension').jointly_supported.all(); supported=[int(d) for d in dims if bool(common.loc[d])]
 paired=observed_held.pivot_table(index=['donor_index','dimension'],columns='sketch',values='heldout_predictability').reset_index(); paired['paired_predictability']=paired[['A','B']].mean(axis=1)
 curve=paired.groupby('dimension').paired_predictability.agg(['mean','std','count']); curve['se']=curve['std']/np.sqrt(curve['count'])
 candidate=None; interval=[]
 if supported:
  valid=curve.loc[supported]; best=int(valid['mean'].idxmax()); threshold=float(valid.loc[best,'mean']-valid.loc[best,'se']); interval=[int(x) for x in valid[valid['mean']>=threshold].index]; candidate=min(interval)
 reason='NO_EMPIRICALLY_SUPPORTED_PREFIX' if candidate is None else ('EMPIRICAL_PREFIX_REACHES_SEARCH_BOUNDARY' if rank in supported else 'EMPIRICAL_CANDIDATE_REQUIRES_SUCCESSIVE_LEVEL_STABILITY')
 status='ADVANCE_LADDER'
 singleton_row=float(singleton_cells.sum()/cell_counts.sum()); singleton_donor=float(np.mean(singleton_cells/cell_counts)); limited_row=float(limited_cells.sum()/cell_counts.sum()); limited_donor=float(np.mean(limited_cells/cell_counts))
 maps=out/'SHARED_EMPIRICAL_NULL_MAPS.npz'; null_manifest=out/'SHARED_NULL_MANIFEST.csv'
 null_files=[maps,out/'SHARED_EMPIRICAL_NULL_A.npz',out/'SHARED_EMPIRICAL_NULL_B.npz',out/'SHARED_EMPIRICAL_NULL_STRATA.csv',out/'SHARED_EMPIRICAL_NULL_HELDOUT.csv']
 pd.DataFrame([{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in null_files]).to_csv(null_manifest,index=False,lineterminator='\n')
 result={'schema':'full104-shared-empirical-level-selection-v1','status':status,'reason':reason,'sample_level':level,'cells':len(rows),'donors':len(donors),'operators':int(rows.operator_index.nunique()),'candidate_D_shared':candidate,'one_se_dimension_interval':[min(interval),max(interval)] if interval else None,'search_rank':rank,'search_boundary_supported':rank in supported,'next_ladder_level_required':True,'terminal_scientific_decision_permitted':False,'analytic_null_role':'DIAGNOSTIC_ONLY','empirical_null_role':'SELECTING','empirical_null_replicates':reps,'ordinary_row_weighted_singleton_fraction':singleton_row,'donor_equal_singleton_fraction':singleton_donor,'ordinary_row_weighted_n_lt_4_fraction':limited_row,'donor_equal_n_lt_4_fraction':limited_donor,'independent_sketches_required':True,'sketches_are_paired_technical_replicates_not_biological_N':True,'input_hashes':{'procedure_amendment':sha(amendment/'PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv'),'matrix_manifest':sha(matrix/'PHASE2_FEATURE_MATRIX_MANIFEST.csv'),'analytic_manifest':sha(am),'folds':sha(fold_path)},'calibration_sha256':sha(out/'TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL.csv'),'null_manifest_sha256':sha(null_manifest),'no_private_or_protected_or_training_work':True}
 atomic_json(out/'SHARED_DIMENSION_SELECTION_LEVEL.json',result)
 package=out/f'SHARED_LEVEL{level}_EMPIRICAL_PACKAGE_MANIFEST.csv'; files=null_files+[null_manifest,out/'TEACHER_DIMENSION_CALIBRATION_SHARED_EMPIRICAL.csv',out/'SHARED_DIMENSION_SELECTION_LEVEL.json',Path(__file__)]
 pd.DataFrame([{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]).to_csv(package,index=False,lineterminator='\n'); (out.parent/f'SHARED_LEVEL{level}_EMPIRICAL_PACKAGE_MANIFEST_SHA256.txt').write_text(sha(package)+'\n',encoding='ascii')
 print(json.dumps({**result,'package_manifest_sha256':sha(package),'wall_seconds':time.time()-started},indent=2))
if __name__=='__main__': main()
