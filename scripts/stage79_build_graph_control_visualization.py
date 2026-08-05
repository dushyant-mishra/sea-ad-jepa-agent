#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path
from typing import Any
import pandas as pd, yaml

APPROVED="Stage79 interpretation describes how the frozen real-graph outputs compare with bounded control distributions. These are model-based control comparisons and do not establish causal regulation, biological benefit, or therapeutic validity."
FALSE={"validated_regulation":False,"validated_grn_claim":False,"causal_validation_pass":False,"therapeutic_target_claim":False,"visualization_recalculates_analysis":False,"jepa_rerun":False,"stage79_rerun":False}
ABS=[r'(?i)\b[A-Z]:[\\/][A-Za-z0-9_ .()\-\\/]+',r'/mnt/[cd]/[A-Za-z0-9_ .()\-/]+']

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def stable(o:Any)->bytes: return json.dumps(o,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b'\n'
def awrite(o:Any,p:Path):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); f.write(stable(o))
    t.replace(p)
def awrite_gz(o:Any,p:Path):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as raw: t=Path(raw.name)
    with gzip.GzipFile(filename='',mode='wb',fileobj=t.open('wb'),mtime=0) as f: f.write(stable(o))
    t.replace(p)
def twrite(s:str,p:Path):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='\n',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); f.write(s)
    t.replace(p)
def yload(p): return yaml.safe_load(p.read_text(encoding='utf-8'))
def jload(p): return json.loads(p.read_text(encoding='utf-8'))
def git_head(project): return subprocess.run(['git','rev-parse','HEAD'],cwd=project,text=True,capture_output=True,check=True).stdout.strip()
def cmd(args,cwd): return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=True).stdout.strip()
def clean(v):
    if pd.isna(v): return None
    try:
        x=float(v)
        if x.is_integer(): return int(x)
        return x
    except Exception: return v
def records(df): return [{k:clean(v) for k,v in r.items()} for r in df.to_dict(orient='records')]
def hits(payload):
    s=payload if isinstance(payload,str) else json.dumps(payload,sort_keys=True)
    out=[]
    for pat in ABS: out += re.findall(pat,s)
    return sorted(set(out))
def source_hashes(project,src): return {k:{'path':v,'sha256':sha(project/v),'byte_size':(project/v).stat().st_size} for k,v in sorted(src.items())}

