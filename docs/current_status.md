# Current Status

Last updated: 2026-06-13

## Executive Summary

The project has moved from v1 flat-vector snRNA JEPA to v2 Graph-JEPA.

v1 established the core SEA-AD Microglia-PVM pipeline:

```text
Microglia-PVM expression
        -> JEPA latent state
        -> donor-held-out pathology prediction
        -> digital knockout / latent Jacobian / confounder-adjusted hypotheses
```

v1 also exposed the key limitations:

```text
genes were independent columns rather than graph-connected nodes
disease fine-tuning could over-pin anchors or collapse into a narrow disease tube
external perturbation alignment was weak for specific microglial regulators
observational counterfactuals remain hypotheses, not causal proof
```

v2 addresses those issues with Graph-JEPA:

```text
node = gene
edge = STRING relationship
node feature = expression scalar + learnable gene identity embedding
training = Stage A healthy/reference pretraining, Stage B SEA-AD low-pathology calibration,
           Stage C disease-vector training with three-stream rehearsal
```

Current best Stage C tuning result by composite score:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.0045
disease covariance weight: 0.0005
pathology contrastive weight: 0.075
architecture: projection-head disease space + pathology-neighborhood loss
composite score: 1.686
AT8 ridge Spearman: 0.213
NeuN ridge Spearman: 0.426
AT8 cosine kNN Spearman: 0.266
NeuN cosine kNN Spearman: 0.303
GFAP cosine kNN Spearman: 0.408
SEA anchor cosine: 0.975
CELLxGENE anchor cosine: 0.961
```

Interpretation: `upgrade_fine_08` is now the strongest balanced v2.1 candidate and is anchor-safe. It does not maximize AT8 ridge performance; `fine_bridge_06` remains an important comparator for AT8-heavy biological analyses.

Latest biology extraction:

```text
active model: upgrade_fine_08_r0045_cov0005_pc0075, epoch 5
AT8 comparator: fine_bridge_06_r0045_cov0005, epoch 5

report:
  results/reports/v2_1_microglia_biological_hypotheses.md

ranked target matrix:
  results/tables/v2_1_ranked_target_matrix.csv

module counterfactual screen:
  strongest AT8-lowering shifts: antigen presentation, vascular/barrier myeloid,
                                 inflammatory signaling, complement
  strongest AT8-up shifts: lipid metabolism, homeostatic microglia,
                           senescence/stress, lysosome/phagocytosis

top ranked gene hypotheses:
  APP, BCL2, TLR2, CD4, P2RY12, APOE, MAPK1, CX3CR1,
  STAT3, CSF1R, UGCG, ROCK1

cross-model Jacobian signal:
  both upgrade_fine_08 and fine_bridge_06 route high-sensitivity predictor
  edges through lysosome/phagocytosis-annotated latent factors
```

Interpretation: v2.1 has moved from representation tuning back into biological extraction. The current result is coherent enough to pause broad tuning and prioritize independent validation of the ranked modules and genes.

Latest external validation:

```text
dataset:
  GSE174367 / Morabito prefrontal cortex snRNA-seq

model:
  upgrade_fine_08_r0045_cov0005_pc0075, epoch 5, strictly frozen

cells:
  4,126 microglia across 18 donors/samples

feature alignment:
  2,924 / 2,957 Graph-JEPA genes matched
  33 missing genes imputed with SEA-AD low-pathology Microglia-PVM means
  control-centroid shift applied

important cohort structure:
  tangle stages 1, 2, 5, and 6 are present
  tangle stages 3 and 4 are absent
```

Result:

```text
AT8/pTau SEA-AD trajectory vs Morabito tangle stage:
  donor Spearman rho: 0.224
  p-value: 0.372

early tangle stages 1-2 vs late stages 5-6:
  AT8/pTau trajectory AUC: 0.623
  rank-biserial effect: 0.247

leave-one-donor-out Spearman range:
  0.131 to 0.320

donor-level covariates:
  PMI, RIN, age, and batch do not dominate the AT8 trajectory score
```

Interpretation: this is a weak/negative tau-transfer stress test, not definitive validation. The direction is slightly positive for AT8/A beta trajectories, but the effect is small and not statistically convincing. The missing tangle stages 3-4 also mean the result should not be described as continuous Braak trajectory tracking.

Outputs:

```text
script:
  scripts/project_gse174367_morabito.py

report:
  results/reports/external_validation_gse174367.md

tables:
  results/tables/v2_1_gse174367_trajectory_correlations.csv
  results/tables/v2_1_gse174367_transition_boundary_auc.csv
  results/tables/v2_1_gse174367_covariate_audit.csv

figure:
  results/figures/v2_1_gse174367_at8_trajectory_by_tangle.svg
```

Latest v2.2 robustness smoke test:

```text
objective:
  harden Graph-JEPA against external feature mismatch before ingesting new cohorts

implementation:
  random expression-scalar dropout
  module expression-scalar dropout
  known external missing-gene mask simulation
  context-only DropEdge
  gene identity embeddings preserved
  master STRING/consensus graph unchanged

external masks generated from local files:
  GSE174367 / Morabito: 33 missing genes
  GSE138852 / Grubman: 331 missing genes

script:
  scripts/build_external_gene_masks.py
  scripts/train_graph_jepa_stage_a.py

smoke data:
  SEA-AD Microglia-PVM, 2,000-cell cap

successful run:
  results/tables/v2_2_topology_dropout_test_history.csv
```

Smoke-test result:

```text
epoch 1 -> epoch 5:
  loss: 0.0988 -> 0.0063
  effective dimensions: 9.4 -> 62.0
  top singular-value ratio: 0.381 -> 0.117
  mean latent dimension std: 0.1246 -> 0.0027

interpretation:
  the augmented run completed without the collapse guard firing when using
  graph-appropriate variance scaling (variance_gamma = 0.02)
```

Important lesson: the first aggressive smoke test with the default `variance_gamma = 1.0` tripped the collapse guard at epoch 5. That did not invalidate the augmentation design; it showed that raw graph-pooled latent scale is much smaller than the old variance floor assumed. v2.2 diagnostics should track effective dimensions and top singular-value ratio, not only raw variance penalty.

Latest v2.2 external-cohort adapter build:

```text
objective:
  prepare public CELLxGENE cohorts for Phase 2 domain-alignment experiments

