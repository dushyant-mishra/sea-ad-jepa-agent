# Stage75F F6 - bounded secondary-regulator motif-support expansion

F6 applies the validated F5b bounded cisTarget engine to the eight descriptive
secondary regulator hypotheses:

- BACH1
- CEBPA
- ELF1
- MITF
- NRF1
- RELA
- SPI1
- STAT3

Each TF uses its existing F5a-mapped SCREEN regions and retains the global
1,837,304-region cisTarget denominator. The batches run sequentially and write
restartable checkpoints. A rerun skips completed TFs unless `FORCE=1` is set.

## Full run

```bash
cd "/mnt/d/Jepa project"

DOCKER_MEMORY=24g \
IMAGE=scenicplus:1.0a2-container.1 \
bash scripts/stage75f_run_secondary_motif_pilot_wsl.sh

echo "EXIT_CODE=$?"
```

## Optional bounded subset

```bash
TFS="BACH1,CEBPA" \
DOCKER_MEMORY=24g \
IMAGE=scenicplus:1.0a2-container.1 \
bash scripts/stage75f_run_secondary_motif_pilot_wsl.sh
```

Later, run the full command without `TFS`; completed selected batches are reused.

## Pass criterion

`expansion_pass=true` and `EXIT_CODE=0` mean all requested calculations
completed. Positive TF-annotated motif support is not required for a technical
pass; absence of support is a valid result.

## Outputs

Detailed local outputs:

- `results/tables/stage75f_secondary_motif_enrichment_all_v1.csv.gz`
- `results/tables/stage75f_secondary_motif_enrichment_enriched_v1.csv`
- `results/tables/stage75f_secondary_motif_hits_v1.csv`
- `results/reports/stage75f_secondary_motif_pilot_v1.json`
- `results/stage75f_secondary_motif_pilot/stage75f_batch_0003_*.{csv,csv.gz,json}` through batch 10

Compact review output:

- `results/tables/stage75f_secondary_tf_motif_support_summary_v1.csv`

## Interpretation

These TFs remain descriptive secondary hypotheses. Motif enrichment provides
enhancer-informed candidate evidence only. It does not establish validated
regulation, a validated GRN, causality, or therapeutic relevance.
