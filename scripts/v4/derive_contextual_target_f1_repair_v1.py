"""Pre-result metadata-only F1 null map and query-support frontier derivation."""
from __future__ import annotations

import csv, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901'
CELL=ROOT/'outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json'
WEIGHTS=ROOT/'exports/contextual_biology_v6r5a_20260822/program_weights.npz'
STATES=ROOT/'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz'
EXPECTED={CELL:'32437e5ebb01deb8fad771f8b2d4d9bd2b62b061f89c1e79fdbc6629d11af9fe',WEIGHTS:'001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70',STATES:'852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'}
PROGRAMS=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail')
FAIR_ORDER=('local_core','local_halo','core_halo','sparse_marker_like','weak_distributed','local','innovation_tail','broad_common')

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def hkey(*x:object)->str:return hashlib.sha256('|'.join(map(str,x)).encode()).hexdigest()

def balanced_map(rows:pd.DataFrame)->tuple[pd.DataFrame,list[dict]]:
 mapped=[];audits=[]
 for op,g in rows.groupby('operator_index',sort=True):
  g=g.sort_values('selection_rank_sha256',kind='stable').reset_index(drop=True);n=len(g)
  donors=g.canonical_donor_id.astype(str).to_numpy(); unique=sorted(set(donors)); dindex={d:i for i,d in enumerate(unique)}
  vars_=[];cost=[]
  for i in range(n):
   for j in range(n):
    if donors[i]!=donors[j]:
     vars_.append((i,j));cost.append(int(hkey('F1-NULL-TIE-V1',op,g.loc[i,'row_locator'],g.loc[j,'row_locator'])[:13],16)/float(16**13))
  m=len(vars_); rr=[];cc=[];vv=[];lb=[];ub=[];rowc=0
  for i in range(n):
   for v,(a,b) in enumerate(vars_):
    if a==i:rr.append(rowc);cc.append(v);vv.append(1.)
   lb.append(1.);ub.append(1.);rowc+=1
  for j in range(n):
   for v,(a,b) in enumerate(vars_):
    if b==j:rr.append(rowc);cc.append(v);vv.append(1.)
   lb.append(1.);ub.append(1.);rowc+=1
  # Most-even allocation is 0/1 because every selected donor has <=2 rows and D-1 >=13.
  for rd in unique:
   for sd in unique:
    if rd==sd:continue
    for v,(i,j) in enumerate(vars_):
     if donors[i]==rd and donors[j]==sd:rr.append(rowc);cc.append(v);vv.append(1.)
    lb.append(0.);ub.append(1.);rowc+=1
  A=coo_matrix((vv,(rr,cc)),shape=(rowc,m)).tocsr()
  res=milp(np.asarray(cost),integrality=np.ones(m),bounds=Bounds(0,1),constraints=LinearConstraint(A,np.asarray(lb),np.asarray(ub)),options={'time_limit':120})
  if not res.success:raise RuntimeError(f'STOP_F1_MATCHED_NULL_UNRESOLVED operator={op}: {res.message}')
  chosen=np.flatnonzero(res.x>.5)
  if len(chosen)!=n:raise RuntimeError('nonintegral/null assignment')
  assign={vars_[v][0]:vars_[v][1] for v in chosen}
  if len(assign)!=n or len(set(assign.values()))!=n:raise RuntimeError('null map not bijective')
  pair_counts={}
  for i,j in sorted(assign.items()):
   r=g.loc[i];s=g.loc[j];pair_counts[(str(r.canonical_donor_id),str(s.canonical_donor_id))]=pair_counts.get((str(r.canonical_donor_id),str(s.canonical_donor_id)),0)+1
   mapped.append({'operator_index':int(op),'recipient_row_locator':r.row_locator,'recipient_canonical_cell_id':r.canonical_cell_id,'recipient_canonical_donor_id':r.canonical_donor_id,'recipient_source':r.source,'source_row_locator':s.row_locator,'source_canonical_cell_id':s.canonical_cell_id,'source_canonical_donor_id':s.canonical_donor_id,'source_source':s.source,'mapping_tiebreak_sha256':hkey('F1-NULL-TIE-V1',op,r.row_locator,s.row_locator)})
  for rd in unique:
   nr=int(np.sum(donors==rd)); elig=len(unique)-1; realized={sd:int(pair_counts.get((rd,sd),0)) for sd in unique if sd!=rd}
   floor=nr//elig;ceil=math.ceil(nr/elig);maxdev=max([max(0,v-ceil,floor-v) for v in realized.values()] or [0])
   audits.append({'operator_index':int(op),'recipient_donor':rd,'recipient_rows':nr,'eligible_distinct_source_donors':elig,'theoretical_floor':floor,'theoretical_ceiling':ceil,'realized_source_donor_counts':realized,'maximum_deviation_from_most_even':int(maxdev)})
 return pd.DataFrame(mapped),audits

