# Graph-JEPA Discovery Atlas

This directory contains the focused discovery layer for the SEA-AD Graph-JEPA project.

The goal is not to add more datasets or retrain the model. The goal is to extract a rigorous, graph-aware discovery atlas from existing Graph-JEPA outputs:

```text
frozen Graph-JEPA outputs
  -> multi-pathology fingerprints
  -> graph-neighborhood coherence
  -> covariate and negative-control checks
  -> discovery candidate scorecard
  -> compact external anchors later
```

## Step 0: Input Availability

Before creating new discovery metrics, run the input audit:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/input_availability_report.py
```

Outputs:

```text
results/tables/discovery_atlas_input_availability_summary.csv
results/reports/discovery_atlas_input_availability.md
```

The audit classifies each required input as:

```text
available
available_but_needs_parsing
missing
optional
blocked
```

This prevents the Atlas from fabricating completeness. Missing analyses should be represented as TODO rows until real inputs exist.

## Phase 1: Pathology-Axis Fingerprints

Build gene and module fingerprints from existing multi-target counterfactual outputs:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/pathology_axis_fingerprints.py
```

Outputs:

```text
results/tables/discovery_pathology_axis_gene_fingerprints.csv
results/tables/discovery_pathology_axis_module_fingerprints.csv
results/tables/discovery_candidate_scorecard_v1.csv
results/reports/discovery_pathology_axis_fingerprints.md
```

Each candidate receives continuous scores for tau lowering, amyloid lowering, NeuN preservation, gliosis penalty, broad shift, therapeutic-like behavior, and axis selectivity. Categorical labels are conservative and should be treated as convenience summaries, not hard biological states.

Important label boundary:

```text
amyloid_lowering_candidate = lowers A beta/6e10, but may have tau/gliosis/broad-state penalties
amyloid_selective = lowers A beta/6e10 with positive amyloid_selectivity_score and low spillover
tau_lowering_candidate = lowers AT8, but may not preserve neurons or avoid gliosis
tau_lowering_neuron_preserving = lowers AT8, preserves/increases NeuN, and avoids gliosis inflation
```

The pipeline also writes `pathology_axis_label_confidence` and `classification_reason` columns. These are still internal model-implied labels; negative controls can later upgrade or downgrade confidence.

The script also emits a label-change audit when previous outputs exist:

```text
results/tables/discovery_pathology_axis_label_changes.csv
```

## Phase 2: Graph-Neighborhood Coherence

Test whether candidate genes sit in coherent one-hop graph neighborhoods relative to degree-matched null nodes:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/graph_neighborhood_coherence.py
```

Outputs:

```text
results/tables/discovery_graph_neighborhood_coherence.csv
results/reports/discovery_graph_neighborhood_coherence.md
```

This is a graph sanity check, not a mechanistic proof. It asks whether candidates are near other scored candidates or same-axis candidates more often than expected for genes with similar graph degree. Targets that fail this check are not discarded automatically; they are treated as isolated or unsupported by the current graph prior.

## Planned A Beta Boundary Module

A beta/6e10 is handled as a boundary problem, not as another forced-positive target. The planned module will ask whether the current SEA-AD Microglia-PVM setup supports:

```text
discrete hidden A beta-responsive population
continuous donor-level A beta axis
graph-neighborhood A beta signal
tau/gliosis/neurodegeneration confound
spatial-data-limited boundary case
```

This module should reuse existing ElasticNet, MIL, responder-cell, graph-neighborhood, and multi-target counterfactual outputs. It must not claim plaque-proximal microglia without spatial/plaque-distance evidence.

## Claim Boundary

Allowed:

```text
Graph-JEPA prioritizes pathology-linked microglial gene-network hypotheses.
Pathology-axis fingerprints distinguish selective pathology shifts from broad reactive-state shifts.
Graph-neighborhood coherence and null models strengthen candidate prioritization.
```

Forbidden:

```text
Do not claim causal mechanisms.
Do not claim validated drug targets.
Do not claim model-implied epistasis is biological epistasis.
Do not claim graph edges are regulatory mechanisms.
Do not claim external signature overlap proves causal validation.
```
