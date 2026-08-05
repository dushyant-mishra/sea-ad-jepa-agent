import cytoscape from 'cytoscape';
import Plotly from 'plotly.js-basic-dist-min';
import './styles.css';

window.cytoscape = cytoscape;
window.Plotly = Plotly;
const data = window.__STAGE79_GRAPH_CONTROL_EXPLORER__;
const $ = id => document.getElementById(id);
const state = { scenario: 'ELF1_down_0p10', metric: 'mean_euclidean_displacement', controlType: 'degree_preserving_edge_shuffle', graphMode: 'real', edgeView: 'active', seedMode: 'mean', graphId: null };
let cy;
const edgeByGraph = new Map();
for (const e of data.networks.edges) {
  if (!edgeByGraph.has(e.control_graph_id)) edgeByGraph.set(e.control_graph_id, []);
  edgeByGraph.get(e.control_graph_id).push(e);
}
const metricLabels = {
  mean_euclidean_displacement: 'Average JEPA latent movement',
  mean_cosine_similarity: 'Baseline-to-perturbed similarity',
  mean_target_only_l1_delta_norm: 'Total propagated target-expression change',
  mean_target_only_l2_delta_norm: 'Concentrated target-expression change',
  mean_full_changed_feature_l1_delta_norm: 'Total input-space change',
  mean_full_changed_feature_l2_delta_norm: 'Concentrated input-space change',
  mean_clipping_fraction: 'Fraction clipped to training range',
};
const metricHelp = {
  mean_euclidean_displacement: 'How far the frozen JEPA embedding moved after the simulated input change.',
  mean_cosine_similarity: 'How similar the perturbed embedding remains to baseline. Values near 1 mean tiny latent movement.',
  mean_target_only_l1_delta_norm: 'Sum of propagated target-gene input changes, ignoring direction.',
  mean_target_only_l2_delta_norm: 'A target-change magnitude that emphasizes larger target shifts.',
  mean_full_changed_feature_l1_delta_norm: 'Total input-space change including the TF input and propagated targets.',
  mean_full_changed_feature_l2_delta_norm: 'Input-space change magnitude emphasizing larger feature shifts.',
  mean_clipping_fraction: 'How often simulated values hit the observed training-data range bounds.',
};
const controlLabels = {
  no_graph: 'No propagated target edges',
  degree_preserving_edge_shuffle: 'Same graph shape, shuffled targets',
  tf_label_shuffle: 'Same targets, shuffled regulator labels',
  expression_matched_random_targets: 'Expression-matched random targets',
};
const controlHelp = {
  no_graph: 'Only the regulator input is changed. No target-gene propagation is applied.',
  degree_preserving_edge_shuffle: 'Keeps how many edges each regulator has, but rewires targets to test topology dependence.',
  tf_label_shuffle: 'Keeps target sets but swaps regulator labels to test whether TF identity matters.',
  expression_matched_random_targets: 'Replaces targets with genes of similar baseline expression patterns.',
};
const directionLabels = { up: 'increased', down: 'decreased' };
function sortedUnique(xs){ return [...new Set(xs)].sort(); }
function fill(sel, vals, labeler = v => v){ sel.innerHTML=''; for (const v of vals) sel.add(new Option(labeler(v), v)); }
function scenarioParts(id){ const p=id.split('_'); return {regulator:p[0], direction:p[1], magnitude:p[2].replace('p','.')}; }
function scenarioLabel(id){ const p=scenarioParts(id); const size=Number(p.magnitude) <= 0.1 ? 'small' : 'larger'; return `${p.regulator} ${directionLabels[p.direction] || p.direction}, ${size} input change (${p.magnitude})`; }
function graphLabel(id){ if (id === 'real_graph') return 'Frozen candidate graph'; if (id === 'no_graph') return 'No propagated edges'; const m=String(id).match(/seed_(\d+)/); return m ? `Control seed ${m[1]}` : id; }
function fmt(v){
  if (v === null || v === undefined || Number.isNaN(Number(v))) return 'undefined';
  const x = Number(v);
  if (x === 0) return '0';
  if (Math.abs(x) < 0.001 || Math.abs(x) >= 10000) return x.toExponential(3);
  return x.toLocaleString(undefined, { maximumSignificantDigits: 5 });
}
function stablePositions(nodes, edges){
  const tfs = [...new Set(nodes.filter(n => n.data.node_type === 'transcription_factor').map(n => n.data.id))].sort();
  const targets = [...new Set(nodes.filter(n => n.data.node_type !== 'transcription_factor').map(n => n.data.id))].sort();
  const targetByTf = new Map();
  for (const e of edges) {
    if (!targetByTf.has(e.data.source)) targetByTf.set(e.data.source, []);
    targetByTf.get(e.data.source).push(e.data.target);
  }
  const pos = new Map();
  tfs.forEach((tf, i) => pos.set(tf, { x: 80, y: 70 + i * 90 }));
  const activeTf = scenarioParts($('scenario').value).regulator;
  const activeTargets = [...new Set(targetByTf.get(activeTf) || [])].sort();
  activeTargets.forEach((g, i) => pos.set(g, { x: 330 + (i % 3) * 170, y: 40 + Math.floor(i / 3) * 58 }));
  targets.filter(g => !pos.has(g)).forEach((g, i) => pos.set(g, { x: 900 + (i % 2) * 155, y: 40 + Math.floor(i / 2) * 48 }));
  for (const n of nodes) n.position = pos.get(n.data.id) || { x: 80, y: 80 };
}
function initControls(){
  const scenarios = data.distributions.scenarios;
  fill($('scenario'), scenarios, scenarioLabel); fill($('regulator'), sortedUnique(scenarios.map(s => scenarioParts(s).regulator)));
  fill($('direction'), sortedUnique(scenarios.map(s => scenarioParts(s).direction)), v => directionLabels[v] || v); fill($('magnitude'), sortedUnique(scenarios.map(s => scenarioParts(s).magnitude)), v => Number(v) <= 0.1 ? `small (${v})` : `larger (${v})`);
  fill($('metric'), data.distributions.metrics, v => metricLabels[v] || v); fill($('controlType'), data.distributions.control_types, v => controlLabels[v] || v);
  $('scenario').value=state.scenario; $('metric').value=state.metric; $('controlType').value=state.controlType;
  const p=scenarioParts(state.scenario); $('regulator').value=p.regulator; $('direction').value=p.direction; $('magnitude').value=p.magnitude;
  updateGraphOptions();
}
function updateGraphOptions(){
  const type=$('controlType').value; const ids=data.networks.graphs.filter(g => g.control_type===type).map(g => g.control_graph_id).sort();
  fill($('controlGraph'), ids, graphLabel); if (!ids.includes(state.graphId)) state.graphId=ids[0] || 'no_graph'; $('controlGraph').value=state.graphId;
}
function scenarioFromTriplet(){ return `${$('regulator').value}_${$('direction').value}_${$('magnitude').value.replace('.','p')}`; }
function graphElements(){
  const mode=$('graphMode').value; const sid=$('scenario').value; const reg=scenarioParts(sid).regulator; const graphId = mode==='real' ? 'real_graph' : $('controlGraph').value;
  const rawEdges=(edgeByGraph.get(graphId)||[]).filter(e => $('edgeView').value==='all' || e.tf===reg);
  const nodes=new Map();
  nodes.set(reg,{data:{id:reg,label:reg,node_type:'transcription_factor'}});
  for (const e of rawEdges){ nodes.set(e.tf,{data:{id:e.tf,label:e.tf,node_type:'transcription_factor'}}); nodes.set(e.target_gene,{data:{id:e.target_gene,label:e.target_gene,node_type:'target_gene'}}); }
  if (mode==='control' && graphId==='no_graph') nodes.set(reg,{data:{id:reg,label:reg,node_type:'transcription_factor'}});
  const nodeEls=[...nodes.values()].sort((a,b)=>a.data.id.localeCompare(b.data.id));
  const edgeEls=rawEdges.map((e,i)=>({data:{id:`${graphId}_${i}_${e.tf}_${e.target_gene}`,source:e.tf,target:e.target_gene,label:mode==='real'?'Coactivity-signed candidate influence':'Control-only propagated edge',plain_label:mode==='real'?'candidate edge from frozen evidence graph':'control edge for comparison only',control_only:mode!=='real',evidence_support:mode==='real'?e.evidence_support:'null_control',control_type:e.control_type,seed:e.seed,weight:e.normalized_outgoing_weight,motif_support_class:e.motif_support_class}}));
  stablePositions(nodeEls, edgeEls);
  return [...nodeEls,...edgeEls];
}
function initGraph(){
  cy=cytoscape({container:$('cy'),elements:graphElements(),layout:{name:'preset',fit:true,padding:28},style:[
    {selector:'node',style:{label:'data(label)',width:34,height:34,'font-size':10,'background-color':'#e7eef8','border-color':'#6b7a90','border-width':1}},
    {selector:'node[node_type="transcription_factor"]',style:{'background-color':'#f3d38b','shape':'round-rectangle'}},
    {selector:'edge',style:{width:2,'line-color':'#7b8798','target-arrow-color':'#7b8798','target-arrow-shape':'triangle','curve-style':'bezier','font-size':8,label:'','text-rotation':'autorotate','text-opacity':0,'text-background-color':'#ffffff','text-background-opacity':0.88,'text-background-padding':2}},
    {selector:'edge.show-label',style:{label:'data(plain_label)','text-opacity':0.9}},
    {selector:'edge[control_only]',style:{'line-style':'dotted','line-color':'#9aa3af','target-arrow-color':'#9aa3af'}},
    {selector:':selected',style:{'border-width':3,'border-color':'#111827','line-color':'#111827','target-arrow-color':'#111827'}}
  ]});
  cy.on('select', 'node, edge', ev => { if (ev.target.isEdge()) ev.target.addClass('show-label'); renderInspector(ev.target.data()); });
  cy.on('unselect', 'edge', ev => ev.target.removeClass('show-label'));
  cy.on('mouseover', 'edge', ev => ev.target.addClass('show-label'));
  cy.on('mouseout', 'edge', ev => { if (!ev.target.selected()) ev.target.removeClass('show-label'); });
}
function updateGraph(){ cy.elements().remove(); cy.add(graphElements()); cy.layout({name:'preset',fit:true,padding:28}).run(); }
function selectedDistribution(){ return data.distributions.rows.find(r => r.scenario_id===$('scenario').value && r.control_type===$('controlType').value && r.metric===$('metric').value); }
function axisFor(vals, observed){
  const nums=[...vals, observed].filter(v=>v!==null && v!==undefined && Number.isFinite(Number(v))).map(Number);
  if (!nums.length) return {};
  const lo=Math.min(...nums), hi=Math.max(...nums); const span=hi-lo; const center=(hi+lo)/2;
  const pad=span > 0 ? span*0.18 : Math.max(Math.abs(center)*0.02, 1e-9);
  return { range:[lo-pad, hi+pad], tickformat: Math.max(Math.abs(lo),Math.abs(hi)) < 0.001 ? '.2e' : undefined };
}
function verdict(row){
  if (!row) return '';
  if (row.control_type === 'no_graph') return `Direct comparison: frozen candidate graph differs from no-edge baseline by ${fmt(row.real_minus_null_mean)} for ${metricLabels[row.metric] || row.metric}.`;
  const pos = row.real_vs_null_95_interval_position;
  const label = pos === 'above_null_95_interval' ? 'above' : pos === 'below_null_95_interval' ? 'below' : 'within';
  const caution = row.zero_variance_status === 'zero_variance_null' ? ' The control values are identical across seeds, so standardized differences are undefined.' : '';
  return `For this scenario, the frozen candidate graph is ${label} the ${controlLabels[row.control_type] || row.control_type} comparison range for ${metricLabels[row.metric] || row.metric}.${caution}`;
}
function updateStory(row){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value;
  $('storyScenario').textContent = scenarioLabel(sid);
  $('storyMetric').textContent = metricLabels[metric] || metric;
  $('storyMetricHelp').textContent = metricHelp[metric] || 'Frozen numerical metric from the Stage79 audit.';
  $('storyControl').textContent = controlLabels[type] || type;
  $('storyControlHelp').textContent = controlHelp[type] || 'Bounded control comparison from Stage79.';
  $('storyVerdict').textContent = verdict(row);
}
function plotDistribution(){
  const row=selectedDistribution(); if(!row) return;
  const vals=row.null_values || []; const constant=vals.length>1 && new Set(vals.map(v=>Number(v).toPrecision(14))).size===1;
  $('distributionNote').textContent = constant ? 'All 50 control seeds produced the same metric value.' : 'Each gray point is a precomputed control graph value.';
  const yaxis={title:metricLabels[row.metric] || row.metric, ...axisFor(vals, row.real_observed_value)};
  if (row.control_type==='no_graph') {
    Plotly.newPlot('distPlot',[{type:'bar',x:['Frozen candidate graph','No propagated edges'],y:[row.real_observed_value,row.null_mean],marker:{color:['#365a8c','#8a8f99']},text:[fmt(row.real_observed_value),fmt(row.null_mean)],textposition:'outside'}],{margin:{t:20,l:70,r:10,b:46},yaxis}, {displayModeBar:false});
  } else {
    Plotly.newPlot('distPlot',[{type:'box',y:vals,name:'control seeds',boxpoints:'all',jitter:0.35,marker:{color:'#7b8798'},hovertemplate:'control %{y:.3e}<extra></extra>'},{type:'scatter',mode:'markers+text',x:['candidate'],y:[row.real_observed_value],name:'frozen candidate graph',marker:{size:12,color:'#2f5d9f'},text:['candidate'],textposition:'top center',hovertemplate:'candidate %{y:.3e}<extra></extra>'}],{margin:{t:20,l:70,r:10,b:48},yaxis}, {displayModeBar:false});
  }
}
function plotEffect(){
  const r=selectedDistribution(); if(!r) return;
  const rows=[
    ['Candidate minus control mean', fmt(r.real_minus_null_mean)],
    ['Candidate / control mean', fmt(r.real_to_null_mean_ratio)],
    ['Standardized difference', r.zero_variance_status==='zero_variance_null' ? 'undefined: null variance is zero' : fmt(r.standardized_difference)],
    ['Empirical p value', r.zero_variance_status==='zero_variance_null' ? 'descriptive only; zero-variance null' : fmt(r.empirical_two_sided_p_value)],
    ['BH q value', r.zero_variance_status==='zero_variance_null' ? 'descriptive only; zero-variance null' : fmt(r.bh_q_value)],
    ['Percentile rank', fmt(r.percentile_rank_descriptive)],
  ];
  Plotly.newPlot('effectPlot',[{type:'table',header:{values:['Question','Answer'],fill:{color:'#e8edf5'},align:'left'},cells:{values:[rows.map(x=>x[0]),rows.map(x=>x[1])],align:'left',height:24}}],{margin:{t:8,l:6,r:6,b:8}}, {displayModeBar:false});
  $('effectText').textContent = `${r.real_vs_null_95_interval_position}; ${r.control_input_diversity_status}. These are descriptive model-control comparisons, not biological proof.`;
}
function plotDonors(){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value, graph=$('controlGraph').value;
  let rows=data.donor_differences.filter(d=>d.scenario_id===sid && d.metric===metric && d.control_type===type);
  if(type!=='no_graph' && $('seedMode').value==='selected') rows=rows.filter(d=>d.control_graph_id===graph);
  if(type!=='no_graph' && $('seedMode').value==='mean'){
    const by={}; for(const r of rows){ by[r.donor_id]??=[]; by[r.donor_id].push(r.paired_difference); }
    rows=Object.entries(by).map(([donor,vals])=>({donor_id:donor,paired_difference:vals.reduce((a,b)=>a+b,0)/vals.length}));
  }
  const vals=rows.map(r=>Number(r.paired_difference));
  $('donorNote').textContent = vals.length && vals.every(v=>Math.abs(v) < 1e-12) ? 'All donor paired differences are approximately zero.' : 'Positive means numerically larger for the frozen candidate graph, not better.';
  Plotly.newPlot('donorPlot',[{type:'bar',x:rows.map(r=>r.donor_id),y:vals,marker:{color:'#7c6f9e'},text:vals.map(fmt),hovertemplate:'%{x}: %{y:.3e}<extra></extra>'}],{margin:{t:20,l:70,r:10,b:70},yaxis:{title:'candidate - control', ...axisFor(vals, 0)}}, {displayModeBar:false});
}
function diagnostics(){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value;
  const d=data.diagnostics.find(x=>x.scenario_id===sid && x.metric===metric && x.control_type===type);
  if (!d) { $('diagnostics').innerHTML=''; return; }
  const lines=[
    ['Control graphs compared', d.number_of_graphs], ['Distinct edge sets', d.distinct_edge_set_hashes], ['Distinct simulated input vectors', d.distinct_input_delta_vector_hashes], ['Distinct JEPA outputs', d.distinct_latent_output_vector_hashes], ['Distinct values for selected metric', d.distinct_metric_values], ['Control range width', fmt(d.null_range)], ['Identical control values?', d.frozen_statistics_zero_variance ? 'yes' : 'no'], ['Did edge sets differ?', d.edge_sets_differ ? 'yes' : 'no'], ['Did input vectors differ?', d.input_deltas_differ ? 'yes' : 'no'], ['Did JEPA outputs differ?', d.latent_outputs_differ ? 'yes' : 'no'], ['Audit interpretation', d.control_input_diversity_status]
  ];
  $('diagnostics').innerHTML = `<dl>${lines.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
}
function renderInspector(d){
  if (!d) { $('inspector').textContent='Select a node or edge to inspect its frozen audit record.'; return; }
  const friendly = d.source && d.target ? { edge: `${d.source} -> ${d.target}`, label: d.plain_label, control_type: d.control_type, seed: d.seed, weight: d.weight, raw_record: d } : { node: d.label, type: d.node_type, raw_record: d };
  $('inspector').textContent=JSON.stringify(friendly,null,2);
}
function refresh(){
  state.scenario=$('scenario').value; state.metric=$('metric').value; state.controlType=$('controlType').value; state.graphId=$('controlGraph').value; updateGraphOptions(); updateGraph(); const row=selectedDistribution(); updateStory(row); plotDistribution(); plotEffect(); plotDonors(); diagnostics(); renderInspector(null); $('summary').textContent=`${scenarioLabel(state.scenario)} | ${controlLabels[state.controlType] || state.controlType} | ${metricLabels[state.metric] || state.metric}`;
}
initControls(); initGraph(); refresh();
for (const id of ['scenario','metric','controlType','controlGraph','graphMode','edgeView','seedMode']) $(id).addEventListener('change', refresh);
for (const id of ['regulator','direction','magnitude']) $(id).addEventListener('change',()=>{$('scenario').value=scenarioFromTriplet(); refresh();});
$('fit').addEventListener('click',()=>cy.fit()); $('reset').addEventListener('click',()=>{cy.layout({name:'preset',fit:true,padding:28}).run();}); $('clear').addEventListener('click',()=>{cy.elements().unselect(); cy.edges().removeClass('show-label'); renderInspector(null);});
