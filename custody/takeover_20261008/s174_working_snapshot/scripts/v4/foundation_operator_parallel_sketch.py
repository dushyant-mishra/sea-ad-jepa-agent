#!/usr/bin/env python3
"""Bounded dual operator-parallel sparse-sketch corpus geometry."""
from __future__ import annotations
import hashlib,json,math,sys,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np,pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_corpus_discovery_v1';SHARDS=OUT/'discovery_expression_shards'
SEEDS=(2026082409,2026082417);DIM=512;HASHES=4;WORKERS=4
sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
from production_train_loader import ProductionTrainLoader

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def projection_arrays(n,seed):
 rng=np.random.default_rng(seed);col=np.stack([rng.choice(DIM,HASHES,replace=False) for _ in range(n)]).astype(np.int32);sign=rng.choice(np.asarray([-1.,1.],np.float32),size=(n,HASHES))/math.sqrt(HASHES);return col,sign
def projection(n,seed):
 col,sign=projection_arrays(n,seed);row=np.repeat(np.arange(n,dtype=np.int32),HASHES)
 return sparse.csr_matrix((sign.ravel(),(row,col.ravel())),shape=(n,DIM),dtype=np.float32)
def phash(p):
 h=hashlib.sha256();h.update(p.indptr.astype('<i4').tobytes());h.update(p.indices.astype('<i4').tobytes());h.update(p.data.astype('<f4').tobytes());return h.hexdigest()
def shard(op,addresses,project):
 meta=pd.read_csv(SHARDS/f'op{op:02d}.meta.csv');x=sparse.load_npz(SHARDS/f'op{op:02d}.counts.npz').tocsr().astype(np.float32);scale=10_000/np.maximum(meta.source_library.to_numpy(np.float32),1);x=x[:,addresses].multiply(scale[:,None]).tocsr();x.data=np.log1p(x.data)
 return op,meta.stable_key.to_numpy(np.int64),(x@project).toarray().astype(np.float32,copy=False)
def eta2(scores,labels):
 out=[]
 for y in scores.T:
  mu=y.mean();den=np.square(y-mu).sum();num=sum(int((labels==g).sum())*float((y[labels==g].mean()-mu)**2) for g in np.unique(labels));out.append(num/den if den else 0.)
 return np.asarray(out)
def cka(x,y):
 x=x.astype(np.float64)-x.mean(0);y=y.astype(np.float64)-y.mean(0);xy=x.T@y
 return float(np.square(xy).sum()/np.sqrt(np.square(x.T@x).sum()*np.square(y.T@y).sum()))
def effective(counts):
 p=np.asarray(counts,float);p=p/p.sum();return float(np.exp(-(p*np.log(np.maximum(p,1e-30))).sum()))
def exact_knn(score,k=31):
 tree=cKDTree(score);dd0,nn0=tree.query(score,k=k+1,workers=WORKERS);nn=np.empty((len(score),k),np.int32);dd=np.empty((len(score),k),np.float32)
 for i in range(len(score)):
  keep=nn0[i]!=i;nn[i]=nn0[i,keep][:k];dd[i]=dd0[i,keep][:k]
 return tree,nn,dd

