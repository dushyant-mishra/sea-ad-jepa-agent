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