script:
  scripts/build_cellxgene_adapters.py

raw local inputs:
  data/external/cellxgene/rexach_cross_dementia.h5ad
  data/external/cellxgene/olah_live_microglia.h5ad

aligned local outputs:
  data/processed/v2_alignment/rexach_cross_dementia_microglia_jepa_aligned.h5ad
  data/processed/v2_alignment/olah_live_microglia_microglia_jepa_aligned.h5ad

tracked summaries:
  results/tables/v2_2_cellxgene_alignment_stats.csv
  results/reports/v2_2_cellxgene_alignment_stats.md
```

Adapter rules:

```text
cell filter:
  cell_type == "microglial cell"
  or cell_type_ontology_term_id == "CL:0000129"

feature alignment:
  exact 2,957-gene Graph-JEPA order from the SEA-AD Phase 1 object
  missing external genes are zero-filled
  master STRING/consensus graph topology is not modified
```

Alignment result:

```text
Rexach cross-dementia:
  microglia: 21,575
  donors: 40
  matched genes: 2,837 / 2,957
  overlap: 95.9%
  diseases: Alzheimer disease, PSP, Pick disease, normal

Olah live microglia:
  microglia: 16,099
  donors: 17
  matched genes: 2,846 / 2,957
  overlap: 96.2%
  diseases: Alzheimer disease, temporal lobe epilepsy
```

Interpretation: Phase 2 now has two public, Graph-JEPA-aligned external microglia cohorts ready for adapter training and domain-adversarial experiments. These are training/alignment resources, not final held-out validation cohorts.

Latest Phase 1 scaling fix:

```text
problem:
  the original PyG Stage A trainer was too slow for full 40,000-cell
  topology-dropout pretraining because it materialized one graph per cell

solution:
  fast shared-topology Graph-JEPA trainer

new files:
  scripts/train_graph_jepa_stage_a_fast.py
  scripts/train_graph_jepa_stage_a_fast_hydra.py
  configs/train/graph_jepa_stage_a_fast.yaml

architecture:
  expression batch: [batch, 2,957 genes]
  graph topology: one shared sparse gene adjacency
  gene identity: learned embedding per gene
  augmentations: vectorized expression-scalar masking, module masking,
                 external missing-gene masks, and DropEdge
```

Benchmark:

```text
2,000-cell benchmark, batch 256:
  8.6 sec/epoch
  231.5 cells/sec

full 40,000-cell benchmark, batch 256:
  171-175 sec/epoch
  228-234 cells/sec

full 40,000-cell benchmark, batch 512:
  187.5 sec/epoch
  213.3 cells/sec
```

Interpretation: the fast trainer resolves the Phase 1 scaling bottleneck. Batch 256 is the current default, and the full 50-epoch Phase 1 pretraining run is now practical on the local RTX 3080 Laptop GPU.

Latest Stage B domain-adversarial alignment scaffold:

```text
objective:
  align SEA-AD, Rexach, and Olah microglia into a more cohort-invariant
  latent space while preserving Graph-JEPA biological structure

new files:
  scripts/train_graph_jepa_stage_b_adversarial.py
  configs/train/stage_b_adversarial.yaml

inputs:
  SEA-AD Microglia-PVM full cohort
  Rexach cross-dementia microglia adapter
  Olah live microglia adapter
  Stage A fast Graph-JEPA checkpoint

batching:
  deterministic balanced batches
  equal SEA-AD, Rexach, and Olah cells per update

loss:
  total = JEPA predictive loss + domain_loss_weight * domain classifier loss
  domain classifier receives z through a Gradient Reversal Layer

default freeze mode:
  partial_encoder
  unfreezes context encoder output layer and predictor
```

Smoke test:

```text
command:
  python scripts/train_graph_jepa_stage_b_adversarial.py epochs=1 max_steps_per_epoch=2 per_domain_batch_size=8 checkpoint_every=0

result:
  completed
  domain accuracy: 0.354
  effective dimensions: 23.84
  top singular-value ratio: 0.283
```

Interpretation: Stage B code is wired and ready. The smoke result only validates implementation mechanics; it is not a biological/domain-alignment result. The real Stage B run should start from the best completed Stage A fast checkpoint.

Latest multi-target counterfactual stability pass:

```text
targets:
  AT8/pTau
  A beta/6e10
  GFAP
  Iba1
  NeuN

reports:
  results/reports/v2_1_multitarget_counterfactual_stability.md
  results/reports/v2_1_named_biological_programs.md

top multi-target module axes by mean absolute effect:
  lysosome/phagocytosis
  homeostatic microglia
  plaque response
  disease-associated microglia
  lipid metabolism
  senescence/stress
  antigen presentation
  vascular/barrier myeloid

top multi-target gene effects by mean absolute effect:
  APP
  STAT3
  GRB2
  HSP90AA1
  BCL2
  HIF1A
  MAPK1
  APOE
  RHOA
  CTSD
  CX3CR1
  CD4
  TLR2
  CD74
  P2RY12
```

Interpretation: the multi-target pass separates broad tissue-state axes from cleaner pathology-lowering hypotheses. Lysosome/phagocytosis, homeostatic surveillance, lipid/plaque/DAM, and stress/survival programs are broad state axes. Antigen presentation, vascular/barrier myeloid, complement, and inflammatory signaling are more directly pathology-lowering in the current AT8/A beta screens. This strengthens the case for validation rather than more broad parameter tuning.

Artifact-control validation of the v2.1 target matrix:

```text
script:
  scripts/validate_v21_target_matrix.py

outputs:
  results/tables/v2_1_target_validation_alien_cell_check.csv
  results/tables/v2_1_target_validation_covariate_correlations.csv
  results/tables/v2_1_target_validation_covariate_flags.csv
  results/tables/v2_1_target_validation_within_state_check.csv
  results/tables/v2_1_target_validation_validated_target_matrix.csv
  results/tables/v2_1_target_validation_report.md

alien-cell check:
  top-10 target perturbations tested
  manifold violations: 0 / 10

covariate-confounder check:
  original available donor covariates: Age at Death, Sex
  original missing fields: PMI, RIN/RNA quality
  flagged latent factor: z_107 only
  affected ranked target: CX3CR1 receives one caution flag via bridge_best_latent z_107

