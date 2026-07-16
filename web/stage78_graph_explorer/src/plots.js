export function fmt(v) {
  return v === null || v === undefined ? 'NA' : Number(v).toExponential(3);
}

const config = {
  displayModeBar: false,
  responsive: true,
  staticPlot: false,
};

const baseLayout = {
  margin: { l: 46, r: 14, t: 18, b: 38 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { family: 'Inter, system-ui, sans-serif', size: 11, color: '#283241' },
  showlegend: false,
};

function plotly() {
  if (!window.Plotly || typeof window.Plotly.react !== 'function') {
    throw new Error('Plotly.js basic distribution is not available at runtime');
  }
  return window.Plotly;
}

function safeDonorLabel(id) {
  return String(id || '').replace(/^H/, '');
}

function colorFor(v) {
  const x = Number(v || 0);
  if (x > 0) return '#6f9657';
  if (x < 0) return '#b35d70';
  return '#708090';
}

export function renderPlots(state) {
  const latent = state.latentByScenario.get(state.selectedScenarioId);
  const donors = state.donorsByScenario.get(state.selectedScenarioId) || [];
  if (!latent) return;

  plotly().react('latent-summary-plot', [{
    type: 'bar',
    x: ['mean', 'median', 'max'],
    y: [
      latent.mean_euclidean_latent_displacement,
      latent.median_euclidean_latent_displacement,
      latent.max_euclidean_latent_displacement,
    ],
    marker: { color: ['#4d778f', '#7aa6a1', '#b78f5d'] },
    hovertemplate: '%{x}<br>%{y:.4e}<extra></extra>',
  }], {
    ...baseLayout,
    yaxis: { title: 'latent displacement', zeroline: true },
    xaxis: { fixedrange: true },
  }, config);

  plotly().react('donor-plot', [{
    type: 'bar',
    x: donors.map(d => safeDonorLabel(d.donor_id)),
    y: donors.map(d => d.mean_euclidean_latent_displacement),
    marker: { color: '#6d7fa7' },
    hovertemplate: 'donor %{x}<br>%{y:.4e}<extra></extra>',
  }], {
    ...baseLayout,
    yaxis: { title: 'mean displacement', zeroline: true },
    xaxis: { title: 'donor', fixedrange: true },
  }, config);

  const cents = latent.supertype_centroid_movements || [];
  plotly().react('centroid-plot', [{
    type: 'bar',
    orientation: 'h',
    y: cents.map(c => c.centroid_label),
    x: cents.map(c => c.mean_movement_toward_centroid),
    marker: { color: cents.map(c => colorFor(c.mean_movement_toward_centroid)) },
    hovertemplate: '%{y}<br>%{x:.4e}<extra></extra>',
  }], {
    ...baseLayout,
    margin: { l: 128, r: 16, t: 12, b: 30 },
    xaxis: { title: 'movement metric', zeroline: true },
    yaxis: { automargin: true, fixedrange: true },
  }, config);

  document.getElementById('latent-stats').innerHTML =
    `<div><b>${latent.scenario_id}</b></div>` +
    `<div>Mean displacement ${fmt(latent.mean_euclidean_latent_displacement)}</div>` +
    `<div>Mean cosine ${fmt(latent.mean_baseline_to_perturbed_cosine_similarity)}</div>` +
    `<div>Cell interval ${fmt(latent.cell_level_displacement_interval.min)} to ${fmt(latent.cell_level_displacement_interval.max)}</div>` +
    `<div>QC ${latent.scenario_qc.deterministic_repeated_inference ? 'pass' : 'check'}</div>`;
}
