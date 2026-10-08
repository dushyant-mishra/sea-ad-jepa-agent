# Stage 39A external metadata rescue report

Stage 39A is a metadata harmonization rescue and acquisition-gap audit only. It does not train models, tune thresholds, select candidates, modify frozen Stage 36E hypotheses, or claim clean external validation, causality, therapeutic effect, disease modification, or gene ablation.

## Summary

Stage 39A inspected local files for GSE138852, GSE157827, and GSE174367 and wrote manual acquisition/preprocessing requirements for GSE160936, GSE125050, and missing GSE157827 assets. The goal was to rescue metadata testability after Stage 38B/38C correctly reported mostly not-testable/no-support evidence.

Datasets ready for some Stage 39B bounded support analysis after rescue: `gse138852`.

## Dataset testability after rescue

| dataset_id | expression_ready | metadata_ready | sample_id_linkage_ready | disease_label_ready | celltype_label_ready | microglia_label_ready | astrocyte_label_ready | tau_ptau_label_ready | amyloid_abeta_label_ready | pathology_label_ready | ready_for_stage39b_any_support | ready_for_stage39b_disease_support | ready_for_stage39b_celltype_support | ready_for_stage39b_microglia_support | ready_for_stage39b_tau_abeta_support | reason_if_not_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | True | True | True | True | True | True | True | False | False | False | True | True | True | True | False | pathology_labels_not_resolved | ready for Stage 39B bounded support analysis |
| gse157827 | True | False | False | False | False | False | False | False | False | False | False | False | False | False | False | metadata_file_missing | acquire missing GSE157827 metadata/expression matrix beyond GEO series metadata |
| gse174367 | True | True | False | True | True | True | True | True | True | True | False | False | False | False | False | sample_id_linkage_not_resolved | manual acquisition/preprocessing/metadata mapping required |
| gse160936 | False | False | False | False | False | False | False | False | False | False | False | False | False | False | False | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required |
| gse125050 | False | False | False | False | False | False | False | False | False | False | False | False | False | False | False | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required |

## Stage 39B-ready input mapping

| dataset_id | expression_path | metadata_path | sample_id_column_expression | sample_id_column_metadata | disease_column | disease_case_values | disease_control_values | celltype_column | microglia_values | astrocyte_values | neuron_values | tau_ptau_columns | amyloid_abeta_columns | other_pathology_columns | ready_for_stage39b | allowed_analysis_type | claim_level_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | data\external\gse138852\processed\stage38a_gse138852_candidate_expression.csv | data\external\gse138852\processed\stage38a_gse138852_metadata.csv | cell_id | cell_id | oupSample.batchCond | AD | ct | oupSample.cellType | mg | astro | neuron |  |  |  | True | disease_support;celltype_support;microglia_specificity | external support / conditional validation support only |
| gse157827 | data/external/public_schema_audit/GSE157827/GSE157827_series_matrix.txt.gz |  |  |  |  |  |  |  |  |  |  |  |  |  | False |  | not testable yet |
| gse174367 | data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5 | data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz | matrix/barcodes | SampleID | Diagnosis | AD | Control | cluster | MG1;MG3;MG2 | ASC3;ASC1;ASC2;ASC4 | INH1;INH2;INH4;INH3;EX2;EX3;EX4;EX1;EX5 | Tangle.Stage | Plaque.Stage |  | False |  | not testable yet |
| gse160936 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | False |  | not testable yet |
| gse125050 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | False |  | not testable yet |

## Disease harmonization

| dataset_id | metadata_path | disease_column | disease_values_detected | disease_case_values | disease_control_values | disease_label_ready | harmonization_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | data\external\gse138852\processed\stage38a_gse138852_metadata.csv | oupSample.batchCond | AD;ct | AD | ct | True | explicit disease/control-like metadata found |
| gse157827 |  |  |  |  |  | False | disease/control labels not safely harmonized |
| gse174367 | data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz | Diagnosis | AD;Control | AD | Control | True | explicit disease/control-like metadata found |
| gse160936 |  |  |  |  |  | False | disease/control labels not safely harmonized |
| gse125050 |  |  |  |  |  | False | disease/control labels not safely harmonized |