within-state compositional-artifact check:
  top-5 target perturbations tested inside top-quartile plaque-response/DAM-like cells
  compositional artifacts: 0 / 5
```

Interpretation: the top five ranked targets survive the first falsification screens. The target matrix should now be read with validation tiers rather than raw rank alone.

SEA-AD full donor metadata audit:

```text
script:
  scripts/audit_sea_ad_full_donor_metadata.py

outputs:
  results/tables/sea_ad_full_metadata_covariate_audit.csv
  results/tables/sea_ad_full_metadata_targets_with_covariates.csv
  results/reports/sea_ad_full_metadata_covariate_audit.md

new covariates recovered from the donor workbook:
  PMI: 84 / 84 donors
  RIN: 84 / 84 donors
  Brain pH: 84 / 84 donors
  Braak: 84 / 84 donors
  Thal: 84 / 84 donors
  APOE Genotype: 84 / 84 donors
  Cognitive Status: 84 / 84 donors
```

Full-covariate v2.1 artifact validation:

```text
command:
  conda run -n sea-ad-jepa python scripts/validate_v21_target_matrix.py --metadata results/tables/sea_ad_full_metadata_targets_with_covariates.csv --out-prefix results/tables/v2_1_target_validation_full_covariates

outputs:
  results/tables/v2_1_target_validation_full_covariates_alien_cell_check.csv
  results/tables/v2_1_target_validation_full_covariates_covariate_correlations.csv
  results/tables/v2_1_target_validation_full_covariates_covariate_flags.csv
  results/tables/v2_1_target_validation_full_covariates_within_state_check.csv
  results/tables/v2_1_target_validation_full_covariates_validated_target_matrix.csv
  results/tables/v2_1_target_validation_full_covariates_report.md

available nuisance covariates:
  Age at Death, Sex, PMI, RIN, Brain pH, Fresh Brain Weight

alien-cell manifold violations:
  0 / 10 tested genes

within-state compositional artifacts:
  0 / 5 tested genes

covariate-confounded latent factors:
  1 / 13 tested factors
  z_107 remains the only caution axis
```

Interpretation: adding PMI, RIN, brain pH, and fresh brain weight did not overturn the main target matrix. `APP`, `BCL2`, `TLR2`, `CD4`, and `P2RY12` still pass all current internal controls. `CX3CR1` remains useful but should carry a caution flag because its bridge-model support routes through `z_107`, where nuisance-covariate correlation is marginally higher than pathology correlation.

First frozen external projection smoke test:

```text
dataset:
  GSE138852 / Grubman-Leng entorhinal cortex

source:
  GEO processed files
  GSE138852_counts.csv.gz
  GSE138852_covariates.csv.gz

script:
  scripts/project_external_ad_microglia.py

model:
  upgrade_fine_08_r0045_cov0005_pc0075, epoch 5
  strict freeze, no weight updates
  projector embedding space

feature alignment:
  projected microglia cells: 449
  external groups: 6
  matched genes: 2,626 / 2,957
  gene overlap fraction: 0.888

outputs:
  results/tables/gse138852_graph_jepa_zero_shot_donor_embeddings.csv
  results/tables/gse138852_graph_jepa_zero_shot_predicted_pathology.csv
  results/tables/gse138852_graph_jepa_zero_shot_module_scores.csv
  results/tables/gse138852_graph_jepa_zero_shot_summary.csv
  results/tables/gse138852_graph_jepa_zero_shot_report.md
```

External smoke-test result:

```text
AD-up modules:
  complement: AUC 1.000
  disease-associated microglia: AUC 1.000
  plaque response: AUC 1.000
  AT8-associated first-pass module: AUC 1.000
  vascular/barrier myeloid: AUC 0.889

Control-up modules:
  homeostatic microglia: AUC 0.000
  chemokine migration: AUC 0.000
  lipid metabolism: AUC 0.111

SEA-AD-calibrated pathology heads:
  did not cleanly transfer in this tiny categorical cohort
```

Interpretation: this is a successful zero-shot engineering smoke test and a promising module-level biological replication signal. It is not yet a continuous pathology-severity validation. The next external target should be `GSE174367`, followed by ROSMAP/Mathys if individual-level clinical/pathology metadata access is available.

Improved external projection alignment:

```text
command:
  conda run -n sea-ad-jepa python scripts/project_external_ad_microglia.py --missing-gene-imputation sea_ad_low_pathology_mean --alignment control_centroid_shift --out-prefix results/tables/gse138852_graph_jepa_zero_shot_aligned

method:
  missing genes imputed with SEA-AD low-pathology Microglia-PVM mean expression
  external control centroid shifted to the SEA-AD low-pathology centroid
  external groups scored along SEA-AD disease trajectory vectors

outputs:
  results/tables/gse138852_graph_jepa_zero_shot_aligned_summary.csv
  results/tables/gse138852_graph_jepa_zero_shot_aligned_report.md
  results/tables/gse138852_graph_jepa_zero_shot_alignment_comparison.csv
```

Aligned-run result:

```text
all five SEA-AD disease trajectories:
  AD groups shifted further along the disease direction than controls

A beta/6e10 model-scale score:
  AUC improved from 0.333 to 0.778
  mean AD-control difference changed from -3.211 to +1.732

AT8/pTau model-scale score:
  AUC improved from 0.333 to 0.556
  mean AD-control difference changed from -1.854 to +0.240
```

Interpretation: control-centroid alignment and trajectory scoring partially solve the Ridge-intercept/batch-shift problem identified in the first GSE138852 run. The module-level signal remains the strongest finding, while the trajectory/pathology-head improvements make the external projection more biologically interpretable.

Latest v2.1 upgrade comparison:

```text
best initial upgrade screen: upgrade_02_projector_pathology
change: projection-head disease space + pathology-neighborhood loss
composite score: 1.634
AT8 ridge Spearman: 0.265
NeuN ridge Spearman: 0.428
AT8 cosine kNN Spearman: 0.277
NeuN cosine kNN Spearman: 0.306
SEA anchor cosine: 0.975
CELLxGENE anchor cosine: 0.961
```

Interpretation: projection-head decoupling plus gentle pathology-aware neighborhood organization became the winning v2.1 direction after the focused `upgrade_fine` sweep. The first pathway-specific elasticity policy did not help at weight 0.01 and should remain experimental rather than the default.

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

- Added a multi-panel JEPA representation overlay figure:

```text
script: scripts/plot_jepa_representation_overlays.py
outputs:
  results/figures/jepa_representation_overlays.svg
  results/reports/jepa_representation_overlays.md
  results/tables/jepa_representation_overlay_plot_data.csv
