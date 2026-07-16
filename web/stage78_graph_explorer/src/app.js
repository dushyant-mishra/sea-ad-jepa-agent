import cytoscape from 'cytoscape';
import Plotly from 'plotly.js-basic-dist-min';
import { createState, scenarioFromControls, scenarioOptions, withState } from './state.js';
import { initGraph, updateGraph, fitGraph, resetGraph, clearHighlight } from './graph.js';
import { renderPlots } from './plots.js';
import { renderInspector } from './inspector.js';
import './styles.css';

window.cytoscape = cytoscape;
window.Plotly = Plotly;

let state = createState(window.__STAGE78_GRAPH_EXPLORER__);
let cy;
const regulator = document.getElementById('regulator');
const direction = document.getElementById('direction');
const magnitude = document.getElementById('magnitude');
const scenario = document.getElementById('scenario');
const mode = document.getElementById('mode');
const usableOnly = document.getElementById('usable-only');

function fillControls() {
  const perturb = state.data.scenarios.filter(s => s.scenario_type === 'perturbation');
  [...new Set(perturb.map(s => s.regulator))].sort().forEach(v => regulator.add(new Option(v, v)));
  ['up', 'down'].forEach(v => direction.add(new Option(v, v)));
  [...new Set(perturb.map(s => String(s.magnitude)))].sort().forEach(v => magnitude.add(new Option(v, v)));
  scenarioOptions(state).forEach(s => scenario.add(new Option(s.scenario_id, s.scenario_id)));
  scenario.value = 'baseline';
}
function selectScenario(id) {
  state = withState(state, { selectedScenarioId: id, showMode: mode.value, showUsableOnly: usableOnly.checked });
  scenario.value = id;
  const sc = state.scenarioById.get(id);
  if (sc && sc.scenario_type === 'perturbation') { regulator.value = sc.regulator; direction.value = sc.direction; magnitude.value = String(sc.magnitude); }
  updateGraph(cy, state);
  renderPlots(state);
  renderInspector(state, null);
}
function fromTriplet() { selectScenario(scenarioFromControls(state, regulator.value, direction.value, magnitude.value, 'perturbation')); }
function fromScenario() { selectScenario(scenario.value); }
function updateFilters() { selectScenario(state.selectedScenarioId); }

fillControls();
cy = initGraph(document.getElementById('cy'), state, selected => renderInspector(state, selected));
window.__STAGE78_CY__ = cy;
renderPlots(state);
renderInspector(state, null);
regulator.addEventListener('change', fromTriplet);
direction.addEventListener('change', fromTriplet);
magnitude.addEventListener('change', fromTriplet);
scenario.addEventListener('change', fromScenario);
mode.addEventListener('change', updateFilters);
usableOnly.addEventListener('change', updateFilters);
document.getElementById('fit').addEventListener('click', () => fitGraph(cy));
document.getElementById('reset').addEventListener('click', () => resetGraph(cy));
document.getElementById('clear').addEventListener('click', () => { clearHighlight(cy); renderInspector(state, null); });
