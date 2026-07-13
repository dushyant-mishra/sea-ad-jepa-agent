# Stage75F F7 - secondary TF-region-gene evidence assembly

F7 reuses the validated F5c evidence assembler. It advances only secondary
regulators with at least one enriched motif annotated to their own TF in F6.
The remaining regulators are retained as explicit negative gate results.

Reviewed F6 gate:

- advance: BACH1, CEBPA, ELF1, RELA, SPI1
- stop: MITF, NRF1, STAT3

Run:

```bash
cd "/mnt/d/Jepa project"
DOCKER_MEMORY=8g IMAGE=scenicplus:1.0a2-container.1 \
  bash scripts/stage75f_run_secondary_tf_region_gene_evidence_wsl.sh
echo "EXIT_CODE=$?"
```

Expected pass conditions:

- all supported TFs represented;
- negative TFs absent from evidence but present in the gate table;
- unmatched peak rows = 0;
- unmatched candidate-edge rows = 0.

Outputs:

- detailed local evidence: `results/tables/stage75f_secondary_tf_region_gene_evidence_v1.csv`
- compact target summary: `results/tables/stage75f_secondary_tf_target_gene_evidence_summary_v1.csv`
- compact supported-TF summary: `results/tables/stage75f_secondary_tf_region_gene_summary_v1.csv`
- compact eight-TF gate: `results/tables/stage75f_secondary_tf_evidence_gate_v1.csv`
- local report: `results/reports/stage75f_secondary_tf_region_gene_evidence_v1.json`

These are descriptive enhancer-informed candidate hypotheses, not validated
regulation, eRegulons, causal evidence, or therapeutic claims.
