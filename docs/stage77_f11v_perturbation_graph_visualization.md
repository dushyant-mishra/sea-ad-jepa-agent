# Stage77 F11V - Perturbation Graph Visualization

F11V exports a read-only visualization data package for the Stage75/F10/F11
network and perturbation results. It is downstream of the analysis pipeline and
must not recalculate weights, change thresholds, infer missing directions,
silently remove genes, run JEPA, calculate rescue scores, or perform drug
matching.

## Data Contract

The exporter writes:

- `results/visualization/stage77_graph_nodes_v1.json`
- `results/visualization/stage77_graph_edges_v1.json`
- `results/visualization/stage77_graph_scenarios_v1.json`
- `results/visualization/stage77_graph_scenario_node_effects_v1.json`
- `results/visualization/stage77_graph_metadata_v1.json`
- `results/visualization/stage77_graph_prototype_v1.html`

Nodes represent transcription factors and target genes. Edges represent directed
TF to target-gene candidate relationships. Scenario-node effects summarize the
already-computed Stage77 expression deltas for display.

Arrows are labeled as:

`Coactivity-signed candidate influence`

Scenario values are labeled as:

`Simulated input-space expression delta`

They are not labels for proven activation, repression, rescue, or treatment
response.

## Scenario-Node Effects

Each scenario-node effect retains:

- scenario ID
- node ID
- gene symbol
- regulator or target role
- input-space delta summary
- unclipped delta summary
- clipped delta summary
- clipping count and fraction
- contributing cell count
- direction and magnitude
- baseline flag
- source Stage77 file path and SHA-256 hash

The package records source hashes for all frozen inputs and omits machine-specific
absolute paths so it can be moved with the repository.

## Visual Encodings

- Node value/intensity: precomputed simulated model-input expression-delta magnitude
- Node hue: positive or negative simulated delta
- Edge width: frozen normalized Stage77 propagation weight
- Edge opacity: bootstrap sign stability
- Solid edge: direct motif evidence
- Dashed edge: extended-only motif evidence
- Gray edge: unavailable for Stage77 simulation
- Warning outline: at least one selected-cell value reached a clipping bound

The legend must say that color represents a simulated input-space delta, not
experimentally observed expression.

## Prototype

The HTML prototype is intentionally static and read-only. It provides selectors
for regulator, up/down direction, magnitude, and baseline versus perturbation.
Some browsers block `fetch()` from local files, so the HTML is best opened
through an IDE preview or a local static server rooted at `results/visualization`.

## Validation Checks

The exporter fails unless the package has:

- 37 stable nodes
- 96 stable directed edges
- 53 Stage77-usable edges
- 13 scenarios
- exactly 12 perturbation scenarios and one baseline
- every scenario ID mapped once
- every node effect mapped once per scenario
- every usable Tier A edge mapped exactly once
- baseline effects exactly zero
- unavailable edges without Stage77 effect weights
- deterministic JSON serialization
- no machine-specific absolute paths in JSON

## Claim Boundaries

Allowed interpretation: evidence and simulation explorer for model-based,
enhancer-informed perturbation hypotheses requiring experimental validation.

Forbidden interpretation: causal effect, transcriptional activation/repression,
therapeutic response, rescue, treatment effect, validated regulation, or a
validated GRN.
