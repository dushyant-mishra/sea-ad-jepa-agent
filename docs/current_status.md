# Current Status

Last updated: 2026-05-27

## Completed

- Created the `sea-ad-jepa` conda environment.
- Downloaded SEA-AD donor metadata and MTG quantitative neuropathology metadata.
- Built donor-level pathology target table with 84 donors and 17 targets.
- Generated metadata QC figures.
- Downloaded the SEA-AD MTG final-nuclei AnnData file:

```text
data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

- Installed CUDA-enabled PyTorch in `sea-ad-jepa`.
- Pinned the scientific Python stack to avoid native Windows crashes from bleeding-edge NumPy/SciPy/scikit-learn builds.
- Verified GPU access:

```text
PyTorch: 2.7.0+cu128
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
VRAM: 16 GB
```

- Added fast H5AD metadata summary tooling.
- Confirmed main expression matrix shape:

```text
1,378,211 nuclei x 36,601 genes
```

- Confirmed relevant columns:

```text
Donor ID
Brain Region
Class
Subclass
Supertype
Continuous Pseudo-progression Score
```

- Confirmed `Subclass = Microglia-PVM` contains 40,000 nuclei.
- Created a fast contiguous 10,000-cell pilot:

```text
data/processed/sea_ad_mtg_contiguous_10k_hvg3k.h5ad
```

- Ran donor-level ridge baseline on the 10k pilot and 500 genes:

```text
results/tables/contiguous_10k_ridge_pathology_500genes.csv
```

- Ran a 2-epoch GPU JEPA smoke test:

```text
results/models/contiguous_10k_jepa_smoke/gene_jepa.pt
```

- Built full Microglia-PVM donor-level pseudobulk features from the full H5AD:

```text
data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv
```

- Created a 10,000-cell Microglia-PVM JEPA pilot:

```text
data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad
```

- Ran Microglia-PVM pseudobulk pathology baselines:

```text
results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv
```

Top held-out donor associations:

```text
number of AT8 positive cells per area_Grey matter: Spearman ~= 0.536
percent AT8 positive area_Grey matter: Spearman ~= 0.531
percent NeuN positive area_Grey matter: Spearman ~= 0.511
```

- Trained JEPA on the 10,000-cell Microglia-PVM pilot:

```text
results/models/microglia_pvm_jepa_10k/gene_jepa.pt
```

Training loss decreased from `0.627` to `0.431` over 20 epochs.

- Extracted JEPA donor embeddings and compared them against pathology targets:

```text
results/tables/microglia_pvm_jepa_embedding_ridge.csv
```

- Added and tested mixed random/module-aware JEPA masking:

```text
results/models/microglia_pvm_jepa_10k_mixed_masking/gene_jepa.pt
results/tables/microglia_pvm_jepa_mixed_embedding_ridge.csv
```

Mixed masking reached lower training loss than the first random-masking JEPA run, and improved NeuN-related donor prediction. It still did not outperform pseudobulk for AT8/pTau, suggesting the next pilot should preserve curated module genes rather than relying only on highly variable gene selection.

- Built and tested a module-preserving Microglia-PVM pilot:

```text
data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad
results/models/microglia_pvm_jepa_10k_module_preserved_mixed/gene_jepa.pt
results/tables/microglia_pvm_jepa_module_preserved_embedding_ridge.csv
```

This increased curated module coverage from partial overlap to all seven curated microglia/AD modules. It also improved the JEPA AT8/pTau signal compared with the earlier JEPA runs:

```text
percent AT8 positive area_Grey matter
  random JEPA: Spearman ~= 0.316
  mixed HVG-only JEPA: Spearman ~= 0.295
  10k module-preserved mixed JEPA: Spearman ~= 0.395
  all-cell module-preserved mixed JEPA, 60 epochs: Spearman ~= 0.454
  all-cell module-preserved mixed JEPA, 100 epochs: Spearman ~= 0.451