def query_frontier(rows:pd.DataFrame)->dict:
 z=np.load(STATES,allow_pickle=False);states=z['states'];ops=z['operator_index'].astype(int);wz=np.load(WEIGHTS,allow_pickle=False)
 weights={p:wz[f'l2__{p}'].astype(np.float64) for p in PROGRAMS}; V=states.shape[1]
 op_support=(states==1).sum(0).astype(int)
 donors_by_op={int(o):set(g.canonical_donor_id.astype(str)) for o,g in rows.groupby('operator_index')}
 donor_support=np.zeros(V,dtype=int)
 for oi,op in enumerate(ops):donor_support += (states[oi]==1).astype(int)*len(donors_by_op.get(int(op),set()))
 unique_donor_support=np.zeros(V,dtype=int)
 for a in range(V):unique_donor_support[a]=len(set().union(*(donors_by_op.get(int(op),set()) for oi,op in enumerate(ops) if states[oi,a]==1)))
 qpath=OUT/'F1_QUERY_NESTED_ORDER.csv'; frontier_by_op={}; summaries=[]
 fields=['operator_index','prefix','address_index','allocator_program','scalar_operator_count','lawful_unique_donor_count','lawful_donor_operator_count']+[f'delta_w2_fraction__{p}' for p in PROGRAMS]
 with qpath.open('w',newline='',encoding='utf-8') as fh:
  writer=csv.DictWriter(fh,fieldnames=fields,lineterminator='\n');writer.writeheader()
  for oi,op in enumerate(ops):
   measured=states[oi]==1; totals={p:float(np.square(weights[p][measured]).sum()) for p in PROGRAMS}
   probs={p:np.where(measured,np.square(weights[p])/max(totals[p],1e-300),0.) for p in PROGRAMS}
   rankings={}
   for p in PROGRAMS:
    cand=np.flatnonzero(probs[p]>0);rankings[p]=cand[np.lexsort((cand,op_support[cand],-probs[p][cand]))]
   curs={p:0 for p in PROGRAMS};selected=set();order=[];allocator=[]
   union=set(np.flatnonzero(measured & np.logical_or.reduce([np.square(weights[p])>0 for p in PROGRAMS])).tolist())
   while len(selected)<len(union):
    progressed=False
    for p in FAIR_ORDER:
     rank=rankings[p];c=curs[p]
     while c<len(rank) and int(rank[c]) in selected:c+=1
     curs[p]=c
     if c<len(rank):
      a=int(rank[c]);curs[p]=c+1;selected.add(a);order.append(a);allocator.append(p);progressed=True
    if not progressed:raise RuntimeError(f'query frontier stalled operator={op}')
   cov=np.zeros((len(order),len(PROGRAMS)),dtype=np.float64);neff=np.zeros_like(cov);hits=np.zeros_like(cov,dtype=np.int32)
   csum=np.zeros(len(PROGRAMS));sqsum=np.zeros(len(PROGRAMS));hcount=np.zeros(len(PROGRAMS),dtype=int)
   for qi,(a,alloc) in enumerate(zip(order,allocator,strict=True)):
    delta=[]
    for k,p in enumerate(PROGRAMS):
     v=float(probs[p][a]);delta.append(v);csum[k]+=v;sqsum[k]+=v*v;hcount[k]+=int(v>0);cov[qi,k]=csum[k];neff[qi,k]=(csum[k]*csum[k]/sqsum[k]) if sqsum[k]>0 else 0.;hits[qi,k]=hcount[k]
    rec={'operator_index':int(op),'prefix':qi+1,'address_index':a,'allocator_program':alloc,'scalar_operator_count':int(op_support[a]),'lawful_unique_donor_count':int(unique_donor_support[a]),'lawful_donor_operator_count':int(donor_support[a])}
    rec.update({f'delta_w2_fraction__{p}':format(delta[k],'.17g') for k,p in enumerate(PROGRAMS)});writer.writerow(rec)
   common=np.cumsum([op_support[a]==42 for a in order]);specific=np.arange(1,len(order)+1)-common
   frontier_by_op[int(op)]={'qmax':len(order),'cov':cov,'neff':neff,'hits':hits,'common':common,'specific':specific,'eval_rows':int((rows.operator_index==op).sum())}
   summaries.append({'operator_index':int(op),'support_union_count':len(order),'scalar_addresses':int(measured.sum()),'programs':{p:{'support_count':int(np.count_nonzero(probs[p])),'W2_total':totals[p],'N_eff':float(1/np.square(probs[p][probs[p]>0]).sum()),'positive_count':int(np.sum(measured&(weights[p]>0))),'negative_count':int(np.sum(measured&(weights[p]<0)))} for p in PROGRAMS}})
 maxq=max(x['qmax'] for x in frontier_by_op.values());fpath=OUT/'F1_QUERY_SUPPORT_FRONTIER.csv'
 flds=['prefix','query_row_pairs','min_program_operator_coverage','mean_common_support_fraction','mean_operator_specific_fraction']
 for p in PROGRAMS:flds += [f'min_coverage__{p}',f'mean_coverage__{p}',f'min_queried_neff__{p}',f'mean_queried_neff__{p}']
 with fpath.open('w',newline='',encoding='utf-8') as fh:
  writer=csv.DictWriter(fh,fieldnames=flds,lineterminator='\n');writer.writeheader()
  for q in range(1,maxq+1):
   allcov=[];allne=[];commons=[];specifics=[];pairs=0
   for op,x in frontier_by_op.items():
    idx=min(q,x['qmax'])-1;allcov.append(x['cov'][idx]);allne.append(x['neff'][idx]);commons.append(x['common'][idx]/(idx+1));specifics.append(x['specific'][idx]/(idx+1));pairs+=x['eval_rows']*(idx+1)
   C=np.stack(allcov);N=np.stack(allne);rec={'prefix':q,'query_row_pairs':pairs,'min_program_operator_coverage':format(float(C.min()),'.17g'),'mean_common_support_fraction':format(float(np.mean(commons)),'.17g'),'mean_operator_specific_fraction':format(float(np.mean(specifics)),'.17g')}
   for k,p in enumerate(PROGRAMS):rec.update({f'min_coverage__{p}':format(float(C[:,k].min()),'.17g'),f'mean_coverage__{p}':format(float(C[:,k].mean()),'.17g'),f'min_queried_neff__{p}':format(float(N[:,k].min()),'.17g'),f'mean_queried_neff__{p}':format(float(N[:,k].mean()),'.17g')})
   writer.writerow(rec)
 return {'programs':PROGRAMS,'fair_cycle':FAIR_ORDER,'operators':summaries,'query_order_rows':sum(x['qmax'] for x in frontier_by_op.values()),'max_prefix':maxq,'delta_encoding':'F1_QUERY_NESTED_ORDER.csv stores exact per-address normalized-w2 increments; cumulative sums losslessly reconstruct every program/operator prefix frontier','query_order_sha256':sha(qpath),'frontier_sha256':sha(fpath)}

