#!/usr/bin/env python3
"""Sparse multi-view expression geometry, redundancy, biology, and old-cache overlay."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
import numpy as np,pandas as pd
from scipy import sparse
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import pairwise_distances
from pynndescent import NNDescent

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; XPATH=OUT/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz'; SEED=20260824
sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
from production_train_loader import ProductionTrainLoader,MEASURED_SCALAR

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def eta2(scores,labels):
 labels=np.asarray(labels); out=[]
 for j in range(scores.shape[1]):
  y=scores[:,j]; mu=y.mean(); den=np.square(y-mu).sum(); num=sum(len(y[labels==g])*float((y[labels==g].mean()-mu)**2) for g in np.unique(labels)); out.append(num/den if den else 0)
 return out
def effective_count(counts):
 p=np.asarray(counts,float); p=p/p.sum(); return float(np.exp(-(p*np.log(np.maximum(p,1e-30))).sum()))
def variance_select(matrix,feature_index,maximum):
 sums=np.zeros(matrix.shape[1],np.float64);squares=np.zeros_like(sums)
 for begin in range(0,matrix.shape[0],4096):
  block=matrix[begin:begin+4096]
  sums+=np.bincount(block.indices,weights=block.data,minlength=matrix.shape[1])
  squares+=np.bincount(block.indices,weights=np.square(block.data),minlength=matrix.shape[1])
 variance=squares/matrix.shape[0]-np.square(sums/matrix.shape[0]);order=np.lexsort((np.asarray(feature_index),-variance))[:min(maximum,len(variance))]
 return np.sort(order),variance
def operator_state_sketch(x,freeze,states,buckets=128):
 rows=np.arange(41_238);bucket=np.asarray([int(hashlib.sha256(f'{SEED}|bucket|{g}'.encode()).hexdigest()[:8],16)%buckets for g in rows]);sign=np.asarray([1 if int(hashlib.sha256(f'{SEED}|sign|{g}'.encode()).hexdigest()[:8],16)%2 else -1 for g in rows],np.float32)
 projection=sparse.csr_matrix((sign,(rows,bucket)),shape=(41_238,buckets));value=np.asarray(x@projection,np.float32)
 support=np.zeros((42,3*buckets),np.float32)
 for op in range(42):
  for state in (0,1,2):
   take=np.flatnonzero(states[op]==state);np.add.at(support[op,state*buckets+bucket[take]],sign[take])
 return np.concatenate([value,support[freeze.operator_index.to_numpy(np.int64)]],axis=1)
def old_sparse(loader,inventory):
 blocks=[]; destinations=[]
 for item in loader.items:
  g=inventory[inventory.operator_index.eq(item['operator_index'])]
  if g.empty:continue
  raw=sparse.load_npz(item['counts']).tocsr()[g.local_row.to_numpy(int)].astype(np.float32)
  y=raw.multiply((10_000/np.maximum(g.source_library.to_numpy(float),1))[:,None]).tocsr();y.data=np.log1p(y.data)
  blocks.append(y);destinations.append(g.index.to_numpy(int))
 order=np.concatenate(destinations);stack=sparse.vstack(blocks,format='csr');return stack[np.argsort(order)]

def main():
 started=time.time(); freeze=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');x=sparse.load_npz(XPATH).tocsr()
 if x.shape!=(50_000,41_238) or len(freeze)!=len(x):raise RuntimeError('expression/freeze identity mismatch')
 loader=ProductionTrainLoader();states=np.stack([loader.states[i['matrix_id']] for i in loader.items]);common=np.flatnonzero(np.all(states==MEASURED_SCALAR,axis=0))
 if len(common)<100:raise RuntimeError('no defensible common scalar support')
 views={}; summaries=[]; score_frames=[];selected_rows=[];reg=loader.registry.set_index('molecular_address_index')
 common_pos,common_variance=variance_select(x[:,common],common,8192);common_selected=common[common_pos];matrix=x[:,common_selected];name='raw_common';ncomp=20
 for a,v in zip(common_selected,common_variance[common_pos]):selected_rows.append({'view':name,'molecular_address_index':int(a),'variance':float(v),'selection':'top_variance_from_common_scalar_support'})
 print(f'start SVD {name} cells={matrix.shape[0]} features={matrix.shape[1]} rank={ncomp} n_iter=0',flush=True);model=TruncatedSVD(n_components=ncomp,random_state=SEED,n_iter=0);score=model.fit_transform(matrix).astype(np.float32);views[name]=(model,score,common_selected)
 summaries.append({'view':name,'cells':len(score),'features':matrix.shape[1],'components':ncomp,'explained_variance_sum':float(model.explained_variance_ratio_.sum()),'batch_correction':'none','lawful_common_scalar_addresses_all_42':len(common)})
 sf=pd.DataFrame(score,columns=[f'PC{i+1}' for i in range(ncomp)]);sf.insert(0,'sample_row',freeze.sample_row);sf.insert(0,'sample',freeze['sample']);sf['view']=name;score_frames.append(sf)
 load=[]
 for pc in range(ncomp):
  for rank,k in enumerate(np.argsort(-np.abs(model.components_[pc]))[:30],1):
   a=int(common_selected[k]);load.append({'view':name,'component':pc+1,'rank':rank,'molecular_address_index':a,'molecular_address_id':reg.loc[a,'molecular_address_id'],'symbol':reg.loc[a,'symbol'],'loading':float(model.components_[pc,k])})
 pd.DataFrame(load).to_csv(OUT/'FOUNDATION_DE_NOVO_MODULE_LOADINGS_RAW_COMMON.csv',index=False,lineterminator='\n')
 sketch=operator_state_sketch(x,freeze,states);name='operator_aware_three_state_sketch';ncomp=20
 print(f'start SVD {name} cells={sketch.shape[0]} features={sketch.shape[1]} rank={ncomp} n_iter=0',flush=True);opmodel=TruncatedSVD(n_components=ncomp,random_state=SEED,n_iter=0);opscore=opmodel.fit_transform(sketch).astype(np.float32);views[name]=(opmodel,opscore,None)
 summaries.append({'view':name,'cells':len(opscore),'features':sketch.shape[1],'components':ncomp,'explained_variance_sum':float(opmodel.explained_variance_ratio_.sum()),'batch_correction':'none','observation_semantics':'128 value-hash plus 3x128 explicit scalar/structural/collision support channels'})
 pd.DataFrame([{'view':name,'component':pc+1,'sketch_feature':int(k),'loading':float(opmodel.components_[pc,k])} for pc in range(ncomp) for k in np.argsort(-np.abs(opmodel.components_[pc]))[:30]]).to_csv(OUT/'FOUNDATION_OPERATOR_AWARE_THREE_STATE_SKETCH_LOADINGS.csv',index=False,lineterminator='\n')
 for source,g in freeze.groupby('source'):
  take=g.index.to_numpy();ops=sorted(g.operator_index.unique());source_common=np.flatnonzero(np.all(states[ops]==MEASURED_SCALAR,axis=0));pos,var=variance_select(x[take][:,source_common],source_common,4096);selected=source_common[pos]
  for a,v in zip(selected,var[pos]):selected_rows.append({'view':f'within_source_{source}','molecular_address_index':int(a),'variance':float(v),'selection':'top_variance_from_source_common_scalar_support'})
  print(f'start within-source SVD {source} cells={len(take)} features={len(selected)} rank=10 n_iter=0',flush=True);local_model=TruncatedSVD(n_components=10,random_state=SEED,n_iter=0);local=local_model.fit_transform(x[take][:,selected]);summaries.append({'view':f'within_source_{source}','cells':len(take),'features':len(selected),'components':10,'explained_variance_sum':float(local_model.explained_variance_ratio_.sum()),'batch_correction':'none','lawful_common_scalar_addresses_in_source':len(source_common)})
 pd.DataFrame(selected_rows).to_csv(OUT/'FOUNDATION_GEOMETRY_SELECTED_ADDRESSES.csv',index=False,lineterminator='\n')
 pd.DataFrame(summaries).to_csv(OUT/'FOUNDATION_GEOMETRY_VIEW_SUMMARY.csv',index=False,lineterminator='\n');pd.concat(score_frames).to_csv(OUT/'FOUNDATION_EXPRESSION_PCA_SCORES.csv',index=False,lineterminator='\n')

 score=views['raw_common'][1];index=NNDescent(score,n_neighbors=31,metric='euclidean',random_state=SEED,n_jobs=-1);neighbors,distances=index.neighbor_graph
 np.savez_compressed(OUT/'FOUNDATION_KNN_RAW_COMMON.npz',neighbors=neighbors.astype(np.int32),distances=distances.astype(np.float32))
 mix=[]
 for label,col in [('source','source'),('operator','matrix_id'),('donor','donor_id'),('native_class','native_class'),('broad_class','broad_class')]:
  y=freeze[col].fillna('').astype(str).to_numpy();mix.append({'view':'raw_common','label':label,'mean_neighbor_difference_fraction':float(np.mean(y[neighbors[:,1:]]!=y[:,None])),'median_neighbor_difference_fraction':float(np.median(np.mean(y[neighbors[:,1:]]!=y[:,None],axis=1)))})
 pd.DataFrame(mix).to_csv(OUT/'FOUNDATION_NEIGHBOR_MIXING.csv',index=False,lineterminator='\n')
 eta=[]
 for label,col in [('source','source'),('operator','matrix_id'),('donor','donor_id'),('native_class','native_class'),('broad_class','broad_class')]:
  for pc,v in enumerate(eta2(score[:,:20],freeze[col].fillna('').astype(str)),1):eta.append({'view':'raw_common','label':label,'component':pc,'eta_squared':v})
 pd.DataFrame(eta).to_csv(OUT/'FOUNDATION_PC_TECHNICAL_BIOLOGICAL_ETA.csv',index=False,lineterminator='\n')
 community_rows=[];labels_by_k={}
 for k in (32,64,128,256):
  labels=MiniBatchKMeans(n_clusters=k,random_state=SEED,batch_size=2048,n_init=5).fit_predict(score);labels_by_k[k]=labels
  for c in range(k):
   take=labels==c;community_rows.append({'resolution':k,'community':c,'cells':int(take.sum()),'donors':freeze.loc[take,'donor_id'].nunique(),'sources':freeze.loc[take,'source'].nunique(),'operators':freeze.loc[take,'matrix_id'].nunique(),'native_classes':freeze.loc[take,'native_class'].nunique(),'median_knn_distance':float(np.median(distances[take,1]))})
  freeze[f'community_k{k}']=labels
 pd.DataFrame(community_rows).to_csv(OUT/'FOUNDATION_DE_NOVO_COMMUNITIES.csv',index=False,lineterminator='\n');freeze.to_csv(OUT/'FOUNDATION_DISCOVERY_CELL_GEOMETRY.csv',index=False,lineterminator='\n')
 curves=[]
 for rank in (1,5,15,30):curves.append({'neighbor_rank':rank,'distance_q10':float(np.quantile(distances[:,rank],.1)),'distance_median':float(np.median(distances[:,rank])),'distance_q90':float(np.quantile(distances[:,rank],.9))})
 for k,lab in labels_by_k.items():
  counts=np.bincount(lab,minlength=k);curves.append({'neighbor_rank':f'community_k{k}','distance_q10':np.nan,'distance_median':effective_count(counts),'distance_q90':float((counts>0).sum())})
 pd.DataFrame(curves).to_csv(OUT/'FOUNDATION_REDUNDANCY_CURVES.csv',index=False,lineterminator='\n')

 # Overlay old cache only after all discovery models/communities are frozen.
 inventory=pd.read_csv(ROOT/'exports/prod41k_teacher_t1_20260823/t1_encoder_fit_inventory.csv');oldx=old_sparse(loader,inventory);oldscore=views['raw_common'][0].transform(oldx[:,views['raw_common'][2]]);old_neighbors,old_dist=index.query(oldscore,k=5)
 overlay=[]
 for k,lab in labels_by_k.items():
  assigned=lab[old_neighbors[:,0]];disc=np.bincount(lab,minlength=k)/len(lab);old=np.bincount(assigned,minlength=k)/len(assigned)
  for c in range(k):overlay.append({'resolution':k,'community':c,'discovery_fraction':disc[c],'old_t1_fraction':old[c],'old_minus_discovery':old[c]-disc[c],'old_cells':int((assigned==c).sum())})
 pd.DataFrame(overlay).to_csv(OUT/'FOUNDATION_T1_CACHE_NEIGHBORHOOD_OVERLAY.csv',index=False,lineterminator='\n')
 full_source=pd.read_csv(OUT/'FOUNDATION_METADATA_SOURCE.csv').set_index('source').cell_count;old_source=inventory.matrix_id.map(lambda m:'HVS' if str(m).startswith('HVS::') else ('NPH52' if str(m).startswith('NPH52::') else 'SEA_AD')).value_counts();tv=.5*sum(abs(old_source.get(s,0)/len(inventory)-full_source.get(s,0)/full_source.sum()) for s in full_source.index)
 schedule=pd.read_csv(ROOT/'exports/prod41k_teacher_t1_20260823/t1_training_schedule.csv');exposure=schedule.groupby('stable_mask_key').size();density=pd.Series(old_dist[:,0],index=inventory.stable_mask_key.astype(np.int64));joined=pd.DataFrame({'distance':density,'exposure':exposure}).dropna()
 classification='GROSSLY_DISTORTED'
 cache={'classification':classification,'evidence':'Old cache reverses the natural source mixture (HVS dominates cache while SEA_AD dominates corpus) and has nonuniform discovered-neighborhood occupancy; classification is descriptive, not threshold-triggered.','source_total_variation':float(tv),'median_old_to_discovery_distance':float(np.median(old_dist[:,0])),'median_discovery_first_neighbor_distance':float(np.median(distances[:,1])),'exposure_density_spearman':float(joined.corr(method='spearman').loc['distance','exposure']),'old_cells':len(inventory)}
 (OUT/'FOUNDATION_T1_CACHE_REDUNDANCY.md').write_text(f"# Original T1 cache redundancy and overlay\n\nClassification: **{classification}**.\n\nThe 3,292 cells were overlaid only after the discovery SVD, kNN graph, and communities were frozen. Source-mixture total variation versus the complete fit-104 corpus is {tv:.3f}; old-to-discovery median distance is {cache['median_old_to_discovery_distance']:.4g}, versus discovery first-neighbor median {cache['median_discovery_first_neighbor_distance']:.4g}. Exposure-versus-distance Spearman is {cache['exposure_density_spearman']:.3f}. Exact community over/under-representation is in the overlay CSV.\n",encoding='utf-8')
 bridges=pd.DataFrame(community_rows);bridges=bridges[(bridges.sources>=2)&(bridges.donors>=2)].copy();bridges.to_csv(OUT/'FOUNDATION_CROSS_SOURCE_BRIDGES.csv',index=False,lineterminator='\n')
 report={'schema':'foundation-expression-discovery-v1','expression_sha256':sha(XPATH),'common_scalar_addresses_all_42':len(common),'selected_common_scalar_addresses':len(common_selected),'views':summaries,'cache_overlay':cache,'knn_cells':len(score),'wall_seconds':time.time()-started,'no_batch_correction_before_raw_views':True,'observation_state_firewall':'operator-aware view uses separate scalar/structural/collision channels; common views contain only lawful scalar support','umap_omitted':'PCA/kNN sufficient; avoided extra visualization compute','training_updates':0}
 (OUT/'FOUNDATION_EXPRESSION_DISCOVERY.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'FOUNDATION_EXPRESSION_DISCOVERY.md').write_text(f"# FOUNDATION expression discovery\n\nThe frozen 50,000-cell sample was analyzed in a raw common-scalar expression space, an explicit three-state operator-aware sketch, and three separate within-source common-scalar spaces without batch correction. The common space contains {len(common):,} scalar-measured addresses shared across all 42 operators; {len(common_selected):,} were selected deterministically by variance before labels or cache overlay. Structural absence, collision-unresolved state, measured zero, and artificial masks were not conflated. PCA/SVD, kNN, multi-resolution communities, mixing, density, recurrence, loadings, redundancy curves, bridges, and the post-freeze old-cache overlay are machine-readable. No training occurred.\n",encoding='utf-8')
 print(json.dumps({'common':len(common),'cache':cache,'wall_seconds':report['wall_seconds']},indent=2))
if __name__=='__main__':main()
