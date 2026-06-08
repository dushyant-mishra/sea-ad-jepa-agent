# External Validation Next Steps

Last updated: 2026-06-08

This document summarizes the next phase: moving from internally validated SEA-AD Graph-JEPA hypotheses to external validation.

## Why This Phase Matters

The current v2.1 target matrix has survived first-pass internal artifact checks:

- alien-cell / manifold off-roading check
- available covariate confounder check
- within-state plaque-response / DAM compositional-artifact check

That is still not external validation. The next scientific step is to freeze the SEA-AD-trained `upgrade_fine_08` encoder and test whether its named biological programs reproduce in independent cohorts.

## Validation Questions

External validation should answer:

1. Do the same Graph-JEPA latent axes separate AD/control, Braak stage, amyloid, tau, or cognitive status outside SEA-AD?
2. Do named programs such as antigen presentation, vascular/barrier myeloid, lysosome/phagocytosis, plaque response, and DAM remain disease-associated?
3. Do top ranked genes such as `APP`, `BCL2`, `TLR2`, `CD4`, `P2RY12`, `APOE`, `CX3CR1`, `CSF1R`, `CTSD`, and `STAT3` remain interpretable in independent data?
4. Are effects robust to covariates such as age, sex, postmortem interval, RIN/RNA quality, brain pH, library chemistry, and donor batch?

## What Is Available

### 1. SEA-AD Covariate Hardening

Source:

- SEA-AD data page: https://brain-map.org/consortia/sea-ad/our-data

Why it matters:

The v2.1 target matrix was initially checked with the covariates present in the joined pathology table. That table included age and sex, but not the full technical/tissue quality fields we wanted. The local donor workbook does contain those fields.

Local outputs:

```text
script:
  scripts/audit_sea_ad_full_donor_metadata.py

audit:
  results/tables/sea_ad_full_metadata_covariate_audit.csv

covariate-enriched target table:
  results/tables/sea_ad_full_metadata_targets_with_covariates.csv

report:
  results/reports/sea_ad_full_metadata_covariate_audit.md
```

Recovered covariates:

```text
PMI: 84 / 84 donors
RIN: 84 / 84 donors
Brain pH: 84 / 84 donors
Braak: 84 / 84 donors
Thal: 84 / 84 donors
APOE Genotype: 84 / 84 donors
Cognitive Status: 84 / 84 donors
```

Next use:

```powershell
python scripts/validate_v21_target_matrix.py --metadata results/tables/sea_ad_full_metadata_targets_with_covariates.csv
```

Completed full-covariate rerun:

```text
outputs:
  results/tables/v2_1_target_validation_full_covariates_validated_target_matrix.csv
  results/tables/v2_1_target_validation_full_covariates_report.md

result:
  APP, BCL2, TLR2, CD4, and P2RY12 still pass all current internal controls
  z_107 remains the only covariate-caution axis
  CX3CR1 remains biologically interesting but should retain a caution flag
```

### 2. Grubman / Leng Entorhinal Cortex Dataset

Access:

- GEO: `GSE138852`
- URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE138852

What it contains:

- Human entorhinal cortex single-nucleus RNA-seq.
- GEO summary reports 13,214 high-quality nuclei from control and AD brains.
- Useful for a fast public zero-shot projection smoke test.

Best use:

```text
First public external projection smoke test.
```

Limitations:

- Small cohort.
- Metadata is more likely to be categorical than continuous AT8/A beta/GFAP/Iba1/NeuN-style pathology.

### 3. Morabito / Swarup PFC Multi-omic AD Dataset

Access:

- GEO: `GSE174367`
- URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174367

What it contains:

- Human postmortem prefrontal cortex single-nucleus RNA-seq and snATAC-seq.
- GEO summary describes late-stage AD single-nucleus multi-omic data.
- The associated study includes AD/control donors and disease-relevant glial/regulatory analyses.

Best use:

```text
First serious public validation dataset after the GSE138852 smoke test.
```

Limitations:

- Late-stage AD/control design rather than SEA-AD's full progression continuum.
- Supplementary metadata and cell annotations need careful parsing.

### 4. Mathys / ROSMAP 2019 DLPFC Dataset

Access:

- Article: https://www.nature.com/articles/s41586-019-1195-2
- Public article/PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC6865822/

What it contains:

- Single-nucleus RNA-seq from prefrontal cortex.
- The paper reports 80,660 droplet-based snRNA-seq profiles from 48 ROSMAP individuals.
- Strong benchmark for AD microglia replication.

Best use:

```text
Medium-priority cross-cohort validation, especially if Synapse/AMP-AD access is available.
```

Limitations:

- Individual-level metadata and convenient processed objects may require controlled access.

### 5. Mathys / ROSMAP 2023 Large PFC Atlas

Access:

- Article/PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC10601493/

What it contains:

- 2.3 million nuclei from 427 ROSMAP participants.
- Participants span non-AD/early AD, intermediate AD, and late AD.
- Rich clinical/pathology metadata including sex, age at death, and postmortem interval.

Best use:

```text
Gold-standard validation once access and data logistics are solved.
```

Limitations:

- Larger access and compute burden.
- Likely controlled-access workflow for individual-level files.

## Recommended Execution Order

### Step 1: Metadata-Hardened SEA-AD Revalidation

Status:

```text
completed
```

Result:

```text
Top disease axes remain more pathology-linked than nuisance-covariate-linked after adding PMI, RIN, brain pH, and fresh brain weight.
```

### Step 2: Public External Smoke Test

Target:

```text
GSE138852 / Grubman-Leng entorhinal cortex
```

Actions:

1. Download or load processed matrix and annotations.
2. Filter to microglia / immune nuclei.
3. Align genes to the 2,957 Graph-JEPA input genes.
4. Freeze `upgrade_fine_08`.
5. Project cells into the Graph-JEPA latent space.
6. Test AD/control separation, module score shifts, and target gene/module shifts.

### Step 3: Public Serious Validation

Target:

```text
GSE174367 / Morabito-Swarup PFC snRNA-seq
```

Actions:

1. Parse snRNA count matrices and cell annotations.
2. Filter microglia/CNS myeloid cells.
3. Align to Graph-JEPA genes.
4. Project into frozen v2.1 space.
5. Test AD/control and Braak/plaque staging if available from supplementary metadata.

### Step 4: Controlled-Access Gold Standard

Target:

```text
ROSMAP / Mathys 2019 or 2023
```

Actions:

1. Confirm access route through Synapse/AMP-AD or processed public mirrors.
2. Project microglia into frozen Graph-JEPA.
3. Validate against pathology and cognitive variables.
4. Run covariate-aware regressions using age, sex, PMI, and other available metadata.

## Immediate Engineering Tasks

1. Create `scripts/project_external_ad_microglia.py`.
2. Create a dataset adapter for `GSE138852`.
3. Create a dataset adapter for `GSE174367`.
4. Extend validation output to include latent-axis, module-score, and target-gene disease separation.

## Current Recommendation

Do not tune the Graph-JEPA model further right now.

The strongest next move is:

```text
1. run GSE138852 as a public smoke test
2. run GSE174367 as the first serious public validation
3. pursue ROSMAP/Mathys controlled-access validation after the public pipeline works
```

This sequence is the fastest route from "internally validated hypothesis engine" to "externally credible biological discovery platform."
