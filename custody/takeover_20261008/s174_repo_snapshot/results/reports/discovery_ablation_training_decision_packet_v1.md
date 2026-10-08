# Discovery Ablation Training Decision Packet v1

## Decision context

- Graph-JEPA superiority over simpler tested baselines was not established.
- Mean OOF Spearman — `module_mean_baseline`: 0.2999
- Mean OOF Spearman — `graph_jepa_real_graph_latent`: 0.2894
- Mean OOF Spearman — `raw_expression_regularized_baseline`: 0.2867
- Mean OOF Spearman — `pca_expression_baseline`: 0.2844
- Current evidence levels: {'not_promoted': 108, '1': 41}
- Level-2 failure patterns: {'passes_non_gliosis_axes_fails_gliosis_only': 40, 'fails_neuron_axis': 1}

## Missing ablation artifacts

- `no_graph_jepa`: `not_available_existing_artifact`
- `shuffled_graph_jepa`: `not_available_existing_artifact`
- `expression_only_autoencoder`: `not_available_existing_artifact`

## Recommended training order

1. `no_graph_jepa` — directly tests whether graph message passing contributes beyond the same broad JEPA setup.
2. `shuffled_graph_jepa` — tests whether biological topology is specifically useful rather than arbitrary connectivity.
3. `expression_only_autoencoder` — tests a learned expression-only representation but requires greater architectural divergence.

## Scientific questions and command readiness

| order | artifact | scientific question | script | smoke command | full command template |
| --- | --- | --- | --- | --- | --- |
| 1 | no_graph_jepa | Does graph message passing add value beyond the same JEPA architecture without informative graph connectivity? | scripts\train_graph_jepa_stage_a_fast.py | smoke_training_not_supported_without_script_patch; identity/no-graph topology is not exposed by confirmed flags | requires_script_patch_or_precomputed_identity_edge_csv; then use confirmed --edge-csv --out-dir --epochs --h5ad flags |
| 2 | shuffled_graph_jepa | Does the biological graph topology matter beyond an arbitrary graph with matched architecture and training budget? | scripts\train_graph_jepa_stage_a_fast.py | smoke_training_not_supported_without_script_patch; a reproducible shuffled-edge generator/input is not exposed by confirmed flags | python scripts/train_graph_jepa_stage_a_fast.py --edge-csv <precomputed_shuffled_edge_csv> --out-dir <output> --epochs <epochs> --h5ad <h5ad> |
| 3 | expression_only_autoencoder | Does Graph-JEPA provide value beyond a learned expression-only representation? | scripts\train_jepa_snrna.py | smoke_training_not_supported_without_script_patch | not_generated_help_failed_or_no_confirmed_flags |

## Required post-training comparisons

- Donor-level pathology prediction under identical donor folds.
- Discovery ranking calibration and top-k overlap.
- Cleaner-versus-broad separation.
- Tier-1 targeted manifold safety using the same audit settings.
- Donor-bootstrap internal robustness and the same strict gliosis diagnostic.

## Compute and design risks

- `no_graph_jepa`: Requires a clearly defined identity/no-graph topology and matched Stage A/B training; GPU time and storage comparable to Graph-JEPA training.
- `shuffled_graph_jepa`: Requires deterministic degree-aware or edge-count-matched shuffling, multiple seeds, and matched training; topology generation can introduce hidden confounds.
- `expression_only_autoencoder`: Requires an explicit architecture/objective and matched latent dimension; architectural divergence complicates fairness and may require new training code.

## Do not train until approved

No ablation training was run while preparing this packet. Every proposed training action requires explicit approval, a frozen comparison protocol, matched compute budgets, and pre-specified seeds and outputs.

## Boundary

Missing ablations are not negative evidence. This packet is a technical decision aid and does not modify candidate evidence levels or scientific claims.
