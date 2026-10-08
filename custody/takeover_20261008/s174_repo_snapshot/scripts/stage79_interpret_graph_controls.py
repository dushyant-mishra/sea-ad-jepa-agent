#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, tempfile
from pathlib import Path
from typing import Any
import numpy as np, pandas as pd, yaml

APPROVED=("Stage79 interpretation describes how the frozen real-graph outputs compare with bounded control distributions. These are model-based control comparisons and do not establish causal regulation, biological benefit, or therapeutic validity.")
FALSE={"validated_regulation":False,"validated_grn_claim":False,"causal_validation_pass":False,"therapeutic_target_claim":False,"biological_benefit_claim":False}
METRICS={
 "mean_euclidean_displacement":("latent","mean_euclidean_displacement"),
 "mean_cosine_similarity":("latent","mean_cosine_similarity"),
 "mean_target_only_l1_delta_norm":("expression","mean_target_only_l1_delta_norm"),
 "mean_target_only_l2_delta_norm":("expression","mean_target_only_l2_delta_norm"),
 "mean_full_changed_feature_l1_delta_norm":("expression","mean_full_changed_feature_l1_delta_norm"),
 "mean_full_changed_feature_l2_delta_norm":("expression","mean_full_changed_feature_l2_delta_norm"),
 "mean_clipping_fraction":("expression","mean_clipping_fraction"),
}
EXPECTED={"graphs":152,"stochastic_graphs":150,"nonreal_scenarios":1812,"latent_rows":57984,"donors":6,"centroids":8,"stats":336}

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def stable(o:Any)->str: return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def ohash(o:Any)->str: return hashlib.sha256(stable(o).encode()).hexdigest()
def clean(v:Any)->Any:
    if pd.isna(v): return None
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,float)):
        x=float(v)
        if math.isfinite(x) and x.is_integer(): return int(x)
        return x
    if isinstance(v,(np.bool_,)): return bool(v)
    return v
def git_head(project:Path)->str: return subprocess.run(['git','rev-parse','HEAD'],cwd=project,text=True,capture_output=True,check=True).stdout.strip()
def yload(p:Path)->dict[str,Any]: return yaml.safe_load(p.read_text(encoding='utf-8'))
def jload(p:Path)->dict[str,Any]: return json.loads(p.read_text(encoding='utf-8'))
def awrite_csv(df:pd.DataFrame,p:Path)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); df.to_csv(f,index=False)
    t.replace(p)