```

The longer all-cell JEPA run improved the AT8 cell-count target and NeuN-related targets, but it did not yet beat the pseudobulk baseline for AT8 area. This suggests the next gains should come from better biological supervision or module design, not simply more epochs.

- Expanded the curated microglia module list from 7 to 15 modules:

```text
plaque response
complement
lipid metabolism
lysosome/phagocytosis
interferon response
inflammatory signaling
AT8-associated first-pass genes
homeostatic microglia
disease-associated microglia
senescence/stress
oxidative stress
synapse pruning
antigen presentation
vascular/barrier myeloid
chemokine/migration
```

- Rebuilt the all-cell Microglia-PVM pilot with expanded module preservation:

```text
data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad
40,000 cells x 2,957 genes
```

- Trained expanded-module JEPA with donor-balanced sampling:

```text
results/models/microglia_pvm_jepa_expanded_modules_balanced_e40/gene_jepa.pt
results/models/microglia_pvm_jepa_expanded_modules_balanced_e80/gene_jepa.pt
```

The expanded-module donor-balanced model gave a small improvement for the main AT8 area target, but lower learning rate continuation did not improve it further:

```text
percent AT8 positive area_Grey matter
  all-cell module-preserved mixed JEPA, 100 epochs: Spearman ~= 0.451
  expanded-module donor-balanced JEPA, 40 epochs: Spearman ~= 0.457
  expanded-module donor-balanced JEPA, 80 epochs: Spearman ~= 0.453
```

- Added pathology-aware fine-tuning with donor-held-out validation:

```text
scripts/finetune_jepa_pathology.py
```

First target:

```text
percent AT8 positive area_Grey matter
```

Held-out validation result from the first split:

```text
best validation Spearman ~= 0.738 at epoch 13
```

This is the strongest AT8 signal so far, but it is a supervised single-split result. It should be repeated across donor splits before being presented as stable model performance.

- Fixed the core JEPA architecture by adding an EMA target encoder:

```text
target_encoder starts as a clone of context_encoder
target_encoder gradients are frozen
after each optimizer step:
  target <- ema_decay * target + (1 - ema_decay) * context
```

This replaced the earlier static random target encoder, which was a major bottleneck.

- Trained a fresh EMA JEPA on the expanded-module donor-balanced pilot:

```text
results/models/microglia_pvm_jepa_ema_expanded_balanced_e40/
```

The EMA loss curve changed sharply:

```text
epoch 1:  loss ~= 0.380
epoch 10: loss ~= 0.012
epoch 20: loss ~= 0.013
epoch 40: loss ~= 0.035
```

The best self-supervised EMA JEPA checkpoints nearly matched the pseudobulk AT8-area baseline:

```text
percent AT8 positive area_Grey matter
  pseudobulk baseline: Spearman ~= 0.531
  static-target expanded-module JEPA, 40 epochs: Spearman ~= 0.457
  EMA expanded-module JEPA, 10 epochs: Spearman ~= 0.513
  EMA expanded-module JEPA, 20 epochs: Spearman ~= 0.516
  EMA expanded-module JEPA, 30 epochs: Spearman ~= 0.515
  EMA expanded-module JEPA, 40 epochs: Spearman ~= 0.515
```

This is the strongest self-supervised JEPA result so far. It does not clearly beat pseudobulk yet, but the EMA fix removed most of the gap.

- Fine-tuned the EMA checkpoint on AT8 pathology with donor-held-out validation:

```text
results/models/microglia_pvm_jepa_ema_expanded_at8_finetune/
best validation Spearman ~= 0.699
```

This was strong, but lower than the earlier single-split pathology-aware result from the static-target encoder. The fine-tuning result should therefore be treated as promising but split-sensitive until repeated donor-split validation is implemented.

- Added a VICReg-style variance hinge to the JEPA loss:

```text
loss = alignment_loss + variance_weight * variance_loss
```

The variance term penalizes latent dimensions whose batch standard deviation falls below a threshold. This is intended to reduce latent contraction during EMA training.

First run:

```text
variance_weight = 0.05
variance_gamma = 1.0
```

The variance term added a small improvement for the main AT8-area endpoint:

```text
percent AT8 positive area_Grey matter
  EMA JEPA, 20 epochs: Spearman ~= 0.516
  EMA + variance JEPA, 10 epochs: Spearman ~= 0.512
  EMA + variance JEPA, 20 epochs: Spearman ~= 0.514
  EMA + variance JEPA, 30 epochs: Spearman ~= 0.519
  EMA + variance JEPA, 40 epochs: Spearman ~= 0.514
  pseudobulk baseline: Spearman ~= 0.531