```

Panels:

```text
jepa_34   dominant homeostatic / vascular axis, rank 1/128, R2 ~= 0.867
jepa_46   complement / synapse-pruning axis, rank 2/128, R2 ~= 0.826
jepa_108  homeostatic / synapse-pruning axis, rank 3/128, R2 ~= 0.779
jepa_63   AT8-linked complement axis, rank 83/128, R2 ~= 0.263
AT8       pathology overlay, R2 ~= 0.079
NeuN      pathology overlay, R2 ~= 0.182
```

Interpretation: this is the current best visual summary of the donor-level JEPA state space. It shows that the visible manifold is mainly a broad microglial-state map, while `jepa_63` marks a secondary AT8-linked substructure. The plot includes 89 donor embeddings; pathology overlays use the 84 donors with available target labels.

- Added a zero-shot external cohort projection workflow for Grubman/GSE138852:

```text
script: scripts/project_grubman_zero_shot.py
default checkpoint:
  results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt
expected outputs:
  results/tables/grubman_zero_shot_donor_embeddings.csv
  results/tables/grubman_zero_shot_generalization.csv
```

Purpose:

```text
Freeze SEA-AD JEPA encoder
Align public Grubman/GSE138852 genes to SEA-AD JEPA gene order
Project external cells without retraining
Aggregate donor-level jepa_63, jepa_34, jepa_46, and jepa_108
Test whether AD/control labels separate in the frozen SEA-AD latent space
```

Interpretation boundary: this is independent observational-cohort validation. If `jepa_63` separates AD/control in Grubman microglia, it supports the generalizability of the AT8-linked hypothesis axis. It still does not prove perturbational causality.

- Ran the Grubman/GSE138852 zero-shot projection on strict public microglia labels:

```text
input files:
  data/external/grubman_gse138852/GSE138852_counts.csv.gz
  data/external/grubman_gse138852/GSE138852_covariates.csv.gz

cell filter:
  oupSample.cellType == mg

outputs:
  results/tables/grubman_zero_shot_sample_pool_embeddings.csv
  results/tables/grubman_zero_shot_generalization.csv
```

Run summary:

```text
microglia nuclei projected: 449
JEPA genes matched: 2,626 / 2,957
aggregation level: 6 public sample pools
  AD pools: AD1_AD2, AD3_AD4, AD5_AD6
  control pools: Ct1_Ct2, Ct3_Ct4, Ct5_Ct6
```

Results:

```text
latent    AD mean    control mean    delta AD-control    rank-biserial    p
jepa_63   -0.0389    -0.0491         +0.0102             +0.556          0.4
jepa_34   +0.1358    +0.0567         +0.0791             +1.000          0.1
jepa_46   +0.1132    +0.0666         +0.0467             +1.000          0.1
jepa_108  +0.0404    +0.1180         -0.0776             -1.000          0.1
```

Interpretation: the zero-shot projection pipeline works, and gene overlap is strong. However, `jepa_63` does not show a decisive Grubman AD/control separation in this tiny public sample-pool view. The strongest separation appears in broader macro axes (`jepa_34`, `jepa_46`, `jepa_108`). This should be treated as a useful boundary on the v1 `jepa_63` claim, not a failure of the project. A better replication test needs individual donor metadata and pathology labels from a larger cohort such as ROSMAP/Mathys or a harmonized AD Knowledge Portal release.

- Built the first JEPA v2 graph-topology foundation:

```text
scripts:
  scripts/build_string_graph.py
  scripts/build_wgcna_tom_graph.py
  scripts/build_consensus_graph.py

report:
  results/reports/v2_graph_foundation.md

outputs:
  results/tables/v2_graph_string_*.csv
  results/tables/v2_graph_wgcna_*.csv
  results/tables/v2_graph_consensus_*.csv
```

STRING prior graph:

```text
threshold 400: 55,027 edges, 2,789 / 2,957 connected genes
threshold 700: 14,565 edges, 2,311 / 2,957 connected genes
threshold 900:  6,781 edges, 1,789 / 2,957 connected genes
```

WGCNA/TOM empirical graph:

```text
power: 6
top TOM edges exported: 100,000
connected genes: 1,821 / 2,957
largest component: 762 genes
```

Consensus graph using STRING threshold 700 plus WGCNA/TOM:

```text
union graph:
  114,029 edges
  2,676 / 2,957 connected genes
  largest component: 2,666 genes

both-supported graph:
  536 edges
  376 / 2,957 connected genes
```

Interpretation: the union of STRING and WGCNA/TOM is the practical first graph for GNN-JEPA v2 because it connects about 90.5% of the JEPA feature space. The strict both-supported graph is too small and housekeeping-heavy to use as the main topology, but it is useful as a high-confidence interpretation or ablation subset.

- Audited SEA-AD low-pathology donors as possible internal v2 control anchors:

```text
script:
  scripts/audit_sea_ad_control_anchors.py

outputs:
  results/tables/sea_ad_low_pathology_anchor_audit_donors.csv
  results/tables/sea_ad_low_pathology_anchor_audit_summary.csv
  results/reports/sea_ad_low_pathology_anchor_audit.md
```

Definitions:

```text
relaxed anchor:
  ADNC Not AD/Low
  low AT8, <= cohort q25
  low 6e10/A beta, <= cohort q25
  no dementia
  >= 200 Microglia-PVM cells

strict anchor:
  relaxed anchor
  plus Braak <= II
  plus Thal <= 2
```

Results:

```text
total donors with metadata/counts: 89
relaxed low-pathology anchors: 10
strict low-pathology anchors: 4