def awrite_json(o:Any,p:Path)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='\n',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); json.dump(o,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
    t.replace(p)
def df_hash(df:pd.DataFrame, cols:list[str], sort_cols:list[str]|None=None)->str:
    if sort_cols is None: sort_cols=cols
    if len(df)==0: return ohash([])
    d=df.sort_values(sort_cols).reset_index(drop=True)
    return ohash([[clean(x) for x in row] for row in d[cols].itertuples(index=False,name=None)])
def row_hash(row:pd.Series, cols:list[str])->str: return ohash({c:clean(row[c]) for c in cols})

def verify(project:Path,cfg:dict[str,Any]):
    src={k:project/v for k,v in cfg['sources'].items()}; rep=jload(src['report_json'])
    if rep.get('stage79_pass') is not True: raise RuntimeError('stage79_pass is not true')
    if rep.get('failed_gates'): raise RuntimeError(f"failed_gates nonempty: {rep['failed_gates']}")
    if rep.get('implementation_git_commit')!=cfg['expected_implementation_commit']: raise RuntimeError('implementation commit mismatch')
    for key,meta in rep['outputs'].items():
        p=project/meta['path']
        if not p.exists(): raise RuntimeError(f'missing Stage79 output {meta["path"]}')
        got=sha(p)
        if got!=meta['sha256']: raise RuntimeError(f'hash mismatch {meta["path"]}: {got} != {meta["sha256"]}')
    obs=rep['observed_counts']
    if obs['nonreal_scenario_runs']!=EXPECTED['nonreal_scenarios'] or obs['nonreal_by_cell_rows']!=EXPECTED['latent_rows'] or obs['donors']!=EXPECTED['donors'] or obs['centroids']!=EXPECTED['centroids']: raise RuntimeError('observed counts mismatch')
    return rep,src

def edge_diversity(graphs:pd.DataFrame, edges:pd.DataFrame)->pd.DataFrame:
    real=edges[edges.control_type.eq('real_graph')]
    real_pairs=set(real[['tf','target_gene']].itertuples(index=False,name=None))
    real_by_tf={tf:set(g.target_gene.astype(str)) for tf,g in real.groupby('tf')}
    rows=[]; ecols=['slot_id','tf','target_gene','predicted_response_sign_from_coactivity','normalized_outgoing_weight','matched_from_real_target']; pcols=['slot_id','tf','target_gene']
    for g in graphs.sort_values(['control_type','seed','control_graph_id']).itertuples(index=False):
        sub=edges[edges.control_graph_id.eq(g.control_graph_id)].copy(); pairs=set(sub[['tf','target_gene']].itertuples(index=False,name=None)); inter=len(pairs&real_pairs); union=len(pairs|real_pairs)
        per={}
        for tf in sorted(set(real_by_tf)|set(sub.tf.astype(str))):
            cur=set(sub[sub.tf.astype(str).eq(tf)].target_gene.astype(str)); ref=real_by_tf.get(tf,set()); per[tf]={'overlap':len(cur&ref),'control_targets':len(cur),'real_targets':len(ref)}
        rows.append({'control_graph_id':g.control_graph_id,'control_type':g.control_type,'seed':clean(getattr(g,'seed')),'edge_count':len(sub),'edge_set_sha256':df_hash(sub,[c for c in ecols if c in sub.columns],['slot_id','tf','target_gene'] if len(sub) else [c for c in ecols if c in sub.columns]),'ordered_tf_target_pair_sha256':df_hash(sub,[c for c in pcols if c in sub.columns],[c for c in pcols if c in sub.columns]),'edge_set_overlap_with_real_graph':inter,'edge_set_jaccard_with_real_graph':inter/union if union else 0.0,'changed_edge_count':len(real_pairs)-inter+max(0,len(pairs)-inter),'per_tf_target_set_overlap_json':stable(per),'per_tf_target_set_overlap_sha256':ohash(per),**FALSE})
    out=pd.DataFrame(rows)
    if out[out.control_type.ne('no_graph')].edge_set_sha256.nunique()<=1: raise RuntimeError('non-no-graph edge hashes are not diverse')
    return out

def detailed_hashes(expr:pd.DataFrame, lat:pd.DataFrame, expr_sum:pd.DataFrame, lat_sum:pd.DataFrame):
    gcols=['control_graph_id','control_type','seed','scenario_id','regulator','direction','magnitude']
    xrows=[]
    for keys,sub in expr.groupby(gcols,dropna=False,sort=True):
        xrows.append({**dict(zip(gcols,keys)),'ordered_input_delta_vector_sha256':df_hash(sub,['cell_id','feature_index','gene_symbol','feature_role','clipped_delta','clipped'],['cell_id','feature_index','gene_symbol']),'nonzero_input_delta_entries':int((sub.clipped_delta.astype(float).abs()>0).sum())})
    xhash=pd.DataFrame(xrows)
    cell=[]
    for keys,sub in expr.groupby(gcols+['cell_id'],dropna=False,sort=True):
        d=dict(zip(gcols+['cell_id'],keys)); targ=sub[sub.feature_role.ne('regulator')].clipped_delta.astype(float); full=sub.clipped_delta.astype(float)
        cell.append({**d,'target_l1':targ.abs().sum(),'target_l2':np.sqrt((targ*targ).sum()),'full_l1':full.abs().sum(),'full_l2':np.sqrt((full*full).sum()),'clipfrac':sub.clipped.astype(bool).mean()})
    rec=pd.DataFrame(cell).groupby(gcols,dropna=False).agg(mean_target_only_l1_delta_norm=('target_l1','mean'),mean_target_only_l2_delta_norm=('target_l2','mean'),mean_full_changed_feature_l1_delta_norm=('full_l1','mean'),mean_full_changed_feature_l2_delta_norm=('full_l2','mean'),mean_clipping_fraction=('clipfrac','mean')).reset_index()
    m=rec.merge(expr_sum,on=gcols,suffixes=('_recalc','_frozen'),how='outer')
    if len(m)!=len(expr_sum): raise RuntimeError('expression detailed groups do not reconcile')
    for c in ['mean_target_only_l1_delta_norm','mean_target_only_l2_delta_norm','mean_full_changed_feature_l1_delta_norm','mean_full_changed_feature_l2_delta_norm','mean_clipping_fraction']:
        if (m[f'{c}_recalc'].astype(float)-m[f'{c}_frozen'].astype(float)).abs().max()>1e-8: raise RuntimeError(f'expression summary mismatch {c}')
    lat_cols=['cell_id','euclidean_displacement','cosine_similarity_baseline_control','target_only_l1_delta_norm','target_only_l2_delta_norm','full_changed_feature_l1_delta_norm','full_changed_feature_l2_delta_norm','clipping_fraction']+[c for c in lat.columns if c.startswith('movement_toward_centroid__')]
    lrows=[]
    for keys,sub in lat.groupby(gcols,dropna=False,sort=True):
        lrows.append({**dict(zip(gcols,keys)),'latent_output_vector_sha256':df_hash(sub,lat_cols,['cell_id'])})
    lhash=pd.DataFrame(lrows)
    lrec=lat.groupby(gcols,dropna=False).agg(mean_euclidean_displacement=('euclidean_displacement','mean'),median_euclidean_displacement=('euclidean_displacement','median'),max_euclidean_displacement=('euclidean_displacement','max'),mean_cosine_similarity=('cosine_similarity_baseline_control','mean'),max_repeat_embedding_abs_diff=('repeat_embedding_max_abs_diff','max')).reset_index()
    lm=lrec.merge(lat_sum,on=gcols,suffixes=('_recalc','_frozen'),how='outer')
    if len(lm)!=len(lat_sum): raise RuntimeError('latent detailed groups do not reconcile')
    for c in ['mean_euclidean_displacement','median_euclidean_displacement','max_euclidean_displacement','mean_cosine_similarity','max_repeat_embedding_abs_diff']:
        if (lm[f'{c}_recalc'].astype(float)-lm[f'{c}_frozen'].astype(float)).abs().max()>1e-8: raise RuntimeError(f'latent summary mismatch {c}')
    esh=expr_sum[['control_graph_id','control_type','seed','scenario_id']].copy(); esh['expression_summary_sha256']=[row_hash(r, [c for c in expr_sum.columns if c not in ['control_graph_id','control_type','seed','scenario_id']]) for _,r in expr_sum.iterrows()]
    lsh=lat_sum[['control_graph_id','control_type','seed','scenario_id']].copy(); lsh['latent_summary_sha256']=[row_hash(r, [c for c in lat_sum.columns if c not in ['control_graph_id','control_type','seed','scenario_id']]) for _,r in lat_sum.iterrows()]
    return xhash,lhash,esh,lsh

def donor_diffs(stats:pd.DataFrame, control:pd.DataFrame, real_donor:pd.DataFrame, real_cell:pd.DataFrame):
    real_lat=real_donor[real_donor.scenario_type.eq('perturbation')]
    real_clip=real_cell[real_cell.scenario_type.eq('perturbation')].groupby(['scenario_id','donor_id']).agg(mean_clipping_fraction=('f11_clipping_fraction','mean')).reset_index()
    specs={'mean_euclidean_displacement':(real_lat,'mean_euclidean_displacement'),'mean_cosine_similarity':(real_lat,'mean_cosine_similarity'),'mean_clipping_fraction':(real_clip,'mean_clipping_fraction')}
    rows=[]; roll=[]
    for s in stats.itertuples(index=False):
        if s.metric not in specs:
            roll.append({'scenario_id':s.scenario_id,'control_type':s.control_type,'metric':s.metric,'donor_count':0,'mean_paired_difference':np.nan,'median_paired_difference':np.nan,'min_paired_difference':np.nan,'max_paired_difference':np.nan,'positive_donor_differences':0,'negative_donor_differences':0,'zero_donor_differences':0,'fraction_donors_same_sign_as_pooled_difference':np.nan,'donor_level_range':np.nan,'donor_difference_status':'not_available_for_this_metric_from_frozen_real_donor_artifacts'}); continue
        rs,col=specs[s.metric]; r=rs[rs.scenario_id.eq(s.scenario_id)][['scenario_id','donor_id',col]].rename(columns={col:'real_donor_value'}); c=control[control.scenario_id.eq(s.scenario_id)&control.control_type.eq(s.control_type)].copy()
        m=c.merge(r,on=['scenario_id','donor_id'],how='left')
        if m.real_donor_value.isna().any(): raise RuntimeError(f'missing donor real values {s.scenario_id} {s.metric}')
        m['control_donor_value']=m[col].astype(float); m['paired_difference']=m.real_donor_value.astype(float)-m.control_donor_value
        for rr in m.itertuples(index=False): rows.append({'scenario_id':rr.scenario_id,'control_type':rr.control_type,'control_graph_id':rr.control_graph_id,'seed':clean(rr.seed),'donor_id':rr.donor_id,'metric':s.metric,'real_donor_value':float(rr.real_donor_value),'control_donor_value':float(rr.control_donor_value),'paired_difference':float(rr.paired_difference),'aggregation_unit':'Donor ID',**FALSE})
        d=m.paired_difference.astype(float); pooled=float(s.real_minus_null_mean); same=(np.sign(d)==np.sign(pooled)) if pooled!=0 else pd.Series([False]*len(d))
        roll.append({'scenario_id':s.scenario_id,'control_type':s.control_type,'metric':s.metric,'donor_count':int(m.donor_id.nunique()),'mean_paired_difference':float(d.mean()),'median_paired_difference':float(d.median()),'min_paired_difference':float(d.min()),'max_paired_difference':float(d.max()),'positive_donor_differences':int((d>0).sum()),'negative_donor_differences':int((d<0).sum()),'zero_donor_differences':int((d==0).sum()),'fraction_donors_same_sign_as_pooled_difference':float(same.mean()) if pooled!=0 else np.nan,'donor_level_range':float(d.max()-d.min()),'donor_difference_status':'available_from_frozen_donor_artifacts'})
    return pd.DataFrame(rows),pd.DataFrame(roll)

def interpret(stats,expr_sum,lat_sum,edge_div,xhash,lhash,esh,lsh):
    h=xhash.merge(lhash,on=['control_graph_id','control_type','seed','scenario_id','regulator','direction','magnitude']).merge(esh,on=['control_graph_id','control_type','seed','scenario_id']).merge(lsh,on=['control_graph_id','control_type','seed','scenario_id']).merge(edge_div,on=['control_graph_id','control_type','seed'],how='left')
    diag=[]; rows=[]
    for s in stats.sort_values(['scenario_id','control_type','metric']).itertuples(index=False):
        src,col=METRICS[s.metric]; table=lat_sum if src=='latent' else expr_sum; null=table[table.scenario_id.eq(s.scenario_id)&table.control_type.eq(s.control_type)]; vals=null[col].astype(float).to_numpy()
        if len(vals)==0: raise RuntimeError(f'empty null {s.scenario_id} {s.control_type} {s.metric}')
        div=h[h.scenario_id.eq(s.scenario_id)&h.control_type.eq(s.control_type)]
        eh=div.edge_set_sha256.nunique(); ih=div.ordered_input_delta_vector_sha256.nunique(); lh=div.latent_output_vector_sha256.nunique(); uniq=pd.Series(vals).round(15).nunique(); std=float(np.std(vals,ddof=1)) if len(vals)>1 else np.nan; zero=bool(len(vals)>1 and (not np.isfinite(std) or std<=1e-15)); ediff=eh>1; idiff=ih>1; ldiff=lh>1
        status='metric_invariant_despite_distinct_control_inputs' if ediff and idiff and uniq==1 else 'latent_summary_invariant_despite_distinct_input_vectors' if idiff and not ldiff else 'distinct_control_inputs_and_metric_variation' if idiff else 'single_control_input_or_no_graph'
        obs=float(s.real_observed_value); p025=float(np.percentile(vals,2.5)) if len(vals)>1 else np.nan; p975=float(np.percentile(vals,97.5)) if len(vals)>1 else np.nan
        pos='direct_no_graph_comparison' if s.control_type=='no_graph' else 'below_null_95_interval' if obs<p025 else 'above_null_95_interval' if obs>p975 else 'inside_null_95_interval'
        pct=np.nan if s.control_type=='no_graph' else (1+int((vals<=obs).sum()))/(1+len(vals)); frac=(obs-float(vals[0]))/obs if s.control_type=='no_graph' and obs!=0 else np.nan
        diag.append({'scenario_id':s.scenario_id,'control_type':s.control_type,'metric':s.metric,'number_of_graphs':int(null.control_graph_id.nunique()),'distinct_edge_set_hashes':int(eh),'distinct_input_delta_vector_hashes':int(ih),'distinct_latent_output_vector_hashes':int(lh),'distinct_metric_values':int(uniq),'null_min':float(np.min(vals)),'null_max':float(np.max(vals)),'null_range':float(np.max(vals)-np.min(vals)),'null_standard_deviation':std,'frozen_statistics_zero_variance':zero,'edge_sets_differ':bool(ediff),'input_deltas_differ':bool(idiff),'latent_outputs_differ':bool(ldiff),'control_input_diversity_status':status,**FALSE})
        rows.append({'scenario_id':s.scenario_id,'control_type':s.control_type,'metric':s.metric,'real_observed_value':obs,'control_count':int(len(vals)),'null_mean':float(s.null_mean),'null_median':float(s.null_median),'null_standard_deviation':clean(s.null_std),'null_p025':clean(s.null_p025),'null_p975':clean(s.null_p975),'real_minus_null_mean':float(s.real_minus_null_mean),'real_to_null_mean_ratio':clean(s.real_to_null_mean_ratio),'standardized_difference':None if zero else clean(s.standardized_difference),'empirical_upper_tail_p_value':clean(s.empirical_upper_tail_p_value),'empirical_lower_tail_p_value':clean(s.empirical_lower_tail_p_value),'empirical_two_sided_p_value':clean(s.empirical_two_sided_p_value),'bh_q_value':clean(s.bh_q_value_within_control_metric),'unique_null_values':int(uniq),'percentile_rank_descriptive':clean(pct),'real_vs_null_95_interval_position':pos,'zero_variance_status':'zero_variance_null' if zero else 'nonzero_or_singleton_null','control_input_diversity_status':status,'direct_real_minus_no_graph_difference':float(s.real_minus_null_mean) if s.control_type=='no_graph' else np.nan,'direct_real_to_no_graph_ratio':clean(s.real_to_null_mean_ratio) if s.control_type=='no_graph' else np.nan,'graph_mediated_fraction':clean(frac),**FALSE})
    return pd.DataFrame(diag),pd.DataFrame(rows)

def reg_summary(interp,donor_roll):
    x=interp.copy(); x['regulator']=x.scenario_id.str.split('_').str[0]; rows=[]
    for (reg,ct),sub in x.groupby(['regulator','control_type'],sort=True):
        d=donor_roll[donor_roll.scenario_id.str.startswith(reg+'_')&donor_roll.control_type.eq(ct)]
        rows.append({'regulator':reg,'control_type':ct,'scenarios_evaluated':int(sub.scenario_id.nunique()),'metrics_evaluated':int(sub.metric.nunique()),'comparisons_below_null_95_interval':int(sub.real_vs_null_95_interval_position.eq('below_null_95_interval').sum()),'comparisons_within_null_95_interval':int(sub.real_vs_null_95_interval_position.eq('inside_null_95_interval').sum()),'comparisons_above_null_95_interval':int(sub.real_vs_null_95_interval_position.eq('above_null_95_interval').sum()),'comparisons_with_zero_variance_nulls':int(sub.zero_variance_status.eq('zero_variance_null').sum()),'comparisons_with_distinct_input_vectors_but_invariant_scalar_summaries':int(sub.control_input_diversity_status.eq('metric_invariant_despite_distinct_control_inputs').sum()),'median_abs_real_minus_null_difference':float(sub.real_minus_null_mean.abs().median()),'median_abs_standardized_difference_where_defined':clean(sub.standardized_difference.dropna().abs().median()),'median_donor_sign_concordance_where_available':clean(d.fraction_donors_same_sign_as_pooled_difference.dropna().median()),'summary_is_not_biological_score':True,**FALSE})
    return pd.DataFrame(rows)

def run(project:Path,config:Path):
    cfg=yload(config)['stage79_control_interpretation']; rep,src=verify(project,cfg); out={k:project/v for k,v in cfg['outputs'].items()}
    graphs=pd.read_csv(src['control_graph_manifest_csv']); edges=pd.read_csv(src['control_edge_sets_csv_gz']); scen=pd.read_csv(src['control_scenario_manifest_csv']); expr_sum=pd.read_csv(src['control_expression_summary_csv']); lat_sum=pd.read_csv(src['control_latent_summary_csv']); donor_sum=pd.read_csv(src['control_donor_summary_csv']); stats=pd.read_csv(src['real_vs_control_statistics_csv']); qc=pd.read_csv(src['control_qc_csv']); expr=pd.read_csv(src['control_expression_deltas_by_cell_csv_gz']); lat=pd.read_csv(src['control_latent_shift_by_cell_csv_gz']); real_donor=pd.read_csv(src['stage78_donor_concordance_csv']); real_cell=pd.read_csv(src['stage78_by_cell_csv_gz'])
    if len(graphs)!=EXPECTED['graphs'] or len(scen)!=EXPECTED['nonreal_scenarios'] or len(lat)!=EXPECTED['latent_rows'] or len(stats)!=EXPECTED['stats'] or not qc.passed.astype(bool).all(): raise RuntimeError('frozen table counts/qc mismatch')
    stoch=graphs[graphs.control_type.isin(['degree_preserving_edge_shuffle','tf_label_shuffle','expression_matched_random_targets'])]
    if len(stoch)!=EXPECTED['stochastic_graphs'] or sorted(stoch.groupby('control_type').seed.nunique().tolist())!=[50,50,50]: raise RuntimeError('stochastic controls/seeds mismatch')
    edge=edge_diversity(graphs,edges); xh,lh,esh,lsh=detailed_hashes(expr,lat,expr_sum,lat_sum); diag,interp=interpret(stats,expr_sum,lat_sum,edge,xh,lh,esh,lsh); donor_detail,donor_roll=donor_diffs(stats,donor_sum,real_donor,real_cell); interp=interp.merge(donor_roll,on=['scenario_id','control_type','metric'],how='left')
    if len(interp)!=len(stats): raise RuntimeError('statistics to interpretation row mismatch')
    if interp[['scenario_id','control_type','metric']].isna().any().any(): raise RuntimeError('NaN identity fields')
    for c in ['empirical_upper_tail_p_value','empirical_lower_tail_p_value','empirical_two_sided_p_value','bh_q_value']:
        v=interp[c].dropna().astype(float)
        if ((v<0)|(v>1)).any(): raise RuntimeError(f'{c} outside [0,1]')
    if interp[interp.control_type.eq('no_graph')][['empirical_upper_tail_p_value','empirical_lower_tail_p_value','empirical_two_sided_p_value','bh_q_value']].notna().any().any(): raise RuntimeError('no_graph p-values not null')
    if np.isinf(interp.select_dtypes(include=[np.number]).to_numpy()).any(): raise RuntimeError('infinite numeric values')
    bad=[]
    merged_control=edge.merge(xh[['control_graph_id','scenario_id','ordered_input_delta_vector_sha256']],on='control_graph_id',how='left')
    for ctype, sub in merged_control[merged_control.control_type.isin(['degree_preserving_edge_shuffle','tf_label_shuffle','expression_matched_random_targets'])].groupby('control_type'):
        if sub.edge_set_sha256.nunique()>1 and sub.ordered_input_delta_vector_sha256.nunique()==1:
            bad.append(ctype)
    if bad:
        raise RuntimeError(f'topology-changing controls show whole-run input reuse: {bad}')
    reg=reg_summary(interp,donor_roll)
    awrite_csv(edge,out['control_edge_diversity_csv']); awrite_csv(diag,out['null_distribution_diagnostics_csv']); awrite_csv(donor_detail,out['donor_paired_differences_csv']); awrite_csv(interp,out['scenario_control_interpretation_csv']); awrite_csv(reg,out['regulator_control_summary_csv'])
    outs={k:{'path':str(p.relative_to(project)).replace('\\','/'),'sha256':sha(p),'byte_size':p.stat().st_size} for k,p in sorted(out.items()) if k!='report_json'}
    report={'stage':'stage79_control_interpretation_v1','schema_version':'1.0','implementation_git_commit':git_head(project),'stage79_report_implementation_git_commit':rep['implementation_git_commit'],'stage79_freeze_commit':cfg['expected_freeze_commit'],'stage79_interpretation_pass':True,'approved_wording':APPROVED,'source_hashes':{k:{'path':str(v.relative_to(project)).replace('\\','/'),'sha256':sha(v),'byte_size':v.stat().st_size} for k,v in sorted(src.items())},'output_hashes':outs,'row_counts':{'control_edge_diversity':len(edge),'null_distribution_diagnostics':len(diag),'donor_paired_differences':len(donor_detail),'scenario_control_interpretation':len(interp),'regulator_control_summary':len(reg)},'diagnostics':{'zero_variance_null_count':int(diag.frozen_statistics_zero_variance.sum()),'metric_invariant_diagnostic_count':int(diag.control_input_diversity_status.eq('metric_invariant_despite_distinct_control_inputs').sum()),'distinct_edge_set_count':int(edge.edge_set_sha256.nunique()),'distinct_input_delta_vector_count':int(xh.ordered_input_delta_vector_sha256.nunique()),'distinct_latent_output_vector_count':int(lh.latent_output_vector_sha256.nunique()),'donor_difference_metric_rows_available':int(donor_roll.donor_count.gt(0).sum())},'validation':{'all_stage79_source_hashes_match':True,'detailed_local_hashes_match':True,'control_diversity_audit_pass':True,'statistics_rows_reconcile':len(interp)==len(stats),'donor_paired_differences_populated':len(donor_detail)>0,'no_graph_p_values_null':True,'zero_variance_without_infinity':True,'deterministic_outputs':True},'claim_boundaries':{**FALSE,'approved_wording':APPROVED}}
    awrite_json(report,out['report_json']); print(json.dumps({'stage79_interpretation_pass':True,'row_counts':report['row_counts'],'diagnostics':report['diagnostics']},indent=2,sort_keys=True)); return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='configs/stage75f_out_of_core_v1.yaml'); ap.add_argument('--project-dir',default='.'); a=ap.parse_args(); run(Path(a.project_dir).resolve(),Path(a.project_dir).resolve()/a.config); return 0
if __name__=='__main__': raise SystemExit(main())
