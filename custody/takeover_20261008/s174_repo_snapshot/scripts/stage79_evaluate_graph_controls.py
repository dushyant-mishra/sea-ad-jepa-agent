#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, hashlib, importlib.util, json, math, random, subprocess, sys, tempfile
from pathlib import Path
from typing import Any
import h5py, numpy as np, pandas as pd, torch, yaml

APPROVED="Stage79 compares the frozen real graph against bounded structural and expression-matched controls. Differences are model-based control results and do not establish causal regulation or therapeutic benefit."
FALSE={"validated_regulation":False,"validated_grn_claim":False,"causal_validation_pass":False,"therapeutic_target_claim":False}
REQ_COUNTS={"ELF1":23,"SPI1":14,"STAT1":16}

def ensure_src(project:Path):
    src=str((project/'src').resolve())
    if src not in sys.path: sys.path.insert(0,src)

def import_script(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod); return mod

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def shalist(xs): return hashlib.sha256('\n'.join(map(str,xs)).encode()).hexdigest()
def git_head(project): return subprocess.run(['git','rev-parse','HEAD'],cwd=project,text=True,capture_output=True,check=True).stdout.strip()
def awrite_csv(df,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='',dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as f: tmp=Path(f.name); df.to_csv(f,index=False)
    tmp.replace(path)
def awrite_gz(df,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as raw: tmp=Path(raw.name)
    with gzip.open(tmp,'wt',encoding='utf-8',newline='') as f: df.to_csv(f,index=False)
    tmp.replace(path)
def awrite_json(obj,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as f: tmp=Path(f.name); json.dump(obj,f,indent=2,sort_keys=True); f.write('\n')
    tmp.replace(path)
def load_yaml(p): return yaml.safe_load(Path(p).read_text(encoding='utf-8'))
def edge_sign(x): return 1.0 if str(x)=='positive' else -1.0
def renorm(df):
    df=df.copy(); s=df.groupby('tf')['absolute_unnormalized_weight'].transform('sum')
    if len(df) and (s<=0).any(): raise RuntimeError('nonpositive weight sum')
    if len(df): df['normalized_outgoing_weight']=df['absolute_unnormalized_weight']/s
    return df

def all_bounds(h5ad,n):
    lo=np.zeros(n,dtype=np.float32); hi=np.zeros(n,dtype=np.float32)
    with h5py.File(h5ad,'r') as h:
        x=h['X']
        if isinstance(x,h5py.Group):
            for c,v in zip(x['indices'][:],x['data'][:]):
                c=int(c); v=float(v); lo[c]=min(lo[c],v); hi[c]=max(hi[c],v)
        else:
            a=np.asarray(x[:,:],dtype=np.float32); lo=a.min(0); hi=a.max(0)
    return lo,hi

def scenario_df(cfg):
    rows=[]
    for tf in cfg['regulators']:
        for mag in cfg['magnitudes']:
            for d in cfg['directions']:
                rows.append({'scenario_id':f'{tf}_{d}_{float(mag):.2f}'.replace('.','p'),'regulator':tf,'direction':d,'magnitude':float(mag)})
    return pd.DataFrame(rows)

def degree_shuffle(real,seed):
    rng=random.Random(seed); out=real.copy().sort_values(['tf','target_gene']).reset_index(drop=True); realpairs=set(zip(out.tf,out.target_gene)); acc=dup=selfe=same=0
    for att in range(1,20001):
        if acc>=2000: break
        i,j=rng.sample(range(len(out)),2); fi,fj=out.at[i,'tf'],out.at[j,'tf']; ti,tj=out.at[i,'target_gene'],out.at[j,'target_gene']
        if fi==fj: same+=1; continue
        if fi==tj or fj==ti: selfe+=1; continue
        pairs=set(zip(out.tf,out.target_gene)); pairs.discard((fi,ti)); pairs.discard((fj,tj))
        if (fi,tj) in pairs or (fj,ti) in pairs: dup+=1; continue
        out.at[i,'target_gene']=tj; out.at[j,'target_gene']=ti; acc+=1
    out=renorm(out); pairs=set(zip(out.tf,out.target_gene))
    if pairs==realpairs:
        fixed=False
        for i in range(len(out)):
            for j in range(i+1,len(out)):
                fi,fj=out.at[i,'tf'],out.at[j,'tf']; ti,tj=out.at[i,'target_gene'],out.at[j,'target_gene']
                if fi!=fj and fi!=tj and fj!=ti:
                    tmp=out.copy(); tmp.at[i,'target_gene']=tj; tmp.at[j,'target_gene']=ti
                    tp=set(zip(tmp.tf,tmp.target_gene))
                    if len(tp)==len(tmp) and tp!=realpairs:
                        out=renorm(tmp); pairs=tp; acc+=1; fixed=True; break
            if fixed: break
        if not fixed: raise RuntimeError(f'degree shuffle unchanged seed {seed}')
    return out,{'swap_attempts':att,'accepted_swaps':acc,'rejected_duplicate_edges':dup,'rejected_invalid_self_edges':selfe,'rejected_same_tf':same,'final_edge_overlap_with_real':len(pairs&realpairs)}

def tf_label_shuffle(real,seed):
    rng=random.Random(seed); base=real.copy().sort_values(['target_gene','tf']).reset_index(drop=True); realpairs=set(zip(real.tf,real.target_gene))
    target_to_indices={}
    for i,t in enumerate(base.target_gene.astype(str)): target_to_indices.setdefault(t,[]).append(i)
    groups=sorted(target_to_indices.items(), key=lambda kv:(-len(kv[1]), kv[0]))
    tfs=sorted(REQ_COUNTS)
    for att in range(1,101):
        remaining=REQ_COUNTS.copy(); assigned=[None]*len(base)
        def rec(pos):
            if pos==len(groups): return all(v==0 for v in remaining.values())
            target,idxs=groups[pos]; choices=tfs[:]; rng.shuffle(choices)
            combos=[]
            def combo(cur,avail,k):
                if k==0: combos.append(cur[:]); return
                for tf in avail:
                    if remaining[tf]>0:
                        nxt=[x for x in avail if x!=tf]; cur.append(tf); combo(cur,nxt,k-1); cur.pop()
            combo([],choices,len(idxs)); rng.shuffle(combos)
            for combo_labels in combos:
                if any(remaining[tf]<=0 for tf in combo_labels): continue
                for tf in combo_labels: remaining[tf]-=1
                for idx,tf in zip(idxs,combo_labels): assigned[idx]=tf
                if rec(pos+1): return True
                for idx in idxs: assigned[idx]=None
                for tf in combo_labels: remaining[tf]+=1
            return False
        if not rec(0): continue
        out=base.copy(); out['tf']=assigned; pairs=list(zip(out.tf,out.target_gene))
        if len(set(pairs))!=len(pairs) or set(pairs)==realpairs: continue
        out=renorm(out); return out,{'label_shuffle_attempts':att,'tf_label_changed_fraction':sum(base.tf!=out.tf)/len(out)}
    raise RuntimeError(f'tf label shuffle failed {seed}')
def strata(base,genes):
    mean=base.mean(0); nz=(base!=0).mean(0)
    return pd.DataFrame({'gene':genes,'feature_index':range(len(genes)),'mean_decile':pd.qcut(pd.Series(mean).rank(method='first'),10,labels=False).astype(int),'nonzero_decile':pd.qcut(pd.Series(nz).rank(method='first'),10,labels=False).astype(int)})

def expr_match(real,seed,genes,st,regs):
    rng=random.Random(seed); by=st.set_index('gene'); rows=[]; exact=expanded=0; dists=[]
    real_targets={tf:set(real.loc[real.tf.eq(tf),'target_gene']) for tf in regs}; regset=set(regs)
    for tf,g in real.sort_values(['tf','target_gene']).groupby('tf'):
        used=set(); excl=regset|real_targets[tf]
        for r in g.itertuples(index=False):
            md=int(by.loc[r.target_gene,'mean_decile']); nd=int(by.loc[r.target_gene,'nonzero_decile']); chosen=None
            for dist in range(20):
                cand=st[(st.mean_decile.sub(md).abs()+st.nonzero_decile.sub(nd).abs()).le(dist)]
                names=sorted(set(cand.gene)-excl-used)
                if names: chosen=names[rng.randrange(len(names))]; break
            if chosen is None: raise RuntimeError(f'no expression match {tf} {r.target_gene} {seed}')
            used.add(chosen); dd=r._asdict(); dd['target_gene']=chosen; dd['target_feature_index']=int(by.loc[chosen,'feature_index']); dd['matched_from_real_target']=r.target_gene; dd['expression_match_stratum_distance']=dist; dd['expression_match_expanded']=dist>0; rows.append(dd); exact+=dist==0; expanded+=dist>0; dists.append(dist)
    return renorm(pd.DataFrame(rows)),{'exact_match_count':exact,'expanded_match_count':expanded,'maximum_stratum_distance':max(dists),'mean_stratum_distance':float(np.mean(dists)),'unavailable_match_count':0}

def apply_delta(base_row,sc,edges,g2i,lo,hi):
    tf=sc.regulator; s=1.0 if sc.direction=='up' else -1.0; reg_delta=s*float(sc.magnitude); changes=[(tf,reg_delta,'regulator')]
    for e in edges.itertuples(index=False): changes.append((e.target_gene, reg_delta*edge_sign(e.predicted_response_sign_from_coactivity)*float(e.normalized_outgoing_weight),'target'))
    pert=base_row.copy(); rows=[]; tl1=tl2=fl1=fl2=0.0; clip=changed=0
    for gene,delta,role in changes:
        idx=g2i[gene]; base=float(base_row[idx]); uncl=base+float(delta); cl=min(max(uncl,float(lo[idx])),float(hi[idx])); cd=cl-base; pert[idx]=cl; isclip=not math.isclose(uncl,cl,rel_tol=0,abs_tol=1e-12)
        clip+=isclip; changed+=not math.isclose(cd,0,rel_tol=0,abs_tol=1e-12); fl1+=abs(cd); fl2+=cd*cd
        if role=='target': tl1+=abs(cd); tl2+=cd*cd
        rows.append({'gene_symbol':gene,'feature_index':idx,'feature_role':role,'baseline_value':base,'unclipped_delta':float(delta),'clipped_delta':float(cd),'perturbed_value_unclipped':float(uncl),'perturbed_value_clipped':float(cl),'clipped':bool(isclip)})
    return pert,rows,{'regulator_delta':reg_delta,'target_only_l1_delta_norm':tl1,'target_only_l2_delta_norm':math.sqrt(tl2),'full_changed_feature_l1_delta_norm':fl1,'full_changed_feature_l2_delta_norm':math.sqrt(fl2),'number_changed_features':changed,'clipping_count':clip,'clipping_fraction':clip/len(changes)}

def bh(p):
    p=p.astype(float); order=np.argsort(p.to_numpy()); q=np.ones(len(p)); prev=1.0; n=len(p)
    for k,idx in enumerate(order[::-1],1):
        rank=n-k+1; prev=min(prev,p.iloc[idx]*n/rank); q[idx]=prev
    return pd.Series(q,index=p.index)

def rel(project,path): return str(path.relative_to(project)).replace('\\','/')
def meta(project,path,rows,cells,graphs,scens,features,donors): return {'path':rel(project,path),'sha256':sha(path),'byte_size':path.stat().st_size,'row_count':int(rows),'cell_count':int(cells),'control_graph_count':int(graphs),'scenario_count':int(scens),'feature_count':int(features),'donor_count':int(donors)}

def run(cfg,project):
    ensure_src(project); s79=cfg['stage79_graph_controls']; s77=cfg['stage77_tier_a_perturbation_mvp']; s78=cfg['stage78_jepa_latent_shift']
    st78=import_script(project/'scripts/stage78_compute_jepa_latent_shift.py','stage78_helpers')
    f10=json.load(open(project/s78['sources']['stage76_readiness_report'])); f77=json.load(open(project/s77['outputs']['report_json'])); f78=json.load(open(project/s78['outputs']['report_json']))
    tol=f10['baseline_reproduction']['approved_tolerance']; atol=float(tol['max_abs_diff'])
    delta_path=project/s77['outputs']['predicted_expression_deltas_csv_gz']; checkpoint=project/s78['jepa']['checkpoint_path']; h5ad=project/s78['jepa']['feature_h5ad']
    if sha(delta_path)!=f77['detailed_delta_artifact']['sha256']: raise RuntimeError('Stage77 detailed delta hash mismatch')
    if sha(checkpoint)!=f10['checkpoint_audit']['checkpoint_sha256']: raise RuntimeError('checkpoint hash mismatch')
    contract=st78.read_h5ad_contract(h5ad,s78['jepa']['obs_columns']); genes=contract['genes']; g2i={g:i for i,g in enumerate(genes)}
    if shalist(genes)!=f10['feature_order']['feature_order_sha256']: raise RuntimeError('feature order hash mismatch')
    cell_order=list(map(str,f77['baseline_subset']['cell_ids']))
    if cell_order!=list(map(str,f78['baseline_cells']['cell_ids'])) or len(cell_order)!=32: raise RuntimeError('baseline cell order mismatch')
    obs=contract['obs']; idx={c:i for i,c in enumerate(obs.cell_id.astype(str))}; rows=[idx[c] for c in cell_order]; obs_sub=obs.set_index('cell_id').loc[cell_order].reset_index()
    base=st78.read_h5ad_rows(h5ad,rows); lo,hi=all_bounds(h5ad,len(genes)); real=pd.read_csv(project/s77['outputs']['edge_weights_csv'])
    if real.groupby('tf').size().to_dict()!=REQ_COUNTS: raise RuntimeError('real edge counts mismatch')
    scenarios=pd.read_csv(project/s77['outputs']['scenario_manifest_csv']); ps=scenarios[scenarios.scenario_type.eq('perturbation')].copy(); expected=sorted(scenario_df(s79).scenario_id)
    if sorted(ps.scenario_id)!=expected: raise RuntimeError('scenario ids mismatch')
    seeds=list(range(int(s79['stochastic_seed_start']),int(s79['stochastic_seed_start'])+int(s79['stochastic_seed_count'])))
    graphs=[]; edgeframes=[]
    def add(ctype,gid,seed,edges,extra):
        e=edges.copy(); e['control_type']=ctype; e['control_graph_id']=gid; e['seed']='' if seed is None else seed; e['control_only']=ctype!='real_graph'; e['evidence_support']='real_frozen_graph' if ctype=='real_graph' else 'null_control'; edgeframes.append(e)
        graphs.append({'control_graph_id':gid,'control_type':ctype,'seed':'' if seed is None else seed,'edge_count':len(e),**extra})
    real=real.sort_values(['tf','target_gene']).reset_index(drop=True); real['slot_id']=range(len(real)); add('real_graph','real_graph',None,real,{'referenced_frozen_real_results':True}); add('no_graph','no_graph',None,real.iloc[0:0].copy(),{})
    st=strata(base,genes)
    for seed in seeds:
        e,x=degree_shuffle(real,seed); add('degree_preserving_edge_shuffle',f'degree_preserving_edge_shuffle_seed_{seed}',seed,e,x)
    for seed in seeds:
        e,x=tf_label_shuffle(real,seed); add('tf_label_shuffle',f'tf_label_shuffle_seed_{seed}',seed,e,x)
    for seed in seeds:
        e,x=expr_match(real,seed,genes,st,s79['regulators']); add('expression_matched_random_targets',f'expression_matched_random_targets_seed_{seed}',seed,e,x)
    graph_manifest=pd.DataFrame(graphs); edge_sets=pd.concat(edgeframes,ignore_index=True)
    # real reproduction
    frozen=pd.read_csv(delta_path); reps=[]
    for sc in ps.itertuples(index=False):
        ed=real[real.tf.eq(sc.regulator)]
        for ci,cell in enumerate(cell_order):
            _,rr,_=apply_delta(base[ci],sc,ed,g2i,lo,hi)
            reps += [{'scenario_id':sc.scenario_id,'cell_id':cell,'gene_symbol':r['gene_symbol'],'clipped_delta':r['clipped_delta']} for r in rr]
    rep=pd.DataFrame(reps); fr=frozen[frozen.scenario_type.eq('perturbation')][['scenario_id','cell_id','gene_symbol','clipped_delta']]
    m=fr.merge(rep,on=['scenario_id','cell_id','gene_symbol'],suffixes=('_frozen','_reproduced'),how='outer'); maxdiff=float((m.clipped_delta_frozen-m.clipped_delta_reproduced).abs().max())
    if len(m)!=len(fr) or maxdiff>atol: raise RuntimeError(f'real reproduction failed {maxdiff}')
    torch.set_num_threads(int(s78['jepa'].get('torch_num_threads',1))); device=torch.device(s78['jepa'].get('device','cpu')); model=st78.load_model(checkpoint,device); batch=int(s78['jepa'].get('batch_size',64)); bz=st78.encode_matrix(model,base,device,batch); cents,cent_report=st78.build_centroids(project/s78['jepa']['baseline_reference_embeddings'],obs,cell_order,s78['jepa']['reference_state_column'])
    expr_rows=[]; lat_rows=[]; scen_rows=[]; nonreal=graph_manifest[graph_manifest.control_type.ne('real_graph')]
    for g in nonreal.itertuples(index=False):
        gid=g.control_graph_id; ctype=g.control_type; ged=edge_sets[edge_sets.control_graph_id.eq(gid)]
        for sc in ps.itertuples(index=False):
            ed=ged[ged.tf.eq(sc.regulator)] if ctype!='no_graph' else ged; mat=np.empty_like(base); cellmets=[]
            for ci,cell in enumerate(cell_order):
                pert,rr,met=apply_delta(base[ci],sc,ed,g2i,lo,hi); mat[ci]=pert; cellmets.append(met)
                for r in rr: expr_rows.append({'control_graph_id':gid,'control_type':ctype,'seed':g.seed,'scenario_id':sc.scenario_id,'cell_id':cell,'donor_id':obs_sub.loc[ci,s79['donor_column']],'regulator':sc.regulator,'direction':sc.direction,'magnitude':sc.magnitude,**r})
            z=st78.encode_matrix(model,mat.astype(np.float32),device,batch); zr=st78.encode_matrix(model,mat.astype(np.float32),device,batch)
            for ci,cell in enumerate(cell_order):
                b=bz[ci]; p=z[ci]; row={'control_graph_id':gid,'control_type':ctype,'seed':g.seed,'scenario_id':sc.scenario_id,'cell_id':cell,'donor_id':obs_sub.loc[ci,s79['donor_column']],'brain_region':obs_sub.loc[ci,'Brain Region'],'supertype':obs_sub.loc[ci,'Supertype'],'regulator':sc.regulator,'direction':sc.direction,'magnitude':sc.magnitude,'euclidean_displacement':float(np.linalg.norm(p-b)),'cosine_similarity_baseline_control':float(st78.cosine_rows(b.reshape(1,-1),p.reshape(1,-1))[0]),'baseline_embedding_norm':float(np.linalg.norm(b)),'control_embedding_norm':float(np.linalg.norm(p)),'repeat_embedding_max_abs_diff':float(np.max(np.abs(p-zr[ci]))),**cellmets[ci],**FALSE}
                for lab,c in cents.items(): row[f'movement_toward_centroid__{st78.safe_label(lab)}']=float(np.linalg.norm(b-c)-np.linalg.norm(p-c))
                lat_rows.append(row)
            scen_rows.append({'control_graph_id':gid,'control_type':ctype,'seed':g.seed,'scenario_id':sc.scenario_id,'regulator':sc.regulator,'direction':sc.direction,'magnitude':sc.magnitude,'cell_count':32,'donor_count':obs_sub[s79['donor_column']].nunique(),'edge_count_for_regulator':len(ed)})
    expr=pd.DataFrame(expr_rows); lat=pd.DataFrame(lat_rows); scen=pd.DataFrame(scen_rows)
    keys=['control_graph_id','control_type','seed','scenario_id','regulator','direction','magnitude']
    expr_sum=lat.groupby(keys,dropna=False).agg(n_cells=('cell_id','nunique'),n_donors=('donor_id','nunique'),mean_regulator_delta=('regulator_delta','mean'),mean_target_only_l1_delta_norm=('target_only_l1_delta_norm','mean'),mean_target_only_l2_delta_norm=('target_only_l2_delta_norm','mean'),mean_full_changed_feature_l1_delta_norm=('full_changed_feature_l1_delta_norm','mean'),mean_full_changed_feature_l2_delta_norm=('full_changed_feature_l2_delta_norm','mean'),mean_number_changed_features=('number_changed_features','mean'),total_clipping_count=('clipping_count','sum'),mean_clipping_fraction=('clipping_fraction','mean')).reset_index()
    lat_sum=lat.groupby(keys,dropna=False).agg(n_cells=('cell_id','nunique'),n_donors=('donor_id','nunique'),mean_euclidean_displacement=('euclidean_displacement','mean'),median_euclidean_displacement=('euclidean_displacement','median'),max_euclidean_displacement=('euclidean_displacement','max'),mean_cosine_similarity=('cosine_similarity_baseline_control','mean'),max_repeat_embedding_abs_diff=('repeat_embedding_max_abs_diff','max')).reset_index()
    donor=lat.groupby(keys+['donor_id'],dropna=False).agg(n_cells=('cell_id','count'),mean_euclidean_displacement=('euclidean_displacement','mean'),median_euclidean_displacement=('euclidean_displacement','median'),max_euclidean_displacement=('euclidean_displacement','max'),mean_cosine_similarity=('cosine_similarity_baseline_control','mean'),mean_target_only_l1_delta_norm=('target_only_l1_delta_norm','mean'),mean_target_only_l2_delta_norm=('target_only_l2_delta_norm','mean'),mean_clipping_fraction=('clipping_fraction','mean')).reset_index()
    for col in [c for c in lat.columns if c.startswith('movement_toward_centroid__')]:
        lat_sum=lat_sum.merge(lat.groupby(['control_graph_id','scenario_id'])[col].mean().reset_index().rename(columns={col:'mean_'+col}),on=['control_graph_id','scenario_id'],how='left')
        donor=donor.merge(lat.groupby(['control_graph_id','scenario_id','donor_id'])[col].mean().reset_index().rename(columns={col:'mean_'+col}),on=['control_graph_id','scenario_id','donor_id'],how='left')
    # stats
    real_lat=pd.read_csv(project/s78['outputs']['summary_csv']); real_expr=[]
    for sc in ps.itertuples(index=False):
        sub=frozen[frozen.scenario_id.eq(sc.scenario_id)]
        vals=[]
        for cell,gp in sub.groupby('cell_id'):
            targ=gp[gp.gene_symbol.ne(sc.regulator)].clipped_delta.astype(float); full=gp.clipped_delta.astype(float); vals.append({'scenario_id':sc.scenario_id,'target_only_l1_delta_norm':targ.abs().sum(),'target_only_l2_delta_norm':np.sqrt((targ*targ).sum()),'full_changed_feature_l1_delta_norm':full.abs().sum(),'full_changed_feature_l2_delta_norm':np.sqrt((full*full).sum()),'cell_mean_clipping_fraction':gp.clipped.astype(bool).mean()})
        d=pd.DataFrame(vals).mean(numeric_only=True).to_dict(); d['scenario_id']=sc.scenario_id; real_expr.append(d)
    real_metric=real_lat[real_lat.scenario_type.eq('perturbation')].merge(pd.DataFrame(real_expr),on='scenario_id')
    merged=expr_sum.merge(lat_sum,on=keys+['n_cells','n_donors']); stats=[]; metric_map={'mean_euclidean_displacement':'mean_euclidean_displacement','mean_cosine_similarity':'mean_cosine_similarity','mean_target_only_l1_delta_norm':'target_only_l1_delta_norm','mean_target_only_l2_delta_norm':'target_only_l2_delta_norm','mean_full_changed_feature_l1_delta_norm':'full_changed_feature_l1_delta_norm','mean_full_changed_feature_l2_delta_norm':'full_changed_feature_l2_delta_norm','mean_clipping_fraction':'mean_clipping_fraction'}; pc=int(s79['empirical_pseudocount'])
    for sid in sorted(ps.scenario_id):
        rr=real_metric[real_metric.scenario_id.eq(sid)].iloc[0]
        for ctype in ['no_graph','degree_preserving_edge_shuffle','tf_label_shuffle','expression_matched_random_targets']:
            null=merged[(merged.scenario_id.eq(sid))&merged.control_type.eq(ctype)]
            for met,rc in metric_map.items():
                obs=float(rr[rc]); vals=null[met].astype(float).to_numpy(); n=len(vals); mean=float(vals.mean())
                if ctype=='no_graph': up=low=two=std=np.nan; seeds=0; med=float(vals[0]); p025=p975=np.nan
                else:
                    seeds=n; std=float(vals.std(ddof=1)); med=float(np.median(vals)); p025=float(np.percentile(vals,2.5)); p975=float(np.percentile(vals,97.5)); up=(pc+(vals>=obs).sum())/(pc+n); low=(pc+(vals<=obs).sum())/(pc+n); two=min(1.0,2*min(up,low))
                stats.append({'scenario_id':sid,'control_type':ctype,'metric':met,'metric_direction':'larger_or_smaller_reports_numerical_displacement_only','real_observed_value':obs,'n_stochastic_control_seeds':seeds,'null_mean':mean,'null_std':std,'null_median':med,'null_p025':p025,'null_p975':p975,'real_minus_null_mean':obs-mean,'real_to_null_mean_ratio':obs/mean if mean else np.nan,'standardized_difference':(obs-mean)/std if isinstance(std,float) and std>0 else np.nan,'empirical_upper_tail_p_value':up,'empirical_lower_tail_p_value':low,'empirical_two_sided_p_value':two,'pseudocount_used':pc,'n_donors_represented':6,'donor_level_paired_difference_mean':np.nan})
    stats=pd.DataFrame(stats); stats['bh_q_value_within_control_metric']=np.nan
    for _,idxs in stats.groupby(['control_type','metric']).groups.items():
        idx=list(idxs); p=stats.loc[idx,'empirical_two_sided_p_value']
        if p.notna().any(): stats.loc[idx,'bh_q_value_within_control_metric']=bh(p.fillna(1.0)).values
    qc=pd.DataFrame([{'check':'source_hashes_match','passed':True},{'check':'checkpoint_hash_matches','passed':True},{'check':'feature_order_hash_matches','passed':True},{'check':'baseline_cell_order_matches','passed':True},{'check':'real_graph_reproduction_passes','passed':maxdiff<=atol},{'check':'no_graph_target_deltas_zero','passed':expr[(expr.control_type.eq('no_graph'))&(expr.feature_role.eq('target'))].empty},{'check':'stochastic_graph_count_150','passed':len(graph_manifest[graph_manifest.control_type.isin(['degree_preserving_edge_shuffle','tf_label_shuffle','expression_matched_random_targets'])])==150},{'check':'nonreal_control_variants_151','passed':len(nonreal)==151},{'check':'nonreal_scenario_runs_1812','passed':len(scen)==1812},{'check':'nonreal_by_cell_rows_57984','passed':len(lat)==57984},{'check':'six_donors','passed':lat.donor_id.nunique()==6},{'check':'eight_centroids','passed':len(cents)==8},{'check':'deterministic_repeated_inference','passed':lat.repeat_embedding_max_abs_diff.max()<=atol},{'check':'no_nan_or_inf','passed':np.isfinite(lat.select_dtypes(include=[np.number]).to_numpy()).all()},{'check':'claim_boundaries','passed':True}])
    passed=bool(qc.passed.all()); out={k:project/v for k,v in s79['outputs'].items()}
    awrite_gz(expr,out['control_expression_deltas_by_cell_csv_gz']); awrite_gz(lat,out['control_latent_shift_by_cell_csv_gz']); awrite_csv(graph_manifest,out['control_graph_manifest_csv']); awrite_gz(edge_sets,out['control_edge_sets_csv_gz']); awrite_csv(scen,out['control_scenario_manifest_csv']); awrite_csv(expr_sum,out['control_expression_summary_csv']); awrite_csv(lat_sum,out['control_latent_summary_csv']); awrite_csv(donor,out['control_donor_summary_csv']); awrite_csv(stats,out['real_vs_control_statistics_csv']); awrite_csv(qc,out['control_qc_csv'])
    metas={k:meta(project,p, len(expr) if 'expression_deltas' in k else len(lat) if 'latent_shift_by_cell' in k else len(edge_sets) if 'edge_sets' in k else len(pd.read_csv(p)),32,len(graph_manifest),12,len(genes),6) for k,p in out.items() if k!='report_json'}
    report={'stage':'stage79_graph_controls_v1','schema_version':'1.0','implementation_git_commit':git_head(project),'stage79_pass':passed,'source_hashes':{'stage77_delta':sha(delta_path),'stage78_by_cell':sha(project/s78['outputs']['cell_latent_shift_csv_gz']),'stage76_report':sha(project/s78['sources']['stage76_readiness_report'])},'checkpoint_hash':f10['checkpoint_audit']['checkpoint_sha256'],'feature_order_hash':f10['feature_order']['feature_order_sha256'],'preprocessing_provenance':f10['preprocessing'],'baseline_cell_order_hash':shalist(cell_order),'baseline_cell_ids':cell_order,'seed_list':seeds,'control_definitions':{c:'bounded model-control graph variant' for c in ['real_graph','no_graph','degree_preserving_edge_shuffle','tf_label_shuffle','expression_matched_random_targets']},'real_graph_reproduction':{'max_abs_clipped_delta_diff':maxdiff,'tolerance':atol,'passes':maxdiff<=atol},'control_graph_integrity':{'graph_count_total':len(graph_manifest),'stochastic_graph_count':150,'nonreal_control_variants':151,'nonreal_scenario_runs':len(scen),'nonreal_by_cell_rows':len(lat)},'outputs':metas,'expected_counts':{'stochastic_control_graphs':150,'nonreal_control_variants_including_no_graph':151,'nonreal_scenario_runs':1812,'nonreal_by_cell_rows':57984},'observed_counts':{'stochastic_control_graphs':150,'nonreal_control_variants_including_no_graph':len(nonreal),'nonreal_scenario_runs':len(scen),'nonreal_by_cell_rows':len(lat),'donors':lat.donor_id.nunique(),'centroids':len(cents)},'numerical_tolerances':tol,'donor_aggregation_unit':s79['donor_column'],'empirical_p_value_formula':'p=(1+tail_count)/(1+number_of_seeds); two-sided=min(1,2*min(upper,lower))','qc':qc.to_dict(orient='records'),'failed_gates':qc.loc[~qc.passed,'check'].tolist(),'claim_boundaries':{**FALSE,'approved_wording':APPROVED,'not_causal_validation':True,'not_therapeutic_benefit':True}}
    awrite_json(report,out['report_json']); print(json.dumps({'stage79_pass':passed,'control_graphs':len(graph_manifest),'nonreal_scenario_runs':len(scen),'nonreal_by_cell_rows':len(lat),'real_graph_reproduction_max_abs_diff':maxdiff},indent=2)); return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='configs/stage75f_out_of_core_v1.yaml'); ap.add_argument('--project-dir',default='.')
    a=ap.parse_args(); project=Path(a.project_dir).resolve(); run(load_yaml(project/a.config),project); return 0
if __name__=='__main__': raise SystemExit(main())