def html_doc(css,js,data):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage79 Graph Control Explorer</title><link rel="icon" href="data:"><style>'+css+'</style></head><body><header><h1>Stage79 Graph Control Explorer</h1><p>Model-based graph-control comparison for frozen rare-microglia regulatory hypotheses.</p></header><main class="app"><aside class="left"><div class="panel story"><h2>What question is this view answering?</h2><div class="story-grid"><b>Scenario</b><span id="storyScenario" class="story-value"></span><b>Metric</b><span id="storyMetric" class="story-value"></span><span id="storyMetricHelp" class="story-help"></span><b>Comparison</b><span id="storyControl" class="story-value"></span><span id="storyControlHelp" class="story-help"></span></div><div id="storyVerdict" class="verdict"></div></div><label>Scenario</label><select id="scenario"></select><label>Regulator</label><select id="regulator"></select><label>Direction</label><select id="direction"></select><label>Magnitude</label><select id="magnitude"></select><label>Metric</label><select id="metric"></select><label>Compare against</label><select id="controlType"></select><label>Control graph / seed</label><select id="controlGraph"></select><label>Network shown</label><select id="graphMode"><option value="real">frozen candidate graph</option><option value="control">selected control graph</option></select><label>Edge view</label><select id="edgeView"><option value="active">active regulator only</option><option value="all">all edges in selected graph</option></select><label>Donor display</label><select id="seedMode"><option value="mean">average across control seeds</option><option value="selected">selected seed only</option></select><div class="panel boundary"><b>Boundary:</b> This is a model-based comparison. It does not establish causal regulation, biological benefit, therapeutic validity, or validated targets.</div></aside><section class="graph-wrap"><div class="toolbar"><button id="fit">Fit</button><button id="reset">Reset</button><button id="clear">Clear selection</button><span id="summary" class="scenario-line"></span></div><div id="cy"></div></section><aside class="right"><div class="panel"><h2>Candidate graph versus controls</h2><div id="distPlot" class="plot"></div><p id="distributionNote" class="notice"></p></div><div class="panel"><h2>How different is it?</h2><div id="effectPlot" class="plot small"></div><pre id="effectText"></pre></div><div class="panel"><h2>Donor-level paired differences</h2><div id="donorPlot" class="plot"></div><p id="donorNote" class="notice"></p></div><div class="panel"><h2>Control sanity check</h2><div id="diagnostics" class="diagnostics"></div></div><div class="panel"><h2>Audit details</h2><pre id="inspector"></pre></div></aside></main><script>window.__STAGE79_GRAPH_CONTROL_EXPLORER__='+json.dumps(data,separators=(",",":"),sort_keys=True,allow_nan=False)+'</script><script>'+js+'</script></body></html>'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='configs/stage75f_out_of_core_v1.yaml'); ap.add_argument('--project-dir',default='.'); a=ap.parse_args(); project=Path(a.project_dir).resolve(); cfg=yload(project/a.config)['stage79_control_visualization']; src=cfg['sources']; out={k:project/v for k,v in cfg['outputs'].items()}
    interp_report=jload(project/src['stage79_interpretation_report_json']); stage79_report=jload(project/src['stage79_graph_controls_report_json'])
    if not interp_report.get('stage79_interpretation_pass'): raise RuntimeError('interpretation report did not pass')
    graphs=pd.read_csv(project/src['stage79_control_graph_manifest_csv']); edges=pd.read_csv(project/src['stage79_control_edge_sets_csv_gz']); scen=pd.read_csv(project/src['stage79_control_scenario_manifest_csv']); lat_sum=pd.read_csv(project/src['stage79_control_latent_summary_csv']); donor=pd.read_csv(project/src['stage79_control_donor_summary_csv']); stats=pd.read_csv(project/src['stage79_real_vs_control_statistics_csv']); edge_div=pd.read_csv(project/src['stage79_control_edge_diversity_csv']); diag=pd.read_csv(project/src['stage79_null_distribution_diagnostics_csv']); donor_diff=pd.read_csv(project/src['stage79_donor_paired_differences_csv']); interp=pd.read_csv(project/src['stage79_scenario_control_interpretation_csv']); reg=pd.read_csv(project/src['stage79_regulator_control_summary_csv'])
    stage77_nodes=jload(project/src['stage77_nodes_json']); stage77_edges=jload(project/src['stage77_edges_json']); stage77_effects=jload(project/src['stage77_scenario_node_effects_json']); stage78_latent=jload(project/src['stage78_latent_effects_json']); stage78_donor=jload(project/src['stage78_donor_concordance_json']); stage78_centroids=jload(project/src['stage78_centroid_effects_json']); stage78_meta=jload(project/src['stage78_metadata_json'])
    dist=[]
    for r in interp.itertuples(index=False):
        metric=r.metric; src_table=lat_sum if metric in ['mean_euclidean_displacement','mean_cosine_similarity'] else pd.read_csv(project/src['stage79_control_scenario_manifest_csv']).iloc[0:0]
        if metric not in ['mean_euclidean_displacement','mean_cosine_similarity']:
            es=pd.read_csv(project/'results/tables/stage79_control_expression_summary_v1.csv'); vals=es[es.scenario_id.eq(r.scenario_id)&es.control_type.eq(r.control_type)][metric].astype(float).tolist()
        else:
            vals=lat_sum[lat_sum.scenario_id.eq(r.scenario_id)&lat_sum.control_type.eq(r.control_type)][metric].astype(float).tolist()
        dist.append({**{k:clean(v) for k,v in r._asdict().items()},'null_values':[clean(v) for v in vals]})
    distributions={'rows':dist,'scenarios':sorted(interp.scenario_id.unique()),'metrics':sorted(interp.metric.unique()),'control_types':sorted(interp.control_type.unique())}
    donor_payload=records(donor_diff)
    networks={'graphs':records(graphs),'edges':records(edges),'real_stage77_nodes':stage77_nodes,'real_stage77_edges':stage77_edges,'stage77_scenario_node_effects':stage77_effects,'stage78_latent_effects':stage78_latent,'stage78_donor_concordance':stage78_donor,'stage78_centroid_effects':stage78_centroids}
    interpretation={'scenario_control_interpretation':records(interp),'null_distribution_diagnostics':records(diag),'regulator_control_summary':records(reg),'edge_diversity':records(edge_div),'approved_wording':APPROVED,'claim_boundaries':FALSE}
    awrite(distributions,out['control_distributions_json']); awrite(donor_payload,out['control_donor_differences_json']); awrite_gz(networks,out['control_networks_json_gz']); awrite(interpretation,out['control_interpretation_json'])
    web=project/'web/stage78_graph_explorer'; js=(web/'dist/stage79_graph_control_explorer.iife.js').read_text(encoding='utf-8'); cssp=web/'dist/stage79_graph_control_explorer.iife.css'; css=cssp.read_text(encoding='utf-8') if cssp.exists() else (web/'src/stage79/styles.css').read_text(encoding='utf-8')
    data={'distributions':distributions,'donor_differences':donor_payload,'networks':networks,'diagnostics':records(diag),'metadata':{'read_only':True,'approved_wording':APPROVED,'stage78_metadata':stage78_meta.get('stage'),'stage79_pass':stage79_report.get('stage79_pass')}}
    html=html_doc(css,js,data)
    html='\n'.join(line.rstrip() for line in html.splitlines())+'\n'
    if re.search(r'<script[^>]+\bsrc\s*=',html,re.I) or re.search(r'<link[^>]+\brel=["\']stylesheet["\']',html,re.I): raise RuntimeError('external script/style tag found')
    if hits(html): raise RuntimeError(f'absolute path leak in html: {hits(html)}')
    twrite(html,out['html'])
    pkg=jload(web/'package.json'); lock=web/'package-lock.json'
    payload_hashes={k:{'path':str(p.relative_to(project)).replace('\\','/'),'sha256':sha(p),'byte_size':p.stat().st_size} for k,p in out.items() if k!='metadata_json'}
    frontend={str(p.relative_to(web)).replace('\\','/'):sha(p) for p in sorted((web/'src/stage79').glob('*'))+[web/'scripts/build-stage79.mjs']}
    metadata={'stage':'stage79_graph_control_explorer_cytoscape_plotly_v3','schema_version':'3.0','stage79_implementation_commit':stage79_report['implementation_git_commit'],'stage79_freeze_commit':'3f6e380034a13fa3bdae0bf18bd0b09d84cc5f1b','implementation_git_commit':git_head(project),'source_hashes':source_hashes(project,src),'interpretation_output_hashes':interp_report['output_hashes'],'visualization_payload_hashes':payload_hashes,'html_hash':sha(out['html']),'frontend_source_hashes':frontend,'package_lock_sha256':sha(lock),'cytoscape_version':pkg['dependencies']['cytoscape'],'plotly_version':pkg['dependencies']['plotly.js-basic-dist-min'],'esbuild_version':pkg['devDependencies']['esbuild'],'graph_counts':{'total_graphs':len(graphs),'edge_rows':len(edges),'real_stage77_nodes':len(stage77_nodes)},'scenario_counts':{'perturbation_scenarios':len(distributions['scenarios']),'control_scenario_rows':len(scen)},'donor_counts':{'donors':int(donor.donor_id.nunique()),'donor_difference_rows':len(donor_diff)},'metric_counts':{'metrics':len(distributions['metrics']),'interpretation_rows':len(interp)},'zero_variance_diagnostic_counts':int(diag.frozen_statistics_zero_variance.sum()),'distinct_control_input_hash_counts':interp_report['diagnostics'],'static_self_contained_validation_pass':True,'self_contained_static_validation':{'cytoscape_bundled':'cytoscape' in js.lower(),'plotly_bundled':'plotly' in js.lower(),'external_script_tags':0,'external_stylesheet_links':0,'absolute_paths_in_generated_outputs':False},'browser_smoke_execution_status':'not_run_tool_unavailable','file_protocol_smoke_results':{'pass':None,'protocol':'file://','artifact':'results/visualization/stage79_graph_control_explorer_cytoscape_plotly_v3.html','console_errors':None},'runtime_network_request_count':None,'claim_boundaries':{**FALSE,'approved_wording':APPROVED},'read_only':True,'visualization_recalculates_analysis':False,'jepa_rerun':False,'stage79_rerun':False}
    if hits({'metadata':metadata,'distributions':distributions,'interpretation':interpretation}): raise RuntimeError('absolute path leak in json payloads')
    awrite(metadata,out['metadata_json'])
    print(json.dumps({'stage79_visualization_pass':True,'graphs':len(graphs),'scenarios':len(distributions['scenarios']),'metrics':len(distributions['metrics']),'browser_smoke_execution_status':'not_run_tool_unavailable','runtime_network_request_count':None},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
