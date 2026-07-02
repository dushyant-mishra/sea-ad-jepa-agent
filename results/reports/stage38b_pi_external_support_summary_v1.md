# Stage 38B PI external support summary v1

## Short answer

Stage 38B is a prepared-input external support analysis. It does not train SEA-AD models, select candidates, tune thresholds, or claim clean external validation.

## Datasets analyzed

| dataset_id | dataset_name | analysis_ready_for_stage38b | analysis_completed | load_status | n_obs | n_genes | disease_metadata_found | celltype_metadata_found | tau_ptau_metadata_found | abeta_amyloid_metadata_found | clean_validation_claim_allowed | claim_level_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | gse138852 | True | True | loaded | 13214 | 13 | False | False | False | False | False |  |

## Datasets skipped / blocked

_No rows available._

## Strongest supported mechanisms

_No rows available._

## Microglia specificity

| dataset_id | dataset_name | mechanism_id | mechanism_name | specificity_celltype | test_performed | effect_size | p_value | q_value | support_tier | limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | gse138852 |  |  | microglia/myeloid | False | 0.0 | 1.0 | 1.0 | not_testable | microglia labels or expression matrix unavailable |

## pTau / Aβ support

_No rows available._

## Cross-dataset concordance

| mechanism_id | mechanism_name | n_datasets_testable | n_datasets_supporting | datasets_supporting | datasets_no_support | datasets_not_testable | cross_dataset_tier | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Endolysosomal / autophagy / proteostasis | 0 | 0 |  |  | gse138852 | not_testable | external support / conditional validation support only; frozen Stage 36E candidates require further validation |
| M2 | Glial activation / disease-associated microglia-astrocyte state | 0 | 0 |  |  | gse138852 | not_testable | external support / conditional validation support only; frozen Stage 36E candidates require further validation |
| M3 | Oxidative stress / antioxidant response | 0 | 0 |  |  | gse138852 | not_testable | external support / conditional validation support only; frozen Stage 36E candidates require further validation |
| M4 | Inflammatory signaling / transport / cell-state modulation | 0 | 0 |  |  | gse138852 | not_testable | external support / conditional validation support only; frozen Stage 36E candidates require further validation |

## Negative/null/not-testable count

33

## Pass/fail

| stage38b_run_pass | ready_dataset_count | analyzed_dataset_count | stage38a_inputs_found | safety_audit_pass |
| --- | --- | --- | --- | --- |
| True | 1 | 1 | True | True |