AT8 q25 threshold: 0.0491383
6e10/A beta q25 threshold: 0.158095
```

Interpretation: SEA-AD does not contain enough strict low-pathology donors to serve as the only homeostatic baseline for v2. Use SEA-AD low-pathology donors as a matched internal aging/postmortem calibration set, but add external healthy/normal microglia, such as CELLxGENE/Siletti, for broad Stage A pretraining.

- Added the strict CELLxGENE Stage A healthy-anchor ingestion script:

```text
scripts/build_cellxgene_healthy_anchor_strict.py
```

Purpose:

```text
stream normal human brain microglia nuclei from CELLxGENE Census
restrict to primary data, nucleus suspension, and 10x 3' v3 transcription profiling
align the result to the exact 2,957-gene SEA-AD JEPA input order
zero-pad missing genes only after fetching matched genes
write a local H5AD anchor plus lightweight QC CSVs
```

This anchor is intended for JEPA v2 Stage A pretraining. It addresses the problem that SEA-AD low-pathology donors are useful matched aging/postmortem controls, but not a large enough or clean enough homeostatic baseline by themselves.

- Added the first translational actionability audit:

```text
script:
  scripts/audit_druggability_biomarkers.py

outputs:
  results/tables/jepa_v2_translational_actionability_matrix.csv
  results/tables/jepa_v2_translational_actionability_summary.csv
  results/reports/jepa_v2_translational_actionability.md
```

The audit joins the 2,957 JEPA genes to Human Protein Atlas protein-class annotations and v1 SEA-AD candidate-gene evidence. Current HPA overlap:

```text
HPA FDA drug targets:        136
HPA predicted membrane:      735
HPA predicted secreted:      105
FDA target and membrane:      66
```

Highest-priority biology-led candidates include:

```text
PTPRG
CHI3L1
MRC1
DRAM1
S100A4
P2RY12
TNFRSF11B
```

Interpretation: this is the bridge from representation learning to translational target prioritization. These annotations should not constrain JEPA/GNN representation learning. They should be used after inference to rank model-implied interventions by druggability, surface accessibility, and biomarker potential.

- Added Graph-JEPA v2 data/model scaffolding:

```text
src/sea_ad_jepa/graph_data.py
src/sea_ad_jepa/graph_jepa.py
scripts/check_graph_jepa_v2_inputs.py
results/tables/graph_jepa_v2_input_check.csv
```

Design:

```text
nodes: genes
edges: STRING/WGCNA consensus graph
graph sample: one cell or nucleus
node features: expression value plus optional annotations
gene identity: learnable embedding indexed by node_id
```

This explicitly avoids the scalar-node collapse problem. The GNN does not see each gene as only a floating-point expression value; it also receives a learnable identity embedding so message passing can distinguish genes such as `CSF1R`, `P2RY12`, `TREM2`, and `CHI3L1`.

Input validation currently passes:

```text
genes: 2,957
edge_index columns after undirected conversion and self-loops: 231,015
max edge node index: 2,956
node annotation rows: 2,957
```

The next Graph-JEPA step is to add the Stage A training loop once the CELLxGENE healthy anchor is available and PyTorch Geometric is installed.

- Built and validated the CELLxGENE Stage A healthy microglia anchor through WSL/Linux:

```text
data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad
```

Anchor summary:

```text
cells: 10,000
donors: 692
matched JEPA genes: 2,863 / 2,957
zero-padded JEPA genes: 94
anchor gene order matches SEA-AD graph order: yes
```

Assay composition:

```text
10x 3' v3:       7,949
10x multiome:    1,295
10x 3' v2:         342
sci-RNA-seq3:      340
other assays:       74
```

The original strict query requiring `assay == "10x 3' v3 transcription profiling"` returned zero cells. The successful anchor keeps the nucleus and normal/microglia/brain filters, but relaxes the assay filter. This is a reasonable Stage A compromise because most retained cells are still 10x 3' v3.

- Added and smoke-tested the Stage A Graph-JEPA trainer:

```text
script:
  scripts/train_graph_jepa_stage_a.py

smoke checkpoint:
  results/models/graph_jepa_stage_a_smoke/graph_jepa.pt

first full-anchor checkpoint:
  results/models/graph_jepa_stage_a_string_t700_rawvar_e5/graph_jepa.pt
```

Training setup:

```text
anchor: CELLxGENE normal microglia nuclei, 10,000 cells
graph: STRING t700 gene graph
node features: expression only
gene identity: learnable embedding
epochs: 5
batch size: 16
device: CUDA
```

Important loss fix:

```text
alignment uses normalized latent vectors
variance hinge now uses raw latent vectors
```

Before this fix, the variance regularizer was applied after L2 normalization, making `variance_gamma=1.0` effectively unreachable in 128D and allowing collapse-like behavior. After the fix, the Stage A run showed meaningful variance improvement:

```text
epoch 1: loss 1.0529, alignment 0.0677, variance 0.9853
epoch 5: loss 0.5062, alignment 0.0450, variance 0.4612
```

Extended Stage A run:

```text
checkpoint:
  results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt

TensorBoard logs:
  runs/graph_jepa_stage_a_string_t700_rawvar_e30
```

The 30-epoch run completed without triggering the collapse guardrail:

```text
epoch 1:  loss 1.0529, alignment 0.0677, variance 0.9853
epoch 10: loss 0.4420, alignment 0.0095, variance 0.4326
epoch 20: loss 0.4005, alignment 0.0031, variance 0.3975
epoch 30: loss 0.3699, alignment 0.0024, variance 0.3675
```

Interpretation: Stage A Graph-JEPA continues to improve past 5 epochs, and the raw-latent variance penalty keeps decreasing rather than remaining frozen. This supports continuing Stage A to a longer run or moving to Stage B calibration with this checkpoint as the current foundation.

Batch-size 64 comparison run:

```text
checkpoint:
  results/models/graph_jepa_stage_a_string_t700_rawvar_e30_b64/graph_jepa.pt

TensorBoard logs:
  runs/graph_jepa_stage_a_string_t700_rawvar_e30_b64
```

The batch-64 run completed without triggering the collapse guardrail:

```text
epoch 1:  loss 1.2518, alignment 0.2658, variance 0.9860
epoch 10: loss 0.6295, alignment 0.1042, variance 0.5253
epoch 20: loss 0.4921, alignment 0.0372, variance 0.4548
epoch 30: loss 0.4614, alignment 0.0154, variance 0.4461
```

Interpretation: batch 64 is stable and likely improves GPU utilization, but it does not reach the same low variance penalty by epoch 30 as the batch-16 run. It may need longer training or a modest learning-rate adjustment. For now, the batch-16 epoch-30 checkpoint remains the stronger Stage A representation candidate by raw variance spread, while batch 64 is a useful efficiency/stability comparison.

GeneJEPA-inspired scheduler/covariance experiment:

```text
checkpoint:
  results/models/graph_jepa_stage_a_string_t700_sched_e30_b64/graph_jepa.pt

