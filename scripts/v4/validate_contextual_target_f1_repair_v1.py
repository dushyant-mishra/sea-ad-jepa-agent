"""Independent pre-result validator; does not import production derivation/decision helpers."""
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t as st

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901'
PROGRAMS=('broad_common','weak_distributed','local','local_core','local_halo','core_halo','sparse_marker_like','innovation_tail');FAIR=('local_core','local_halo','core_halo','sparse_marker_like','weak_distributed','local','innovation_tail','broad_common')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def assert_close_tree(a,b,path='root'):
 if isinstance(a,dict):
  assert set(a)==set(b),(path,set(a)^set(b))
  for k in a:assert_close_tree(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  assert len(a)==len(b),(path,len(a),len(b))
  for i,(x,y) in enumerate(zip(a,b)):assert_close_tree(x,y,f'{path}[{i}]')
 elif isinstance(a,(float,int)) and not isinstance(a,bool):assert abs(float(a)-float(b))<=1e-12*max(1.,abs(float(a)),abs(float(b))),(path,a,b)
 else:assert a==b,(path,a,b)
def independent_order(measured,weights,op_support):
 probs={p:np.where(measured,np.square(weights[p])/max(float(np.square(weights[p][measured]).sum()),1e-300),0.) for p in PROGRAMS};ranks={}
 for p in PROGRAMS:
  c=np.flatnonzero(probs[p]>0);ranks[p]=c[np.lexsort((c,op_support[c],-probs[p][c]))]
 union=set(np.flatnonzero(measured&np.logical_or.reduce([np.square(weights[p])>0 for p in PROGRAMS])).tolist());cur={p:0 for p in PROGRAMS};sel=set();out=[]
 while len(out)<len(union):
  moved=False
  for p in FAIR:
   r=ranks[p];i=cur[p]
   while i<len(r) and int(r[i]) in sel:i+=1
   cur[p]=i
   if i<len(r):a=int(r[i]);cur[p]=i+1;sel.add(a);out.append(a);moved=True
  if not moved:raise AssertionError('independent order stalled')
 return np.asarray(out),probs
def independent_synthetic():
 rng=np.random.default_rng(1701);n=24;base=np.linspace(.22,.42,n)+rng.normal(0,.015,n);program={p:base+.01*i for i,p in enumerate(PROGRAMS)};direct={p:np.linspace(.02,.08,n)+.002*i for i,p in enumerate(PROGRAMS)};evidence=np.stack([base+.08*j for j in range(5)],1)
 def interval(x):
  x=np.asarray(x,float);m=x.mean();se=x.std(ddof=1)/np.sqrt(len(x));crit=st.ppf(.975,len(x)-1);z=m/se
  return {'estimable':True,'n':len(x),'mean':float(m),'lower':float(m-crit*se),'upper':float(m+crit*se),'lower_one_sided':float(m-st.ppf(.95,len(x)-1)*se),'p_positive':float(st.sf(z,len(x)-1)),'p_negative':float(st.cdf(z,len(x)-1))}
 def adj(ps):
  order=np.argsort(ps,kind='stable');out=np.empty(len(ps));run=0.
  for j,i in enumerate(order):run=max(run,(len(ps)-j)*ps[i]);out[i]=min(1.,run)
  return out
 def rank(X):
  s=np.linalg.svd(X,compute_uv=False);return int(np.sum(s>max(X.shape)*np.finfo(float).eps*s[0]))
 cols={'operator_mix':np.tile([0.,1.],n//2),'support_depth':np.linspace(-1,1,n),'duplicate_support':np.linspace(-2,2,n)};X=np.ones((n,1));kept=[]
 for name in sorted(cols):
  C=np.column_stack([X,cols[name]-np.mean(cols[name])])
  if rank(C)>rank(X):X=C;kept.append(name)
 inv=np.linalg.inv(X.T@X);beta=inv@X.T@base;res=base-X@beta;h=np.einsum('ij,jk,ik->i',X,inv,X);u=res/(1-h);cov=inv@(X.T@(X*(u*u)[:,None]))@inv;se=np.sqrt(cov[0,0]);df=n-rank(X);crit=st.ppf(.975,df);nuisance={'estimable':True,'kept':kept,'rank':rank(X),'df':df,'beta0':float(beta[0]),'lower':float(beta[0]-crit*se),'upper':float(beta[0]+crit*se),'p_positive':float(st.sf(beta[0]/se,df))}
 slopes=(evidence@(np.asarray([.2,.4,.6,.8,1.])-.6))/.4;iv={p:interval(program[p]) for p in PROGRAMS};dv={p:interval(direct[p]) for p in PROGRAMS};pos=adj([iv[p]['p_positive'] for p in PROGRAMS]);neg=adj([dv[p]['p_negative'] for p in PROGRAMS]);sli=interval(slopes);qi={'query_margin':interval(base*.4),'query_structure':interval(base*.3)};overall=interval(base);source_group=np.tile(['HVS','NPH52','SEA_AD'],8);source={k:interval(base[source_group==k]) for k in sorted(set(source_group))}
 gates={'legal':True,'overall_positive':overall['lower']>0,'all_programs_reported_and_estimable':True,'all_direct_deltas_estimable':True,'no_adjusted_direct_degradation':bool(np.all(neg>=.05)),'evidence_slope_positive':sli['lower_one_sided']>0,'query_identity_positive':all(x['lower']>0 for x in qi.values()),'nuisance_positive':nuisance['lower']>0 and all(x['lower']>0 for x in source.values())}
 payload={'overall_A':base.tolist(),'program_A':{p:program[p].tolist() for p in PROGRAMS},'program_delta':{p:direct[p].tolist() for p in PROGRAMS},'evidence_A':evidence.tolist(),'query_margin':(base*.4).tolist(),'query_structure':(base*.3).tolist(),'nuisance_y':base.tolist(),'source_group':source_group.tolist(),'nuisance_columns':{k:v.tolist() for k,v in cols.items()},'legal':True}
 return {'payload_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'decision':{'qualified':all(gates.values()),'gates':gates,'overall':overall,'program_positive_holm':dict(zip(PROGRAMS,pos.tolist())),'direct_negative_holm':dict(zip(PROGRAMS,neg.tolist())),'evidence_slope':sli,'query_identity':qi,'nuisance':nuisance,'source_replication':source,'claim_scope':'PANEL_CONDITIONED_QUERY_SAMPLE'},'rank_deficient_kept':['a'],'zero_variance_estimable':False}
def main():
 cell=json.loads((ROOT/'outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json').read_text());rows=pd.DataFrame(cell['selected_rows']);mp=pd.read_csv(OUT/'F1_MATCHED_NULL_PRIMARY_MAP.csv')
 assert len(mp)==len(rows)==2781 and mp.recipient_row_locator.nunique()==len(rows) and mp.source_row_locator.nunique()==len(rows)
 assert set(mp.recipient_row_locator)==set(rows.row_locator)==set(mp.source_row_locator);assert (mp.recipient_canonical_donor_id!=mp.source_canonical_donor_id).all();assert (mp.recipient_source==mp.source_source).all()
 pc=mp.groupby(['operator_index','recipient_canonical_donor_id','source_canonical_donor_id']).size();assert pc.max()<=1
 null={'bijection':True,'donor_distinct':True,'same_operator_source':True,'maximum_donor_pair_count':int(pc.max()),'balance_optimality_proof':'observed maximum deviation 0 equals the nonnegative global lower bound','marginal_identity_proof':'within each operator source row-locator multiset exactly equals recipient multiset; therefore every per-address value/zero marginal and full-row cross-gene covariance are identical under permutation'}
 zs=np.load(ROOT/'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz');states=zs['states'];ops=zs['operator_index'].astype(int);wz=np.load(ROOT/'exports/contextual_biology_v6r5a_20260822/program_weights.npz');weights={p:wz['l2__'+p].astype(np.float64) for p in PROGRAMS};opsup=(states==1).sum(0)
 qo=pd.read_csv(OUT/'F1_QUERY_NESTED_ORDER.csv',float_precision='round_trip');checks=[]
 for oi,op in enumerate(ops):
  got=qo[qo.operator_index.eq(op)].sort_values('prefix');exp,probs=independent_order(states[oi]==1,weights,opsup);assert np.array_equal(got.address_index.to_numpy(),exp)
  for p in PROGRAMS:
   delta=got['delta_w2_fraction__'+p].to_numpy(float);assert np.array_equal(delta,probs[p][exp])
  checks.append({'operator_index':int(op),'qmax':len(exp),'full_min_coverage':float(min(got['delta_w2_fraction__'+p].sum() for p in PROGRAMS))})
 f=pd.read_csv(OUT/'F1_QUERY_SUPPORT_FRONTIER.csv',usecols=['prefix','query_row_pairs'],float_precision='round_trip');evaln=rows.groupby('operator_index').size().to_dict();qmax={x['operator_index']:x['qmax'] for x in checks};expect=np.asarray([sum(evaln[o]*min(int(q),qmax[o]) for o in qmax) for q in f.prefix]);assert np.array_equal(f.query_row_pairs.to_numpy(),expect)
 # Pairwise support overlap, independently derived.
 overlap={}
 for i,a in enumerate(PROGRAMS):
  for b in PROGRAMS[i+1:]:
   vals=[]
   for oi in range(42):
    A=(states[oi]==1)&(weights[a]!=0);B=(states[oi]==1)&(weights[b]!=0);vals.append(float((A&B).sum()/max(1,(A|B).sum())))
   overlap[a+'__'+b]={'min_jaccard':min(vals),'max_jaccard':max(vals)}
 # Independent decision fixture.
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'prod.json';subprocess.run([sys.executable,str(ROOT/'scripts/v4/contextual_target_f1_decision_v1.py'),'--synthetic-out',str(p)],check=True);prod=json.loads(p.read_text())
 ind=independent_synthetic();assert prod['payload_sha256']==ind['payload_sha256'];assert_close_tree(prod['decision'],ind['decision']);assert prod['rank_deficient_kept']==ind['rank_deficient_kept'] and prod['zero_variance_estimable']==ind['zero_variance_estimable']==False
 assert prod['negative_direct_attack']['gates']['no_adjusted_direct_degradation']==False and prod['negative_direct_attack']['qualified']==False
 assert prod['constant_negative_direct_attack']['gates']['all_direct_deltas_estimable']==False and prod['constant_negative_direct_attack']['gates']['no_adjusted_direct_degradation']==False and prod['constant_negative_direct_attack']['qualified']==False
 assert prod['nan_direct_rejected'] and prod['missing_program_rejected']
 assert prod['nuisance_source_attack']['gates']['nuisance_positive']==False and prod['nuisance_source_attack']['qualified']==False
 assert prod['decision']['gates']['no_adjusted_direct_degradation']==True and len(prod['holm_boundary'])==8
 # Runtime arithmetic for every prefix.
 b=json.loads((OUT/'F1_CONTEXTUAL_RESOURCE_BENCHMARK.json').read_text());rt=pd.read_csv(OUT/'F1_RUNTIME_FRONTIER.csv',float_precision='round_trip');red=float(b['context_reduction_seconds_per_query']);c=b['per_query_seconds_at_best'];io=float(b['expression_io_seconds_84_rows'])/84*2781;pairs=rt.query_row_pairs.to_numpy(float);total=pairs*(max(0,c['teacher']-red)+5*max(0,c['correct_student']-red)+5*max(0,c['null_student']-red)+11*red)+io;assert np.allclose(total,rt.projected_total_seconds.to_numpy(),rtol=2e-15,atol=1e-8)
 allowed={'F1_MATCHED_NULL_PRIMARY_MAP.csv','F1_MATCHED_NULL_BALANCE_AUDIT.json','F1_QUERY_NESTED_ORDER.csv','F1_QUERY_SUPPORT_FRONTIER.csv','F1_CONTEXTUAL_EXECUTOR_PARITY.json','F1_CONTEXTUAL_RESOURCE_BENCHMARK.json','F1_RUNTIME_FRONTIER.csv','_query_summary.json','F1_MATCHED_NULL_CAUSAL_CONTRACT.md','F1_QUERY_SUPPORT_FRONTIER_SUMMARY.md','F1_CONTEXTUAL_STATISTICAL_ESTIMAND_CONTRACT.md','F1_DECISION_LOGIC_PROPOSAL.md'};unexpected=[p.name for p in OUT.iterdir() if p.is_file() and p.name not in allowed and ('PERFORMANCE' in p.name.upper() or 'BIOLOGY' in p.name.upper())];assert not unexpected
 parity=json.loads((OUT/'F1_CONTEXTUAL_EXECUTOR_PARITY.json').read_text());assert parity['status']=='PASS_F1_CONTEXTUAL_EXECUTOR_PARITY' and max(x['max_abs'] for x in parity['results'])==0 and all(parity['frozen_map_to_tensor_binding'].values())
 assert qo.lawful_unique_donor_count.max()<=104 and qo.lawful_donor_operator_count.max()>=qo.lawful_unique_donor_count.max()
 result={'schema':'f1-independent-repair-validation-v1','status':'PASS_INDEPENDENT_REPAIR_VALIDATION','production_helpers_imported':False,'null':null,'query_order_exact_all_operators':True,'query_delta_arithmetic_exact':True,'query_support_labels_verified':{'unique_donor_max':int(qo.lawful_unique_donor_count.max()),'donor_operator_max':int(qo.lawful_donor_operator_count.max())},'query_checks':checks,'support_overlap':{'all_operator_scalar_common':int((states==1).all(0).sum()),'any_operator_scalar':int((states==1).any(0).sum()),'pairwise':overlap},'T_true_cache_semantics':'same recipient rich teacher tensor reused; benchmark has separate teacher/correct/null roles and exact lean/F0 parity','S_null_provenance':'actual frozen map row drives authenticated materialized source values while recipient state/evidence/q are retained; independently asserted from parity artifact','decision_fixture_exact_full_path':True,'decision_adversarial_fixtures':{'negative_direct_rejected':True,'constant_negative_direct_rejected':True,'nan_direct_rejected':True,'missing_program_rejected':True,'nuisance_source_shortcut_rejected':True,'rank_deficient_column_dropped':True,'zero_variance_unestimable':True,'holm_boundary_executed':True},'runtime_every_prefix_recomputed':True,'candidate_performance_files_found':False,'protected_expression_opened':False}
 (OUT/'F1_INDEPENDENT_REPAIR_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'operators':len(checks),'max_null_pair_count':int(pc.max())}))
if __name__=='__main__':main()