```

This is the best self-supervised JEPA result so far, but it still does not clearly beat pseudobulk. The next evaluation step should be repeated donor-held-out validation across pseudobulk, EMA JEPA, EMA+variance JEPA, and pathology-aware JEPA.

- Added donor-grouped 5-fold validation:

```text
scripts/repeated_donor_groupkfold_validation.py
```

This uses `GroupKFold` with `Donor ID` as the group, so every cell or donor feature profile from a donor stays entirely in either the training fold or validation fold. The same donor folds are reused across pseudobulk, JEPA embeddings, EMA+variance JEPA embeddings, and pathology-aware fine-tuning.

First target:

```text
percent AT8 positive area_Grey matter
```

Results:

```text
model                              mean Spearman +/- std
pathology-aware EMA+variance JEPA   0.462 +/- 0.295
EMA+variance JEPA embeddings        0.425 +/- 0.251
EMA JEPA embeddings                 0.406 +/- 0.257
pseudobulk ridge                    0.355 +/- 0.337
```

This is the first fair donor-held-out comparison where JEPA variants are ahead of pseudobulk on mean Spearman. The high standard deviations mean the result should still be treated cautiously. The next validation improvement is repeated shuffled donor-group splits or repeated GroupShuffleSplit to estimate uncertainty over more than five folds.

- Stabilized donor-held-out validation with pooled out-of-fold scoring:

```text
same donor-held-out folds
collect every held-out donor prediction
compute one pooled Spearman across all 84 held-out donors
```

The validation script now supports:

```text
--splitter groupkfold|stratified_groupkfold
--target-bins 5
--target-transform raw|log1p|rank
```

Using stratified donor folds and a log-transformed AT8 target reduced sensitivity to fold composition and target outliers. The pooled out-of-fold results were:

```text
percent AT8 positive area_Grey matter

