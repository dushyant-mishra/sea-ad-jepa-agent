# Graph-JEPA v3 Scorecard

Last locked: 2026-06-20

## Plain-language summary

The v3 scorecard separates different kinds of evidence so the project does not overclaim. A model can be good at internal prediction without proving the graph topology matters. A dataset can be useful for pretraining without being clean validation. A gene can be a strong model-implied hypothesis without being a proven therapeutic target.

The scorecard answers six questions:

1. Does the model beat the official internal baseline?
2. Does external pretraining make the representation more robust without contaminating validation?
3. Does the real graph outperform no-graph and strict-shuffled graph controls?
4. Do frozen external projections behave sensibly?
5. Has a truly untouched external holdout reproduced the result?
6. What level of evidence supports each candidate gene?

## Technical summary

The official internal metric is pooled donor-level out-of-fold Spearman across five pathology targets: AT8, 6e10/A beta, GFAP, Iba1, and NeuN. The official complete baseline is `module_mean_baseline = 0.3128`; the minimum v3 success threshold is `0.3228`. No target may drop by more than `-0.02` versus module mean.

Graph-specificity requires:

```text
real graph > no-graph/identity
real graph > strict-shuffled graph
```

External datasets are role-frozen. Any dataset used for training, pretraining, auxiliary supervision, architecture choice, threshold setting, candidate filtering, or model selection cannot later be counted as clean validation.

## Internal prediction score

Evidence label: `internal prediction`

This score covers SEA-AD donor-held-out prediction only. Passing it means v3 beats the official internal baseline under the pooled donor-level OOF Spearman policy while reporting all five pathology targets.

Passing internal prediction does not prove graph specificity, external generalization, causality, or therapeutic validity.

## External-pretraining robustness score

Evidence label: `external-pretrained prediction`

This score asks whether external pretraining improves v3 robustness while preserving the internal benchmark rules. If a dataset contributes to external pretraining, it is no longer clean validation.

When successful but not graph-specific, the correct claim is domain-robust representation learning, not graph-topology discovery.

## Graph-specificity score

Evidence label: `domain-robust representation`

This score compares real graph, no-graph/identity, and strict-shuffled graph conditions. Graph claims require the real graph to beat both controls under the same benchmark protocol.

If real graph beats expression baselines but not strict-shuffled graph, the result supports architecture or regularization, not biological graph topology.

## External projection/stress-test score

Evidence labels:

- `external projection support`
- `external stress-test support`

These labels apply to frozen projections or stress tests in datasets not used for the training decision being evaluated. Projection support can show directional plausibility or transfer boundaries, but it is not clean validation if the dataset was previously used or influenced decisions.

## Clean external validation score

Evidence label: `clean external validation`

Clean external validation requires an untouched dataset held out from training, pretraining, auxiliary supervision, architecture choice, threshold setting, candidate filtering, and model selection. The validation question must be frozen before use.

No current v3 result has this label.

## Candidate evidence score

Evidence labels:

- `model-implied counterfactual hypothesis`
- `causal-prior-supported hypothesis`
- `experimentally validated target`

Model-implied counterfactuals are not causal proof. Prior biology can raise interpretation priority but does not turn an observational counterfactual into an experimentally validated target. Experimental validation requires independent perturbational or mechanistic evidence.

## Causal language tier

Use the lowest accurate causal language:

| Tier | Label | Allowed language |
| --- | --- | --- |
| 1 | `model-implied counterfactual hypothesis` | "The model predicts..." or "The candidate is hypothesis-generating..." |
| 2 | `causal-prior-supported hypothesis` | "The model prediction is consistent with prior causal biology..." |
| 3 | `experimentally validated target` | "Perturbation/experiment supports..." |

Do not use "therapeutic target," "causal regulator," "drug target," or "validated mechanism" unless the evidence tier supports it.

## Stage 27 non-graph status

Best completed SEA-AD-only non-graph condition: `module_only_mlp` (`0.1883`). Stage 27B external-pretrained status: `missing_external_matrix`. These are non-graph training regimes and do not support graph-specific claims.

## Stage 27C rescue status

Best controlled non-graph rescue: `module_pca_ridge` (`0.3267`). Module baseline reproduction pass: `True`. Overall Stage 27C pass: `True`. Graph-control status: non-graph gate passed; graph controls may proceed under locked protocol. Stage 27C itself makes no graph-specific claim.

## Stage 30 graph-control result

Real graph: `0.3205`; real minus Stage 27C reference: `-0.0062`; real minus no-graph: `-0.0062`; real minus strict-shuffled: `0.0219`. Graph-specific pass: `False`. Interpretation: `real_topology_beats_strict_shuffle_but_identity_no_graph_remains_best`.

## Stage 31 residual graph-control result

Best Stage 31 condition: `weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05`; mean pooled OOF Spearman: `0.3264`; best minus Stage 27C reference: `-0.0003`; best minus no-graph residual: `-0.0003`; best minus strict-shuffled residual: `0.0581`. Full pass: `False`. Interpretation: `graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established`.

## Stage 32 external pretraining matrix result

Audit complete: `True`; matrix built: `False`; Stage 33 may proceed: `False`. No model was trained and no benchmark/manuscript claims are updated.
