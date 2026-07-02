# Stage 39A PI metadata gap summary

## Bottom line

The Stage 38B/38C null/not-testable result should primarily be read as a metadata/testability bottleneck, not as biological failure. Stage 39A rescued explicit metadata mappings where possible and listed exact remaining acquisition/preprocessing gaps.

## What is now ready

| dataset_id | ready_for_stage39b_any_support | ready_for_stage39b_disease_support | ready_for_stage39b_celltype_support | ready_for_stage39b_microglia_support | ready_for_stage39b_tau_abeta_support | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| gse138852 | True | True | True | True | False | ready for Stage 39B bounded support analysis |
| gse157827 | False | False | False | False | False | acquire missing GSE157827 metadata/expression matrix beyond GEO series metadata |
| gse174367 | False | False | False | False | False | manual acquisition/preprocessing/metadata mapping required |
| gse160936 | False | False | False | False | False | manual acquisition of expression and metadata files required |
| gse125050 | False | False | False | False | False | manual acquisition of expression and metadata files required |

## Main manual fixes

| dataset_id | manual_fix_needed | exact_requirement | priority | claim_impact |
| --- | --- | --- | --- | --- |
| gse138852 | pathology_labels_not_resolved | ready for Stage 39B bounded support analysis | high | prevents or limits Stage 39B testability |
| gse157827 | metadata_file_missing | acquire missing GSE157827 metadata/expression matrix beyond GEO series metadata | high | prevents or limits Stage 39B testability |
| gse174367 | sample_id_linkage_not_resolved | manual acquisition/preprocessing/metadata mapping required | high | prevents or limits Stage 39B testability |
| gse160936 | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required | medium | prevents or limits Stage 39B testability |
| gse125050 | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required | medium | prevents or limits Stage 39B testability |

## Safe interpretation

Use this as a metadata rescue and Stage 39B planning package only. Do not describe these outputs as clean external validation or experimental validation.