model                              pooled OOF Spearman
pathology-aware EMA+variance JEPA   0.497
EMA+variance JEPA embeddings        0.439
EMA JEPA embeddings                 0.437
pseudobulk ridge                    0.422
```

This is the clearest current comparison: every prediction is held-out by donor, the final metric uses all donors at once, and JEPA remains ahead of pseudobulk on the pooled OOF rank metric.

- Added the first causal-discovery workflow:

```text
scripts/causal_in_silico_knockout.py
docs/causal_discovery.md
```

The workflow runs frozen-model in-silico perturbations and reports model-implied counterfactual effects:

```text
delta = perturbed predicted AT8 - baseline predicted AT8
```

Supported interventions:

```text
global_mean
donor_mean
zero
```

First module-level AT8 screen with global-mean replacement:

```text
module                         mean donor delta
at8_associated_first_pass       -0.0195
homeostatic_microglia           -0.0038
vascular_barrier_myeloid        -0.0036
complement                      +0.0035
antigen_presentation            +0.0030
inflammatory_signaling          -0.0028
```

First gene-level follow-up inside top modules highlighted:

```text
PTPRG
CHI3L1
MRC1
CTSD
DRAM1
P2RY12
S100A4
MSR1
TNFRSF11B
NFKBIA
```

These are model-implied causal hypotheses, not validated causal effects.

- Added latent Jacobian causal analysis:

```text
scripts/causal_latent_jacobian.py
```

This extracts directed latent-state sensitivities from the JEPA predictor:

```text
J[i, j] = d predicted_target_latent_i / d context_latent_j
```

First run:

```text
checkpoint: results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt
sample: 2,048 cells
```

Outputs:

```text
results/tables/latent_jacobian_ema_var_e30_matrix.csv
results/tables/latent_jacobian_ema_var_e30_top_edges.csv
results/tables/latent_jacobian_ema_var_e30_module_annotations.csv
```

The strongest directed latent edges were annotated with modules including:

```text
homeostatic microglia
lysosome/phagocytosis
vascular/barrier myeloid
complement
antigen presentation
synapse pruning
```

- Added confounder-adjusted donor-level causal estimates:

```text
scripts/causal_confounder_adjusted_effects.py
```

This residualizes candidate treatments and AT8 pathology against:

```text
JEPA donor embeddings
Age at Death
Sex
APOE Genotype
```

Top adjusted module-level AT8 associations:

```text
at8_associated_first_pass: partial Spearman ~= +0.441
lipid_metabolism:          partial Spearman ~= -0.314
vascular_barrier_myeloid:  partial Spearman ~= -0.282
complement:                partial Spearman ~= -0.201
inflammatory_signaling:    partial Spearman ~= +0.198
```

Top adjusted gene-level AT8 associations among knockout candidates:

```text
CHI3L1
PTPRG
NFKBIA
S100A4
TNFRSF11B
DRAM1
```

- Added external perturbation benchmark plan:

```text
docs/external_perturbation_benchmarks.md
```

Recommended first external benchmark:

```text
Norman et al. Perturb-seq
```

Rationale:

```text
tractable size
single and combinatorial perturbations
useful for testing whether digital knockouts and latent interactions match real CRISPR perturbation responses
```

Recommended scale-up benchmark:

```text
Replogle et al. genome-scale Perturb-seq
```

- Extended pooled out-of-fold validation across multiple SEA-AD pathology targets:

```text
results/tables/multitarget_stratified_groupkfold_oof_log1p_ridge_summary.csv
results/tables/multitarget_oof_jepa_vs_pseudobulk_summary.csv
```

Setup:

```text
splitter: StratifiedGroupKFold
target transform: log1p
models: pseudobulk, EMA JEPA, EMA+variance JEPA
metric: pooled out-of-fold Spearman
```

Targets where the best JEPA embedding model beat pseudobulk:

```text
percent NeuN positive area:  +0.149
percent AT8 positive area:   +0.018
guhcl abeta42:               +0.014
percent GFAP positive area:  +0.007
guhcl pTau:                  +0.003
```

Targets where pseudobulk remained stronger:

```text
percent 6e10 positive area
ripa abeta42
percent Iba1 positive area
ripa pTau
```

Interpretation: JEPA appears strongest for neuronal-density and AT8-related axes, competitive for some biochemical amyloid/tau targets, and weak for Iba1 in the current Microglia-PVM transcriptomic setup.

- Added fold-specific causal knockout workflow:

```text
scripts/causal_fold_specific_knockout.py
```

Purpose:

```text
train pathology head on 4 donor folds
run digital knockouts only on the held-out donor fold
pool held-out donor deltas across all 5 folds
```

This is stricter than the first knockout screen because each counterfactual effect is measured on donors that were not used to fit that fold's pathology head.

First AT8 module runs:

```text
results/tables/causal_fold_specific_module_knockouts_at8_global_mean.csv
results/tables/causal_fold_specific_module_knockouts_at8_donor_mean.csv
results/tables/causal_fold_specific_module_knockouts_at8_zero.csv
results/tables/causal_fold_specific_module_knockout_intervention_comparison.csv
```

Setup:

```text
checkpoint: EMA+variance JEPA epoch 30
target: percent AT8 positive area_Grey matter
splitter: StratifiedGroupKFold
target transform: log1p
encoder: frozen
head: trained inside each fold
```

Mean held-out fold validation Spearman:

```text
0.443
```

Most stable conservative replacement effects:

```text
vascular_barrier_myeloid: positive under global_mean and donor_mean
complement:               positive under global_mean and donor_mean
lipid_metabolism:         positive under global_mean and donor_mean
at8_associated_first_pass: negative under global_mean and donor_mean
```

Strongest zero-replacement effects:

```text
at8_associated_first_pass:       -0.0214
lysosome_phagocytosis:           -0.0182
disease_associated_microglia:    -0.0141
plaque_response:                 -0.0135
vascular_barrier_myeloid:        -0.0115
lipid_metabolism:                -0.0102
homeostatic_microglia:           +0.0093
```

Interpretation: fold-specific knockouts make the effect sizes smaller and more conservative. The AT8-associated first-pass module is the clearest cross-intervention negative signal. Vascular/barrier, complement, lipid, plaque-response, lysosomal/phagocytic, and disease-associated microglia modules are important to the model, but their sign depends on whether the intervention is a conservative mean replacement or an aggressive zero replacement.

- Added PCA-vs-JEPA latent-space evaluation for the dimensionality-reduction story:

```text
scripts/evaluate_latent_spaces.py
```

Outputs:

```text
results/tables/latent_space_evaluation_metrics.csv
results/tables/latent_space_evaluation_jepa_vs_pca_summary.csv
results/tables/latent_space_umap_coordinates.csv
results/figures/latent_space_pca_vs_jepa_umap_at8_neun.svg
results/figures/latent_space_pca_vs_jepa_umap_at8_neun.html
```

This evaluates donor-level pseudobulk PCA against donor-level 128D JEPA embeddings. The visual output is a 2x2 PCA-vs-JEPA map colored by AT8 and NeuN, and the quantitative output tests whether the representation predicts donor pathology with out-of-fold kNN.

JEPA minus PCA kNN Spearman deltas:

```text
GFAP:       +0.220
A beta/6e10:+0.071
Iba1:       +0.025
AT8/pTau:   +0.017
NeuN:       -0.007
```

Interpretation: JEPA is not simply a prettier t-SNE/UMAP. It is a disease-state representation that can be visualized with UMAP. In this first donor-level test, JEPA carries stronger predictive geometry for several glial/pathology axes, especially GFAP and A beta/6e10, while NeuN remains essentially tied/slightly PCA-favored.

Environment note: default UMAP spectral initialization still crashed on Windows even after upgrading SciPy to 1.15.3. The analysis uses fixed UMAP `a/b` parameters and `init="random"` to avoid unstable SciPy `curve_fit` and ARPACK paths while preserving real UMAP optimization.

- Added cell-level donor leakage and pathology mixing evaluation:

```text
scripts/evaluate_cell_level_mixing.py
```

Outputs:

```text
results/tables/cell_level_mixing_metrics.csv
results/tables/cell_level_mixing_sample_metadata.csv
```

Setup:

```text
sample: 9,799 Microglia-PVM cells
donors: 89
target: percent AT8 positive area_Grey matter
device: CUDA
comparison: cell-level expression PCA-128 vs cell-level JEPA-128
```

Results:

```text
metric                         expression PCA     JEPA
donor silhouette               -0.0403            -0.1181
donor kNN accuracy              0.4450             0.2388
donor majority baseline         0.0115             0.0115
AT8 pathology silhouette       -0.0018            -0.0041
permuted pathology silhouette  -0.0034            -0.0064
pathology minus permuted        0.0016             0.0024
pathology / abs(donor) ratio   -0.0447            -0.0343
```

Interpretation: JEPA does not appear to be simply memorizing donor identity in this cell-level test. Donor kNN accuracy is substantially lower in JEPA than in PCA, and donor silhouette is more negative, suggesting stronger donor mixing. Cell-level AT8 pathology separation is weak for both representations, which is expected because AT8 is a donor-level label broadcast to cells. After donor-level permutation control, JEPA has a modestly stronger AT8 signal than PCA.

- Ran the first K562 Perturb-seq engineering smoke test:

```text
script: scripts/benchmark_perturbseq_streaming.py
data: local ReplogleWeissman2022_K562_gwps.h5ad
targets: HSP90B1, SOD1, BRD4
controls streamed: 100
KO cells per target: 50
null shuffles: 5
output: results/tables/perturbseq_streaming_validation.csv
```

Zenodo HTTPS streaming successfully connected and read metadata, but repeated row streaming was too slow and timed out. The same benchmark machinery completed against the local K562 GWPS file.

Results:

```text
target   cosine    spearman   empirical p
HSP90B1  -0.452    -0.440     0.2
SOD1      0.051    -0.031     0.8
BRD4     -0.197    -0.167     1.0
```

Interpretation: this is an engineering smoke test, not AD microglia validation. It proves the benchmark pipeline can align a Perturb-seq dataset to the SEA-AD JEPA gene space, stream selected cells, compute observed CRISPR latent shifts, compute digital knockout latent shifts, and write result CSVs. The weak/negative alignment is expected to remain biologically ambiguous in K562 because it is a leukemia cell line and not a microglia model.

- Hardened the K562 benchmark script for the next round:

```text
script: scripts/benchmark_perturbseq_streaming.py
new flags:
  --counterfactual-mode input_erasure | predictive
  --max-retries
  --retry-wait-seconds
