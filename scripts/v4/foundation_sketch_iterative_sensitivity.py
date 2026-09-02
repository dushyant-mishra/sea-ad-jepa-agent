#!/usr/bin/env python3
"""Read-only iterative-SVD sensitivity after material coarse-view disagreement."""
from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from sklearn.decomposition import TruncatedSVD

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/foundation_corpus_discovery_v1'
SEEDS=(2026082409,2026082417)
N_ITER=5
K=30
WORKERS=4

def cka(x,y):
 x=x.astype(np.float64)-x.mean(0);y=y.astype(np.float64)-y.mean(0);xy=x.T@y
 return float(np.square(xy).sum()/np.sqrt(np.square(x.T@x).sum()*np.square(y.T@y).sum()))

def neighbors(x):
 dd0,nn0=cKDTree(x).query(x,k=K+2,workers=WORKERS);out=np.empty((len(x),K),np.int32)
 for i in range(len(x)):out[i]=nn0[i,nn0[i]!=i][:K]
 return out

def main():
 started=time.time();cache=np.load(OUT/'FOUNDATION_DUAL_SKETCH_MATERIALIZED.npz');coarse=np.load(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_EMBEDDING.npz')
 scores=[];models=[];knn=[]
 for z,seed in ((cache['score_A'],SEEDS[0]),(cache['score_B'],SEEDS[1])):
  model=TruncatedSVD(n_components=20,n_iter=N_ITER,random_state=seed);score=model.fit_transform(z).astype(np.float32);models.append(model);scores.append(score);knn.append(neighbors(score))
 qx,_=np.linalg.qr(scores[0]-scores[0].mean(0));qy,_=np.linalg.qr(scores[1]-scores[1].mean(0));sing=np.linalg.svd(qx.T@qy,compute_uv=False)
 recall=np.asarray([len(set(knn[0][i]).intersection(knn[1][i]))/K for i in range(len(scores[0]))])
 within=[]
 for new,old in ((scores[0],coarse['score_A']),(scores[1],coarse['score_B'])):
  qn,_=np.linalg.qr(new-new.mean(0));qo,_=np.linalg.qr(old-old.mean(0));s=np.linalg.svd(qn.T@qo,compute_uv=False);within.append({'linear_CKA':cka(new,old),'mean_canonical_cosine':float(s.mean()),'minimum_canonical_cosine':float(s.min())})
 result={'schema':'foundation-sketch-iterative-sensitivity-v1','power_iterations':N_ITER,'seeds':SEEDS,'neighbor_backend':'scipy.spatial.cKDTree exact','labels_used_to_fit':False,'old_cache_used_to_fit':False,'between_seed':{'linear_CKA_20d':cka(scores[0],scores[1]),'mean_canonical_subspace_cosine':float(sing.mean()),'minimum_canonical_subspace_cosine':float(sing.min()),'neighbor_recall_at_30_mean':float(recall.mean()),'neighbor_recall_at_30_median':float(np.median(recall))},'within_seed_iterative_vs_coarse':within,'explained_variance_sum':[float(m.explained_variance_ratio_.sum()) for m in models],'wall_seconds':time.time()-started,'training_updates':0}
 np.savez_compressed(OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_ITERATIVE_SENSITIVITY.npz',score_A=scores[0],score_B=scores[1],stable_key=cache['stable_key'])
 (OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_ITERATIVE_SENSITIVITY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 (OUT/'FOUNDATION_OPERATOR_PARALLEL_SKETCH_ITERATIVE_SENSITIVITY.md').write_text('# Iterative sketch sensitivity\n\nThis read-only sensitivity was triggered prospectively by material disagreement between the two frozen zero-power sketch views. It does not overwrite the coarse result and uses no biological labels or old-cache cells during fitting.\n',encoding='utf-8')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
