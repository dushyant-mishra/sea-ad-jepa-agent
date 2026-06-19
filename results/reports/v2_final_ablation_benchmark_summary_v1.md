# V2 Final Ablation Benchmark Summary v1

## Final v2 interpretation

- v2 supports graph-specific benefit: the real graph beat identity/no-graph and the zero-overlap degree-preserving strict shuffled graph.
- v2 does not dominate all baselines.
- The module mean baseline remains the best absolute donor-level predictor.
- v3 must integrate module structure rather than compete with it.
- Candidate scores remain model-implied hypotheses, not causal validation.
- Conservative Discovery Atlas evidence gates must be preserved.

## Mean OOF Spearman ranking

| rank | representation | display_name | mean_oof_spearman | benchmark_role |
| --- | --- | --- | --- | --- |
| 1.0000 | module_mean_baseline | Module mean baseline | 0.2999 | strongest_absolute_baseline |
| 2.0000 | graph_jepa_real_graph_latent | Graph-JEPA v2 real graph | 0.2892 | v2_real_graph_model |
| 3.0000 | raw_expression_regularized_baseline | Raw expression regularized baseline | 0.2867 | regularized_expression_baseline |
| 4.0000 | pca_expression_baseline | PCA expression baseline | 0.2844 | linear_embedding_baseline |
| 5.0000 | graph_jepa_no_graph_identity_latent | Graph-JEPA v2 identity/no-graph | 0.2514 | identity_control |
| 6.0000 | graph_jepa_strict_shuffled_graph_latent | Graph-JEPA v2 strict shuffled graph | 0.2470 | degree_preserving_zero_overlap_control |

## Pairwise deltas

| comparison | delta_mean_oof_spearman | interpretation |
| --- | --- | --- |
| real_graph_minus_no_graph | 0.0378 | Real graph improves over identity/no-graph by more than the 0.01 band. |
| real_graph_minus_strict_shuffled | 0.0422 | Real graph improves over zero-overlap degree-preserving shuffle. |
| strict_shuffled_minus_no_graph | -0.0043 | Strict shuffled and no-graph are within the 0.01 small-difference band. |
| module_mean_minus_real_graph | 0.0107 | Module mean remains the strongest absolute predictor. |
| raw_expression_minus_real_graph | -0.0025 | Raw regularized expression is slightly below real graph. |
| pca_expression_minus_real_graph | -0.0048 | PCA expression is slightly below real graph. |

## V3 implications

- Graph-JEPA v3 must benchmark against manifold/embedding methods including PCA, t-SNE, UMAP, PHATE, and diffusion maps.
- Graph-JEPA v3 must benchmark against WGCNA/module and STRING/graph sources.
- Graph-JEPA v3 should treat the module baseline as signal to absorb through a module-aware branch, not as an opponent to ignore.
- Graph-JEPA v3 must preserve conservative Discovery Atlas evidence boundaries: donor robustness, manifold QC, gliosis diagnostics, negative controls, and graph-neighborhood checks.

## Boundary

- This wrap-up ran no training.
- This wrap-up ran no external validation.
- Evidence levels were not changed.
- No manuscript prose or candidate biology cards were created.
