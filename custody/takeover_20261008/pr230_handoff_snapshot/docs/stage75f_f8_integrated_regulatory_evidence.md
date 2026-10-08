# Stage75F F8 - integrated Stage75 regulatory evidence freeze

F8 freezes the compact Stage75 regulatory evidence into deterministic regulator,
TF-target, and negative-gate tables. It uses only tracked compact Stage75 inputs
from F5b, F5c, F6, and F7.

The evidence tiers are fixed:

- Tier A: STAT1, ELF1, SPI1 with direct motif support
- Tier B: IRF8, BACH1, CEBPA, RELA with extended-only motif support
- Tier C: MITF, NRF1, STAT3 with no TF-annotated enriched motif at configured thresholds

Run:

```bash
cd "/mnt/d/Jepa project"
DOCKER_MEMORY=4g IMAGE=scenicplus:1.0a2-container.1 \
  bash scripts/stage75f_run_integrated_regulatory_evidence_wsl.sh
echo "EXIT_CODE=$?"
```

Outputs:

- `results/tables/stage75_integrated_regulator_summary_v1.csv`
- `results/tables/stage75_integrated_tf_target_summary_v1.csv`
- `results/tables/stage75_integrated_negative_regulator_gate_v1.csv`
- `results/reports/stage75_integrated_evidence_manifest_v1.json`

The manifest records source-table SHA256 hashes, the current git commit,
cisTarget/motif thresholds, row counts, tier counts, and claim boundaries.

This is an evidence freeze for downstream audits. It is not validated regulation,
an eRegulon set, a validated GRN, causal evidence, or a therapeutic claim.