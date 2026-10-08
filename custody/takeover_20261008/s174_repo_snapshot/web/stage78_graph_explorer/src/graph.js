export function valueColor(value) {
  const v = Number(value || 0);
  if (Math.abs(v) < 1e-12) return '#d9e0e8';
  const x = Math.max(-0.08, Math.min(0.08, v));
  if (x > 0) return `rgb(184,${Math.round(221 - x * 650)},${Math.round(214 - x * 1000)})`;
  return `rgb(${Math.round(214 + x * 950)},${Math.round(218 + x * 620)},238)`;
}
export function edgeColor(edge) { return edge.usable_in_stage77 ? '#5b6472' : '#aeb6c2'; }
export function buildElements(state) {
  const sc = state.scenarioById.get(state.selectedScenarioId);
  const effectMap = state.effectsByScenario.get(sc.scenario_id) || new Map();
  const activeReg = sc.scenario_type === 'perturbation' ? sc.regulator : null;
  const edges = state.data.edges.filter(e => {
    if (state.showUsableOnly && !e.usable_in_stage77) return false;
    if (state.showMode === 'active' && activeReg) return e.source_tf === activeReg;
    return true;
  });
  const keep = new Set();
  edges.forEach(e => { keep.add(e.source); keep.add(e.target); });
  if (!activeReg) state.data.nodes.forEach(n => keep.add(n.id));
  const nodes = state.data.nodes.filter(n => keep.has(n.id));
  return [
    ...nodes.map(n => {
      const ef = effectMap.get(n.id);
      const delta = ef?.input_space_delta_summary?.median || 0;
      const clipped = (ef?.clipping_count || 0) > 0;
      return { group: 'nodes', data: { ...n, delta, clipped, effect: ef || null }, position: n.position };
    }),
    ...edges.map(e => ({ group: 'edges', data: { ...e, id: e.id, lineStyle: e.visual_motif_line_style, width: Math.max(1, 10 * (e.normalized_outgoing_weight || 0.025)), opacity: Math.max(0.18, e.edge_bootstrap_sign_stability || 0.35), color: edgeColor(e) } }))
  ];
}
export function initGraph(container, state, onSelect) {
  const cy = cytoscape({
    container,
    elements: buildElements(state),
    layout: { name: 'preset', fit: true, padding: 30 },
    minZoom: 0.25,
    maxZoom: 3,
    style: [
      { selector: 'node', style: { 'background-color': ele => valueColor(ele.data('delta')), 'border-width': ele => ele.data('clipped') ? 4 : 1, 'border-color': ele => ele.data('clipped') ? '#111827' : '#687385', 'label': 'data(label)', 'font-size': 10, 'text-valign': 'center', 'text-halign': 'right', 'text-margin-x': 8, 'width': ele => ele.data('node_type') === 'transcription_factor' ? 28 : 20, 'height': ele => ele.data('node_type') === 'transcription_factor' ? 28 : 20, 'shape': ele => ele.data('node_type') === 'transcription_factor' ? 'round-rectangle' : 'ellipse', 'opacity': ele => ele.data('stage75_integrated_gate') === 'negative_motif_gate' ? 0.42 : 1 } },
      { selector: 'edge', style: { 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'target-arrow-color': 'data(color)', 'line-color': 'data(color)', 'width': 'data(width)', 'opacity': 'data(opacity)', 'line-style': ele => ele.data('lineStyle') === 'dashed' ? 'dashed' : 'solid' } },
      { selector: '.highlight', style: { 'border-color': '#1f4e79', 'border-width': 4, 'opacity': 1 } },
      { selector: '.faded', style: { 'opacity': 0.15 } }
    ]
  });
  cy.on('tap', 'node,edge', evt => { highlight(cy, evt.target); onSelect(evt.target.data()); });
  cy.on('tap', evt => { if (evt.target === cy) { clearHighlight(cy); onSelect(null); } });
  return cy;
}
export function updateGraph(cy, state) { cy.elements().remove(); cy.add(buildElements(state)); cy.layout({ name: 'preset', fit: false }).run(); }
export function fitGraph(cy) { cy.fit(undefined, 30); }
export function resetGraph(cy) { cy.zoom(1); cy.center(); }
export function clearHighlight(cy) { cy.elements().removeClass('highlight faded'); }
function highlight(cy, ele) { clearHighlight(cy); const hood = ele.closedNeighborhood ? ele.closedNeighborhood() : ele; cy.elements().not(hood).addClass('faded'); hood.addClass('highlight'); }
