# Stage78 F12 - Frozen-JEPA Latent Displacement

Stage78/F12 encodes the 12 frozen Stage77 Tier A perturbation scenarios plus the
unperturbed baseline through the frozen epoch-30 GeneJEPA encoder.

The stage reconstructs each perturbed input as:

`frozen baseline input + precomputed Stage77 clipped_delta`

It does not rerun or alter Stage77 perturbation logic, recompute edge weights,
infer perturbation direction, calculate drug matches, compute rescue scores, or
make therapeutic/causal claims.

Allowed wording:

`Predicted latent displacement under a bounded input-space perturbation.`

## Inputs

- `results/reports/stage76_perturbation_readiness_v1.json`
- `results/tables/stage77_perturbation_scenario_manifest_v1.csv`
- `results/tables/stage77_predicted_expression_deltas_v1.csv.gz`
- `results/tables/stage77_tier_a_edge_weights_v1.csv`
- `results/reports/stage77_tier_a_perturbation_mvp_v1.json`
- frozen H5AD and epoch-30 checkpoint recorded by Stage76/F10

## Outputs

- `results/tables/stage78_jepa_latent_shift_by_cell_v1.csv.gz`
- `results/tables/stage78_jepa_latent_shift_summary_v1.csv`
- `results/tables/stage78_jepa_donor_concordance_v1.csv`
- `results/tables/stage78_jepa_scenario_qc_v1.csv`
- `results/reports/stage78_jepa_latent_shift_v1.json`

## Reference Centroids

F12 does not invent rare-high or background centroids. When available, it computes
reference movement only for existing H5AD `Supertype` labels using the archived
epoch-30 embedding table grouped by those labels. These are state-label reference
centroids only, not disease-rescue targets.

## Claim Boundaries

The output is a model-space displacement audit. It is not validated regulation,
a validated GRN, causal evidence, biological rescue, drug matching, or a
therapeutic claim.