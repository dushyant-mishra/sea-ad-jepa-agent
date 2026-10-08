# Stage 35E graph diagnostics synthesis report v1

## 1. Executive summary

Module-scale graph topology produced a small guarded internal improvement, while gene-scale graph strategies remained negative or diagnostic.
Stage 35E synthesized completed graph diagnostics. Gene-scale graph strategies and graph regularization did not replace the Stage 27C no-graph reference. Stage 35C produced a small guarded internal module-scale graph improvement over Stage 27C and passed matched no-graph and strict-shuffled module graph controls. External validation, causal interpretation, and therapeutic-target claims remain untested.

## 2. Why Stage 35E was run

Stage 35E was run to synthesize completed graph diagnostics into one report-only decision layer. It did not train models, create graph features, rerun benchmarks, run in silico ablation, or use external validation.

## 3. Official benchmark policy

The official metric remains pooled donor-level out-of-fold Spearman under locked SEA-AD donor folds. Stage 27C remains the main no-graph reference except when explicitly comparing against the small Stage 35C module-scale graph result.

## 4. Stage-by-stage graph diagnostic timeline

```csv
stage,graph_strategy,best_condition,mean_pooled_oof_spearman,delta_vs_stage27c,beats_stage27c,beats_no_graph_control,beats_strict_shuffled_control,internal_performance_pass,graph_specific_pass,target_specific_rescue_candidates,benchmark_run,controlled_interpretation
Stage 30,gene-scale graph feature controls,v3_real_graph,0.320473828085451,-0.006228611926698491,False,False,True,False,False,0,True,Gene-scale graph feature controls did not replace the Stage 27C no-graph reference.
Stage 31,weak residual gene-scale graph controls,weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05,0.326370355371064,-0.00033208464108547275,False,False,True,False,False,1,True,graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established
Stage 35A,target-aware weak graph injection,target_aware_no_graph_identity_aux_ridge,0.3267024400121495,0.0,False,False,False,False,False,0,True,Target-aware weak graph injection did not improve over the Stage 27C internal no-graph reference under this implementation.
Stage 35B,graph Laplacian regularized ridge,laplacian_real_graph_lambda_0_1_ridge,0.3194087273463603,-0.0072937126657892,False,True,True,False,True,0,True,Graph Laplacian regularization showed topology-control signal but did not beat Stage 27C.
Stage 35C,latent module graph topology,module_graph_real_overlap_aux_weight_0_1_ridge,0.3272653639769161,0.0005629239647666,True,True,True,True,True,1,True,Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls.
Stage 35D,perturbation-derived graph feasibility,benchmark_not_run,,,False,False,False,False,False,0,False,Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available.
```

## 5. Stage 30 summary

Stage 30 evaluated mandatory gene-scale graph controls. The real gene-scale graph condition did not replace the Stage 27C no-graph reference.

## 6. Stage 31 summary

Stage 31 evaluated weak residual graph controls. It nearly matched Stage 27C but did not establish global topology-specific utility.

## 7. Stage 35A summary

Stage 35A evaluated target-aware weak graph injection. The best condition was the no-graph identity auxiliary reference, with no global graph-specific pass and no target-specific rescue candidates.

## 8. Stage 35B summary

Stage 35B evaluated graph Laplacian regularized ridge. It showed topology-control signal against matched no-graph and strict-shuffled controls, but its best mean did not beat Stage 27C.

## 9. Stage 35C summary

Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls. Best condition `module_graph_real_overlap_aux_weight_0_1_ridge` reached mean pooled OOF Spearman `0.327265` versus Stage 27C `0.326702`, delta `+0.000563`.
The target-specific rescue candidate was 6e10/A_beta at module graph weight 0.1. The module graph used predefined microglia module gene-membership Jaccard overlap.
```csv
module_graph_source,n_modules,real_module_edges,strict_shuffled_module_edges,real_strict_edge_overlap,target_values_used_to_construct_graph,module_graph_constructed,module_graph_pass
predefined_microglia_module_gene_membership_jaccard_overlap,15,21,21,0,False,True,True
```

## 10. Stage 35D summary

Perturbation-derived graph benchmarking was not run because no approved local perturbation graph was available.

## 11. What changed scientifically after Stage 35C

The graph story is no longer uniformly negative: module-scale graph topology produced a small guarded internal improvement and passed matched no-graph and strict-shuffled module graph controls.

## 12. What did not change

Gene-scale graph injection, target-aware weak graph injection, and graph Laplacian regularization did not replace the Stage 27C reference. External validation has not been run. Causal and therapeutic claims are not supported.

## 13. Safe claim language