TensorBoard logs:
  runs/graph_jepa_stage_a_string_t700_sched_e30_b64
```

Training changes:

```text
mask fraction warmup: 0.20 -> 0.50 over 10 epochs
EMA decay warmup: 0.992 -> 0.9995 over 10 epochs
gradient clipping: 1.0
raw-latent covariance penalty: weight 0.01
```

Result:

```text
epoch 1:  loss 1.2344, alignment 0.2440, variance 0.9860, covariance 0.4423
epoch 10: loss 0.9899, alignment 0.0007, variance 0.9855, covariance 0.3742
epoch 20: loss 0.9399, alignment 0.0231, variance 0.8675, covariance 4.9270
epoch 30: loss 0.8306, alignment 0.0330, variance 0.6597, covariance 13.7966
```

Interpretation: the scheduler works, but this exact covariance setting is not yet better than the simpler raw-variance run. The covariance penalty rises as the latent dimensions spread, suggesting that the model is learning broader variance but not yet decorrelating dimensions effectively. Treat this as a useful diagnostic, not the new best checkpoint. The current best Stage A checkpoint remains:

```text
results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt
```

- Built SEA-AD low-pathology anchor H5AD subsets for Stage B calibration:

```text
script:
  scripts/build_sea_ad_low_pathology_anchor_subset.py

relaxed anchor:
  data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad
  donors: 10
  cells: 4,467

strict anchor:
  data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad
  donors: 4
  cells: 1,883
```

- Extracted frozen Stage A reference coordinates:

```text
script:
  scripts/extract_stage_a_frozen_anchors.py

summary:
  results/tables/stage_a_frozen_anchor_coordinate_summary.csv

local coordinate banks:
  results/tables/stage_a_frozen_cellxgene_normal_microglia_coordinates.csv
  results/tables/stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv
  results/tables/stage_a_frozen_sea_ad_low_pathology_strict_coordinates.csv
```

These are frozen healthy/reference coordinates from the Stage A teacher encoder, not causal labels. They are intended for Stage B/C rehearsal so later SEA-AD calibration does not erase the Stage A healthy microglia reference geometry.

- Added and smoke-tested Stage B Graph-JEPA low-pathology calibration with rehearsal:

```text
script:
  scripts/train_graph_jepa_stage_b_rehearsal.py

smoke checkpoint:
  results/models/graph_jepa_stage_b_rehearsal_smoke/graph_jepa_stage_b.pt

TensorBoard logs:
  runs/graph_jepa_stage_b_rehearsal_smoke
```

Design:

```text
initialize from best Stage A Graph-JEPA checkpoint
primary batch: SEA-AD low-pathology Microglia-PVM nuclei
rehearsal batch: CELLxGENE normal-labeled microglia nuclei
primary rehearsal loss: keep SEA-AD low-pathology cells near frozen Stage A coordinates
external rehearsal loss: keep CELLxGENE anchor cells near frozen Stage A coordinates
```

Smoke-test result:

```text
epoch 1: loss 0.400822, JEPA 0.399966, primary rehearsal 0.001419, external rehearsal 0.002006
epoch 2: loss 0.408651, JEPA 0.407133, primary rehearsal 0.002597, external rehearsal 0.003474
```

Interpretation: the Stage B rehearsal machinery works and does not immediately erase the Stage A anchor geometry. The rehearsal losses are small in the smoke test, which is expected because Stage B starts from the Stage A checkpoint and should calibrate gently rather than relearn the manifold from scratch.

Full 20-epoch Stage B run:

```text
checkpoint:
  results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt

TensorBoard logs:
  runs/graph_jepa_stage_b_low_pathology_rehearsal_e20
```

Training summary:

```text
epoch 1:  loss 0.409593, JEPA 0.408263, primary rehearsal 0.002270, external rehearsal 0.003050, variance 0.396048
epoch 10: loss 0.384238, JEPA 0.384006, primary rehearsal 0.000279, external rehearsal 0.000647, variance 0.381008
epoch 20: loss 0.377224, JEPA 0.377146, primary rehearsal 0.000080, external rehearsal 0.000229, variance 0.375715
```

Stage A-to-B coordinate drift audit:

```text
script:
  scripts/audit_latent_coordinate_drift.py

summary:
  results/tables/stage_b_rehearsal_anchor_drift_summary.csv
```

Results:

```text
sea_ad_low_pathology_relaxed:
  cells: 4,467
  mean cosine before/after: 0.9916
  mean L2 delta: 1.0873

cellxgene_normal_microglia:
  cells: 10,000
  mean cosine before/after: 0.9754
  mean L2 delta: 1.3305
```

Interpretation: Stage B calibrated the latent space without catastrophic forgetting. SEA-AD low-pathology anchors stayed very close to their Stage A coordinates, and external CELLxGENE rehearsal cells also remained strongly aligned. These are reference-coordinate diagnostics, not biological validation metrics.

- Added and smoke-tested Stage C Graph-JEPA disease-vector training with three-stream rehearsal:

```text
script:
  scripts/train_graph_jepa_stage_c_disease.py

smoke checkpoint:
  results/models/graph_jepa_stage_c_disease_rehearsal_smoke/graph_jepa_stage_c.pt

smoke history:
  results/tables/graph_jepa_stage_c_disease_rehearsal_smoke_history.csv

TensorBoard logs:
  runs/graph_jepa_stage_c_disease_rehearsal_smoke
