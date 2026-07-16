const HIDDEN_DISPLAY_KEYS = new Set([
  'forbidden_wording',
  'rescue_calculated',
  'no_rescue_causal_therapeutic_claim',
]);

function displayPayload(value) {
  if (Array.isArray(value)) return value.map(displayPayload);
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, item] of Object.entries(value)) {
      if (!HIDDEN_DISPLAY_KEYS.has(key)) out[key] = displayPayload(item);
    }
    return out;
  }
  return value;
}

export function renderInspector(state, selected) {
  const sc = state.scenarioById.get(state.selectedScenarioId);
  const latent = state.latentByScenario.get(state.selectedScenarioId);
  const payload = selected ? { selected, scenario: sc, latent_effect: latent } : { scenario: sc, latent_effect: latent, metadata: state.data.metadata };
  document.getElementById('inspector-json').textContent = JSON.stringify(displayPayload(payload), null, 2);
  document.getElementById('scenario-summary').textContent = `${sc.scenario_id} | ${sc.regulator} ${sc.direction} ${sc.magnitude} | cells ${sc.cell_count} donors ${sc.donor_count}`;
}
