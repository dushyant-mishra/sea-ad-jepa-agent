# Stage77 F11 - Tier A perturbation MVP

Stage77/F11 generates bounded input-space expression deltas for the Tier A
regulators `STAT1`, `ELF1`, and `SPI1`. It uses only the 53 usable signed edges
classified by F10 and does not run JEPA embeddings, latent shifts, drug matching,
rescue scores, or therapeutic interpretation.

The MVP uses a transparent one-hop linear fallback because prior repository
perturbation code either runs broader one/two-hop program audits or applies JEPA
and pathology heads. F11 is deliberately narrower.

## Input Scale

The model input is the existing processed H5AD `X` matrix from
`data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`.
F10 established that the training and embedding scripts do not apply additional
normalization, log1p, scaling, clipping, or imputation after reading this matrix.
Perturbation magnitudes are therefore unitless changes in this model-input
space. They are not doses, fold changes, activation strengths, repression
strengths, or experimentally calibrated effects.

## Simulation

For each Tier A regulator, F11 generates:

- `up`, magnitude `0.10`
- `down`, magnitude `0.10`
- `up`, magnitude `0.25`
- `down`, magnitude `0.25`

This gives 12 perturbation scenarios plus one unperturbed baseline. Outgoing
edge weights are `abs(edge_bootstrap_median_rho) * edge_bootstrap_sign_stability`
normalized separately within each TF. Coactivity signs are preserved only as
`predicted_response_sign_from_coactivity`; they are not activation/repression
labels.

Every perturbed value is bounded to the observed model-input range for that
feature, and both unclipped and clipped deltas are reported.

## Outputs

- `results/tables/stage77_perturbation_scenario_manifest_v1.csv`
- `results/tables/stage77_tier_a_edge_weights_v1.csv`
- `results/tables/stage77_perturbation_qc_summary_v1.csv`
- `results/tables/stage77_predicted_expression_deltas_v1.csv.gz`
- `results/reports/stage77_tier_a_perturbation_mvp_v1.json`

Allowed interpretation: bounded one-hop coactivity-signed model-input expression
delta hypotheses requiring experimental validation.

Forbidden interpretation: causal effect, transcriptional activation/repression,
therapeutic response, rescue, treatment effect, validated regulation, or a
validated GRN.
