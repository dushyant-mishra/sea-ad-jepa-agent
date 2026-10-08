export function createState(payload) {
  const data = Object.freeze(payload);
  const scenarioById = new Map(data.scenarios.map(s => [s.scenario_id, s]));
  const effectsByScenario = new Map();
  for (const e of data.nodeEffects) {
    if (!effectsByScenario.has(e.scenario_id)) effectsByScenario.set(e.scenario_id, new Map());
    effectsByScenario.get(e.scenario_id).set(e.node_id, e);
  }
  const latentByScenario = new Map(data.latentEffects.map(e => [e.scenario_id, e]));
  const donorsByScenario = new Map();
  for (const d of data.donorConcordance) {
    if (!donorsByScenario.has(d.scenario_id)) donorsByScenario.set(d.scenario_id, []);
    donorsByScenario.get(d.scenario_id).push(d);
  }
  return Object.freeze({ data, scenarioById, effectsByScenario, latentByScenario, donorsByScenario, selectedScenarioId: 'baseline', selectedElement: null, showMode: 'active', showUsableOnly: false });
}
export function scenarioOptions(state) { return state.data.scenarios.slice().sort((a,b)=>a.scenario_id.localeCompare(b.scenario_id)); }
export function scenarioFromControls(state, regulator, direction, magnitude, kind) {
  if (kind === 'baseline') return 'baseline';
  const hit = state.data.scenarios.find(s => s.scenario_type === 'perturbation' && s.regulator === regulator && s.direction === direction && String(s.magnitude) === String(magnitude));
  return hit ? hit.scenario_id : 'baseline';
}
export function withState(state, patch) { return Object.freeze({ ...state, ...patch }); }