```

The original `input_erasure` mode measures a context-encoder shift after replacing the target gene in control cells. The new `predictive` mode measures a predictor-space shift after the same masking step, then compares it with the observed CRISPR context-encoder shift. This separates local input sensitivity from the JEPA predictor's learned latent-to-latent counterfactual behavior.

Tiny local predictive-mode smoke test completed for HSP90B1:

```text
controls streamed: 20
KO cells streamed: 10
null shuffles: 1
cosine: -0.688
spearman: -0.628
```

This test only verifies that the new path executes. It should not be treated as a biological conclusion.

- Secured the Dräger/Kampmann iPSC-derived microglia CRISPRi/a dataset:

```text
GEO accession: GSE178317
paper: A CRISPRi/a platform in human iPSC-derived microglia uncovers regulators of disease states
local raw folder: data/raw/kampmann_gse178317/
```

The GEO series contains CROP-seq 10X expression lanes and sgRNA-enrichment lanes. The public H5 files are Cell Ranger count matrices; the final per-cell sgRNA assignments were produced by a separate guide-mapping/demux workflow and are not exposed as a simple metadata table in GEO.

Because of that, the first automated Kampmann benchmark uses the published target-gene DEG vectors from Supplementary Table 9:

```text
script: scripts/benchmark_kampmann_deg_alignment.py
outputs:
  results/tables/kampmann_deg_jepa_alignment_input_erasure.csv
  results/tables/kampmann_deg_jepa_alignment_predictive.csv
