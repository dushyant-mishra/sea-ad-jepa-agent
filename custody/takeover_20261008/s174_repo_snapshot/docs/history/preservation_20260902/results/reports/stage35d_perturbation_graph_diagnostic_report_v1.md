# Stage 35D perturbation graph diagnostic report v1

## Executive summary

Audit run pass: `True`. Perturbation graph benchmark run: `False`.

## Controlled interpretation

Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available.
This is not external validation, graph topology validation, causal validation, in silico ablation validation, or therapeutic-target discovery.

## Resource audit
```csv
path,size_bytes,keyword_hits,candidate_edge_schema,approved_local_perturbation_graph,forbidden_or_clean_holdout_risk,benchmark_eligible,notes
configs\train\stage35d_perturbation_graph_diagnostic_v1.yaml,529,perturbation,False,False,False,False,filename/resource audit only; no download or web scraping performed
docs\external_perturbation_benchmarks.md,11014,perturbation,False,False,False,False,filename/resource audit only; no download or web scraping performed
```
## Graph alignment audit
```csv
approved_local_perturbation_graph_exists,selected_graph_path,graph_aligned_to_canonical_gene_universe,benchmark_alignment_pass,skipped_reason
False,,False,False,Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available.
```
## Graph-control audit
```csv
comparison,left_condition,right_condition,delta_mean_pooled_oof_spearman,graph_gate_pass,notes
perturbation_graph_benchmark_not_run,,,,False,No approved local perturbation-derived graph was available for matched graph controls.
```
## Leakage audit
```csv
clean_holdout_used,external_pretraining_matrix_used,external_labels_used_for_supervised_pathology_prediction,newly_downloaded_perturbation_data,target_values_used_to_construct_graph,sea_ad_used_for_downstream_only,locked_donor_folds_used,fold_local_downstream_scaling_and_ridge,in_silico_ablation_run,leakage_audit_pass
False,False,False,False,False,True,False,False,False,True
```
## Pass/fail
```csv
stage35d_run,resource_search_completed,perturbation_resource_audit_written,graph_alignment_audit_written,leakage_audit_written,report_written,stage35d_audit_run_pass,perturbation_graph_benchmark_run,stage35d_benchmark_run_pass,stage35d_internal_performance_pass,stage35d_graph_specific_pass,controlled_interpretation
True,True,True,True,True,True,True,False,False,False,False,Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available.
```
