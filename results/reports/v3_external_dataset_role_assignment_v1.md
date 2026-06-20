# v3 external dataset role assignment v1

## 1. Executive summary

Stage 26A inventories external or non-SEA-AD-like v1/v2 artifacts before v3 training and freezes conservative dataset roles. Any dataset used for training, tuning, model selection, or architecture decisions cannot later be claimed as untouched external validation.

Datasets/artifact groups found: `15`. No dataset is currently reserved as untouched external validation because the discovered external artifacts have already been used/generated in v1/v2 analyses or have mixed/unclear provenance.

No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.

## 2. External datasets found

- `align_to_graph_jepa`: Align To Graph Jepa (repository artifact); artifacts=1
- `cellxgene_normal_microglia`: cellxgene normal microglia anchor artifacts (cellxgene external normal microglia); artifacts=20
- `compare_representation_geometry`: Compare Representation Geometry (repository artifact); artifacts=1
- `external_gene_masks`: External gene masks and overlap artifacts (external gene universe overlap); artifacts=2
- `external_validation_related`: External validation planning/projection artifacts (mixed external validation artifacts); artifacts=11
- `gse138852_grubman`: GSE138852/Grubman external AD microglia zero-shot artifacts (GEO / GSE138852); artifacts=25
- `gse174367_morabito`: GSE174367 Morabito external AD microglia/projection artifacts (GEO / GSE174367); artifacts=21
- `open_validation_framework_plan_v1`: Open Validation Framework Plan V1 (repository artifact); artifacts=1
- `perturbation_related`: Perturb-seq / perturbation benchmark artifacts (external perturbation references or synthetic placeholders); artifacts=5
- `public_pca_vs_jepa_pathology_geometry`: Public Pca Vs Jepa Pathology Geometry (repository artifact); artifacts=1
- `stage_c_finetuning_artifacts`: Stage C fine-tuning documentation/artifacts (internal SEA-AD model-development artifacts); artifacts=1
- `test_open_validation_alignment`: Test Open Validation Alignment (repository artifact); artifacts=1
- `v2_1_external_or_projection_artifacts`: v2.1 external/projection artifacts (mixed v2.1 artifacts); artifacts=48
- `v2_2_abeta_responsive_microglia`: v2.2 Aβ-responsive microglia derived artifacts (SEA-AD derived / internal v2.2 analysis); artifacts=24
- `v2_2_external_or_projection_artifacts`: v2.2 external/projection artifacts (mixed v2.2 artifacts); artifacts=30

## 3. What each dataset contains

- `align_to_graph_jepa`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `cellxgene_normal_microglia`: rows_total_known=53880; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=False; cell_state=True; trajectory=False; perturbation=False
- `compare_representation_geometry`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `external_gene_masks`: rows_total_known=2; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `external_validation_related`: rows_total_known=8592; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=True; trajectory=True; perturbation=True
- `gse138852_grubman`: rows_total_known=538; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=True; trajectory=True; perturbation=False
- `gse174367_morabito`: rows_total_known=4383; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=True; trajectory=True; perturbation=False
- `open_validation_framework_plan_v1`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `perturbation_related`: rows_total_known=4; gene_expression=True; donor_level=False; cell_level=True; pathology_targets=False; cell_state=False; trajectory=False; perturbation=True
- `public_pca_vs_jepa_pathology_geometry`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=True; cell_state=False; trajectory=False; perturbation=False
- `stage_c_finetuning_artifacts`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `test_open_validation_alignment`: rows_total_known=0; gene_expression=False; donor_level=False; cell_level=False; pathology_targets=False; cell_state=False; trajectory=False; perturbation=False
- `v2_1_external_or_projection_artifacts`: rows_total_known=93909; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=True; trajectory=False; perturbation=True
- `v2_2_abeta_responsive_microglia`: rows_total_known=138080; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=False; trajectory=False; perturbation=False
- `v2_2_external_or_projection_artifacts`: rows_total_known=455; gene_expression=True; donor_level=True; cell_level=True; pathology_targets=True; cell_state=True; trajectory=False; perturbation=False