```

Available CROP-seq targets include `CSF1R`, `INPP5D`, `TGFBR2`, `CDK8`, `CDK12`, `MED1`, `NDUFA8`, and `NDUFS5`. The first SEA-AD candidates `P2RY12`, `CX3CR1`, `TREM2`, `APOE`, complement genes, `TYROBP`, and `F13A1` are not directly perturbed in this public CROP-seq screen.

First DEG-vector alignment results:

```text
input_erasure:
  CSF1R   cosine -0.515   Spearman -0.488
  TGFBR2  cosine -0.269   Spearman -0.270
  CDK8    cosine -0.510   Spearman -0.425
  CDK12   cosine  0.350   Spearman  0.311

predictive:
  CSF1R   cosine -0.616   Spearman -0.587
  TGFBR2  cosine -0.402   Spearman -0.399
  CDK8    cosine -0.543   Spearman -0.493
  CDK12   cosine  0.288   Spearman  0.258
```

Interpretation: this is the first biology-matched external stress test. The current v1 SEA-AD JEPA does not broadly align with observed iPSC-microglia CRISPRi DEG responses. That is not a failure of the project; it is a useful boundary on v1 and a concrete reason to add stronger module-level perturbations, CRISPRi-aware knockdown modeling, and cross-domain/foundation pretraining in JEPA v2.

- Generated the v1 internal SEA-AD biological hypothesis report:

```text
script: scripts/generate_v1_biological_hypothesis_report.py
report: results/reports/v1_microglia_biological_hypotheses.md
tables:
  results/tables/v1_hypothesis_candidate_genes.csv
  results/tables/v1_hypothesis_candidate_modules.csv
  results/tables/v1_jepa_63_decode.csv