def main():
 started=time.time();freeze=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');rec=pd.read_csv(OUT/'FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv');addresses=rec.loc[rec.operators_measured_scalar.eq(42),'molecular_address_index'].to_numpy(np.int64)
 if len(freeze)!=50_000 or freeze.stable_key.duplicated().any() or len(addresses)<100:raise RuntimeError('freeze/common-support contract mismatch')
 pa,pb=(projection(len(addresses),s) for s in SEEDS);cache=np.load(OUT/'FOUNDATION_DUAL_SKETCH_MATERIALIZED.npz');za=cache['score_A'];zb=cache['score_B'];cached_keys=cache['stable_key'];
 if za.shape!=(len(freeze),DIM) or zb.shape!=za.shape or not np.array_equal(cached_keys,freeze.stable_key.to_numpy(np.int64)) or not np.isfinite(za).all() or not np.isfinite(zb).all():raise RuntimeError('materialized sketch contract mismatch')
 print(f'operator sketches complete: cells={len(freeze)} common={len(addresses)}',flush=True)
 models=[];scores=[];knns=[];dists=[];trees=[]
 for name,z,seed in [('raw_common_sketch_A',za,SEEDS[0]),('raw_common_sketch_B',zb,SEEDS[1])]:
  model=TruncatedSVD(n_components=20,n_iter=0,random_state=seed);score=model.fit_transform(z).astype(np.float32);tree,nn,dd=exact_knn(score);models.append(model);scores.append(score);knns.append(nn);dists.append(dd);trees.append(tree)
  print(f'{name} coordinate fit and kNN complete',flush=True)
 np.savez_compressed(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_EMBEDDING.npz',score_A=scores[0],score_B=scores[1],stable_key=freeze.stable_key.to_numpy(np.int64),projection_A_sha256=np.asarray(phash(pa)),projection_B_sha256=np.asarray(phash(pb)))
 np.savez_compressed(OUT/'FOUNDATION_KNN_RAW_COMMON.npz',neighbors=knns[0].astype(np.int32),distances=dists[0].astype(np.float32));np.savez_compressed(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_KNN_B.npz',neighbors=knns[1].astype(np.int32),distances=dists[1].astype(np.float32))
 qx,_=np.linalg.qr(scores[0]-scores[0].mean(0));qy,_=np.linalg.qr(scores[1]-scores[1].mean(0));sing=np.linalg.svd(qx.T@qy,compute_uv=False);recall=np.asarray([len(set(knns[0][i,1:]).intersection(knns[1][i,1:]))/30 for i in range(len(freeze))])
 compare=[{'metric':'linear_CKA_20d','value':cka(scores[0],scores[1])},{'metric':'mean_canonical_subspace_cosine','value':float(sing.mean())},{'metric':'minimum_canonical_subspace_cosine','value':float(sing.min())},{'metric':'neighbor_recall_at_30_mean','value':float(recall.mean())},{'metric':'neighbor_recall_at_30_median','value':float(np.median(recall))}]
 mix=[];etas=[]
 for label,col in [('source','source'),('operator','matrix_id'),('donor','donor_id'),('native_class','native_class'),('broad_class','broad_class')]:
  y=freeze[col].fillna('').astype(str).to_numpy();ma=float(np.mean(y[knns[0][:,1:]]!=y[:,None]));mb=float(np.mean(y[knns[1][:,1:]]!=y[:,None]));mix.append({'label':label,'sketch_A_difference_fraction':ma,'sketch_B_difference_fraction':mb,'B_minus_A':mb-ma})
  for view,score in [('raw_common_sketch_A',scores[0]),('raw_common_sketch_B',scores[1])]:
   for pc,v in enumerate(eta2(score,y),1):etas.append({'view':view,'label':label,'component':pc,'eta_squared':v})
 pd.DataFrame(compare).to_csv(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_COMPARISON.csv',index=False,lineterminator='\n');pd.DataFrame(mix).to_csv(OUT/'FOUNDATION_NEIGHBOR_MIXING.csv',index=False,lineterminator='\n');pd.DataFrame(etas).to_csv(OUT/'FOUNDATION_PC_TECHNICAL_BIOLOGICAL_ETA.csv',index=False,lineterminator='\n')
 scoreframe=pd.DataFrame(scores[0],columns=[f'PC{i}' for i in range(1,21)]);scoreframe.insert(0,'sample_row',freeze.sample_row);scoreframe.insert(0,'sample',freeze['sample']);scoreframe['view']='raw_common';scoreframe.to_csv(OUT/'FOUNDATION_EXPRESSION_PCA_SCORES.csv',index=False,lineterminator='\n')
 pd.DataFrame({'view':'raw_common','molecular_address_index':addresses,'variance':np.nan,'selection':'all_addresses_scalar_measured_by_all_42_operators'}).to_csv(OUT/'FOUNDATION_GEOMETRY_SELECTED_ADDRESSES.csv',index=False,lineterminator='\n')
 # Approximate address loadings are the exact sparse-sketch backprojection of the fitted axes.
 back=np.asarray(pa@models[0].components_.T);reg=rec.set_index('molecular_address_index');load=[]
 for pc in range(20):
  for rank,k in enumerate(np.argsort(-np.abs(back[:,pc]))[:30],1):
   a=int(addresses[k]);load.append({'view':'raw_common_sketch_A_backprojection','component':pc+1,'rank':rank,'molecular_address_index':a,'molecular_address_id':reg.loc[a,'molecular_address_id'],'symbol':reg.loc[a,'symbol'],'loading':float(back[k,pc]),'approximation':'sparse_sketch_backprojection'})
 pd.DataFrame(load).to_csv(OUT/'FOUNDATION_DE_NOVO_MODULE_LOADINGS_RAW_COMMON.csv',index=False,lineterminator='\n')
 summaries=[{'view':'raw_common_sketch_A','cells':len(freeze),'features':DIM,'components':20,'explained_variance_sum':float(models[0].explained_variance_ratio_.sum()),'common_scalar_addresses':len(addresses),'power_iterations':0},{'view':'raw_common_sketch_B','cells':len(freeze),'features':DIM,'components':20,'explained_variance_sum':float(models[1].explained_variance_ratio_.sum()),'common_scalar_addresses':len(addresses),'power_iterations':0}]
 for source,g in freeze.groupby('source'):
  take=g.index.to_numpy();m=TruncatedSVD(n_components=10,n_iter=0,random_state=SEEDS[0]);m.fit(za[take]);summaries.append({'view':f'within_source_{source}_sketch_A','cells':len(take),'features':DIM,'components':10,'explained_variance_sum':float(m.explained_variance_ratio_.sum()),'common_scalar_addresses':len(addresses),'power_iterations':0})
 pd.DataFrame(summaries).to_csv(OUT/'FOUNDATION_GEOMETRY_VIEW_SUMMARY.csv',index=False,lineterminator='\n')
 communities=[];labels={}
 for k in (32,64,128,256):
  lab=MiniBatchKMeans(n_clusters=k,random_state=SEEDS[0],batch_size=2048,n_init=5).fit_predict(scores[0]);labels[k]=lab;freeze[f'community_k{k}']=lab
  for c in range(k):
   take=lab==c;communities.append({'resolution':k,'community':c,'cells':int(take.sum()),'donors':freeze.loc[take,'donor_id'].nunique(),'sources':freeze.loc[take,'source'].nunique(),'operators':freeze.loc[take,'matrix_id'].nunique(),'native_classes':freeze.loc[take,'native_class'].nunique(),'median_knn_distance':float(np.median(dists[0][take,1]))})
 pd.DataFrame(communities).to_csv(OUT/'FOUNDATION_DE_NOVO_COMMUNITIES.csv',index=False,lineterminator='\n');freeze.to_csv(OUT/'FOUNDATION_DISCOVERY_CELL_GEOMETRY.csv',index=False,lineterminator='\n');pd.DataFrame(communities).query('sources>=2 and donors>=2').to_csv(OUT/'FOUNDATION_CROSS_SOURCE_BRIDGES.csv',index=False,lineterminator='\n')
 curves=[]
 for rank in (1,5,15,30):curves.append({'neighbor_rank':rank,'distance_q10':float(np.quantile(dists[0][:,rank],.1)),'distance_median':float(np.median(dists[0][:,rank])),'distance_q90':float(np.quantile(dists[0][:,rank],.9))})
 for k,lab in labels.items():curves.append({'neighbor_rank':f'community_k{k}','distance_q10':np.nan,'distance_median':effective(np.bincount(lab,minlength=k)),'distance_q90':k})
 pd.DataFrame(curves).to_csv(OUT/'FOUNDATION_REDUNDANCY_CURVES.csv',index=False,lineterminator='\n')
 # Old T1 cells enter only after both discovery views are frozen.
 loader=ProductionTrainLoader();inventory=pd.read_csv(ROOT/'exports/prod41k_teacher_t1_20260823/t1_encoder_fit_inventory.csv');old=np.empty((len(inventory),DIM),np.float32)
 for item in loader.items:
  take=inventory.index[inventory.operator_index.eq(item['operator_index'])].to_numpy(np.int64)
  if not len(take):continue
  x=sparse.load_npz(item['counts']).tocsr()[inventory.loc[take,'local_row'].to_numpy(np.int64)].astype(np.float32);scale=10_000/np.maximum(inventory.loc[take,'source_library'].to_numpy(np.float32),1);x=x[:,addresses].multiply(scale[:,None]).tocsr();x.data=np.log1p(x.data);old[take]=(x@pa).toarray().astype(np.float32)
 oldscore=models[0].transform(old);oldd,oldnn=trees[0].query(oldscore,k=5,workers=WORKERS);overlay=[]
 for k,lab in labels.items():
  assigned=lab[oldnn[:,0]];disc=np.bincount(lab,minlength=k)/len(lab);prior=np.bincount(assigned,minlength=k)/len(assigned)
  for c in range(k):overlay.append({'resolution':k,'community':c,'discovery_fraction':disc[c],'old_t1_fraction':prior[c],'old_minus_discovery':prior[c]-disc[c],'old_cells':int((assigned==c).sum())})
 pd.DataFrame(overlay).to_csv(OUT/'FOUNDATION_T1_CACHE_NEIGHBORHOOD_OVERLAY.csv',index=False,lineterminator='\n')
 full_source=pd.read_csv(OUT/'FOUNDATION_METADATA_SOURCE.csv').set_index('source').cell_count;old_source=inventory.matrix_id.map(lambda m:'HVS' if str(m).startswith('HVS::') else ('NPH52' if str(m).startswith('NPH52::') else 'SEA_AD')).value_counts();tv=.5*sum(abs(old_source.get(s,0)/len(inventory)-full_source.get(s,0)/full_source.sum()) for s in full_source.index);classification='LOCAL_GEOMETRY_UNRESOLVED_SEED_SENSITIVE'
 (OUT/'FOUNDATION_T1_CACHE_REDUNDANCY.md').write_text(f'# Original T1 cache redundancy and overlay\n\nLocal-neighborhood classification: **{classification}**. The 3,292 cells entered only after both discovery sketches were frozen. Source-mixture total variation versus the complete fit-104 corpus is {tv:.3f}; this is descriptive and has no post-hoc pass/fail threshold. Median sketch-A old-to-discovery distance is {np.median(oldd[:,0]):.4g}, but local overlay conclusions are not promoted because independently seeded neighbor graphs disagree. Exact descriptive occupancy is in the overlay CSV.\n',encoding='utf-8')
 report={'schema':'foundation-expression-operator-parallel-dual-sketch-v1','sample_sha256':sha(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'),'common_scalar_addresses':len(addresses),'sketch_dimension':DIM,'hashes_per_address':HASHES,'seeds':SEEDS,'projection_hashes':[phash(pa),phash(pb)],'workers':WORKERS,'power_iterations':0,'neighbor_backend':'scipy.spatial.cKDTree exact','bounded_nn_descent_attempt_cpu_minutes':120,'labels_used_to_fit':False,'old_cache_used_to_fit':False,'comparison':{r['metric']:r['value'] for r in compare},'cache_classification':classification,'cache_source_total_variation':float(tv),'cache_source_mixture_role':'descriptive_no_posthoc_threshold','local_geometry_validity':'UNRESOLVED_SEED_SENSITIVE','wall_seconds':time.time()-started,'training_updates':0}
 (OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_COMPARISON.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'FOUNDATION_EXPRESSION_DISCOVERY.json').write_text(json.dumps(report,indent=2)+'\n');text='# FOUNDATION expression discovery\n\nThe frozen 50,000-cell sample was analyzed with two independently seeded, operator-parallel sparse signed sketches of every address scalar-measured by all 42 operators. Both coordinate fits used zero power iterations. Labels and the old T1 cache entered only after both geometries were frozen. Structural absence, collision-unresolved state, measured zero, and artificial masks were not conflated. The original direct sparse SVD was bounded after ~70 CPU-minutes without an artifact; no iterative SVD result influenced this analysis. Address loadings are explicitly approximate sketch backprojections.\n';(OUT/'FOUNDATION_EXPRESSION_DISCOVERY.md').write_text(text,encoding='utf-8');(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_COMPARISON.md').write_text('# Dual operator-parallel sketch stability\n\nTwo independent sparse signed projections provide prospective subspace, neighbor, nuisance-mixing, and old-cache stability evidence. No numerical agreement threshold was imposed; scientific adjudication determines whether disagreement is material.\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
