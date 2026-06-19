# Graph-JEPA v3 Benchmark-Discovery Design Spec v1

Model name: `Module-Gated Typed Perturbation Graph-JEPA v3`

## 1. V3 objective

Graph-JEPA v3 has two required goals:

1. Benchmark dominance first: v3 must beat the strongest v2 donor-level predictor, not merely beat graph controls.
2. Conservative Discovery Atlas second: v3 must remain usable for gene-ablation-style hypothesis generation without weakening evidence gates.

Both goals are required. A model that wins benchmarks but breaks Discovery Atlas discipline is not acceptable, and a model that generates attractive candidate rankings but fails simple baselines is not sufficient.

## 2. Reusable v2 assets

- SEA-AD H5AD preprocessing.
- The 2,957-gene universe.
- Identity edge file as the canonical gene-index map.
- Real graph edge file.
- Strict zero-overlap shuffled graph generator.
- No-graph identity control.
- Donor-level fold logic.
- Pathology targets: AT8, 6e10/Aβ, GFAP, Iba1, NeuN.
- Baseline harness.
- Manifold QC.
- Scorecard/evidence discipline.

## 3. Expanded benchmark suite

### A. Manifold/embedding baselines

- PCA.
- t-SNE.
- UMAP.
- Supervised UMAP if leakage-safe.
- PHATE.
- Diffusion maps.

### B. Expression baselines

- Raw expression ridge.
- Raw expression ElasticNet.
- Raw expression tree/boosting baseline if available.
- Expression-only MLP.

### C. Module baselines

- Module mean.
- WGCNA module eigengenes.
- Module-only MLP.

### D. Deep latent baselines

- Autoencoder latent.
- VAE / scVI-style latent if feasible.

### E. Graph baselines

- STRING graph.
- WGCNA/TOM graph.
- Real graph.
- No graph.
- Strict shuffled graph.
- Graph-only GNN.

### F. Perturbation/gene-ablation baselines

- Simple latent-delta perturbation model.
- Module-delta perturbation model.
- scGen/CPA/GEARS-style models if feasible.

## 4. V3 architecture

- Expression branch for raw gene-expression signal.
- Module branch using WGCNA/module information.
- Typed graph branch using STRING, WGCNA/TOM, pathway, and coexpression edges.
- Learned edge gates.
- Residual no-graph branch.
- Target-specific heads for AT8, 6e10/Aβ, GFAP, Iba1, and NeuN.
- Perturbation/discovery head for gene-ablation-style counterfactuals.

## 5. Graph source handling

- Keep edge source/type labels.
- Do not collapse STRING, WGCNA, pathway, and coexpression edges into one anonymous edge type.
- Learn edge-type embeddings.
- Learn edge gates.
- Include strict shuffled controls for each graph type where feasible.
- Include no-graph control.

## 6. Training objectives

- Donor pathology prediction loss.
- JEPA latent prediction loss.
- Module alignment/reconstruction loss.
- Graph contrastive or edge-type consistency loss.
- Edge-gate sparsity/regularization.
- Optional perturbation-shift consistency loss.

## 7. Success criteria

Primary benchmark criterion:

- v3 real graph mean OOF Spearman must exceed `0.2999` by at least `0.01`.

Strong benchmark criterion:

- v3 real graph mean OOF Spearman should reach at least `0.315–0.330`.

Graph-specific criterion:

- v3 real graph > v3 no graph by at least `0.01`.
- v3 real graph > v3 strict shuffled graph by at least `0.01`.

Discovery criterion:

- Top perturbation candidates must pass manifold QC, donor robustness, gliosis diagnostics, negative controls, and graph-neighborhood checks.

## 8. Anti-leakage rules

- Locked donor folds.
- No test-fold model selection.
- No candidate-gene tuning.
- No external validation during model selection.
- No dropping targets after seeing results.
- No changing small-difference thresholds post hoc.

## 9. Implementation stages

- Stage 23: inventory available module annotations, WGCNA outputs, STRING edges, pathway edges, and embedding packages.
- Stage 24: build locked benchmark harness for PCA/t-SNE/UMAP/PHATE/diffusion/WGCNA/STRING/expression baselines.
- Stage 25: implement v3 minimum architecture.
- Stage 26: train v3 real graph single seed.
- Stage 27: train v3 controls.
- Stage 28: evaluate v3 benchmark suite.
- Stage 29: multi-seed confirmation if promising.
- Stage 30: restore counterfactual/gene-ablation Discovery Atlas ranking.

## V2 lessons preserved

- Real graph beat no-graph and strict shuffled controls.
- Strict shuffled graph had 0% original-edge overlap and exact degree preservation.
- Module-mean baseline remained strongest absolute predictor.
- v2 was graph-specific but not benchmark-dominating.
- Candidate scores remain model-implied hypotheses, not causal validation.
- Evidence gates are not relaxed.

## Boundary

This design spec ran no training, no external validation, and no evidence-level changes.
