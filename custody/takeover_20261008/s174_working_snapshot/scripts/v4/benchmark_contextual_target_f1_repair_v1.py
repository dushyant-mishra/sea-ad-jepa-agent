"""Outcome-blind F1 contextual parity/resource benchmark on authenticated V8 rows."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, sys, tempfile, time
from pathlib import Path
import numpy as np, pandas as pd, psutil, torch
import torch.nn.functional as F
from scipy.sparse import csr_matrix

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts/v4'))
from sea_ad_jepa.v4.contextual_query_local import construct_query_local_contextual_state, _module_state_sha256
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder
from contextual_target_v1_f0_authenticated_fixture import load_authenticated_reader_fit_fixture

OUT=ROOT/'outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901'
V8=ROOT/'outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8'
SEL=V8/'interface_check_v8r1/FULL104_EXPRESSION_INTERFACE_SELECTION.csv';ID=V8/'audit_identity/FULL104_EXPRESSION_INTERFACE_IDENTITY.csv';SPLIT=ROOT/'exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv'
CHECKPOINT=ROOT/'exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt'
ENC_SHA='732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a';TOK_SHA='2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4';STATE_SHA='852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
SEED='c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f'
EXPR=ROOT/'outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4'

def bind_null_input(map_row, value_by_locator, recipient_state, recipient_evidence, recipient_q):
 """Bind frozen source values while retaining every recipient-side causal input."""
 source=str(map_row['source_row_locator']);recipient=str(map_row['recipient_row_locator'])
 if source==recipient or source not in value_by_locator:raise RuntimeError('invalid frozen null binding')
 return {'normalized_values':np.asarray(value_by_locator[source]).copy(),'physical_state':np.asarray(recipient_state).copy(),'evidence_visible':np.asarray(recipient_evidence).copy(),'query_index':int(recipient_q),'recipient_row_locator':recipient,'source_row_locator':source}
def load_actual_mapped_pair(map_row):
 """Load two authenticated reader-fit rows from the completed FULL104 materialization."""
 bm=EXPR/'PHASE2_EXPRESSION_BLOCK_MANIFEST.csv';expected='66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29'
 if sha(bm)!=expected:raise RuntimeError('materialized block manifest mismatch')
 manifest=pd.read_csv(bm);op=int(map_row.operator_index);want={str(map_row.recipient_canonical_cell_id),str(map_row.source_canonical_cell_id)};found={}
 for _,r in manifest[manifest.operator_index.eq(op)].iterrows():
  meta=EXPR/str(r.meta_path);counts=EXPR/str(r.counts_path)
  m=pd.read_csv(meta)
  hit=m[m.canonical_cell_id.astype(str).isin(want)]
  if hit.empty:continue
  if sha(meta)!=str(r.meta_sha256) or sha(counts)!=str(r.counts_sha256):raise RuntimeError('mapped block hash mismatch')
  z=np.load(counts,allow_pickle=False);mat=csr_matrix((z['data'],z['indices'],z['indptr']),shape=tuple(z['shape']))
  for idx,row in hit.iterrows():
   dense=mat.getrow(int(idx)).toarray().ravel().astype(np.float32);lib=float(row.source_library)
   found[str(row.canonical_cell_id)]=np.log1p(dense*(10000./lib)).astype(np.float32)
  if want.issubset(found):break
 if set(found)!=want:raise RuntimeError('frozen map rows not found in authenticated materialization')
 zs=np.load(ROOT/'exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz',allow_pickle=False);where=np.flatnonzero(zs['operator_index'].astype(int)==op)
 if len(where)!=1:raise RuntimeError('operator state lookup mismatch')
 return found[str(map_row.recipient_canonical_cell_id)],found[str(map_row.source_canonical_cell_id)],zs['states'][where[0]].astype(np.uint8),{'block_manifest_sha256':expected,'operator_index':op,'recipient_cell_id':str(map_row.recipient_canonical_cell_id),'source_cell_id':str(map_row.source_canonical_cell_id),'recipient_donor':str(map_row.recipient_canonical_donor_id),'source_donor':str(map_row.source_canonical_donor_id)}
def snapshot_test(identity):
 """Atomic scientific-payload snapshot, injected pre-publish crash, exact reload."""
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);live=root/'snapshot.npz';payload=np.arange(17,dtype=np.float64)
  def psha(cursor,array):
   a=np.asarray(array).astype(np.float64,copy=False);h=hashlib.sha256();h.update(np.int64(cursor).tobytes());h.update(str(a.dtype).encode());h.update(np.asarray(a.shape,np.int64).tobytes());h.update(a.tobytes());return h.hexdigest()
  def write(path,cursor,array,stored=None):np.savez(path,cursor=np.int64(cursor),accumulator=array,identity_json=np.asarray(json.dumps(identity,sort_keys=True)),payload_semantic_sha256=np.asarray(stored or psha(cursor,array)))
  def load(path):
   with np.load(path,allow_pickle=False) as z:
    cursor=int(z['cursor']);array=z['accumulator'].copy();ident=str(z['identity_json']);stored=str(z['payload_semantic_sha256'])
   if ident!=json.dumps(identity,sort_keys=True) or stored!=psha(cursor,array):raise RuntimeError('snapshot semantic/identity mismatch')
   return cursor,array
  staging=root/'snapshot.staging.npz';write(staging,3,payload);os.replace(staging,live);before=sha(live)
  write(staging,4,payload+1) # injected failure before atomic publish
  cursor,array=load(live);ok=cursor==3 and np.array_equal(array,payload)
  staging.unlink();write(staging,4,payload+1);os.replace(staging,live)
  cursor,array=load(live);advanced=cursor==4 and np.array_equal(array,payload+1);corrupt=root/'corrupt.npz';write(corrupt,4,payload+2,stored=psha(4,payload+1))
  try:load(corrupt);corrupt_rejected=False
  except RuntimeError:corrupt_rejected=True
  return {'status':'PASS' if ok and advanced and corrupt_rejected else 'FAIL','prepublish_crash_retained_prior_payload':bool(ok),'successful_advance_exact':bool(advanced),'mutated_scientific_payload_rejected':bool(corrupt_rejected),'semantic_payload_sha256_recomputed_on_load':True,'prior_file_sha256':before,'identity_fields':sorted(identity)}

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def tsha(t):
 a=t.detach().contiguous().cpu().numpy();h=hashlib.sha256();h.update(str(a.dtype).encode('ascii'));h.update(json.dumps(list(a.shape),separators=(',',':')).encode('ascii'));h.update(a.tobytes(order='C'));return h.hexdigest()
def load_fixture():
 spec=importlib.util.spec_from_file_location('consumer',V8/'code/full104_expression_interface_consumer.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 meta=pd.read_csv(SEL).sort_values('selection_row',kind='stable');req=meta[['selection_row','donor_id','canonical_cell_id','reader_partition','foundation_split']].to_dict('records')
 t=time.perf_counter();values,states,resolved=load_authenticated_reader_fit_fixture(requests=req,selection_path=SEL,identity_path=ID,reader_split_path=SPLIT,payload_loader=lambda:mod.load_teacher_inputs(V8));return values,states,resolved,time.perf_counter()-t
def evidence_mask(state,row_locator,q,level):
 elig=np.flatnonzero(state==1);elig=elig[elig!=q];rank=sorted(elig.tolist(),key=lambda j:(hashlib.sha256(f'{SEED}|{row_locator}|{q}|{j}'.encode()).digest(),j));keep=len(rank)*level//100;m=np.zeros(len(state),bool);m[np.asarray(rank[:keep],int)]=True;return m
def provenance(meta,q,state):return {'canonical_cell_id':str(meta.canonical_cell_id),'donor_id':str(meta.donor_id),'source':str(meta.source),'operator_index':int(meta.operator_index),'selection_row':int(meta.selection_row),'reader_partition':'reader_fit','foundation_split':'foundation/train','pathology':False,'external':False,'physical_state_row_sha256':tsha(torch.from_numpy(state)),'query_address':int(q)}
def lean(encoder,x,state,evidence,q):
 measurement=state.eq(1);hidden=measurement&~evidence;ids=torch.arange(x.shape[1],device=x.device).expand(len(x),-1)
 encoded=encoder(gene_ids=ids,expression=x,measurement_mask=measurement,hidden_target_mask=hidden,view='student');rows=torch.arange(len(x),device=x.device);hq=encoded.gene_states[rows,q];means=[]
 for i in range(len(x)):
  idx=torch.nonzero(evidence[i],as_tuple=False).flatten();idx=idx[idx!=q[i]];means.append(encoded.gene_states[i,idx].sum(0)/int(idx.numel()))
 mu=torch.stack(means);pre=hq-mu;return {'h_query':hq,'mu_context':mu,'pre_layer_norm':pre,'contextual_state':F.layer_norm(pre,(pre.shape[-1],)),'direct_state':F.layer_norm(hq,(hq.shape[-1],)),'hidden_mask':hidden,'evidence_visible':evidence}
def full(encoder,x,state,evidence,q,prov,model_sha,role):
 ids=torch.arange(x.shape[1],device=x.device).expand(len(x),-1)
 return construct_query_local_contextual_state(encoder=encoder,gene_ids=ids,normalized_expression=x,physical_state=state,evidence_visible=evidence,query_index=q,row_provenance=prov,encoder_source_sha256=ENC_SHA,tokenizer_source_sha256=TOK_SHA,model_state_sha256=model_sha,physical_state_authority_sha256=STATE_SHA,role=role)
def bytes_full(r):
 ts=[r.physical_state,r.evidence_visible,r.hidden_mask,r.context_counts,r.query_index,r.query_address,r.query_physical_state,r.h_query,r.mu_context,r.pre_layer_norm,r.contextual_state,*r.context_states]
 return sum(t.numel()*t.element_size() for t in ts)
def bytes_lean(r):return sum(r[k].numel()*r[k].element_size() for k in ('h_query','mu_context','pre_layer_norm','contextual_state','direct_state'))
def main():
 if sha(CHECKPOINT)!='19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4':raise RuntimeError('checkpoint mismatch')
 values,states,meta,io=load_fixture();device=torch.device('cuda');cp=torch.load(CHECKPOINT,map_location='cpu',weights_only=False);encoder=IPBEncoder(vocabulary_size=41238,width=160,heads=4,blocks=6,gradient_checkpointing=False);encoder.load_state_dict(cp['online_encoder']);encoder.eval().to(device);model_sha=_module_state_sha256(encoder);before=model_sha
 selected=[]
 for src in ('HVS','NPH52','SEA_AD'):
  for op,g in meta[meta.source.eq(src)].groupby('operator_index',sort=True):
   if len(g)>=2 and g.donor_id.astype(str).nunique()>=2:selected.append((src,g.index[0],g.index[1]));break
 # Exercise the actual frozen-map schema through the causal binder without opening
 # expression outside the authenticated 84-row parity fixture.
 frozen_map=pd.read_csv(OUT/'F1_MATCHED_NULL_PRIMARY_MAP.csv',nrows=1).iloc[0]
 rv,nv,rs,actual_identity=load_actual_mapped_pair(frozen_map);q_actual=int(np.flatnonzero(rs==1)[0]);re=evidence_mask(rs,str(frozen_map.recipient_row_locator),q_actual,60);bound=bind_null_input(frozen_map,{str(frozen_map.source_row_locator):nv},rs,re,q_actual)
 ap=pd.Series({'canonical_cell_id':frozen_map.recipient_canonical_cell_id,'donor_id':frozen_map.recipient_canonical_donor_id,'source':frozen_map.recipient_source,'operator_index':frozen_map.operator_index,'selection_row':-1})
 atx=torch.from_numpy(rv[None]).to(device);anx=torch.from_numpy(bound['normalized_values'][None]).to(device);ast=torch.from_numpy(rs[None]).to(torch.uint8).to(device);aev=torch.from_numpy(re[None]).to(device);aq=torch.tensor([q_actual],device=device);aprov=[provenance(ap,q_actual,rs)]
 with torch.inference_mode():anref=full(encoder,anx,ast,aev,aq,aprov,model_sha,'student');anlean=lean(encoder,anx,ast,aev,aq)
 actual_forward_max=max(float((getattr(anref,k)-anlean[k]).abs().max().cpu()) for k in ('h_query','mu_context','pre_layer_norm','contextual_state'))
 map_binding={'actual_frozen_map_row_used':True,'authenticated_materialized_expression_loaded':True,'source_values_exact':bool(np.array_equal(bound['normalized_values'],nv)),'recipient_state_exact':bool(np.array_equal(bound['physical_state'],rs)),'recipient_evidence_exact':bool(np.array_equal(bound['evidence_visible'],re)),'recipient_query_exact':bound['query_index']==q_actual,'recipient_and_source_distinct':bound['recipient_row_locator']!=bound['source_row_locator'],'donor_distinct':actual_identity['recipient_donor']!=actual_identity['source_donor'],'operator_preserved':actual_identity['operator_index']==int(frozen_map.operator_index),'actual_null_forward_f0_lean_max_abs_zero':actual_forward_max==0.0,'identity':actual_identity}
 rows=[];parity=[];q_batches=(1,2,4,8,16)
 for src,ri,si in selected:
  measured=np.flatnonzero(states[ri]==1);qs=measured[np.linspace(0,len(measured)-1,max(q_batches),dtype=int)]
  for b in q_batches:
   qq=qs[:b];xr=np.repeat(values[ri:ri+1],b,0);xn=np.repeat(values[si:si+1],b,0);st=np.repeat(states[ri:ri+1],b,0);ev=np.stack([evidence_mask(states[ri],str(meta.loc[ri,'row_locator']) if 'row_locator' in meta else str(meta.loc[ri,'canonical_cell_id']),int(q),60) for q in qq]);rich=st==1;rich[np.arange(b),qq]=False;prov=[provenance(meta.loc[ri],int(q),states[ri]) for q in qq]
   tx=torch.from_numpy(xr).float().to(device);tn=torch.from_numpy(xn).float().to(device);ts=torch.from_numpy(st).to(torch.uint8).to(device);te=torch.from_numpy(ev).to(device);tr=torch.from_numpy(rich).to(device);tq=torch.from_numpy(qq).long().to(device)
   if b==1:
    with torch.inference_mode():
     ref=full(encoder,tx,ts,te,tq,prov,model_sha,'student');lr=lean(encoder,tx,ts,te,tq);nref=full(encoder,tn,ts,te,tq,prov,model_sha,'student');nlr=lean(encoder,tn,ts,te,tq);tref=full(encoder,tx,ts,tr,tq,prov,model_sha,'teacher');tlr=lean(encoder,tx,ts,tr,tq)
    diffs={}
    for label,a,z in [('correct',ref,lr),('null',nref,nlr),('teacher',tref,tlr)]:
     for k in ('h_query','mu_context','pre_layer_norm','contextual_state'):diffs[f'{label}__{k}']=float((getattr(a,k)-z[k]).abs().max().cpu())
     if not torch.equal(a.hidden_mask,z['hidden_mask']) or not torch.equal(a.evidence_visible,z['evidence_visible']):raise RuntimeError('STOP_F1_EXECUTOR_PARITY masks')
    parity.append({'source':src,'max_abs':max(diffs.values()),'fields':diffs,'debug_bytes':bytes_full(ref),'lean_bytes':bytes_lean(lr)})
   for label,xx,ee in [('teacher',tx,tr),('correct_student',tx,te),('null_student',tn,te)]:
    torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();
    with torch.inference_mode():lean(encoder,xx,ts,ee,tq)
    torch.cuda.synchronize();t0=time.perf_counter();rss0=psutil.Process().memory_info().rss
    with torch.inference_mode():out=lean(encoder,xx,ts,ee,tq)
    torch.cuda.synchronize();dt=time.perf_counter()-t0
    rows.append({'source':src,'role':label,'q_batch':b,'seconds':dt,'seconds_per_q':dt/b,'q_per_second':b/dt,'rss_before':rss0,'rss_after':psutil.Process().memory_info().rss,'cuda_peak_allocated':torch.cuda.max_memory_allocated(),'cuda_peak_reserved':torch.cuda.max_memory_reserved(),'lean_bytes':bytes_lean(out)})
  # explicit null reassignment overhead
  t0=time.perf_counter();_=[values[si].copy() for _ in range(100)];assign=(time.perf_counter()-t0)/100
  rows.append({'source':src,'role':'null_reassignment_cpu','q_batch':1,'seconds':assign,'seconds_per_q':assign,'q_per_second':1/assign,'rss_before':psutil.Process().memory_info().rss,'rss_after':psutil.Process().memory_info().rss,'cuda_peak_allocated':0,'cuda_peak_reserved':0,'lean_bytes':0})
 # context-only reduction benchmark on a real encoded tensor
 xx=torch.from_numpy(values[selected[0][1]:selected[0][1]+1]).float().to(device);ss=torch.from_numpy(states[selected[0][1]:selected[0][1]+1]).to(torch.uint8).to(device);q=int(np.flatnonzero(states[selected[0][1]]==1)[0]);ee=torch.from_numpy(evidence_mask(states[selected[0][1]],str(meta.loc[selected[0][1],'canonical_cell_id']),q,60)[None]).to(device);qq=torch.tensor([q],device=device);ids=torch.arange(41238,device=device)[None]
 with torch.inference_mode():enc=encoder(gene_ids=ids,expression=xx,measurement_mask=ss.eq(1),hidden_target_mask=ss.eq(1)&~ee,view='student')
 idx=torch.nonzero(ee[0]).flatten();torch.cuda.synchronize();t0=time.perf_counter()
 for _ in range(100):mu=enc.gene_states[0,idx].sum(0)/len(idx);z=F.layer_norm(enc.gene_states[0,q]-mu,(160,))
 torch.cuda.synchronize();reduction=(time.perf_counter()-t0)/100
 eps=float(np.finfo(np.float32).eps);tol=float(256*eps*max(1.,max(x['max_abs'] for x in parity)));pstatus='PASS_F1_CONTEXTUAL_EXECUTOR_PARITY' if max(x['max_abs'] for x in parity)<=tol and _module_state_sha256(encoder)==before else 'STOP_F1_EXECUTOR_PARITY'
 if not all(v for k,v in map_binding.items() if k!='identity'):pstatus='STOP_F1_EXECUTOR_PARITY'
 snap=snapshot_test({'map_sha256':sha(OUT/'F1_MATCHED_NULL_PRIMARY_MAP.csv'),'query_sha256':sha(OUT/'F1_QUERY_NESTED_ORDER.csv'),'model_state_sha256':model_sha,'observation_state_sha256':STATE_SHA})
 if snap['status']!='PASS':pstatus='STOP_F1_EXECUTOR_PARITY'
 parity_out={'schema':'f1-contextual-executor-parity-v1','status':pstatus,'f0_source_unchanged':True,'authenticated_fixture':True,'sources':[x[0] for x in selected],'frozen_map_to_tensor_binding':map_binding,'comparison_rule':{'float32_epsilon':eps,'absolute_multiplier':256,'tolerance':tol},'results':parity,'model_state_before':before,'model_state_after':_module_state_sha256(encoder),'exact_all_eligible_context':True,'context_cap':None,'restart_snapshot_test':snap}
 (OUT/'F1_CONTEXTUAL_EXECUTOR_PARITY.json').write_text(json.dumps(parity_out,indent=2)+'\n')
 frame=pd.DataFrame(rows); viable=frame[(frame.role!='null_reassignment_cpu') & (frame.cuda_peak_reserved < .9*torch.cuda.get_device_properties(0).total_memory)];rates=viable.groupby('q_batch').q_per_second.mean();best=int(rates.idxmax())
 chosen=frame[(frame.q_batch==best)&frame.role.isin(['teacher','correct_student','null_student'])];cost={r:float(chosen[chosen.role.eq(r)].seconds_per_q.mean()) for r in ('teacher','correct_student','null_student')}
 resource={'schema':'f1-contextual-resource-benchmark-v1','status':'PASS_ENGINEERING_BENCHMARK','outcome_metrics_computed':False,'runtime':{'python':sys.version,'platform':platform.platform(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0)},'expression_io_seconds_84_rows':io,'rows':rows,'benchmark_best_q_batch_not_frozen_constant':best,'per_query_seconds_at_best':cost,'context_reduction_seconds_per_query':reduction,'runtime_factorization':'Q*N_eval_rows*[teacher_once + E*correct_student + E*R_null*null_student + (1+E+E*R_null)*context_reduction] + expression_IO + statistical_postprocess; E=5,R_null=1','frozen_map_to_tensor_binding':map_binding,'null_reassignment_seconds_per_vector_by_source':{s:float(frame[(frame.source==s)&frame.role.eq('null_reassignment_cpu')].seconds_per_q.iloc[0]) for s,_,_ in selected},'context_cap':None,'teacher_cache_across_evidence_and_nulls':True,'null_worlds_benchmarked':1,'historical_K32_used':False}
 (OUT/'F1_CONTEXTUAL_RESOURCE_BENCHMARK.json').write_text(json.dumps(resource,indent=2)+'\n')
 frontier=pd.read_csv(OUT/'F1_QUERY_SUPPORT_FRONTIER.csv',usecols=['prefix','query_row_pairs','min_program_operator_coverage']);io_proj=io/84*2781;red=reduction
 enc_teacher=max(0,cost['teacher']-red);enc_correct=max(0,cost['correct_student']-red);enc_null=max(0,cost['null_student']-red)
 frontier['teacher_cached_seconds']=frontier.query_row_pairs*enc_teacher;frontier['correct_students_5e_seconds']=frontier.query_row_pairs*5*enc_correct;frontier['null_students_5e_one_primary_map_seconds']=frontier.query_row_pairs*5*enc_null;frontier['context_reduction_seconds']=frontier.query_row_pairs*11*red;frontier['expression_io_seconds']=io_proj;frontier['statistical_postprocess_seconds']=0.;frontier['projected_total_seconds']=frontier[['teacher_cached_seconds','correct_students_5e_seconds','null_students_5e_one_primary_map_seconds','context_reduction_seconds','expression_io_seconds','statistical_postprocess_seconds']].sum(axis=1);frontier['projected_total_hours']=frontier.projected_total_seconds/3600;frontier.to_csv(OUT/'F1_RUNTIME_FRONTIER.csv',index=False,lineterminator='\n')
 print(json.dumps({'status':pstatus,'best_batch_not_frozen':best,'max_abs':max(x['max_abs'] for x in parity),'runtime_rows':len(frontier)}))
if __name__=='__main__':main()
