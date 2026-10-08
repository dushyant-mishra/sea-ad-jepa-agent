# Stage75F F5b - bounded primary-regulator motif-support pilot

F5b runs true cisTarget ranking enrichment for IRF8 and STAT1 using the
F5a-mapped SCREEN regions only. It retains the full 1,837,304-region cisTarget
universe for AUC/NES normalization.

Defaults match pycisTarget cisTarget:

- AUC threshold: `0.005`
- NES threshold: `3.0`
- recovery rank threshold: `0.05 x total database regions`

The script uses `ctxcore.recovery.aucs` for AUC/NES and
`ctxcore.recovery.leading_edge` for motif-hit regions. Recovery-curve reference
statistics are accumulated in bounded motif batches rather than holding the
full all-motif recovery matrix in memory.

Run:

```bash
cd "/mnt/d/Jepa project"

DOCKER_MEMORY=24g \
IMAGE=scenicplus:1.0a2-container.1 \
bash scripts/stage75f_run_primary_motif_pilot_wsl.sh

echo "EXIT_CODE=$?"
```

Completed IRF8/STAT1 batches are reused automatically. Set `FORCE=1` only for a
deliberate rerun.

Outputs:

- `results/tables/stage75f_primary_motif_enrichment_all_v1.csv.gz`
- `results/tables/stage75f_primary_motif_enrichment_enriched_v1.csv`
- `results/tables/stage75f_primary_motif_hits_v1.csv`
- `results/tables/stage75f_primary_tf_motif_support_summary_v1.csv`
- `results/reports/stage75f_primary_motif_pilot_v1.json`
- `results/stage75f_motif_pilot/stage75f_batch_0001_IRF8.*`
- `results/stage75f_motif_pilot/stage75f_batch_0002_STAT1.*`

Completion is the technical pass condition. Finding no enriched IRF8/STAT1
motif would be a valid scientific result, not a mechanics failure.

Interpretation remains limited to enhancer-informed candidate evidence. This is
not validated regulation, a validated GRN, causal validation, or a therapeutic
claim.
