# Discovery Targeted Manifold Audit v1

## Result

- Genes audited: 45
- Perturbations successful: 45/45
- Within the pre-specified manifold threshold: 45/45
- Maximum manifold violation fraction: 0
- Baseline nearest-neighbor p95 threshold: 0.0174693
- Nearest-neighbor backend: `torch` (`torch.cdist`, batched, CUDA).

All 45 targeted genes passed the candidate-level nearest-neighbor manifold check under this sampled-cell configuration. This removes the specific missing-QC flag for these candidates; it does not add biological or causal support.

## Audit groups

| audit_group | n_genes | n_pass | max_violation_fraction | max_mean_latent_shift |
| --- | --- | --- | --- | --- |
| top20_tier1 | 20 | 20 | 0 | 0.000302314 |
| prior_anchor_group | 11 | 11 | 0 | 0.000536245 |
| broad_state_control_group | 9 | 9 | 0 | 0.00373123 |
| special_review_group | 12 | 12 | 0 | 0.0017264 |

## Agreement with the official pathology-delta screen

The full feature-wide graph-connected screen remains the official pathology-delta ranking. The targeted rerun reproduces those deltas up to small GPU numerical differences:

| pathology_axis | max_absolute_difference | pearson | spearman |
| --- | --- | --- | --- |
| AT8_delta | 7.59102e-05 | 1 | 1 |
| A_beta_6e10_delta | 0.000119686 | 1 | 1 |
| GFAP_delta | 0.00010551 | 1 | 0.999868 |
| Iba1_delta | 8.35527e-05 | 1 | 1 |
| NeuN_delta | 5.75036e-05 | 1 | 1 |

## Largest latent shifts in the targeted set

| gene | final_tier | audit_groups | mean_latent_shift | p95_nearest_real_cell_distance | baseline_nn_p95_threshold | manifold_violation_fraction | targeted_manifold_qc_result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RC3H1 | broad_state_caution | broad_state_caution_control | 0.00373123 | 0.010335 | 0.0174693 | 0 | pass_within_manifold_threshold |
| DLG1 | broad_state_caution | broad_state_caution_control | 0.0027193 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| SMG1 | broad_state_caution | broad_state_caution_control | 0.00235302 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| PAFAH1B1 | broad_state_caution | broad_state_caution_control | 0.0023475 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| HDAC8 | broad_state_caution | broad_state_caution_control | 0.00223821 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| POLK | broad_state_caution | broad_state_caution_control | 0.00187416 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| ERC1 | broad_state_caution | special_review | 0.0017264 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| HECTD1 | broad_state_caution | broad_state_caution_control | 0.000916703 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| GSK3B | unsupported_or_deprioritized | special_review | 0.000567845 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| APP | broad_state_caution | prior_anchor/broad_state_caution_control | 0.000536245 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| SLAIN2 | broad_state_caution | special_review | 0.00049826 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |
| FIP1L1 | broad_state_caution | special_review | 0.000489837 | 0.00956832 | 0.0174693 | 0 | pass_within_manifold_threshold |

## Interpretation boundaries

- The full feature-wide graph-connected screen remains the official pathology-delta ranking.
- The full run skipped nearest-neighbor manifold checking because of the Windows sklearn/threadpoolctl failure.
- The successful pilot established feasibility for its subset; this targeted torch audit now supplies candidate-level manifold QC for the 45 pre-specified genes.
- Passing manifold QC means the perturbed embeddings remained near the sampled real-cell latent support under the pre-specified threshold. It does not validate scorecard balance, graph coherence, biological direction, or intervention safety.
- Graph-neighborhood evidence remains penalty/context only because no coherent cleaner 1-hop neighborhood survived FDR.
- No current result proves causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.