```

Design:

```text
stream 1: full SEA-AD Microglia-PVM disease manifold, masked JEPA objective
stream 2: SEA-AD low-pathology anchor, unmasked rehearsal objective
stream 3: CELLxGENE normal microglia anchor, unmasked rehearsal objective
```

Default batch composition:

```text
disease: 16 cells
SEA-AD low-pathology anchor: 8 cells
CELLxGENE normal anchor: 8 cells
```

Smoke-test result:

```text
epoch 1: loss 0.503819, disease JEPA 0.503760, SEA rehearsal 0.000043, CELLxGENE rehearsal 0.000076, variance 0.431909
epoch 2: loss 0.430117, disease JEPA 0.430047, SEA rehearsal 0.000054, CELLxGENE rehearsal 0.000086, variance 0.389643
```

Interpretation: the Stage C trainer runs with deterministic three-stream batch composition and tensorized frozen-coordinate rehearsal. The smoke test shows the disease objective can move while both anchor losses remain near zero. The full Stage C run should be followed by a Stage B-to-C anchor drift audit and pathology-axis evaluation before claiming any disease-vector improvement.

Full 20-epoch Stage C run:

```text
checkpoint:
  results/models/graph_jepa_stage_c_disease_rehearsal_e20/graph_jepa_stage_c.pt

history:
  results/tables/graph_jepa_stage_c_disease_rehearsal_history.csv

TensorBoard logs:
  runs/graph_jepa_stage_c_disease_rehearsal_e20
```

Training summary:

```text
epoch 1:  loss 0.407584, disease JEPA 0.404780, SEA rehearsal 0.002740, CELLxGENE rehearsal 0.002868, variance 0.393387
epoch 10: loss 0.360180, disease JEPA 0.360125, SEA rehearsal 0.000027, CELLxGENE rehearsal 0.000083, variance 0.359478
epoch 20: loss 0.355651, disease JEPA 0.355642, SEA rehearsal 0.000005, CELLxGENE rehearsal 0.000014, variance 0.355031
```

Stage B-to-C anchor drift audit:

```text
summary:
  results/tables/stage_c_rehearsal_anchor_drift_summary.csv
```

Results:

```text
SEA-AD low-pathology anchors:
  cells: 4,467
  mean cosine before/after: 0.9998
  mean L2 delta: 0.5186

CELLxGENE normal microglia anchors:
  cells: 10,000
  mean cosine before/after: 0.9992
  mean L2 delta: 0.3082
```

First donor-level pathology readout from Stage C embeddings:

```text
donor embeddings:
  results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv

ridge pathology result:
  results/tables/stage_c_rehearsal_donor_embedding_ridge_pathology.csv

latent-space geometry result:
  results/tables/stage_c_latent_space_evaluation_metrics.csv
```

Top ridge Spearman signals:

```text
percent NeuN positive area:             0.315
guhcl pTau:                             0.287
AT8 positive cells per area:            0.278
NeuN positive cells per area:           0.261
percent AT8 positive area:              0.260
percent GFAP positive area:             0.253
percent Iba1 positive area:             0.201
```

PCA-vs-Stage-C kNN geometry:

```text
target                       PCA kNN Spearman   Stage C kNN Spearman
AT8 / pTau                   0.219              0.053
NeuN                         0.330              0.269
A beta / 6e10                0.099              0.159
GFAP                        -0.012             -0.150
Iba1                        -0.044              0.013
```

Interpretation: Stage C preserved both reference anchors extremely well, so the three-stream rehearsal design worked. The first disease-readout is biologically plausible but not yet a clear representational win over PCA in donor-neighborhood geometry. Treat this as a successful Stage C engineering milestone plus a tuning target: the next pass should test less aggressive anchor weights, a shorter checkpoint such as epoch 10/15, or a pathology-aware Stage C objective.

- Evaluated intermediate Stage C checkpoints:

```text
script:
  scripts/summarize_stage_c_checkpoint_evaluation.py

summary:
  results/tables/stage_c_checkpoint_evaluation_summary.csv
```

Ridge Spearman checkpoint comparison:

```text
target                       epoch 5   epoch 10   epoch 15   epoch 20
AT8 / pTau                   0.316     0.256      0.243      0.260
NeuN                         0.457     0.250      0.272      0.315
A beta / 6e10               -0.088    -0.213     -0.199     -0.097
GFAP                         0.278     0.235      0.242      0.253
Iba1                         0.209     0.224      0.216      0.201
```

kNN geometry comparison against PCA:

```text
target                       best Stage C kNN Spearman   PCA kNN Spearman
AT8 / pTau                   0.053                       0.219
NeuN                         0.332                       0.330
A beta / 6e10                0.207                       0.099
GFAP                        -0.066                      -0.012
Iba1                         0.013                      -0.044
```

Interpretation: the early-checkpoint hypothesis is partly supported. Epoch 5 is the best Stage C checkpoint by ridge for AT8, NeuN, and GFAP, suggesting useful disease signal appears early and then fades under continued training. However, donor-neighborhood kNN geometry still does not recover AT8 better than PCA. The main geometry improvement is for A beta/6e10, with NeuN roughly tied to PCA at epoch 5. The next experiment should loosen rehearsal weights rather than simply selecting a later checkpoint.

- Ran the first elastic Stage C rehearsal experiment:

```text
script:
  scripts/train_graph_jepa_stage_c_disease.py

checkpoint:
  results/models/graph_jepa_stage_c_elastic_w005_e10/graph_jepa_stage_c.pt

history:
  results/tables/graph_jepa_stage_c_elastic_w005_e10_history.csv

TensorBoard logs:
  runs/graph_jepa_stage_c_elastic_w005_e10
```

Training changes:

```text
SEA rehearsal weight: 0.05
CELLxGENE rehearsal weight: 0.05
rehearsal loss: cosine softplus margin
margin: 0.95
temperature: 100
epochs: 10
```

New telemetry:

```text
anchor cosines
disease-to-CELLxGENE-centroid L2 distance
disease latent variance spread
disease effective dimensionality
disease top singular value ratio
```

Elastic telemetry summary:

```text
epoch 1:
  disease-to-CELLxGENE L2: 107.85
  disease variance spread: 23.57
  effective dims: 3.47
  top singular value ratio: 0.695
  SEA / CELLxGENE anchor cosine: 0.939 / 0.945

epoch 5:
  disease-to-CELLxGENE L2: 111.19
  disease variance spread: 23.85
  effective dims: 3.29
  top singular value ratio: 0.712
  SEA / CELLxGENE anchor cosine: 0.988 / 0.982

epoch 10:
  disease-to-CELLxGENE L2: 132.27
  disease variance spread: 36.54
  effective dims: 2.10
  top singular value ratio: 0.821
  SEA / CELLxGENE anchor cosine: 0.987 / 0.981
