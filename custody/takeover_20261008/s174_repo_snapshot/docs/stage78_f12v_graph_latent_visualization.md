# Stage78 F12V-C - Cytoscape/Plotly Graph Explorer

F12V-C creates a versioned, self-contained browser explorer for frozen Stage77 graph perturbation display data and frozen Stage78 JEPA latent-displacement summaries.

The application uses Cytoscape.js for the directed TF-to-target graph and Plotly.js for display-only latent, donor, and existing Supertype centroid panels. It embeds all data, JavaScript, and CSS in one HTML artifact that can be opened with `file://` and has no CDN or runtime server dependency.

Allowed wording:

- `Predicted latent displacement under a bounded input-space perturbation`
- `Existing Supertype reference centroid`
- `Donor-level concordance`
- `Simulated input-space expression delta`
- `Coactivity-signed candidate influence`
- `Model-based perturbation hypothesis`

The browser does not rerun JEPA, recompute embeddings, recompute centroids, recompute perturbation deltas, modify graph weights, infer disease direction, calculate rescue, calculate benefit, or calculate therapeutic potential.

## Versioned Outputs

- `results/visualization/stage78_graph_scenario_latent_effects_v1.json`
- `results/visualization/stage78_graph_donor_concordance_v1.json`
- `results/visualization/stage78_graph_supertype_centroid_effects_v1.json`
- `results/visualization/stage78_graph_explorer_metadata_v2.json`
- `results/visualization/stage78_graph_explorer_cytoscape_plotly_v2.html`

The frozen Stage77 v1 JSON and HTML artifacts are read as inputs and must remain unchanged.

## Portable Provenance

The browser smoke test is executed through `file://`, but machine-specific file URLs are not serialized into the frozen metadata. The metadata records only:

- `smoke_test_protocol: file://`
- `smoke_test_artifact: results/visualization/stage78_graph_explorer_cytoscape_plotly_v2.html`

The builder rejects absolute-path leaks across generated HTML, generated JSON payloads, and the renderer metadata.