```

Key extracted findings:

```text
jepa_63
  strongest AT8/pTau latent coefficient
  AT8 mean coefficient ~= -0.118
  NeuN mean coefficient ~= -0.055
  top module annotations: complement, antigen presentation, synapse pruning

top model-implied AT8-lowering genes
  CHI3L1
  PTPRG
  NFKBIA
  S100A4
  TNFRSF11B
  DRAM1
  P2RY12
  MRC1
  MSR1
  CTSD

cleanest AT8-lowering module
  at8_associated_first_pass
```

Interpretation: the most useful v1 biology is internal to SEA-AD rather than the external Kampmann stress test. The current model points to an AT8-linked inflammatory/stress program, a `jepa_63` complement/antigen-presentation/synapse-pruning axis, and vascular/barrier or lipid-context modules as follow-up hypotheses. These remain model-implied counterfactual hypotheses until tested against perturbation, spatial, or orthogonal pathology data.

- Tested whether `jepa_63` aligns with the donor-level UMAP geometry:

```text
script: scripts/evaluate_jepa63_umap_alignment.py
outputs:
  results/tables/jepa63_umap_alignment_metrics.csv
  results/figures/jepa63_umap_alignment.svg
```

Main result:

```text
expression PCA UMAP
  linear 2D-coordinate R2 for jepa_63 ~= 0.097
  Spearman x ~= 0.374
  Spearman y ~= 0.140

JEPA latent UMAP
  linear 2D-coordinate R2 for jepa_63 ~= 0.263
  Spearman x ~= 0.231
  Spearman y ~= -0.434
```

Interpretation: `jepa_63` is visibly part of the JEPA UMAP geometry, especially along the JEPA UMAP y-axis, but it does not explain the whole manifold. This is the right interpretation: UMAP is a 2D projection of the full 128D state space, while `jepa_63` is one latent axis inside that state space.

- Ranked every JEPA latent dimension by alignment with the donor-level UMAP geometry:

```text
script: scripts/rank_all_latent_umap_alignment.py
outputs:
  results/tables/all_jepa_umap_variance_rankings.csv
  results/reports/all_jepa_umap_variance_rankings.md
```

Main result:

```text
JEPA latent UMAP
  top latent R2 ~= 0.867
  median latent R2 ~= 0.385
  jepa_63 rank: 83 of 128
  jepa_63 R2 ~= 0.263

Expression PCA UMAP
  top latent R2 ~= 0.564
  median latent R2 ~= 0.237
  jepa_63 rank: 92 of 128
  jepa_63 R2 ~= 0.097
```

Interpretation: `jepa_63` is pathology-relevant but not a dominant UMAP-shaping axis. The JEPA UMAP is mostly organized by stronger homeostatic, vascular/barrier, complement, and synapse-pruning axes. This is a useful correction to the v1 story: `jepa_63` should be presented as an AT8-linked latent hypothesis inside the broader manifold, not as the main visual axis of the manifold.

- Ranked Microglia-PVM pseudobulk genes associated with AT8 pathology:

```text
results/tables/microglia_pvm_percent_AT8_gene_rankings.csv
results/tables/microglia_pvm_percent_AT8_gene_set_scores.csv
```

Top AT8-associated genes in the first pass include:

```text
PTPRG
S100A4
CHI3L1
DRAM1
TNFRSF11B
IL27RA
CTSD
NFKBIA
```

## Notes

The first attempted microglia-specific extraction was slow because microglia rows are distributed across the full H5AD file. This is now handled by sequential CSR streaming in `scripts/build_microglia_streaming_pilot.py`.

## Next Steps

1. Add JEPA embedding-to-pathology comparison plots.
2. Extract pathology-associated latent factors.
3. Rank genes/modules associated with A beta, pTau, GFAP, Iba1, and NeuN targets.
4. Add richer hypothesis reports that compare pseudobulk, random-masking JEPA, mixed-masking JEPA, and module-preserved mixed JEPA.
