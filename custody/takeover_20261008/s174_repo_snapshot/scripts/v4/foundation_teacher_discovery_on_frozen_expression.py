#!/usr/bin/env python3
"""Exact-mask cross-view/ceiling/support analyses on a frozen fit-104 subset."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
import numpy as np,pandas as pd,torch
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge,RidgeClassifier,LogisticRegression
from sklearn.metrics import r2_score,balanced_accuracy_score,average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/foundation_corpus_discovery_v1';sys.path.insert(0,str(ROOT/'scripts/v4'));sys.path.insert(0,str(ROOT/'exports/static_context_decomposition_v4_20260821'))
import stage81a3_prod41k_engineering_smoke as phase_e
from production_train_loader import ProductionTrainLoader,MEASURED_SCALAR
SEED=2026082407; SUBSET=5000; PROGRAMS=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail')
def hval(*p):return int.from_bytes(hashlib.sha256('|'.join(map(str,p)).encode()).digest()[:8],'big')&((1<<63)-1)
def reader(kind,x,y,fit,test):
 if kind=='continuous':
  m=make_pipeline(StandardScaler(),Ridge(alpha=10)).fit(x[fit],y[fit]);return r2_score(y[test],m.predict(x[test]))
 if kind=='rare':
  if np.unique(y[fit]).size<2 or np.unique(y[test]).size<2:return np.nan
  m=make_pipeline(StandardScaler(),LogisticRegression(C=1,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=SEED)).fit(x[fit],y[fit]);return average_precision_score(y[test],m.predict_proba(x[test])[:,1])
 m=make_pipeline(StandardScaler(),RidgeClassifier(alpha=10)).fit(x[fit],y[fit]);return balanced_accuracy_score(y[test],m.predict(x[test]))
def main():
 started=time.time();fz=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv');x=sparse.load_npz(OUT/'FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz').tocsr();loader=ProductionTrainLoader()
 ranked=sorted(range(len(fz)),key=lambda i:hval(SEED,fz.stable_key.iloc[i]))[:SUBSET];sub=fz.iloc[ranked].reset_index().rename(columns={'index':'discovery_row'});xs=x[ranked]
 # Frozen donor split is source-stratified and metadata-only.
 eval_donors=set()
 for source,g in sub[['source','donor_id']].drop_duplicates().groupby('source'):
  ds=sorted(g.donor_id.astype(str),key=lambda d:hval(SEED,'eval-donor',source,d));eval_donors.update(ds[::3])
 is_eval=sub.donor_id.astype(str).isin(eval_donors).to_numpy();is_fit=~is_eval
 split_path=OUT/'FOUNDATION_CROSSVIEW_DONOR_SPLIT.csv';sub[['source','donor_id']].drop_duplicates().assign(crossview_partition=lambda d:np.where(d.donor_id.astype(str).isin(eval_donors),'held_donor_evaluation','reader_fit')).to_csv(split_path,index=False,lineterminator='\n')
 weights_file=np.load(ROOT/'exports/contextual_biology_v6r5a_20260822/program_weights.npz');weights=np.stack([weights_file[f'l2__{p}'] for p in PROGRAMS]).astype(np.float32);w2=np.square(weights);w4=np.square(w2)
 opstates={i:int(i) for i in sub.operator_index.unique()};partial=[];difficulty=[];mask_hash=[]
 for view in (0,1):
  out_rows=[];out_cols=[];out_data=[]
  for begin in range(0,SUBSET,8):
   end=min(begin+8,SUBSET);masks=np.stack([loader.states[str(m)]==MEASURED_SCALAR for m in sub.matrix_id.iloc[begin:end]])
   blocks=phase_e.sample_uniform_target_blocks(torch.from_numpy(masks),production_seed=8_113_002,cell_indices=torch.from_numpy(sub.stable_key.iloc[begin:end].to_numpy(np.int64)),sample_pass=1_800_001,view_index=view)
   hidden=blocks.hidden_mask.cpu().numpy()
   for local,rowid in enumerate(range(begin,end)):
    row=xs.getrow(rowid);keep=~hidden[local,row.indices];out_rows.extend([rowid]*int(keep.sum()));out_cols.extend(row.indices[keep].tolist());out_data.extend(row.data[keep].tolist())
    packed=np.packbits(hidden[local],bitorder='little');mask_hash.append({'view':view,'subset_row':rowid,'stable_key':int(sub.stable_key.iloc[rowid]),'mask_sha256':hashlib.sha256(packed.tobytes()).hexdigest()})
    if view==0:
     measured=masks[local];visible=measured&~hidden[local]
     for j,p in enumerate(PROGRAMS):
      e_total=float(w2[j,measured].sum());e_visible=float(w2[j,visible].sum());den=float(w4[j,visible].sum());neff=e_visible*e_visible/den if den else 0
      difficulty.append({'subset_row':rowid,'source':sub.source.iloc[rowid],'matrix_id':sub.matrix_id.iloc[rowid],'program':p,'total_scalar_measured_support':int(measured.sum()),'visible_scalar_support':int(visible.sum()),'hidden_scalar_support':int(hidden[local].sum()),'E_ik_total':e_total,'E_ik_visible':e_visible,'N_eff_visible':neff})
  partial.append(sparse.csr_matrix((out_data,(out_rows,out_cols)),shape=xs.shape,dtype=np.float32))
  sparse.save_npz(OUT/f'FOUNDATION_CROSSVIEW_PARTIAL_VIEW{view}.npz',partial[-1],compressed=True)
 pd.DataFrame(mask_hash).to_csv(OUT/'FOUNDATION_CROSSVIEW_MASK_HASHES.csv',index=False,lineterminator='\n');diff=pd.DataFrame(difficulty);diff.to_csv(OUT/'FOUNDATION_MASK_DIFFICULTY_CELL_PROGRAM.csv',index=False,lineterminator='\n')
 agg=diff.groupby(['source','matrix_id','program'],as_index=False).agg(cells=('subset_row','size'),total_scalar_measured_support=('total_scalar_measured_support','first'),visible_support_median=('visible_scalar_support','median'),hidden_support_median=('hidden_scalar_support','median'),E_ik_total=('E_ik_total','first'),E_ik_visible_q10=('E_ik_visible',lambda z:np.quantile(z,.1)),E_ik_visible_median=('E_ik_visible','median'),E_ik_visible_q90=('E_ik_visible',lambda z:np.quantile(z,.9)),N_eff_visible_q10=('N_eff_visible',lambda z:np.quantile(z,.1)),N_eff_visible_median=('N_eff_visible','median'),zero_visible_evidence_cells=('E_ik_visible',lambda z:int((z==0).sum())))
 agg.to_csv(OUT/'FOUNDATION_MASK_DIFFICULTY_ATLAS.csv',index=False,lineterminator='\n')
 # Fixed-capacity shared partial-RNA coordinates.
 common=np.flatnonzero(np.all(np.stack([loader.states[i['matrix_id']]==MEASURED_SCALAR for i in loader.items]),axis=0));svd=TruncatedSVD(n_components=40,random_state=SEED,n_iter=0);z0=svd.fit_transform(partial[0][:,common]);z1=svd.transform(partial[1][:,common]);full_scores=np.asarray(xs@weights.T)
 labels={'source':('class',sub.source.astype(str).to_numpy()),'operator':('class',sub.matrix_id.astype(str).to_numpy()),'support_regime':('class',sub.support_fingerprint.astype(str).to_numpy()),'broad_annotation':('class',sub.broad_class.fillna('').astype(str).to_numpy())}
 for j,p in enumerate(PROGRAMS):labels[p]=('continuous',full_scores[:,j])
 labels['recurrent_5pct']=('rare',(full_scores[:,PROGRAMS.index('innovation_tail')]>=47.829504776000938).astype(int));labels['recurrent_1pct']=('rare',(full_scores[:,PROGRAMS.index('innovation_tail')]>=67.904151611328118).astype(int))
 geo=pd.read_csv(OUT/'FOUNDATION_DISCOVERY_CELL_GEOMETRY.csv').set_index(['sample','sample_row']);community=np.asarray([geo.loc[(r['sample'],r['sample_row']),'community_k64'] for _,r in sub.iterrows()]);labels['de_novo_community_k64']=('class',community)
 rows=[]
 for target,(kind,y) in labels.items():
  for view,z in [('partial_view0',z0),('partial_view1',z1)]:rows.append({'target':target,'target_type':kind,'representation':view,'metric':'R2' if kind=='continuous' else ('average_precision' if kind=='rare' else 'balanced_accuracy'),'value':reader(kind,z,y,is_fit,is_eval),'fit_donors':sub.loc[is_fit,'donor_id'].nunique(),'heldout_donors':sub.loc[is_eval,'donor_id'].nunique()})
 # Cross-view coordinate predictability itself.
 for j in range(z1.shape[1]):rows.append({'target':f'partial_view1_PC{j+1}','target_type':'continuous','representation':'partial_view0','metric':'R2','value':reader('continuous',z0,z1[:,j],is_fit,is_eval),'fit_donors':sub.loc[is_fit,'donor_id'].nunique(),'heldout_donors':sub.loc[is_eval,'donor_id'].nunique()})
 pred=pd.DataFrame(rows);pred.to_csv(OUT/'FOUNDATION_REAL_CROSSVIEW_PREDICTABILITY.csv',index=False,lineterminator='\n')
 ceiling=pred[pred.target.isin(PROGRAMS+('recurrent_5pct','recurrent_1pct'))].copy();ceiling['comparator']='lawful_partial_RNA_exact_T1_mask';ceiling.to_csv(OUT/'FOUNDATION_PARTIAL_EVIDENCE_CEILING.csv',index=False,lineterminator='\n')
 # Operator/source/donor score consistency and recurrence.
 cons=[]
 for j,p in enumerate(PROGRAMS):
  frame=sub[['source','matrix_id','donor_id']].copy();frame['score']=full_scores[:,j]
  for level in ('source','matrix_id','donor_id'):
   means=frame.groupby(level).score.mean();cons.append({'program':p,'level':level,'groups':len(means),'group_mean_min':means.min(),'group_mean_median':means.median(),'group_mean_max':means.max(),'between_group_variance':means.var(ddof=0),'within_cell_variance':frame.score.var(ddof=0)})
 pd.DataFrame(cons).to_csv(OUT/'FOUNDATION_OPERATOR_PROGRAM_CONSISTENCY.csv',index=False,lineterminator='\n')
 report={'schema':'foundation-teacher-frozen-expression-v1','subset_cells':SUBSET,'subset_selection':'lowest deterministic metadata hash; before any reader fit','fit_donors':int(sub.loc[is_fit,'donor_id'].nunique()),'heldout_donors':int(sub.loc[is_eval,'donor_id'].nunique()),'mask_rule':'exact floor(0.40*MEASURED_SCALAR), 16 blocks, production keyed randperm','sample_pass':1_800_001,'views':[0,1],'partial_coordinate_power_iterations':0,'rare5_threshold':47.829504776000938,'rare1_threshold':67.904151611328118,'rare1_role':'descriptive','neural_updates':0,'wall_seconds':time.time()-started}
 (OUT/'FOUNDATION_TEACHER_FROZEN_EXPRESSION_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