def main():
 for p,h in EXPECTED.items():
  if sha(p)!=h:raise RuntimeError('STOP_F1_REPAIR_AUTHORITY_MISMATCH '+str(p))
 OUT.mkdir(parents=True,exist_ok=False)
 cell=json.loads(CELL.read_text());rows=pd.DataFrame(cell['selected_rows'])
 if len(rows)!=2781 or rows.canonical_donor_id.nunique()!=104 or rows.operator_index.nunique()!=42:raise RuntimeError('STOP_F1_CELL_SAMPLING_UNRESOLVED')
 mapping,audits=balanced_map(rows);mapping.to_csv(OUT/'F1_MATCHED_NULL_PRIMARY_MAP.csv',index=False,lineterminator='\n')
 if mapping.source_row_locator.nunique()!=len(rows) or (mapping.recipient_canonical_donor_id==mapping.source_canonical_donor_id).any():raise RuntimeError('STOP_F1_MATCHED_NULL_UNRESOLVED')
 audit={'schema':'f1-matched-null-balance-audit-v1','status':'PASS_BALANCED_BIJECTIVE_DERANGEMENT','rows':len(mapping),'operators':mapping.operator_index.nunique(),'donors':rows.canonical_donor_id.nunique(),'map_sha256':sha(OUT/'F1_MATCHED_NULL_PRIMARY_MAP.csv'),'maximum_balance_deviation':max(x['maximum_deviation_from_most_even'] for x in audits),'operator_row_multisets_preserved':True,'per_gene_value_marginals_preserved_by_bijection':True,'measured_zero_frequencies_preserved_by_bijection':True,'source_expression_cross_gene_covariance_preserved_by_row_bijection':True,'construction_used_expression_values':False,'recipient_masks_and_query_replaced':False,'donor_audit':audits}
 (OUT/'F1_MATCHED_NULL_BALANCE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
 summary=query_frontier(rows);(OUT/'_query_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({'status':'PASS_METADATA_DERIVATION','map_rows':len(mapping),'query_rows':summary['query_order_rows'],'max_prefix':summary['max_prefix']}))
if __name__=='__main__':main()
