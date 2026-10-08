# Stage75F F5c - primary TF-region-gene evidence assembly

F5c keeps only enriched motifs annotated to their own primary TF, then joins
leading-edge SCREEN-region hits to the Stage75F peak-to-nearest-gene scaffold
and frozen Stage72B candidate TF-target coactivity edges.

Run:

```bash
cd "/mnt/d/Jepa project"
DOCKER_MEMORY=8g IMAGE=scenicplus:1.0a2-container.1 \
  bash scripts/stage75f_run_primary_tf_region_gene_evidence_wsl.sh
echo "EXIT_CODE=$?"
```

Technical pass requires zero unmatched peak rows, zero unmatched candidate-edge
rows, and representation of both IRF8 and STAT1.

These outputs are candidate evidence, not eRegulons, validated regulation,
causality, or therapeutic claims.
