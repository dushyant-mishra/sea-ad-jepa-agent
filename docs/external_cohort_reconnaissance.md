# External Cohort Reconnaissance

Last updated: 2026-06-09

This document separates external datasets into three roles:

```text
alignment/training:
  can be used to build v2.2 invariance

tuning/stress test:
  can be used to diagnose transfer failures

locked validation:
  must remain untouched until the model and analysis plan are frozen
```

The current Morabito result means we should not claim that v2.1 is externally validated for tau-stage prediction. The next phase should use public cohorts to build cross-cohort robustness, then reserve a stronger cohort for the final locked test.

## Key Decision

Do not use Morabito/GSE174367 as a locked validation cohort anymore.

It has already been used as an external stress test:

```text
AT8/pTau trajectory vs Morabito tangle stage:
  rho = 0.224
  p = 0.372

early tangle stages 1-2 vs late stages 5-6:
  AUC = 0.623
```

This is useful falsification, but not a validation win.

## Candidate Matrix

| Dataset | Access | Exact identifier | Scale | Best role | Why it matters | Main risk |
| --- | --- | --- | --- | --- | --- | --- |
| SEA-AD | Public Allen/CELLxGENE/AWS | CELLxGENE collection `1ca90a2d-2943-483d-b678-b809bf464c30`; DOI `10.1038/s41593-024-01774-5` | multi-region SEA-AD atlas | discovery/training | Primary pathology-grounded dataset with quantitative neuropathology | Discovery cohort; cannot validate itself |
| GSE138852 / Leng-Grubman | Public GEO/CELLxGENE | CELLxGENE collection `180bff9c-c8a5-4539-b13b-ddbc00d643e6`; DOI `10.1038/s41593-020-00764-7` | small cell-type split datasets; microglia datasets exist | smoke test / alignment | Good public AD/control and region-transfer stress test | Small N; categorical labels; not continuous pathology |
| GSE174367 / Morabito | Public GEO | GEO `GSE174367` | 4,126 microglia in our filtered run | stress test / future alignment | Has diagnosis, tangle stage, plaque stage, age, sex, PMI, RIN, batch | Failed/weak tau transfer; missing stages 3-4 |
| Rexach cross-dementia | Public CELLxGENE | collection `c53573b2-eff4-4c5e-9ad0-b24d422dfd9b`; dataset `ac0c6561-7a48-4185-af6f-af799f699172`; DOI `10.1016/j.cell.2024.08.019` | 432,555 cells | alignment/training and disease-specificity stress test | AD vs PSP vs Pick disease/bvFTD vs normal across BA4, insular cortex, visual cortex | If used for supervised alignment, cannot be final validation |
| Population-scale cross-disorder PFC atlas | Public CELLxGENE | collection `84ce6837-548d-4a1f-919f-0bc0d9a3952f`; DOI/preprint `10.1101/2024.10.31.24316513` | datasets from ~693k to 4.1M cells | large-scale alignment pool | Huge DLPFC disease/control corpus with microglia and many disease labels | Very large downloads; disease labels are complex/comorbid |
| ROSMAP / Mathys | Synapse/AD Knowledge Portal | controlled-access ROSMAP/AMP-AD resources | cohort-dependent | locked validation | Best final test because it has deeper donor-level pathology/cognitive metadata | Requires data-use approval and careful access workflow |

## Rexach Cross-Dementia Details

CELLxGENE confirms:

```text
collection:
  Cross-dementia human brain snRNA-seq (Rexach et al 2024)

collection ID:
  c53573b2-eff4-4c5e-9ad0-b24d422dfd9b

dataset ID:
  ac0c6561-7a48-4185-af6f-af799f699172

DOI:
  10.1016/j.cell.2024.08.019

cells:
  432,555

diseases:
  Alzheimer disease
  Pick disease
  progressive supranuclear palsy
  normal

tissues:
  Brodmann area 4
  insular cortex
  primary visual cortex

assays:
  10x 3' v2
  10x 3' v3

H5AD asset size:
  about 5.0 GB
```

This is the strongest immediate public candidate for v2.2 alignment and disease-specificity testing. It should not be the final locked validation if its labels are used during training.

## Recommended v2.2 Data Split

```text
train/alignment:
  SEA-AD
  GSE174367 / Morabito
  Rexach cross-dementia
  optional GSE138852

tuning/stress tests:
  hold out one public cohort at a time
  run frozen transfer after every architecture change

locked validation:
  ROSMAP/Mathys or another cohort not used during alignment
```

## Architecture Implications

The next model should be built for invariance rather than only better SEA-AD prediction.

Prioritized changes:

1. Add feature/node dropout and edge dropout to Graph-JEPA training.
2. Add a cohort/domain adversarial head with gradient reversal.
3. Add optional covariate adversarial heads for PMI/RIN/batch where available.
4. Add supervised contrastive disease alignment only after the validation split is legally clean.

## Immediate Next Actions

1. Build a CELLxGENE metadata adapter for Rexach, but do not train yet.
2. Count microglia by disease, donor, tissue, and assay before downloading the full H5AD.
3. Decide whether Rexach is an alignment cohort or a held-out disease-specificity test.
4. Start the ROSMAP/Synapse access path in parallel.

## Sources

- CELLxGENE Discover: https://cellxgene.cziscience.com/
- Rexach cross-dementia collection: https://cellxgene.cziscience.com/collections/c53573b2-eff4-4c5e-9ad0-b24d422dfd9b
- Population-scale cross-disorder PFC atlas: https://cellxgene.cziscience.com/collections/84ce6837-548d-4a1f-919f-0bc0d9a3952f
- SEA-AD CELLxGENE collection: https://cellxgene.cziscience.com/collections/1ca90a2d-2943-483d-b678-b809bf464c30
- Leng/Grubman CELLxGENE collection: https://cellxgene.cziscience.com/collections/180bff9c-c8a5-4539-b13b-ddbc00d643e6
- AD Knowledge Portal: https://adknowledgeportal.synapse.org/