- Stage 35C provides guarded internal evidence that module-scale topology can add a small predictive signal under locked SEA-AD donor-fold controls.
- The effect size is small and requires independent validation.
- Gene-scale graph injection, target-aware weak graph injection, and graph Laplacian regularization did not replace the Stage 27C reference.
- Perturbation-derived graph benchmarking was not run because no approved local perturbation graph was available.
- External validation has not been run.
- Causal and therapeutic claims are not supported.

## 14. Forbidden claim language

- Do not claim that graph topology is validated.
- Do not claim that external validation succeeded.
- Do not claim that Graph-JEPA proves causality.
- Do not claim that in silico ablation is validated.
- Do not claim that therapeutic targets were discovered.
- Do not claim that causal regulators were identified.

## 15. Recommended next steps

- Treat Stage 35C as a small internal signal that needs independent validation.
- Prioritize a clean external validation design before manuscript-level graph claims.
- If a vetted perturbation-derived graph becomes locally available, rerun Stage 35D as a benchmark under the existing gates.
- Keep Stage 27C as the primary reference for non-graph comparisons, with Stage 35C reported only as a guarded module-scale graph diagnostic.

## Decision matrix

```csv
decision_question,answer,evidence_stage,evidence_metric,safe_claim,forbidden_claim
Did gene-scale graph features help?,No; Stage 30 real gene-scale graph features did not replace the Stage 27C no-graph reference.,Stage 30,mean=0.320473828085451,Gene-scale graph features remained negative or diagnostic in the internal benchmark.,Graph topology is validated.
Did weak residual graph help?,No global pass; Stage 31 nearly matched Stage 27C but did not beat the reference.,Stage 31,delta_vs_stage27c=-0.00033208464108547275,Weak residual graph features did not establish topology-specific global utility.,External validation succeeded.
Did target-aware weak graph injection help?,No; Stage 35A best condition was no-graph identity and graph-specific pass was false.,Stage 35A,graph_specific_pass=False,Target-aware weak graph injection did not improve over Stage 27C.,Graph-JEPA proves causality.
Did graph Laplacian regularization help?,Diagnostic only; Stage 35B passed graph controls but did not beat Stage 27C.,Stage 35B,mean=0.3194087273463603; graph_specific_pass=True,Graph Laplacian regularization showed topology-control signal but not a replacement for Stage 27C.,In silico ablation is validated.
Did module-scale graph topology help?,"Yes, guarded and small; Stage 35C beat Stage 27C by +0.000563 and passed matched graph controls.",Stage 35C,delta_vs_stage27c=0.0005629239647666; graph_specific_pass=True,Module-scale topology can add a small guarded internal predictive signal under locked SEA-AD donor-fold controls.,Therapeutic targets were discovered.
Did perturbation graph benchmark run?,No; no approved local perturbation-derived graph was available.,Stage 35D,benchmark_run=False,Perturbation-derived graph benchmarking was not run.,Causal regulators were identified.
What is the safest current graph claim?,"Module-scale graph topology produced a small guarded internal improvement, while gene-scale graph strategies remained negative or diagnostic.",Stage 35E,synthesis_report_only,The Stage 35C effect size is small and requires independent validation.,External validation succeeded.
What remains unvalidated?,"External validity, causal interpretation, therapeutic relevance, and perturbation-derived graph utility remain untested.",Stage 35E,claims_audit,External validation has not been run; causal and therapeutic claims are not supported.,Graph topology is validated.
```

## Claims audit

```csv
external_validation_claim_made,graph_topology_validated_claim_made,causal_claim_made,therapeutic_target_claim_made,in_silico_ablation_validated_claim_made,stage35c_guarded_internal_signal_claim_made,stage35c_effect_size_reported,stage35c_external_validation_status_reported,audit_pass
False,False,False,False,False,True,True,not_run,True
```

## Pass/fail

```csv
stage35e_run,report_only_stage,all_available_stage35_tables_read,stage30_31_status_included,stage35a_included,stage35b_included,stage35c_included,stage35d_included,stage35c_guarded_positive_result_reported,no_external_validation_claim,no_causal_claim,no_therapeutic_target_claim,no_new_modeling_run,synthesis_pass,controlled_interpretation
True,True,True,True,True,True,True,True,True,True,True,True,True,True,"Stage 35E synthesized completed graph diagnostics. Gene-scale graph strategies and graph regularization did not replace the Stage 27C no-graph reference. Stage 35C produced a small guarded internal module-scale graph improvement over Stage 27C and passed matched no-graph and strict-shuffled module graph controls. External validation, causal interpretation, and therapeutic-target claims remain untested."
```
