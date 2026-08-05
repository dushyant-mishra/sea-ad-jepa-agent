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
function sortedUnique(xs){ return [...new Set(xs)].sort(); }
function fill(sel, vals){ sel.innerHTML=''; for (const v of vals) sel.add(new Option(v, v)); }
function scenarioParts(id){ const p=id.split('_'); return {regulator:p[0], direction:p[1], magnitude:p[2].replace('p','.')}; }
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
  fill($('scenario'), scenarios); fill($('regulator'), sortedUnique(scenarios.map(s => scenarioParts(s).regulator)));
  fill($('direction'), sortedUnique(scenarios.map(s => scenarioParts(s).direction))); fill($('magnitude'), sortedUnique(scenarios.map(s => scenarioParts(s).magnitude)));
  fill($('metric'), data.distributions.metrics); fill($('controlType'), data.distributions.control_types);
  $('scenario').value=state.scenario; $('metric').value=state.metric; $('controlType').value=state.controlType;
  const p=scenarioParts(state.scenario); $('regulator').value=p.regulator; $('direction').value=p.direction; $('magnitude').value=p.magnitude;
  updateGraphOptions();
}
function updateGraphOptions(){
  const type=$('controlType').value; const ids=data.networks.graphs.filter(g => g.control_type===type).map(g => g.control_graph_id).sort();
  fill($('controlGraph'), ids); if (!ids.includes(state.graphId)) state.graphId=ids[0] || 'no_graph'; $('controlGraph').value=state.graphId;
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
  const edgeEls=rawEdges.map((e,i)=>({data:{id:`${graphId}_${i}_${e.tf}_${e.target_gene}`,source:e.tf,target:e.target_gene,label:mode==='real'?'Coactivity-signed candidate influence':'Control-only propagated edge',control_only:mode!=='real',evidence_support:mode==='real'?e.evidence_support:'null_control',control_type:e.control_type,seed:e.seed,weight:e.normalized_outgoing_weight,motif_support_class:e.motif_support_class}}));
  stablePositions(nodeEls, edgeEls);
  return [...nodeEls,...edgeEls];
}
function initGraph(){
  cy=cytoscape({container:$('cy'),elements:graphElements(),layout:{name:'preset',fit:true,padding:28},style:[
    {selector:'node',style:{label:'data(label)',width:34,height:34,'font-size':10,'background-color':'#e7eef8','border-color':'#6b7a90','border-width':1}},
    {selector:'node[node_type="transcription_factor"]',style:{'background-color':'#f3d38b','shape':'round-rectangle'}},
    {selector:'edge',style:{width:2,'line-color':'#7b8798','target-arrow-color':'#7b8798','target-arrow-shape':'triangle','curve-style':'bezier','font-size':8,label:'','text-rotation':'autorotate','text-opacity':0,'text-background-color':'#ffffff','text-background-opacity':0.88,'text-background-padding':2}},
    {selector:'edge.show-label',style:{label:'data(label)','text-opacity':0.9}},
    {selector:'edge[control_only]',style:{'line-style':'dotted','line-color':'#9aa3af','target-arrow-color':'#9aa3af'}},
    {selector:':selected',style:{'border-width':3,'border-color':'#111827','line-color':'#111827','target-arrow-color':'#111827'}}
  ]});
  cy.on('select', 'node, edge', ev => { if (ev.target.isEdge()) ev.target.addClass('show-label'); $('inspector').textContent=JSON.stringify(ev.target.data(),null,2); });
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
function plotDistribution(){
  const row=selectedDistribution(); if(!row) return;
  const vals=row.null_values || []; const constant=vals.length>1 && new Set(vals.map(v=>Number(v).toPrecision(14))).size===1;
  $('distributionNote').textContent = constant ? 'All 50 control seeds produced the same metric value.' : '';
  const yaxis={title:row.metric, ...axisFor(vals, row.real_observed_value)};
  if (row.control_type==='no_graph') {
    Plotly.newPlot('distPlot',[{type:'bar',x:['real','no graph'],y:[row.real_observed_value,row.null_mean],marker:{color:['#365a8c','#8a8f99']},text:[fmt(row.real_observed_value),fmt(row.null_mean)],textposition:'outside'}],{margin:{t:20,l:65,r:10,b:40},yaxis}, {displayModeBar:false});
  } else {
    Plotly.newPlot('distPlot',[{type:'box',y:vals,name:'control seeds',boxpoints:'all',jitter:0.35,marker:{color:'#7b8798'},hovertemplate:'seed value %{y:.3e}<extra></extra>'},{type:'scatter',mode:'markers+text',x:['real'],y:[row.real_observed_value],name:'real graph',marker:{size:12,color:'#2f5d9f'},text:['real'],textposition:'top center',hovertemplate:'real %{y:.3e}<extra></extra>'}],{margin:{t:20,l:65,r:10,b:45},yaxis}, {displayModeBar:false});
  }
}
function plotEffect(){
  const r=selectedDistribution(); if(!r) return;
  const rows=[
    ['Real - null mean', fmt(r.real_minus_null_mean)],
    ['Real / null mean', fmt(r.real_to_null_mean_ratio)],
    ['Standardized difference', r.zero_variance_status==='zero_variance_null' ? 'undefined: null variance is zero' : fmt(r.standardized_difference)],
    ['Empirical p value', r.zero_variance_status==='zero_variance_null' ? 'descriptive only; zero-variance null' : fmt(r.empirical_two_sided_p_value)],
    ['BH q value', r.zero_variance_status==='zero_variance_null' ? 'descriptive only; zero-variance null' : fmt(r.bh_q_value)],
    ['Percentile rank', fmt(r.percentile_rank_descriptive)],
  ];
  Plotly.newPlot('effectPlot',[{type:'table',header:{values:['Quantity','Value'],fill:{color:'#e8edf5'},align:'left'},cells:{values:[rows.map(x=>x[0]),rows.map(x=>x[1])],align:'left',height:24}}],{margin:{t:8,l:6,r:6,b:8}}, {displayModeBar:false});
  $('effectText').textContent = `${r.real_vs_null_95_interval_position}; ${r.control_input_diversity_status}`;
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
  $('donorNote').textContent = vals.length && vals.every(v=>Math.abs(v) < 1e-12) ? 'All donor paired differences are approximately zero.' : '';
  Plotly.newPlot('donorPlot',[{type:'bar',x:rows.map(r=>r.donor_id),y:vals,marker:{color:'#7c6f9e'},text:vals.map(fmt),hovertemplate:'%{x}: %{y:.3e}<extra></extra>'}],{margin:{t:20,l:65,r:10,b:70},yaxis:{title:'real - control', ...axisFor(vals, 0)}}, {displayModeBar:false});
}
function diagnostics(){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value;
  const d=data.diagnostics.find(x=>x.scenario_id===sid && x.metric===metric && x.control_type===type);
  if (!d) { $('diagnostics').innerHTML=''; return; }
  const lines=[
    ['Graphs', d.number_of_graphs], ['Distinct edge sets', d.distinct_edge_set_hashes], ['Distinct input vectors', d.distinct_input_delta_vector_hashes], ['Distinct latent outputs', d.distinct_latent_output_vector_hashes], ['Distinct metric values', d.distinct_metric_values], ['Null range', fmt(d.null_range)], ['Zero-variance null', d.frozen_statistics_zero_variance], ['Edge sets differ', d.edge_sets_differ], ['Input deltas differ', d.input_deltas_differ], ['Latent outputs differ', d.latent_outputs_differ], ['Diversity status', d.control_input_diversity_status]
  ];
  $('diagnostics').innerHTML = `<dl>${lines.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;
}
function refresh(){ state.scenario=$('scenario').value; state.metric=$('metric').value; state.controlType=$('controlType').value; state.graphId=$('controlGraph').value; updateGraphOptions(); updateGraph(); plotDistribution(); plotEffect(); plotDonors(); diagnostics(); $('summary').textContent=`${state.scenario} | ${state.controlType} | ${state.metric}`; }
initControls(); initGraph(); refresh();
for (const id of ['scenario','metric','controlType','controlGraph','graphMode','edgeView','seedMode']) $(id).addEventListener('change', refresh);
for (const id of ['regulator','direction','magnitude']) $(id).addEventListener('change',()=>{$('scenario').value=scenarioFromTriplet(); refresh();});
$('fit').addEventListener('click',()=>cy.fit()); $('reset').addEventListener('click',()=>{cy.layout({name:'preset',fit:true,padding:28}).run();}); $('clear').addEventListener('click',()=>{cy.elements().unselect(); cy.edges().removeClass('show-label'); $('inspector').textContent='';});
