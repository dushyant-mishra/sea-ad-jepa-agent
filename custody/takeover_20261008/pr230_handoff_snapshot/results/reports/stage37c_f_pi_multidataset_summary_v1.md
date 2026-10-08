# Stage 37C-F PI multi-dataset summary v1

## Short answer

The multi-dataset support suite is ready as a reproducible framework. Local usable data are limited, so most datasets need acquisition/readiness work before substantive support analysis.

## Local availability

| dataset_id | stage_label | analysis_can_run | reason_if_not_ready | safe_claim_level |
| --- | --- | --- | --- | --- |
| gse157827 | Stage37E | False | gene universe could not be extracted | conditional_validation_support_pending_manual_approval |
| gse138852 | Stage37F | True |  | external_biological_support |
| gse174367 | optional_secondary | False | gene universe could not be extracted | stress_test_projection_support_only |

## Datasets needing acquisition/readiness

| dataset_id | stage_label | reason_if_not_ready |
| --- | --- | --- |
| gse160936 | Stage37C | no local files found in declared search roots |
| gse125050 | Stage37D | no local files found in declared search roots |
| gse157827 | Stage37E | gene universe could not be extracted |
| gse174367 | optional_secondary | gene universe could not be extracted |

## Mechanisms supported, unsupported, or not testable

| mechanism_id | mechanism_name | best_support_tier | cross_dataset_concordance_tier |
| --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | weak_or_incomplete_external_support | single_dataset_support |
| M2 | Glial activation / disease-associated microglia-astrocyte state | weak_or_incomplete_external_support | single_dataset_support |
| M3 | Oxidative stress / antioxidant response | weak_or_incomplete_external_support | single_dataset_support |
| M4 | Inflammatory signaling / transport / cell-state modulation | weak_or_incomplete_external_support | single_dataset_support |

## Claim level

| dataset_id | analysis_completed | claim_level_allowed | clean_validation_claim_allowed |
| --- | --- | --- | --- |
| gse160936 | False | readiness_or_missing_data_only | False |
| gse125050 | False | readiness_or_missing_data_only | False |
| gse157827 | False | readiness_or_missing_data_only | False |
| gse138852 | True | external_support_claim_only | False |
| gse174367 | False | readiness_or_missing_data_only | False |

## Why this is not causal or therapeutic validation

The stage uses frozen candidates and external-support/readiness checks only. It does not perform perturbation, disease-modifying experiments, or clean external validation.

## Recommended next action

Acquire/prepare GSE160936, GSE125050, and GSE157827 metadata/expression first, then rerun Stage 37C-F without changing frozen Stage 36E candidates.