# Graph-JEPA v3 Dataset Registry

Last locked: 2026-06-20

This registry explains which datasets can be used for which v3 purpose. It is deliberately conservative: a dataset becomes less useful as clean validation once it influences training or decisions.

Primary source tables and reports:

- `results/reports/v3_cellxgene_relevant_dataset_search_v1.md`
- `results/tables/v3_cellxgene_relevant_dataset_candidates_v1.csv`
- `results/tables/v3_cellxgene_dataset_role_assignment_v1.csv`
- `results/reports/v3_public_external_dataset_schema_audit_v1.md`
- `results/tables/v3_public_external_dataset_integration_map_v1.csv`
- `results/reports/v3_external_dataset_role_assignment_v1.md`
- `results/tables/v3_dataset_role_registry_v1.csv`

## Non-expert summary

Think of each dataset as having a job. Some datasets are allowed to teach the model. Some are only allowed to test whether the model travels. Some have already been looked at and therefore cannot be called untouched validation. The registry prevents these jobs from getting mixed up.

## Role rules

- If a dataset is used for training, pretraining, auxiliary supervision, architecture choice, threshold setting, candidate filtering, or model selection, it cannot later be clean validation.
- Clean holdout candidates remain untouched until architecture and training decisions are frozen.
- Already-used datasets are plausibility/context only.
- Mouse datasets require ortholog mapping and are not human validation.
- Peripheral immune datasets are plausibility/auxiliary only, not brain microglia validation.
- No external dataset is allowed for model selection under the current registry.

## SEA-AD main internal benchmark

SEA-AD Microglia-PVM is the internal pathology-grounded benchmark. It is allowed for Stage 27 internal training and donor-held-out evaluation. It is not external validation.

## External training/pretraining pool

These datasets may support self-supervised or domain-robust representation learning after matrix, gene-overlap, and donor/sample audits:

- Human Brain Cell Atlas v1.0 non-neuronal/brain entries.
- Population-scale cross-disorder PFC `HBCC_Cohort` and `Aging_Cohort` if intentionally assigned to pretraining.
- GSE98969 as mouse DAM/microglia auxiliary pretraining only with ortholog mapping.

Using any of these for pretraining forfeits clean-validation status.

## Auxiliary training pool

Auxiliary datasets can support biological side tasks or plausibility heads, not final validation:

- GSE181279 peripheral immune plausibility/auxiliary context.
- Tabula Sapiens immune/myeloid entries.
- v2.2 A beta-responsive microglia outputs if explicitly used as auxiliary supervision.

Peripheral immune datasets cannot validate brain microglia behavior directly.

## Clean external holdout pool

These are currently metadata-only candidates. They must remain untouched until Stage 27 architecture, training regime, and evaluation rules are frozen:

- GSE157827.
- GSE147528.
- Selected CELLxGENE clean holdout candidates, including MSSM_Cohort, RADC_Cohort, Molecular Signatures of Resilience to Alzheimer disease in Layer 4 Neurons, Brain vascular multi-omics disease-risk snRNA-seq, and CSF1R-related disorder full/microglia datasets.

## External stress-test pool

Stress tests can define transfer boundaries without becoming clean validation:

- GSE203206 bulk sample-level stress test.
- CELLxGENE external projection/stress-test candidates without clean holdout status.

Bulk datasets cannot validate cell-level microglia/PVM extraction directly.

## Already-used plausibility-only pool

These are useful context but not untouched validation:

- GSE174367 / Morabito.
- GSE138852 / Grubman-Leng.
- SEA-AD CELLxGENE MTG/DLPFC entries.
- Rexach cross-dementia human brain snRNA-seq.
- Olah live human microglia.

## Do-not-use-until-reviewed pool

These datasets require subseries, provenance, or schema review before use:

- GSE127893.
- Any CELLxGENE candidate labeled `do_not_use_until_reviewed`.
- Any local external artifacts with mixed or unclear provenance.

## Current registry output

The merged registry is `results/tables/v3_dataset_role_registry_v1.csv`. It standardizes GEO and CELLxGENE roles into one table with training, pretraining, auxiliary, holdout, model-selection, and audit flags.