## Cell-type and microglia/astrocyte harmonization

| dataset_id | metadata_path | celltype_column | celltype_values_detected | microglia_values | astrocyte_values | neuron_values | oligodendrocyte_values | opc_values | endothelial_values | celltype_label_ready | microglia_label_ready | astrocyte_label_ready | harmonization_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | data\external\gse138852\processed\stage38a_gse138852_metadata.csv | oupSample.cellType | oligo;unID;astro;OPC;neuron;endo;mg;doublet | mg | astro | neuron | oligo | OPC |  | True | True | True | cell-type labels found |
| gse157827 |  |  |  |  |  |  |  |  |  | False | False | False | cell-type labels not safely harmonized |
| gse174367 | data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz | cluster | ODC9;ODC7;ODC1;ODC2;ODC6;ODC13;ODC11;ODC8;ODC4;ODC12;ODC3;ODC5;ODC10;MG1;MG3;MG2;OPC1;OPC2;INH1;INH2;INH4;INH3;EX2;EX3;EX4;EX1;EX5;ASC3;ASC1;ASC2;ASC4;PER.END2;PER.END3;PER.END1 | MG1;MG3;MG2 | ASC3;ASC1;ASC2;ASC4 | INH1;INH2;INH4;INH3;EX2;EX3;EX4;EX1;EX5 | ODC9;ODC7;ODC1;ODC2;ODC6;ODC13;ODC11;ODC8;ODC4;ODC12;ODC3;ODC5;ODC10 | OPC1;OPC2 | PER.END2;PER.END3;PER.END1 | True | True | True | cell-type labels found |
| gse160936 |  |  |  |  |  |  |  |  |  | False | False | False | cell-type labels not safely harmonized |
| gse125050 |  |  |  |  |  |  |  |  |  | False | False | False | cell-type labels not safely harmonized |

## Pathology harmonization

| dataset_id | metadata_path | tau_ptau_columns | amyloid_abeta_columns | other_pathology_columns | tau_ptau_label_ready | amyloid_abeta_label_ready | pathology_label_ready | harmonization_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gse138852 | data\external\gse138852\processed\stage38a_gse138852_metadata.csv |  |  |  | False | False | False | pathology columns not safely harmonized |
| gse157827 |  |  |  |  | False | False | False | pathology columns not safely harmonized |
| gse174367 | data/external/gse174367/GSE174367_snRNA-seq_cell_meta.csv.gz | Tangle.Stage | Plaque.Stage |  | True | True | True | pathology columns found |
| gse160936 |  |  |  |  | False | False | False | pathology columns not safely harmonized |
| gse125050 |  |  |  |  | False | False | False | pathology columns not safely harmonized |

## Manual fixes

| dataset_id | manual_fix_needed | exact_requirement | priority | claim_impact |
| --- | --- | --- | --- | --- |
| gse138852 | pathology_labels_not_resolved | ready for Stage 39B bounded support analysis | high | prevents or limits Stage 39B testability |
| gse157827 | metadata_file_missing | acquire missing GSE157827 metadata/expression matrix beyond GEO series metadata | high | prevents or limits Stage 39B testability |
| gse174367 | sample_id_linkage_not_resolved | manual acquisition/preprocessing/metadata mapping required | high | prevents or limits Stage 39B testability |
| gse160936 | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required | medium | prevents or limits Stage 39B testability |
| gse125050 | expression_file_missing;metadata_file_missing | manual acquisition of expression and metadata files required | medium | prevents or limits Stage 39B testability |

## Claim boundary

Stage 39A is a metadata/testability rescue. It does not establish clean external validation, causality, therapeutic relevance, disease modification, or gene-ablation evidence.
