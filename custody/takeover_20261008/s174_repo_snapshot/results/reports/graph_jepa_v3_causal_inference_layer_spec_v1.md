# Graph-JEPA v3 Causal Inference Layer Spec v1

Model name: `Causal Module-Gated Typed Perturbation Graph-JEPA v3`

## 1. Purpose

The causal inference layer adds formal hypothesis-prioritization, stress-testing, and refutation machinery to Graph-JEPA v3. It is not a license to claim causality from SEA-AD observational data alone.

## 2. What causal inference can add

- Rank gene-ablation hypotheses by causal plausibility, not only by predictive counterfactual movement.
- Separate graph-prior support from observational effect estimates.
- Test whether gene/pathology relationships are stable across donor, batch, sex, pathology, and cell-state environments.
- Add refutation and sensitivity tests before promoting causal language.
- Provide an interface for future perturbation-supervised calibration.

## 3. What causal inference cannot prove from SEA-AD alone

SEA-AD is observational. Model counterfactuals, graph priors, environment-invariant associations, and doubly robust observational estimates remain assumption-dependent. They do not prove experimental causality, druggability, therapeutic efficacy, or validated target status. Perturbation, CRISPR, Perturb-seq, or related functional evidence is required for experimental causal claims.

## 4. Causal-prior sources

- STRING edges.
- WGCNA/TOM edges.
- Pathway edges.
- Coexpression edges.
- Module membership or module eigengene structure.
- GRN/TF-target edges where available.

These are causal/biological priors, not causal truth. Source/type labels must be preserved, edge-type embeddings and gates should be learned, and all edge sources need no-graph and strict shuffled controls where feasible.

## 5. Environment definitions

Candidate environments include:

- Donor.
- Batch or technical cohort metadata.
- Sex.
- Diagnosis/pathology strata.
- Cell-state cluster.
- Microglia/PVM state.
- Other safe metadata fields that are locked before evaluation.

The environment module should penalize unstable gene/pathology relationships and report environment-specific effect signs, magnitudes, and sign consistency. Stable effects are causal-plausibility evidence, not proof.

## 6. Causal discovery methods, exploratory only

Optional methods include NOTEARS, additive-noise models, and DAG-style learners on module-level or otherwise reduced feature spaces. Outputs must be labeled exploratory causal priors only. Learned DAGs must not override benchmark performance, robustness checks, refutation tests, or Discovery Atlas evidence gates.

## 7. Observational effect-estimation methods

For shortlisted genes only, v3 may run doubly robust, TMLE, DoWhy, or EconML-style observational effect estimation. Estimates must report treatment definition, outcome axis, covariates, environments, confidence intervals, and estimator assumptions. Estimates are assumption-dependent observational estimates.

## 8. Refutation/sensitivity tests

Required where feasible:

- Placebo treatment.
- Bootstrap.
- Covariate subset refutation.
- Random common-cause addition.
- Unobserved-confounding sensitivity if available.

Failures should demote or block causal-support language.

## 9. Perturbation-supervised extension

Graph-JEPA v3 should include an interface for Perturb-seq, CRISPRi, CRISPRa, or related perturbation datasets. If perturbation data are unavailable for SEA-AD, this remains future calibration/validation. Do not claim perturbation validation from SEA-AD observational data alone.

## 10. Causal evidence tiers

- `causal_hypothesis_only`: model-implied or counterfactual hypothesis without causal-prior or stability support.
- `causal_prior_supported`: supported by typed biological/causal priors such as STRING, WGCNA/TOM, pathway, coexpression, module, or GRN/TF-target evidence.
- `environment_invariant_supported`: shows sign/magnitude stability across locked environments.
- `observational_effect_supported`: has assumption-dependent observational effect estimates.
- `refutation_resistant_observational`: observational estimates survive prespecified refutation/sensitivity checks.
- `experimentally_supported`: supported by perturbation, CRISPR, Perturb-seq, or related functional evidence.
- `not_causal_supported`: causal support failed, was contradicted, or was insufficient.

## 11. Allowed claims

- Observational/model-only candidates: “causal-hypothesis candidate”.
- Candidates with causal priors and invariant effects: “causal-plausibility-supported hypothesis”.
- Candidates with observational effect estimates passing refutation: “refutation-resistant observational causal hypothesis”.
- Candidates with perturbation evidence: “experimentally supported causal candidate”.
- Never call a gene a validated therapeutic target without experimental/functional validation.

## 12. Integration with Discovery Atlas scorecard

The causal layer should be an additional evidence layer, not a replacement for the existing scorecard. It should add columns for causal priors, environment stability, observational estimates, refutation status, perturbation evidence, allowed claim language, and disallowed claims. It must not relax manifold QC, donor robustness, gliosis diagnostics, negative controls, graph-neighborhood checks, or evidence tiers.

## 13. Anti-leakage and anti-overclaiming rules

- Lock donor folds and environment definitions before model selection.
- Do not tune candidate genes using test folds.
- Do not run external validation during model selection.
- Do not change small-difference thresholds after seeing results.
- Do not let learned DAGs override benchmark or evidence gates.
- Do not claim experimental causality without experimental/functional perturbation support.
- Keep prediction, counterfactual simulation, observational causal estimate, and experimental validation separate in all outputs.

## Boundary

This spec implements no causal model code, runs no training, runs no external validation, and changes no evidence levels.