```

Elastic pathology readout:

```text
epoch 5 ridge Spearman:
  NeuN percent: 0.388
  guhcl pTau:   0.307
  AT8 percent:  0.204
  GFAP percent: 0.168

epoch 10 ridge Spearman:
  NeuN percent: 0.391
  AT8 percent:  0.283
  GFAP percent: 0.258
  Iba1 percent: 0.175
```

Elastic kNN geometry:

```text
target                       epoch 5 Stage C   epoch 10 Stage C   PCA reference
AT8 / pTau                  -0.100            -0.086             0.219
NeuN                         0.267             0.312             0.330
A beta / 6e10                0.079             0.162             0.099
GFAP                        -0.038            -0.077            -0.012
Iba1                        -0.143            -0.103            -0.044
```

Interpretation: elastic rehearsal released the anchors enough for disease distance and variance to grow, but it did not create a rich local disease manifold. Effective dimensionality fell from 3.47 to 2.10 while the top singular value ratio rose to 0.821, indicating a narrow disease tube. This explains why ridge can still recover some AT8/NeuN signal but kNN remains weak. The next Stage C objective should add a controlled disease-manifold spreading term or evaluate a non-Euclidean/neighborhood metric before adding a stronger contrastive loss.

- Ran a Stage C elastic rehearsal plus disease-covariance diagnostic:

```text
checkpoint:
  results/models/graph_jepa_stage_c_elastic_cov001_e10/graph_jepa_stage_c.pt

history:
  results/tables/graph_jepa_stage_c_elastic_cov001_e10_history.csv

TensorBoard logs:
  runs/graph_jepa_stage_c_elastic_cov001_e10
```

Training changes relative to the elastic run:

```text
disease_covariance_weight: 0.01
all other elastic settings unchanged
```

Telemetry summary:

```text
epoch 1:
  disease-to-CELLxGENE L2: 80.76
  disease variance spread: 1.94
  effective dims: 4.48
  top singular value ratio: 0.592
  SEA / CELLxGENE anchor cosine: 0.913 / 0.913

epoch 5:
  disease-to-CELLxGENE L2: 39.34
  disease variance spread: 1.60
  effective dims: 4.95
  top singular value ratio: 0.437
  SEA / CELLxGENE anchor cosine: 0.977 / 0.975

epoch 10:
  disease-to-CELLxGENE L2: 45.38
  disease variance spread: 1.55
  effective dims: 4.72
  top singular value ratio: 0.435
  SEA / CELLxGENE anchor cosine: 0.974 / 0.967
```

Disease-covariance pathology readout:

```text
epoch 5 ridge Spearman:
  NeuN percent: 0.344
  Iba1 percent: 0.286
  guhcl pTau:   0.271
  AT8 percent:  0.191

epoch 10 ridge Spearman:
  NeuN percent: 0.317
  AT8 percent:  0.269
  GFAP percent: 0.228
  Iba1 percent: 0.216
```

Disease-covariance kNN geometry:

```text
target                       epoch 5 Stage C   epoch 10 Stage C   PCA reference
AT8 / pTau                  -0.118            -0.020             0.219
NeuN                         0.244             0.275             0.330
A beta / 6e10                0.209             0.154             0.099
GFAP                        -0.063            -0.015            -0.012
Iba1                        -0.062            -0.042            -0.044
```

Interpretation: disease covariance reduced the narrow-tube pathology (`top_sv_ratio` improved from about 0.82 in elastic-only to about 0.43), but it also over-damped the disease manifold. Disease-to-anchor distance and variance spread fell sharply, and AT8 kNN still did not improve. The current evidence suggests a simple covariance penalty is too blunt at `0.01`; the next diagnostic should either use a much smaller covariance weight, apply covariance only after a warmup, or shift toward metric/evaluation changes before adding stronger contrastive pressure.

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

- Added a reproducible Stage C fine-tuning sweep:

```text
script:
  scripts/sweep_stage_c_finetuning.py

summaries:
  results/tables/stage_c_finetuning_sweep_summary.csv
  results/tables/stage_c_finetuning_fine_tight_summary.csv
  results/tables/stage_c_finetuning_fine_loose_summary.csv
  results/tables/stage_c_finetuning_combined_leaderboard.csv
```

The sweep evaluates each Stage C checkpoint with:

```text
AT8 and NeuN ridge Spearman
AT8 and NeuN Euclidean kNN Spearman
AT8 and NeuN cosine kNN Spearman
disease effective dimensionality
top singular value ratio
SEA-AD and CELLxGENE anchor cosine safety checks
```

Best current configuration:

```text
run: fine_loose_01_r005_cov0005
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.005
disease covariance weight: 0.0005
composite score: 1.544
AT8 ridge Spearman: 0.356
NeuN ridge Spearman: 0.374
AT8 Euclidean kNN Spearman: 0.065
NeuN Euclidean kNN Spearman: 0.271
AT8 cosine kNN Spearman: 0.227
NeuN cosine kNN Spearman: 0.258
disease effective dimensions: 4.76
top singular value ratio: 0.481
SEA anchor cosine: 0.956
CELLxGENE anchor cosine: 0.952
```

Interpretation: the best run found so far is much more elastic than the first Stage C run. It lets the disease manifold move while keeping both healthy/reference anchors just above the 0.95 cosine safety boundary. The result supports using a small rehearsal weight plus a very small covariance term as the current Stage C default. This is a tuning result, not a claim of final biological validation.

## Notes

The first attempted microglia-specific extraction was slow because microglia rows are distributed across the full H5AD file. This is now handled by sequential CSR streaming in `scripts/build_microglia_streaming_pilot.py`.

## Next Steps

1. Use `fine_loose_01_r005_cov0005` at epoch 5 as the active Stage C v2 baseline.
2. Run a narrow Stage C sweep around rehearsal `0.003-0.008` and disease covariance `0.00025-0.00075`.
3. Evaluate the best narrow-sweep checkpoint with donor-held-out pathology prediction and module/gene attribution.
4. Generate a model-implied hypothesis report from the current best Stage C checkpoint, keeping the causal boundary explicit.
5. Use external perturbation, spatial, imaging, or independent cohort data as validation layers rather than claiming causality from SEA-AD counterfactuals alone.
