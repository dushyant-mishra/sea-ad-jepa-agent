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

## Phase 3A: Feature-Wide Pathology-Axis Counterfactuals

Candidate-space nulls are useful but limited because pathology-axis scores currently exist only for the scored candidate/fingerprint table. A stronger Atlas needs feature-wide or graph-connected feature-gene counterfactual scores first.

Dry run:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/feature_wide_counterfactuals.py --dry-run
```

Pilot run:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/feature_wide_counterfactuals.py --pilot
```

Validated pilot command used:

```powershell
conda run -n sea-ad-jepa python discovery_atlas/feature_wide_counterfactuals.py --pilot --scope graph_connected --batch-size 32 --pilot-out results\tables\discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv
conda run -n sea-ad-jepa python discovery_atlas/validate_feature_wide_pilot.py --observed-runtime-seconds 3277
```

Pilot validation output:

```text
results/tables/discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv
results/tables/discovery_pilot_feature_wide_reference_comparison.csv
results/reports/discovery_pilot_feature_wide_counterfactual_validation.md
```

Pilot result summary:

```text
221 / 221 perturbations succeeded
0 manifold violations
~54.6 minutes observed runtime
~14.8 seconds per gene
overlap with existing pathology-head gene counterfactuals: sign agreement = 1.0 and Spearman = 1.0 across AT8, 6e10, GFAP, Iba1, and NeuN
```

Full graph-connected feature run:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/feature_wide_counterfactuals.py --scope graph_connected
```

Full feature-wide run:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/feature_wide_counterfactuals.py --scope feature_wide
```

Outputs:

```text
results/reports/discovery_feature_wide_counterfactual_feasibility.md
results/tables/discovery_pilot_feature_wide_pathology_axis_counterfactuals.csv
results/tables/discovery_feature_wide_pathology_axis_counterfactuals.csv
```

Terminology:

```text
feature-wide = all Graph-JEPA feature genes, not genome-wide
graph-connected = Graph-JEPA feature genes present in the consensus graph
```

Feature-wide counterfactuals are still model-implied perturbation scores, not biological intervention results. They improve null testing and ranking robustness, but they do not prove causality.

## Phase 3B: Preliminary Negative Controls

Run the first falsification layer:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python discovery_atlas/negative_controls.py
```

Outputs:

```text
results/tables/discovery_negative_control_summary.csv
results/tables/discovery_degree_matched_decoy_controls.csv
results/tables/discovery_label_shuffle_controls.csv
results/tables/discovery_housekeeping_hub_controls.csv
results/reports/discovery_negative_controls.md
```

Important scope limit: this is a score-available candidate-space negative-control layer, not a genome-wide null. Current pathology-axis scores exist only for the scored candidate/fingerprint table. Degree-matched decoys therefore sample only from genes with available pathology-axis scores.

Status interpretation:

```text
preliminary_support = candidate has some decoy-relative or graph-control support inside the scored candidate space
not_extreme_within_scored_candidate_space = candidate is not extreme against available scored decoys
not_testable_due_to_thin_null_pool = fewer than a defensible number of matched scored decoys
requires_expanded_decoy_perturbations = current controls are inconclusive or hub-like
```

Negative controls are a falsification layer, not validation. Stronger nulls require either counterfactual scores for a much larger gene universe or rerunning perturbations for degree/expression-matched decoy genes.

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