## 4. Recommended role for each dataset

- `align_to_graph_jepa` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. No clear v3-safe use inferred from file names/columns.
- `cellxgene_normal_microglia` -> `self_supervised_pretraining`; training=True; validation_holdout=False. Normal microglia expression anchors may support self-supervised representation pretraining; no SEA-AD-like pathology targets.
- `compare_representation_geometry` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. No clear v3-safe use inferred from file names/columns.
- `external_gene_masks` -> `biological_plausibility_check`; training=False; validation_holdout=False. Gene masks are overlap/provenance aids, not direct outcome datasets.
- `external_validation_related` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. Provenance or role is unclear/mixed; freeze out of training and validation until reviewed.
- `gse138852_grubman` -> `biological_plausibility_check`; training=False; validation_holdout=False. Already used in zero-shot/projection artifacts; useful as plausibility context, not untouched validation.
- `gse174367_morabito` -> `biological_plausibility_check`; training=False; validation_holdout=False. Already used/generated in v2 external projection/trajectory artifacts; not untouched for v3 external validation.
- `open_validation_framework_plan_v1` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. No clear v3-safe use inferred from file names/columns.
- `perturbation_related` -> `future_perturbation_calibration`; training=False; validation_holdout=False. Perturbation artifacts are relevant to future calibration, not current pathology prediction validation.
- `public_pca_vs_jepa_pathology_geometry` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. No clear v3-safe use inferred from file names/columns.
- `stage_c_finetuning_artifacts` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. Provenance or role is unclear/mixed; freeze out of training and validation until reviewed.
- `test_open_validation_alignment` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. No clear v3-safe use inferred from file names/columns.
- `v2_1_external_or_projection_artifacts` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. Provenance or role is unclear/mixed; freeze out of training and validation until reviewed.
- `v2_2_abeta_responsive_microglia` -> `auxiliary_supervised_training`; training=True; validation_holdout=False. Aβ-responsive cell/axis labels can supervise auxiliary biological heads, but are not main donor-level pathology targets.
- `v2_2_external_or_projection_artifacts` -> `do_not_use_until_reviewed`; training=False; validation_holdout=False. Provenance or role is unclear/mixed; freeze out of training and validation until reviewed.

## 5. Training-safe uses

- Self-supervised pretraining candidates: cellxgene_normal_microglia
- Auxiliary supervision candidates: v2_2_abeta_responsive_microglia
- Main donor-level pathology prediction head: use SEA-AD locked donor folds only unless a future dataset has compatible donor-level pathology targets and is explicitly approved.

## 6. Validation-safe uses

- Reserved untouched external validation datasets: none currently identified
- GSE174367/GSE138852-derived artifacts should be treated as biological plausibility or prior external-projection context, not untouched v3 validation holdouts.

## 7. Risks of overfitting/generalization leakage

- A dataset used for pretraining or auxiliary supervision is no longer untouched validation.
- A dataset used for model selection, threshold choices, architecture choices, or candidate filtering cannot later support final external-validation claims.
- Provenance-unclear artifacts are frozen as do-not-use until reviewed.

## 8. Recommended v3 training strategy

- Use SEA-AD locked donor folds for the main pathology benchmark.
- Use external expression/cell-state datasets only for self-supervised pretraining or auxiliary biological heads unless compatible pathology labels are proven.
- Keep role flags frozen in the CSV before any v3 training begins.

## 9. Recommended untouched validation strategy

- Keep at least one future external dataset untouched if a final external generalization claim is desired.
- Do not use external validation data during model selection.
- Do-not-use-until-reviewed groups: align_to_graph_jepa, compare_representation_geometry, external_validation_related, open_validation_framework_plan_v1, public_pca_vs_jepa_pathology_geometry, stage_c_finetuning_artifacts, test_open_validation_alignment, v2_1_external_or_projection_artifacts, v2_2_external_or_projection_artifacts
