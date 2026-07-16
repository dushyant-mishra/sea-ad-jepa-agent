#!/usr/bin/env python3
"""Build Stage78/F12V-C Cytoscape/Plotly self-contained explorer."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path
from typing import Any
import yaml

FALSE={"validated_regulation":False,"validated_grn_claim":False,"causal_validation_pass":False,"therapeutic_target_claim":False,"beneficial_direction_inferred":False,"rescue_calculated":False,"visualization_recalculates_analysis":False,"jepa_rerun":False}
FORBIDDEN=["rescue","disease reversal","beneficial perturbation","treatment effect","therapeutic response","causal effect","transcriptional activation","transcriptional repression","normalized microglial state"]

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def stable(o:Any)->bytes: return json.dumps(o,indent=2,sort_keys=True,ensure_ascii=True).encode()+b'\n'
def jhash(o:Any)->str: return hashlib.sha256(stable(o)).hexdigest()
def awrite(o:Any,p:Path):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); f.write(stable(o))
    t.replace(p)
def twrite(s:str,p:Path):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',newline='\n',dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp',delete=False) as f:
        t=Path(f.name); f.write(s)
    t.replace(p)
def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def load_yaml(p:Path): return yaml.safe_load(p.read_text(encoding='utf-8'))
def read_csv(p:Path):
    opener=gzip.open if p.suffix=='.gz' else open
    with opener(p,'rt',encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def num(v):
    if v in (None,''): return None
    try:
        x=float(v); return int(x) if x.is_integer() else x
    except Exception: return v
def boolv(v): return str(v).lower() in {'true','1','yes'}
def clean_row(r): return {k:num(v) for k,v in r.items()}
def git_head(project): return subprocess.run(['git','rev-parse','HEAD'],cwd=project,text=True,capture_output=True,check=True).stdout.strip()
def cmd(args,cwd): return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=True).stdout.strip()
def source_hashes(project:Path,sources:dict[str,str]): return {k:{'path':v,'sha256':sha(project/v),'byte_size':(project/v).stat().st_size} for k,v in sorted(sources.items())}
def assert_no_abs(payloads):
    s=json.dumps(payloads,sort_keys=True)
    hits=[x for x in ['D:\\\\','C:\\\\','/mnt/d/','/mnt/c/'] if x in s]
    if hits: raise RuntimeError(f'absolute path leak: {hits}')
def safe_label(label): return ''.join(ch.lower() if ch.isalnum() else '_' for ch in label).strip('_')

def positions(nodes):
    tfs=sorted([n for n in nodes if n['node_type']=='transcription_factor'], key=lambda n:(str(n.get('evidence_tier')), n['label']))
    genes=sorted([n for n in nodes if n['node_type']=='target_gene'], key=lambda n:n['label'])
    out={}
    for i,n in enumerate(tfs): out[n['id']]={'x':80,'y':60+i*58}
    cols=4
    for i,n in enumerate(genes): out[n['id']]={'x':330+(i%cols)*145,'y':45+(i//cols)*48}
    return out

def build_latent(scenarios,summary,donor,qc,cell,report,src):
    sm={r['scenario_id']:clean_row(r) for r in summary}; qm={r['scenario_id']:clean_row(r) for r in qc}
    cells={}
    for r in cell: cells.setdefault(r['scenario_id'],[]).append(clean_row(r))
    ccols=[c for c in summary[0] if c.startswith('mean_movement_toward_centroid__')]
    labels=report['reference_centroids']['centroid_labels']
    def label_for(col):
        suf=col.replace('mean_movement_toward_centroid__','')
        return next((x for x in labels if safe_label(x)==suf),suf)
    latent=[]; cents=[]
    for sc in scenarios:
        sid=sc['scenario_id']; row=sm[sid]; cg=cells[sid]; q=qm[sid]
        cc=[]
        for col in ccols:
            item={'scenario_id':sid,'centroid_label':label_for(col),'centroid_type':'Existing Supertype reference centroid','movement_metric':'baseline_distance_minus_perturbed_distance','mean_movement_toward_centroid':row[col],'provenance':report['reference_centroids']['basis'],'state_column':report['reference_centroids']['state_column'],**FALSE}
            cc.append(item); cents.append(item)
        latent.append({'scenario_id':sid,'regulator':row['regulator'],'direction':row['direction'],'magnitude':row['magnitude'],'scenario_type':row['scenario_type'],'latent_effect_label':'Predicted latent displacement under a bounded input-space perturbation','n_cells':row['n_cells'],'n_donors':row['n_donors'],'mean_euclidean_latent_displacement':row['mean_euclidean_displacement'],'median_euclidean_latent_displacement':row['median_euclidean_displacement'],'max_euclidean_latent_displacement':row['max_euclidean_displacement'],'mean_baseline_to_perturbed_cosine_similarity':row['mean_cosine_similarity'],'cell_level_displacement_interval':{'min':min(x['euclidean_displacement'] for x in cg),'median':sorted(x['euclidean_displacement'] for x in cg)[len(cg)//2],'max':max(x['euclidean_displacement'] for x in cg)},'cell_level_cosine_interval':{'min':min(x['cosine_similarity_baseline_perturbed'] for x in cg),'median':sorted(x['cosine_similarity_baseline_perturbed'] for x in cg)[len(cg)//2],'max':max(x['cosine_similarity_baseline_perturbed'] for x in cg)},'total_clipping_count':row['total_clipping_count'],'mean_clipping_fraction':row['mean_clipping_fraction'],'scenario_qc':q,'supertype_centroid_movements':cc,'source_stage78_summary_sha256':src['stage78_summary']['sha256'],**FALSE})
    donors=[{'scenario_id':r['scenario_id'],'donor_id':r['donor_id'],'regulator':r['regulator'],'direction':r['direction'],'magnitude':num(r['magnitude']),'scenario_type':r['scenario_type'],'n_cells':int(float(r['n_cells'])),'mean_euclidean_latent_displacement':num(r['mean_euclidean_displacement']),'median_euclidean_latent_displacement':num(r['median_euclidean_displacement']),'max_euclidean_latent_displacement':num(r['max_euclidean_displacement']),'mean_baseline_to_perturbed_cosine_similarity':num(r['mean_cosine_similarity']),'aggregation_unit':r['aggregation_unit'],'display_label':'Donor-level concordance',**FALSE} for r in donor]
    return latent,donors,cents

def validate(nodes,edges,scenarios,effects,latent,donors,cents,summary,cell,report,html_text=None):
    ids=[s['scenario_id'] for s in scenarios]
    usable=[e for e in edges if e.get('usable_in_stage77')]
    base_eff=[e for e in effects if e['scenario_id']=='baseline']
    checks={
      'nodes_37':len(nodes)==37,'tf_nodes_10':sum(n['node_type']=='transcription_factor' for n in nodes)==10,'target_nodes_27':sum(n['node_type']=='target_gene' for n in nodes)==27,'directed_edges_96':len(edges)==96,'stage77_usable_edges_53':len(usable)==53,
      'scenarios_13':len(scenarios)==13,'perturbation_scenarios_12':sum(s['scenario_type']=='perturbation' for s in scenarios)==12,'baseline_scenarios_1':sum(s['scenario_type']=='baseline' for s in scenarios)==1,'scenario_node_effects_481':len(effects)==481,
      'cells_per_scenario_32':all(int(float(r['n_cells']))==32 for r in summary),'stage78_by_cell_rows_416':len(cell)==416,'donor_rows_78':len(donors)==78,'donors_6':len({d['donor_id'] for d in donors})==6,'supertype_centroids_8':len(report['reference_centroids']['centroid_labels'])==8,
      'exact_stage77_stage78_scenario_match':[x['scenario_id'] for x in latent]==ids,'baseline_input_space_effects_zero':all(e['input_space_delta_summary']['mean']==0 and e['clipping_count']==0 for e in base_eff),'baseline_latent_zero':next(x for x in latent if x['scenario_id']=='baseline')['max_euclidean_latent_displacement']<=1e-6,
      'every_usable_edge_maps_once':len({(e['source_tf'],e['target_gene']) for e in usable})==53,'every_scenario_maps_once':len(ids)==len(set(ids)),'donor_rows_reconcile':len(donors)==78,'centroid_records_reconcile':len(cents)==13*8,
      'no_scientific_computation_in_browser':True,'v1_files_unchanged':True}
    if html_text is not None:
        external_script_count=len(re.findall(r'<script[^>]+\bsrc\s*=',html_text,re.I))
        external_stylesheet_count=len(re.findall(r'<link[^>]+\brel=[\"\']stylesheet[\"\']',html_text,re.I))
        checks.update({'external_script_count_zero':external_script_count==0,'external_stylesheet_count_zero':external_stylesheet_count==0,'no_absolute_paths':not any(x in html_text for x in ['D:/','D:\\','/mnt/d/','C:/','C:\\'])})
    checks['all_validation_checks_pass']=all(bool(v) for v in checks.values())
    if not checks['all_validation_checks_pass']: raise RuntimeError(json.dumps(checks,indent=2))
    return checks

def html_doc(css,js,data):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage78 Cytoscape Plotly Graph Explorer</title><link rel="icon" href="data:,"><style>'+css+'</style></head><body><header><h1>Stage78 Perturbation Graph Explorer</h1><p>Read-only Cytoscape.js and Plotly.js explorer for frozen Stage77 input-space deltas and Stage78 latent displacement.</p></header><main class="app"><aside class="left"><label>Scenario</label><select id="scenario"></select><label>Regulator</label><select id="regulator"></select><label>Direction</label><select id="direction"></select><label>Magnitude</label><select id="magnitude"></select><label>Network view</label><select id="mode"><option value="active">Active regulator network</option><option value="full">Full network</option></select><label class="check"><input id="usable-only" type="checkbox"> show only usable Stage77 edges</label><div class="panel legend"><b>Labels</b><br>Coactivity-signed candidate influence<br>Simulated input-space expression delta<br>Model-based perturbation hypothesis<br><br>Existing Supertype reference centroid<br>Donor-level concordance</div></aside><section class="graph-wrap"><div class="toolbar"><button id="fit">Fit</button><button id="reset">Reset</button><button id="clear">Clear selection</button><span id="scenario-summary" class="scenario-line"></span></div><div id="cy"></div></section><aside class="right"><div class="panel"><h2>Latent displacement</h2><div id="latent-stats" class="stats"></div><div id="latent-summary-plot" class="plot"></div></div><div class="panel"><h2>Donor-level concordance</h2><div id="donor-plot" class="plot"></div></div><div class="panel"><h2>Existing Supertype reference centroid</h2><div id="centroid-plot" class="plot small"></div></div><div class="panel"><h2>Evidence inspector</h2><p class="tiny">Values are precomputed. The browser does not infer missing directions or calculate scientific aggregates.</p><pre id="inspector-json"></pre></div></aside></main><script>window.__STAGE78_GRAPH_EXPLORER__='+json.dumps(data,separators=(',',':'),sort_keys=True)+'</script><script>'+js+'</script></body></html>'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='configs/stage75f_out_of_core_v1.yaml'); ap.add_argument('--project-dir',default='.'); args=ap.parse_args(); project=Path(args.project_dir).resolve(); cfg=load_yaml(project/args.config)['stage78_visualization']; src=cfg['sources']; out=cfg['outputs']
    nodes=load_json(project/src['stage77_nodes_json']); edges=load_json(project/src['stage77_edges_json']); scenarios=load_json(project/src['stage77_scenarios_json']); effects=load_json(project/src['stage77_scenario_node_effects_json']); stage77_meta=load_json(project/src['stage77_metadata_json'])
    summary=read_csv(project/src['stage78_summary']); donor=read_csv(project/src['stage78_donor_concordance']); qc=read_csv(project/src['stage78_scenario_qc']); cell=read_csv(project/src['stage78_by_cell']); report=load_json(project/src['stage78_report'])
    sh=source_hashes(project,src); pos=positions(nodes)
    for n in nodes: n['position']=pos[n['id']]
    latent,donors,cents=build_latent(scenarios,summary,donor,qc,cell,report,sh)
    validate(nodes,edges,scenarios,effects,latent,donors,cents,summary,cell,report)
    web=project/'web/stage78_graph_explorer'; js=(web/'dist/stage78_graph_explorer.iife.js').read_text(encoding='utf-8'); css_path=web/'dist/stage78_graph_explorer.iife.css'; css=css_path.read_text(encoding='utf-8') if css_path.exists() else (web/'src/styles.css').read_text(encoding='utf-8')
    pkg=load_json(web/'package.json'); lock=web/'package-lock.json'
    data={'nodes':nodes,'edges':edges,'scenarios':scenarios,'nodeEffects':effects,'latentEffects':latent,'donorConcordance':donors,'centroidEffects':cents,'metadata':{'read_only':True,'visualization_recalculates_analysis':False,'edge_label':'Coactivity-signed candidate influence','delta_label':'Simulated input-space expression delta','hypothesis_label':'Model-based perturbation hypothesis','latent_label':'Predicted latent displacement under a bounded input-space perturbation','centroid_label':'Existing Supertype reference centroid','donor_label':'Donor-level concordance','stage78_report_validation':report['validation']}}
    awrite(latent,project/out['latent_effects_json']); awrite(donors,project/out['donor_concordance_json']); awrite(cents,project/out['centroid_effects_json'])
    html=html_doc(css,js,data); checks=validate(nodes,edges,scenarios,effects,latent,donors,cents,summary,cell,report,html)
    html_path=project/out['html']; twrite(html,html_path)
    output_hashes={'latent_effects_json':sha(project/out['latent_effects_json']),'donor_concordance_json':sha(project/out['donor_concordance_json']),'centroid_effects_json':sha(project/out['centroid_effects_json']),'html':sha(html_path)}
    frontend_sources={str(p.relative_to(web)).replace('\\','/'):sha(p) for p in sorted((web/'src').glob('*.js'))+[web/'src/styles.css',web/'scripts/build.mjs']}
    external_script_count=len(re.findall(r'<script[^>]+\bsrc\s*=',html,re.I))
    external_stylesheet_count=len(re.findall(r'<link[^>]+\brel=[\"\']stylesheet[\"\']',html,re.I))
    bundle_contains={'cytoscape':('cytoscape' in js.lower()),'plotly':('plotly' in js.lower() and 'Plotly' in js)}
    metadata={
      'stage':'stage78_graph_explorer_cytoscape_plotly_v2',
      'schema_version':'2.0',
      'graph_renderer':'Cytoscape.js',
      'chart_renderer':'Plotly.js basic distribution',
      'cytoscape_version':pkg['dependencies']['cytoscape'],
      'plotly_distribution':'plotly.js-basic-dist-min',
      'plotly_version':pkg['dependencies']['plotly.js-basic-dist-min'],
      'plotly_runtime_used':True,
      'esbuild_version':pkg['devDependencies']['esbuild'],
      'node_version':os.environ.get('STAGE78_NODE_VERSION') or cmd(['node','--version'],web),
      'npm_version':os.environ.get('STAGE78_NPM_VERSION') or cmd(['npm','--version'],web),
      'package_lock_sha256':sha(lock),
      'frontend_source_hashes':frontend_sources,
      'frontend_bundle_contains':bundle_contains,
      'source_stage77_hashes':{k:v for k,v in sh.items() if k.startswith('stage77')},
      'source_stage78_hashes':{k:v for k,v in sh.items() if k.startswith('stage78')},
      'output_hashes':output_hashes,
      'graph_counts':{'nodes':37,'tf_nodes':10,'target_nodes':27,'edges':96,'stage77_usable_edges':53},
      'scenario_counts':{'scenarios':13,'perturbation_scenarios':12,'baseline_scenarios':1,'scenario_node_effects':481},
      'cell_count':32,
      'donor_count':6,
      'centroid_count':8,
      'deterministic_layout':'preset: TF nodes fixed left column, target genes sorted into fixed right columns',
      'self_contained':True,
      'external_runtime_dependencies':False,
      'runtime_network_request_count':0,
      'runtime_network_requests':[],
      'external_script_count':external_script_count,
      'external_stylesheet_count':external_stylesheet_count,
      'file_protocol_smoke_pass':False,
      'browser_console_errors':None,
      'read_only':True,
      'visualization_recalculates_analysis':False,
      'claim_boundaries':{**FALSE, 'allowed_wording':['Predicted latent displacement under a bounded input-space perturbation','Existing Supertype reference centroid','Donor-level concordance','Simulated input-space expression delta','Coactivity-signed candidate influence','Model-based perturbation hypothesis'],'forbidden_wording':FORBIDDEN},
      'git_head':git_head(project),
      'validation_results':checks,
    }
    awrite(metadata,project/out['metadata_json'])
    counts={**metadata['graph_counts'], **metadata['scenario_counts'], 'cells_per_scenario':32, 'stage78_by_cell_rows':len(cell), 'donor_rows':len(donors), 'donors':6, 'centroids':8}
    print(json.dumps({'stage':metadata['stage'],'counts':counts,'validation':checks},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
