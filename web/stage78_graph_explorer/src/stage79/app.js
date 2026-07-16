import cytoscape from 'cytoscape';
import Plotly from 'plotly.js-basic-dist-min';
import './styles.css';

window.cytoscape = cytoscape;
window.Plotly = Plotly;
const data = window.__STAGE79_GRAPH_CONTROL_EXPLORER__;
const $ = id => document.getElementById(id);
const state = { scenario: 'ELF1_down_0p10', metric: 'mean_euclidean_displacement', controlType: 'degree_preserving_edge_shuffle', graphMode: 'real', edgeView: 'active', seedMode: 'mean', graphId: null };
let cy;
const byId = Object.fromEntries(data.networks.graphs.map(g => [g.control_graph_id, g]));
const edgeByGraph = new Map();
for (const e of data.networks.edges) {
  if (!edgeByGraph.has(e.control_graph_id)) edgeByGraph.set(e.control_graph_id, []);
  edgeByGraph.get(e.control_graph_id).push(e);
}
function sortedUnique(xs){ return [...new Set(xs)].sort(); }
function fill(sel, vals){ sel.innerHTML=''; for (const v of vals) sel.add(new Option(v, v)); }
function scenarioParts(id){ const p=id.split('_'); return {regulator:p[0], direction:p[1], magnitude:p[2].replace('p','.')}; }
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
  const edges=(edgeByGraph.get(graphId)||[]).filter(e => $('edgeView').value==='all' || e.tf===reg);
  const nodes=new Map();
  nodes.set(reg,{data:{id:reg,label:reg,node_type:'transcription_factor'}});
  for (const e of edges){ nodes.set(e.tf,{data:{id:e.tf,label:e.tf,node_type:'transcription_factor'}}); nodes.set(e.target_gene,{data:{id:e.target_gene,label:e.target_gene,node_type:'target_gene'}}); }
  if (mode==='control' && graphId==='no_graph') nodes.set(reg,{data:{id:reg,label:reg,node_type:'transcription_factor'}});
  const nodeEls=[...nodes.values()].sort((a,b)=>a.data.id.localeCompare(b.data.id));
  const edgeEls=edges.map((e,i)=>({data:{id:`${graphId}_${i}_${e.tf}_${e.target_gene}`,source:e.tf,target:e.target_gene,label:mode==='real'?'Coactivity-signed candidate influence':'Control-only propagated edge',control_only:mode!=='real',evidence_support:mode==='real'?e.evidence_support:'null_control',control_type:e.control_type,seed:e.seed,weight:e.normalized_outgoing_weight,motif_support_class:e.motif_support_class}}));
  return [...nodeEls,...edgeEls];
}
function initGraph(){
  cy=cytoscape({container:$('cy'),elements:graphElements(),layout:{name:'cose',animate:false},style:[
    {selector:'node',style:{label:'data(label)',width:34,height:34,'font-size':10,'background-color':'#e7eef8','border-color':'#6b7a90','border-width':1}},
    {selector:'node[node_type="transcription_factor"]',style:{'background-color':'#f3d38b','shape':'round-rectangle'}},
    {selector:'edge',style:{width:2,'line-color':'#7b8798','target-arrow-color':'#7b8798','target-arrow-shape':'triangle','curve-style':'bezier','font-size':8,label:'data(label)','text-rotation':'autorotate','text-opacity':0.55}},
    {selector:'edge[control_only]',style:{'line-style':'dotted','line-color':'#9aa3af','target-arrow-color':'#9aa3af'}},
    {selector:':selected',style:{'border-width':3,'border-color':'#111827','line-color':'#111827','target-arrow-color':'#111827'}}
  ]});
  cy.on('select', 'node, edge', ev => $('inspector').textContent=JSON.stringify(ev.target.data(),null,2));
}
function updateGraph(){ cy.elements().remove(); cy.add(graphElements()); cy.layout({name:'cose',animate:false}).run(); }
function selectedDistribution(){ return data.distributions.rows.find(r => r.scenario_id===$('scenario').value && r.control_type===$('controlType').value && r.metric===$('metric').value); }
function plotDistribution(){
  const row=selectedDistribution(); if(!row) return;
  const vals=row.null_values || [];
  if (row.control_type==='no_graph') {
    Plotly.newPlot('distPlot',[{type:'bar',x:['real','no graph'],y:[row.real_observed_value,row.null_mean],marker:{color:['#365a8c','#8a8f99']}}],{margin:{t:20,l:55,r:10,b:40},yaxis:{title:row.metric}}, {displayModeBar:false});
  } else {
    Plotly.newPlot('distPlot',[{type:'box',y:vals,name:'control seeds',boxpoints:'all',jitter:0.35,marker:{color:'#7b8798'}},{type:'scatter',mode:'markers',x:['real'],y:[row.real_observed_value],name:'real graph',marker:{size:12,color:'#2f5d9f'}}],{margin:{t:20,l:55,r:10,b:45},yaxis:{title:row.metric}}, {displayModeBar:false});
  }
}
function plotEffect(){
  const r=selectedDistribution(); if(!r) return;
  const vals=[r.real_minus_null_mean,r.real_to_null_mean_ratio,r.standardized_difference ?? 0,r.empirical_two_sided_p_value ?? 0,r.bh_q_value ?? 0,r.percentile_rank_descriptive ?? 0];
  const labels=['real-null','real/null','std diff','p two-sided','BH q','percentile'];
  Plotly.newPlot('effectPlot',[{type:'bar',x:labels,y:vals,marker:{color:'#5f738c'}}],{margin:{t:20,l:45,r:10,b:70}}, {displayModeBar:false});
  $('effectText').textContent = r.zero_variance_status==='zero_variance_null' ? 'Standardized difference unavailable: null variance is zero.' : JSON.stringify({status:r.control_input_diversity_status, interval:r.real_vs_null_95_interval_position}, null, 2);
}
function plotDonors(){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value, graph=$('controlGraph').value;
  let rows=data.donor_differences.filter(d=>d.scenario_id===sid && d.metric===metric && d.control_type===type);
  if(type!=='no_graph' && $('seedMode').value==='selected') rows=rows.filter(d=>d.control_graph_id===graph);
  if(type!=='no_graph' && $('seedMode').value==='mean'){
    const by={}; for(const r of rows){ by[r.donor_id]??=[]; by[r.donor_id].push(r.paired_difference); }
    rows=Object.entries(by).map(([donor,vals])=>({donor_id:donor,paired_difference:vals.reduce((a,b)=>a+b,0)/vals.length}));
  }
  Plotly.newPlot('donorPlot',[{type:'bar',x:rows.map(r=>r.donor_id),y:rows.map(r=>r.paired_difference),marker:{color:'#7c6f9e'}}],{margin:{t:20,l:55,r:10,b:70},yaxis:{title:'real - control'}}, {displayModeBar:false});
}
function diagnostics(){
  const sid=$('scenario').value, metric=$('metric').value, type=$('controlType').value;
  const d=data.diagnostics.find(x=>x.scenario_id===sid && x.metric===metric && x.control_type===type);
  $('diagnostics').textContent=JSON.stringify(d||{},null,2);
}
function refresh(){ state.scenario=$('scenario').value; state.metric=$('metric').value; state.controlType=$('controlType').value; state.graphId=$('controlGraph').value; updateGraphOptions(); updateGraph(); plotDistribution(); plotEffect(); plotDonors(); diagnostics(); $('summary').textContent=`${state.scenario} | ${state.controlType} | ${state.metric}`; }
initControls(); initGraph(); refresh();
for (const id of ['scenario','metric','controlType','controlGraph','graphMode','edgeView','seedMode']) $(id).addEventListener('change', refresh);
for (const id of ['regulator','direction','magnitude']) $(id).addEventListener('change',()=>{$('scenario').value=scenarioFromTriplet(); refresh();});
$('fit').addEventListener('click',()=>cy.fit()); $('reset').addEventListener('click',()=>{cy.layout({name:'cose',animate:false}).run();}); $('clear').addEventListener('click',()=>{cy.elements().unselect(); $('inspector').textContent='';});
