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

## Stage 32B external pretraining acquisition result

Stage 32B pass: `True`; matrix built: `False`; Stage 33A ready: `False`.

## Stage 33A external-pretrained JEPA result

Stage 33A skipped: `True`; full pass: `False`; graph-specific pass: `False`. Interpretation: `Stage 33A skipped because no approved external pretraining matrix was available`.

## Stage 32C bulk external acquisition result
Stage 32C pass: `True`; downloads attempted: `True`; human matrix built: `True`; Stage 33 ready: `True`.

## Stage 33B external-pretrained benchmark result
Best external condition: `external_pretrained_no_graph_identity_jepa_ridge`; mean pooled OOF Spearman: `0.2711`; minus Stage 27C: `-0.0556`; graph-specific pass: `False`.

## Stage 33C external-pretrained diagnostic/rescue result
Best Stage 33C condition: `ext_svd32_raw_count_size_factor_log1p_direct_no_graph`; mean pooled OOF Spearman: `0.3049`; minus Stage 33B: `0.0338`; minus Stage 27C: `-0.0218`; graph-specific pass: `False`. Stage 33C rescued part of the external-pretraining deficit but did not improve over the Stage 27C internal no-graph reference.

## Stage 34A HBCA microglia/myeloid-filtered external pretraining result
Best Stage 34A condition: `filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph`; mean pooled OOF Spearman: `0.2945`; minus Stage 33C: `-0.0104`; minus Stage 27C: `-0.0322`; biological-filter rescue pass: `False`; graph-specific pass: `False`. Microglia/myeloid filtering did not rescue the external-pretraining deficit under this implementation.

## Stage 34B HBCC external pretraining result
Best Stage 34B condition: `hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph`; mean pooled OOF Spearman: `0.2782`; minus Stage 33C: `-0.0267`; minus Stage 27C: `-0.0485`; dataset rescue pass: `False`; graph-specific pass: `False`. HBCC external pretraining did not rescue the external-pretraining deficit under this compact benchmark.

## Stage 35A target-aware weak graph rescue result
Best Stage 35A condition: `target_aware_no_graph_identity_aux_ridge`; mean pooled OOF Spearman: `0.3267`; minus Stage 27C: `0.0000`; global graph-specific pass: `False`; target-specific rescue candidates: `0`. Target-aware weak graph injection did not improve over the Stage 27C internal no-graph reference under this implementation.

## Stage 36A module counterfactual agent result
Stage 36A produced module-level model-implied counterfactual hypotheses from the Stage 27C module_pca_ridge backbone. Run pass: `True`; gene-level pass: `True`; knowledge-grounding pass: `False`; validation pass: `False`. These are hypothesis-generation outputs only.

## Stage 35B graph Laplacian regularized ridge result
Best Stage 35B condition: `laplacian_real_graph_lambda_0_1_ridge`; mean pooled OOF Spearman: `0.3194`; minus Stage 27C: `-0.0073`; graph-specific pass: `True`. Graph Laplacian regularization did not improve over the Stage 27C internal no-graph reference under this implementation.

## Stage 35C latent module graph diagnostic result
Best Stage 35C condition: `module_graph_real_overlap_aux_weight_0_1_ridge`; mean pooled OOF Spearman: `0.3273`; minus Stage 27C: `0.0006`; module graph-specific pass: `True`. Stage 35C completed under guarded internal benchmark rules.

## Stage 35D perturbation graph diagnostic result
Stage 35D completed the perturbation graph feasibility audit. Benchmark run: `False`; internal performance pass: `False`; graph-specific pass: `False`. Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available.

## Stage 35E graph diagnostics synthesis result
Stage 35E graph diagnostics synthesis is complete. Across Stage 30, Stage 31, Stage 35A, Stage 35B, Stage 35C, and Stage 35D, most graph strategies did not improve over the Stage 27C no-graph reference. Stage 35C is the first guarded internal positive module-scale graph result, with best mean pooled OOF Spearman 0.327265 versus Stage 27C 0.326702 and matched module graph controls passed. The result is small, internal only, and not external validation.

## Stage 36B local knowledge grounding result
Stage 36B local knowledge grounding is complete. Knowledge grounding pass: `True`; schema-stable local resources: `103`; annotated Stage 36A gene hypotheses: `770`. This is local prior-knowledge annotation only, not validation, causality, or therapeutic evidence.

## Stage 36C ranked hypothesis package result
Stage 36C ranked hypothesis package is complete. It combines Stage 36A model-implied counterfactual sensitivity with Stage 36B local knowledge grounding for follow-up prioritization only. No new modeling, external validation, causal validation, or treatment claim was made.

## Stage 36D validation handoff result
Stage 36D is complete. Run pass: `True`. It used Stage 36C outputs only to produce a frozen candidate shortlist, assay-planning table, PI meeting summary, and validation-readiness audit. This is a planning handoff only, not validation.

## Stage 36E frozen validation protocol result
Stage 36E is complete. Run pass: `True`. It froze four mechanism bins and validation decision rules from Stage 36C/36D outputs only. This is a protocol/registry package only, not validation.
