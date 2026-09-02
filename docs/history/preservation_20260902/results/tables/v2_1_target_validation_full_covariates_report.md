# v2.1 Target Matrix Artifact Validation

This report stress-tests the v2.1 ranked target matrix before accepting model-implied counterfactual hypotheses.

## Alien Cell Check

Top-10 gene perturbations were embedded and compared with the nearest real, unperturbed cell in latent space. A target is flagged if more than 5% of perturbed cells exceed the 95th percentile of normal nearest-neighbor distances.

- Normal nearest-neighbor 95th percentile: 0.045434
- Manifold violations: 0 / 10 tested genes

## Covariate Confounder Check

Donor-level latent factors were correlated with available nuisance covariates and pathology targets.

- Available nuisance covariates: Age at Death, Brain pH, Fresh Brain Weight, PMI, RIN, Sex
- Missing nuisance covariates: none
- Covariate-confounded latent factors: 1 / 13 tested factors

## Within-State Compositional Artifact Check

Top-5 gene perturbations were rerun only on cells in the top quartile of plaque-response/DAM module score. A target is flagged if its sign flips or less than 25% of the full effect remains.

- Compositional artifacts: 0 / 5 tested genes

## Validated Matrix Tiers

validation_tier
partial_controls_passed    16
passes_current_controls     5
caution_one_flag            3

## Recommendation

Targets passing all current controls remain hypotheses, not causal facts. The next validation step is independent external cohort or perturbation validation.