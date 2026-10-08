from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


STAGE_ID = "stage81a0"
SCHEMA_VERSION = "1.0"
CONTRACT_PATH = Path("configs/v4/stage81a0_v4_design_contract.yaml")
OUTPUT_PATHS = {
    "registry_json": "results/v4/stage81a0_v4_failure_registry.json",
    "registry_csv": "results/v4/stage81a0_v4_failure_registry.csv",
    "stage_report": "results/v4/stage81a0_v4_stage_report.json",
}
FIELDS = [
    "failure_id",
    "historical_lineage",
    "category",
    "description",
    "evidence_status",
    "evidence_source_path",
    "evidence_section_or_field",
    "observed_metric_or_result",
    "scientific_consequence",
    "v4_prevention",
    "blocking_for_v4",
    "requires_human_decision",
]

CONFIRMED = "confirmed_from_repository_evidence"
RESOLVED = "resolved_with_repository_evidence"
RISK = "documented_risk_from_repository_evidence"
UNRESOLVED = "unresolved_from_current_repository_evidence"


def issue(
    failure_id: str,
    lineage: str,
    category: str,
    description: str,
    status: str,
    source: str,
    section: str,
    result: str,
    consequence: str,
    prevention: str,
    blocking: bool,
    human: bool,
) -> dict[str, Any]:
    return dict(zip(FIELDS, [failure_id, lineage, category, description, status, source, section, result, consequence, prevention, blocking, human]))


ISSUES = [
    issue("D01_matrix_scale_semantics", "v1-v3", "data_and_preprocessing", "The repository does not provide one lineage-wide contract distinguishing raw, normalized, and scaled model inputs.", UNRESOLVED, "", "repository search: raw/normalized/scaled input semantics", "No single authoritative lineage-wide matrix-scale declaration was found.", "A hidden scale change could invalidate transfer, masking, and perturbation interpretation.", "Freeze matrix semantics, transform parameters, and matrix hashes before v4A training.", True, True),
    issue("D02_source_layer_semantics", "v1-v3", "data_and_preprocessing", "The source AnnData layer used by every historical model is not established by one current repository artifact.", UNRESOLVED, "", "repository search: AnnData X/layers/raw provenance", "Lineage-wide source-layer equivalence remains unverified.", "The same H5AD can yield materially different inputs depending on X, raw, or layers selection.", "Record source object, source layer, sparsity, dtype, and transform in the v4 dataset manifest.", True, True),
    issue("D03_feature_order_drift", "v3", "data_and_preprocessing", "Feature order was treated as a reproducibility boundary in the frozen perturbation pipeline.", RESOLVED, "results/tables/stage77_perturbation_scenario_manifest_v1.csv", "feature_order_hash", "All Stage77 scenarios record feature_order_hash=4f65c677c8673754756118c6d978a3c04e73a57f7002d42e8550932b94b89662.", "Unnoticed reordering would apply expression and graph effects to the wrong genes.", "Require ordered feature files plus hashes at build, checkpoint load, and inference.", True, False),
    issue("D04_gene_symbol_uniqueness", "v1-v3", "data_and_preprocessing", "A complete audit of duplicate, alias-colliding, or ambiguous gene symbols is not discoverable for the frozen feature vocabulary.", UNRESOLVED, "", "repository search: duplicate and ambiguous symbols", "No lineage-wide uniqueness decision table was found.", "Ambiguous symbols can merge genes or disconnect graph and regulatory inputs.", "Create a versioned canonical symbol and stable-ID map with explicit duplicate policy.", True, True),
    issue("D05_missing_regulators_and_targets", "v3", "data_and_preprocessing", "The frozen 2,957-gene feature space omits regulators and candidate targets needed by Stage75 evidence.", CONFIRMED, "results/tables/stage76_regulator_readiness_v1.csv", "regulator_present_in_jepa_feature_space and target_genes_absent_from_jepa_feature_space", "CEBPA and RELA are absent; Tier A target coverage is ELF1 23/25, SPI1 14/15, and STAT1 16/18.", "Regulatory simulations were restricted by vocabulary rather than only by evidence strength.", "Design the v4 vocabulary before training and report coverage against frozen regulatory candidates.", True, True),
    issue("D06_cross_dataset_transform_mismatch", "v3", "data_and_preprocessing", "External benchmarks required dataset-specific raw-count size-factor log1p handling and did not establish transform equivalence to SEA-AD.", RISK, "results/reports/stage34b_hbcc_external_pretraining_report_v1.md", "dataset manifest and benchmark_transform", "HBCC used raw_count_size_factor_log1p with 0.9682 gene overlap; external pretraining still did not rescue the deficit.", "Uncontrolled transform differences can masquerade as domain or model failure.", "Fit and freeze one train-derived transform contract and test scale diagnostics per dataset.", True, True),
    issue("D07_donor_sample_identity_lineage_audit", "v1-v3", "data_and_preprocessing", "A single cross-dataset donor and sample identity reconciliation for all historical inputs was not found.", UNRESOLVED, "", "repository search: donor/sample identity reconciliation", "Dataset-specific donor fields exist, but lineage-wide identity equivalence is unresolved.", "Identity collisions or aliases can create leakage or incorrect aggregation.", "Freeze canonical donor, sample, and section IDs with source-specific mapping hashes.", True, True),
    issue("D08_silent_preprocessing_change", "v3", "data_and_preprocessing", "Stage76 showed that preprocessing and archived baselines require explicit reproducibility checks.", RESOLVED, "results/reports/stage76_perturbation_readiness_v1.json", "preprocessing provenance and deterministic repeated inference", "Repeated inference matched exactly and the frozen readiness report retained preprocessing and feature-order provenance.", "Silent preprocessing drift can make checkpoint outputs incomparable while code still runs.", "Make preprocessing hashes and archived-reference reproduction mandatory v4 load gates.", True, False),

    issue("S01_lineage_wide_split_audit", "v1-v3", "split_and_leakage", "The current repository does not provide one audit proving every historical training and evaluation path used donor-level rather than random-cell splits.", UNRESOLVED, "", "repository search: all lineage split implementations", "Later evaluations are donor-held-out, but lineage-wide split provenance is incomplete.", "Cell-level leakage can inflate generalization through donor-specific signatures.", "Generate immutable donor split manifests and reject cell-level final evaluation splits.", True, True),
    issue("S02_lineage_wide_donor_overlap_audit", "v1-v3", "split_and_leakage", "Dataset-specific audits passed, but complete donor overlap across all v4 candidate datasets is not yet established.", UNRESOLVED, "", "repository search plus dataset-specific leakage tables", "Stage33B and Stage34A report leakage_audit_pass=True; cross-source v4 overlap is not audited.", "The same donor in pretraining and test data would invalidate holdout claims.", "Hash normalized donor identities across every source before assigning roles.", True, True),
    issue("S03_spatial_section_split_provenance", "v4C", "split_and_leakage", "No implemented spatial dataset or section-level split manifest exists yet.", UNRESOLVED, "", "repository search: section-level split manifests", "Spatial modeling is future work in docs/architecture.md.", "Cells from one section in train and test would leak local tissue context.", "Treat tissue section as the indivisible spatial split unit and freeze section manifests.", True, True),
    issue("S04_clean_holdout_contamination", "v3", "split_and_leakage", "Several public datasets were already used for plausibility or development and cannot be called untouched validation.", CONFIRMED, "docs/DATASET_REGISTRY.md", "Already-used plausibility-only pool and role rules", "GSE174367, GSE138852, SEA-AD CELLxGENE, Rexach, and Olah are explicitly not clean holdouts.", "Reusing development data as validation would overstate external generalization.", "Keep immutable dataset roles and seal clean holdouts until design freeze.", True, False),
    issue("S05_metadata_composition_proxy_risk", "v3", "split_and_leakage", "Metadata and fine cell-state composition produced large apparent gains that failed proxy-safe locking rules.", CONFIRMED, "results/tables/stage39h_proxy_leakage_decision_v1.csv", "proxy_leakage_decision", "Full reconstruction mean OOF Spearman=0.4934 but proxy_leakage_risk_pass=False; latent-only=0.3458 and passed.", "A model can predict disease-associated composition or metadata proxies instead of expression state.", "Exclude pathology-linked metadata from foundation training and retain proxy-only controls.", True, False),
    issue("S06_downstream_label_selection_damage", "v2", "split_and_leakage", "Pathology-supervised encoder tuning could optimize labels while degrading the self-supervised manifold.", CONFIRMED, "docs/current_status.md", "v2.2 Stage B and Fast Stage C Diagnostics", "Aggressive SupCon moved the encoder but collapsed global geometry; the frozen Stage B backbone retained decodable pathology signal.", "Selecting foundation checkpoints on pathology can destroy the emergent geometry and leak downstream objectives upstream.", "Use only self-supervised geometry and stability metrics for foundation checkpoint selection.", True, False),

    issue("R01_variance_regularizer_collapse_bug", "v2", "representation_learning", "Variance regularization was once applied after L2 normalization, making variance_gamma=1.0 unreachable in 128 dimensions.", CONFIRMED, "docs/current_status.md", "Important loss fix", "Moving the variance hinge to raw latents reduced the variance penalty from 0.9853 at epoch 1 to 0.4612 at epoch 5.", "The incorrect loss allowed collapse-like behavior despite an apparent anti-collapse term.", "Compute anti-collapse telemetry on raw latents and unit-test attainable targets.", True, False),
    issue("R02_narrow_disease_tube_geometry", "v1-v2", "representation_learning", "Disease fine-tuning could concentrate biological variation into a narrow latent tube.", CONFIRMED, "docs/architecture.md", "Stage C Losses and Telemetry", "The architecture explicitly introduced disease covariance, effective-dimension, and top-singular-ratio telemetry to detect narrow-tube collapse.", "Linear readouts may succeed while local state geometry remains poor.", "Gate v4 checkpoints on broad geometry, not downstream ridge performance alone.", True, False),
    issue("R03_low_effective_dimensionality", "v2", "representation_learning", "Early disease-stage configurations had low effective dimensionality relative to the selected foundation checkpoint.", CONFIRMED, "docs/current_status.md", "Stage C diagnostics and v2.2 Stage A checkpoint selection", "A Stage C configuration reported effective dimensions=4.76; selected Stage A epoch 30 reported 65.67.", "Low-dimensional latents can compress distinct microglial programs into one dominant axis.", "Track effective dimension on full datasets and set predeclared non-collapse gates.", True, True),
    issue("R04_top_singular_value_dominance", "v2", "representation_learning", "Some disease-stage embeddings were dominated by the leading singular direction.", CONFIRMED, "docs/current_status.md", "Stage C diagnostics and v2.2 Stage A checkpoint selection", "A Stage C configuration reported top singular ratio=0.481 versus 0.056 for selected Stage A epoch 30.", "A dominant axis can create visually compelling but biologically narrow geometry.", "Monitor singular spectrum on full train and validation donors before checkpoint selection.", True, True),
    issue("R05_ema_target_stability", "v1-v3", "representation_learning", "EMA target encoders are implemented, but a dedicated lineage-wide target-drift stability report was not found.", UNRESOLVED, "", "repository search: EMA target drift/stability", "EMA updates are implemented in src/sea_ad_jepa/graph_jepa.py; stability thresholds remain unspecified.", "An unstable target encoder can make JEPA loss misleading or seed-sensitive.", "Log context-target parameter drift, target variance, and EMA schedule in v4.", True, True),
    issue("R06_reference_manifold_drift", "v2", "representation_learning", "Reference drift was controlled but remained an explicit failure mode during calibration.", RESOLVED, "docs/architecture.md", "Stage A/B/C Curriculum", "Stage B drift audit: SEA-AD low-pathology cosine=0.9916 and CELLxGENE cosine=0.9754.", "Uncontrolled adaptation could overwrite the reference manifold.", "Retain anchor-drift telemetry where anchors are scientifically justified, without using pathology labels for selection.", False, False),
    issue("R07_checkpoint_telemetry_mismatch", "v2", "representation_learning", "Short-run telemetry did not reliably predict full-dataset geometry.", CONFIRMED, "docs/current_status.md", "Regression head smoke evaluator", "20-step effective dimensions=75.51, while full-dataset evaluation was 40.62 with top singular ratio=0.268.", "A checkpoint can appear safe during minibatch telemetry yet fail on the complete evaluation set.", "Require full-dataset self-supervised geometry audits before checkpoint acceptance.", True, False),
    issue("R08_seed_stability", "v1-v3", "representation_learning", "The stability of central representation conclusions across training seeds is not established by one current report.", UNRESOLVED, "", "repository search: repeated training seeds", "Several historical ablations explicitly report a single seed; no lineage-wide seed interval was found.", "Single-seed improvements may not reproduce.", "Predeclare multiple training seeds and report distributions for every v4 gate.", True, True),

    issue("G01_gene_identity_loss", "v2", "graph_modeling", "Scalar-only graph nodes risk forgetting which gene generated a message.", RESOLVED, "src/sea_ad_jepa/graph_jepa.py", "GraphGeneEncoder docstring and gene_embedding", "The encoder concatenates expression/node annotations with a learnable gene identity embedding.", "Without identity, message passing can reduce distinct genes to neighborhood averages.", "Retain explicit gene tokens/identity in v4A and every graph-aware extension.", True, False),
    issue("G02_oversmoothing", "v3", "graph_modeling", "Graph diffusion required a residual anti-oversmoothing experiment and still failed the full gate.", CONFIRMED, "docs/ACTIVE_V3_STATUS.md", "Stage 31 residual graph-control status", "Best weak residual graph=0.3264; full Stage31 pass=False; topology-specific utility not established.", "Message passing can erase expression-specific information without adding useful topology.", "Use soft adapters, residual paths, shallow propagation, and expression-only parent comparisons.", True, False),
    issue("G03_graph_failed_expression_only_reference", "v3", "graph_modeling", "The real graph did not beat the locked no-graph internal reference under mandatory controls.", CONFIRMED, "docs/ACTIVE_V3_STATUS.md", "Stage 30 graph-control status", "Real graph mean pooled OOF Spearman=0.3205; graph-specific pass=False; identity/no-graph remained best.", "A graph branch cannot be credited for representation value without beating expression-only.", "Make v4A the required parent and reject v4B gains that do not beat it under matched training.", True, False),
    issue("G04_real_graph_control_specificity", "v3", "graph_modeling", "Real topology did not consistently separate from all matched controls across later analyses.", CONFIRMED, "results/reports/stage79_control_interpretation_v1.json", "diagnostics", "The frozen interpretation reports 10 metric-invariant diagnostics and 38 zero-variance null comparisons.", "Apparent perturbation effects may reflect input arithmetic rather than regulatory topology.", "Require no-prior, zero-weight, TF-label, edge-shuffle, and matched-target controls.", True, False),
    issue("G05_small_internal_graph_gain", "v3", "graph_modeling", "The first guarded positive module-scale graph result was extremely small and internal only.", CONFIRMED, "docs/ACTIVE_V3_STATUS.md", "Stage 35E graph diagnostics synthesis status", "Stage35C=0.327265 versus Stage27C no-graph=0.326702, delta=0.000563.", "A technically positive gate does not imply meaningful biological utility.", "Report effect size and uncertainty and keep technical and biological pass criteria separate.", False, False),
    issue("G06_graph_lineage_separation", "v1-v3", "graph_modeling", "A machine-readable mapping that prevents unrelated historical graph priors from being mixed into v4 is not yet frozen.", UNRESOLVED, "", "repository search: graph lineage compatibility contract", "STRING, module, residual, perturbation, and Stage75 regulatory graphs have distinct roles.", "Combining incompatible priors can make controls uninterpretable.", "Version every graph source, transform, vocabulary, and allowed role before v4B.", True, True),
    issue("G07_generic_prior_context_gap", "v3", "graph_modeling", "A generic interaction prior did not establish context-specific microglial regulatory utility.", RISK, "results/reports/stage35d_perturbation_graph_diagnostic_report_v1.md", "feasibility audit conclusion", "No benchmark ran because no approved local perturbation-derived graph was available.", "Generic topology may not encode state-specific regulator-target behavior.", "Treat regulatory priors as soft masks/adapters and demand context-specific controls.", True, True),

    issue("E01_external_domain_compatibility", "v3", "external_pretraining", "The causal contribution of domain mismatch to the external-pretraining deficit remains unresolved.", UNRESOLVED, "", "repository search: quantitative domain equivalence", "External pretraining underperformed, but domain mismatch was not isolated as the cause.", "A failed transfer run cannot identify which domain axis caused failure.", "Audit tissue, assay, donor, cell state, and distribution shift before v4 pretraining.", True, True),
    issue("E02_external_cell_type_mismatch", "v3", "external_pretraining", "Filtering an external atlas to microglia/myeloid cells did not rescue transfer.", CONFIRMED, "results/reports/stage34a_hbca_microglia_filtered_external_pretraining_report_v1.md", "summary and cell-type filter audit", "10,325 filtered cells; best mean pooled OOF Spearman=0.2945; rescue pass=False.", "Broad-cell pretraining mismatch was not the only cause of the deficit.", "Use cell-state-aware sampling and compare matched and broad external pools.", False, False),
    issue("E03_external_gene_space_contract", "v3", "external_pretraining", "High overlap was reported, but exact ordered gene-space equivalence and missing-gene effects were not isolated.", UNRESOLVED, "", "repository search: ordered external gene-space equivalence", "Stage34A/34B report overlap fraction=0.9682, not complete equivalence.", "Small but important missing regulators can limit transfer and perturbation coverage.", "Freeze an ordered union/intersection policy and report biologically important missing genes.", True, True),
    issue("E04_external_normalization_equivalence", "v3", "external_pretraining", "Normalization mismatch was considered through benchmark transforms but not proven equivalent across sources.", UNRESOLVED, "", "repository search: cross-dataset normalization equivalence test", "Raw-count-like sources used size-factor log1p transforms; latent-scale equivalence remains unestablished.", "Scale artifacts can dominate cross-domain alignment.", "Fit transforms on training data and run per-source distribution and reconstruction checks.", True, True),
    issue("E05_external_pretraining_deficit", "v3", "external_pretraining", "Approved external pretraining conditions failed to beat the locked internal no-graph reference.", CONFIRMED, "docs/ACTIVE_V3_STATUS.md", "Stage 33B, 33C, 34A, and 34B status", "Best Stage33B=0.2711, Stage33C=0.3049, Stage34A=0.2945, Stage34B=0.2782 versus Stage27C=0.3267.", "More external data did not automatically produce a better SEA-AD representation.", "Require parent-baseline comparisons and diagnose transfer dimensions independently.", False, False),
    issue("E06_external_data_role_reuse", "v3", "external_pretraining", "Data used in training or development cannot later serve as clean validation.", CONFIRMED, "docs/DATASET_REGISTRY.md", "Role rules", "The registry explicitly forbids clean-validation status after training, architecture, threshold, filtering, or model-selection use.", "Role reuse would contaminate external validation claims.", "Maintain immutable dataset-role records and sealed holdout hashes.", True, False),

    issue("P01_arbitrary_model_input_magnitudes", "v3", "perturbation_analysis", "The frozen perturbation scenarios used model-input magnitudes 0.10 and 0.25 without biological dose semantics.", CONFIRMED, "results/tables/stage77_perturbation_scenario_manifest_v1.csv", "magnitude", "Twelve scenarios used up/down at 0.10 and 0.25 for STAT1, ELF1, and SPI1.", "Model-space magnitudes cannot be interpreted as percent expression, dose, or fold change.", "v4E must learn or anchor perturbation magnitude to measured perturbation data.", True, True),
    issue("P02_no_biological_dose_calibration", "v3", "perturbation_analysis", "No measured dose-response mapping calibrated the Stage77 perturbation inputs.", CONFIRMED, "docs/stage77_tier_a_perturbation_mvp.md", "claim boundaries", "The stage produced bounded expression deltas only and did not claim biological calibration.", "Scenario size has no direct biological effect-size interpretation.", "Require perturbation datasets with dose, time, and direction metadata before v4E claims.", True, True),
    issue("P03_one_hop_propagation", "v3", "perturbation_analysis", "The perturbation MVP propagated signed TF effects only through the frozen candidate TF-target edge set.", RISK, "docs/stage77_tier_a_perturbation_mvp.md", "bounded simulation design", "The model used 53 usable signed edges for three Tier A regulators.", "One-hop propagation omits feedback, indirect pathways, and temporal response.", "Define explicit controller dynamics and compare one-hop, multi-step, and no-propagation controls.", True, True),
    issue("P04_weak_directionality_evidence", "v3", "perturbation_analysis", "Desired TF direction remained unresolved for simulated regulators.", CONFIRMED, "results/tables/stage76_regulator_readiness_v1.csv", "unresolved_desired_perturbation_direction", "All ten regulator rows mark unresolved_desired_perturbation_direction=True.", "Up or down simulations cannot be framed as rescue directions.", "Keep both directions until independent state and perturbation evidence resolves sign.", True, True),
    issue("P05_missing_tf_target_features", "v3", "perturbation_analysis", "Feature-space omissions blocked two regulators and removed target edges.", CONFIRMED, "results/tables/stage76_regulator_readiness_v1.csv", "readiness_status and usable_signed_edges", "CEBPA and RELA were blocked; Tier A usable edges were 23, 14, and 16.", "The perturbation set was selected partly by model vocabulary.", "Audit regulatory coverage before v4 feature selection and never impute absent targets silently.", True, True),
    issue("P06_negligible_latent_displacement", "v3", "perturbation_analysis", "All frozen perturbation scenarios produced very small latent displacements.", CONFIRMED, "results/tables/stage78_jepa_latent_shift_summary_v1.csv", "mean_euclidean_displacement", "Across 0.25 scenarios, mean displacement ranged from 0.000193 to 0.000877; cosine similarity remained approximately 1.", "The v3 controller did not demonstrate meaningful state movement relative to natural geometry.", "Predeclare natural-distance-normalized effect gates before interpreting v4E perturbations.", True, True),
    issue("P07_graph_independent_effects", "v3", "perturbation_analysis", "Many graph-control comparisons were invariant or had zero-variance nulls.", CONFIRMED, "results/reports/stage79_control_interpretation_v1.json", "diagnostics and validation", "10 metric-invariant diagnostics and 38 zero-variance null comparisons were retained; no-graph p-values were null by design.", "A visible effect may not depend on the claimed regulatory graph.", "Require topology-specific control separation before any regulatory-controller claim.", True, False),
    issue("P08_geometric_overinterpretation", "v3", "perturbation_analysis", "Movement toward a latent centroid was explicitly not treated as rescue or benefit.", RESOLVED, "results/reports/stage78_jepa_latent_shift_v1.json", "claim_boundaries", "biological_rescue_claim, causal_validation_pass, and therapeutic_target_claim are false.", "Geometric proximity alone cannot establish biological improvement.", "Keep geometric, biological, causal, and therapeutic conclusions as separate gates.", False, False),

    issue("SP01_spatial_panel_coverage", "v4C", "spatial_modeling_risks", "No frozen audit establishes whether a targeted spatial panel covers the required v4 genes.", UNRESOLVED, "", "repository search: spatial panel feature coverage", "Spatial-panel modeling has not been implemented.", "Missing genes can make teacher-student alignment or regulatory interpretation underdetermined.", "Audit panel coverage and define missing-token behavior before v4C.", True, True),
    issue("SP02_spatial_cell_matching", "v4C", "spatial_modeling_risks", "No validated cross-modality cell matching procedure is present.", UNRESOLVED, "", "repository search: spatial cell matching validation", "No implemented matching artifact was found.", "Unsupported matching can transfer identities or states incorrectly.", "Use probabilistic matching with held-out checks and retain unmatched cells explicitly.", True, True),
    issue("SP03_coordinate_units", "v4C", "spatial_modeling_risks", "Coordinate units and scale are not yet frozen for any spatial source.", UNRESOLVED, "", "repository search: coordinate units", "No spatial coordinate contract was found.", "Distance thresholds are meaningless without physical units and slide transforms.", "Record units, transforms, orientation, and coordinate hashes per section.", True, True),
    issue("SP04_cross_section_edge_prevention", "v4C", "spatial_modeling_risks", "No implemented graph builder currently proves zero cross-section edges.", UNRESOLVED, "", "repository search: section-local spatial edge audit", "No spatial graph artifact was found.", "Cross-section edges would create impossible tissue neighborhoods and leakage.", "Assert section identity before neighbor search and fail on any cross-section edge.", True, False),
    issue("SP05_spatial_split_design", "v4C", "spatial_modeling_risks", "Section-level train, validation, and test assignment is not yet defined in an executable manifest.", UNRESOLVED, "", "repository search: spatial split manifest", "No spatial split artifact was found.", "Random-cell splitting would leak local morphology and neighborhood structure.", "Split by donor first and tissue section within the spatial policy.", True, True),
    issue("SP06_spatial_expression_scale", "v4C", "spatial_modeling_risks", "Equivalence between spatial-panel and full-transcriptome expression scales is untested.", UNRESOLVED, "", "repository search: panel/full-transcriptome scale audit", "No teacher-student scale calibration report was found.", "A modality shift could dominate the spatial latent branch.", "Use modality-aware normalization and held-out teacher-student reconstruction diagnostics.", True, True),
    issue("SP07_spatial_causal_wording", "v4C", "spatial_modeling_risks", "No evidence yet supports interpreting modeled spatial propagation as causal signaling.", UNRESOLVED, "", "repository search: spatial causal validation", "Spatial modeling is planned but not implemented or validated.", "Neighborhood association could be mislabeled as cell-cell communication.", "Freeze association-only wording until intervention or orthogonal causal evidence exists.", True, False),

    issue("N01_nondeterministic_artifacts", "v3", "engineering_and_provenance", "Generated artifacts required explicit deterministic serialization and byte-hash handling.", RESOLVED, "results/tables/project_git_provenance_index_v1.csv", "latest commit subjects for Stage79 visualization artifacts", "Tracked history includes deterministic gzip and visualization byte-hash corrections before the v4 launchpad.", "Byte instability breaks provenance even when scientific content is unchanged.", "Use sorted serialization, fixed gzip metadata, and byte-level repeat-run tests.", False, False),
    issue("N02_unmeasured_browser_runtime", "v3", "engineering_and_provenance", "The frozen Stage79 explorer did not claim an instrumented browser test when the tool was unavailable.", CONFIRMED, "results/visualization/stage79_graph_control_explorer_metadata_v3.json", "browser_smoke_execution_status", "browser_smoke_execution_status=not_run_tool_unavailable and runtime network request count is not asserted.", "Static generation success does not prove runtime interaction quality.", "Keep static and instrumented browser validation separate and record both honestly.", False, False),
    issue("N03_machine_specific_paths", "v3", "engineering_and_provenance", "Historical reports serialized machine-specific Windows paths before portability cleanup.", CONFIRMED, "results/reports/stage34a_hbca_microglia_filtered_external_pretraining_report_v1.md", "dataset manifest source_matrix", "The report contains a machine-specific Windows absolute source path.", "Machine paths make artifacts nonportable and can expose irrelevant local details.", "Serialize repository-relative logical paths and scan every compact output.", False, False),
    issue("N04_generated_html_and_gzip_stability", "v3", "engineering_and_provenance", "Large self-contained HTML and compressed payloads needed deterministic build and hash verification.", RESOLVED, "results/visualization/stage79_graph_control_explorer_metadata_v3.json", "html_hash and output hashes", "The frozen explorer records an HTML SHA-256 plus hashes for all embedded source artifacts.", "Unstable generated bytes obscure whether a scientific result changed.", "Pin bundled dependencies, stable ordering, fixed compression metadata, and source hashes.", False, False),
    issue("N05_code_output_provenance_mismatch", "v3", "engineering_and_provenance", "Implementation and artifact provenance required explicit commit and source-hash linkage.", RESOLVED, "results/reports/stage79_control_interpretation_v1.json", "implementation_git_commit, stage79_freeze_commit, and source_hashes", "The report records separate implementation/freeze commits and validates all source hashes.", "Outputs can otherwise outlive or mismatch the code that produced them.", "Retain separate implementation and freeze commits with source commit and hashes.", False, False),
    issue("N06_large_local_output_staging", "v3-v4", "engineering_and_provenance", "The repository explicitly protects raw data, checkpoints, run folders, logs, and unreviewed generated artifacts from commits.", RISK, "docs/v4/v4_start_checklist.md", "Do Not Commit", "The v4 checklist lists raw data, large resources, checkpoints, runs, logs, scratch bundles, and unreviewed artifacts as local-only.", "Accidental staging can bloat history or publish restricted data.", "Use ignored v4 namespaces, explicit staging paths, and staged-file review before every commit.", True, False),
]


def git_output(project: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(project), *args], text=True, encoding="utf-8").strip()


def stable_tree_status(project: Path) -> list[str]:
    ignored = set(OUTPUT_PATHS.values())
    lines = git_output(project, "status", "--short", "--untracked-files=all").splitlines()
    return sorted(line for line in lines if line[3:].replace("\\", "/") not in ignored)


def validate(project: Path, contract: dict[str, Any]) -> None:
    if len({row["failure_id"] for row in ISSUES}) != len(ISSUES):
        raise ValueError("failure_id values must be unique")
    for row in ISSUES:
        if set(row) != set(FIELDS):
            raise ValueError(f"schema mismatch for {row['failure_id']}")
        source = row["evidence_source_path"]
        if row["evidence_status"] == UNRESOLVED:
            if source:
                raise ValueError(f"unresolved item unexpectedly has source: {row['failure_id']}")
        elif not source or not (project / source).is_file():
            raise ValueError(f"evidence source missing for {row['failure_id']}: {source}")
    firewall = contract["pathology_firewall"]
    if not firewall["enabled"] or contract["foundation_training_mode"] != "self_supervised_pathology_label_free":
        raise ValueError("pathology firewall is not enabled")
    if contract["checkpoint_selection_policy"]["pathology_or_diagnosis_labels_allowed"]:
        raise ValueError("pathology labels cannot select foundation checkpoints")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(ISSUES, key=lambda row: row["failure_id"]))


def ensure_portable(paths: list[Path]) -> None:
    forbidden = [re.compile(r"[A-Za-z]:[/\\]"), re.compile(r"/mnt/[a-zA-Z]/"), re.compile(r"file://", re.I)]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern.search(text):
                raise ValueError(f"absolute or file URL leaked into {path}: {pattern.pattern}")


def build(project: Path, output_dir: Path | None = None) -> list[Path]:
    contract = yaml.safe_load((project / CONTRACT_PATH).read_text(encoding="utf-8"))
    validate(project, contract)
    source_commit = git_output(project, "rev-parse", "HEAD")
    output_dir = output_dir or project / "results/v4"
    actual_files = {
        "registry_json": output_dir / Path(OUTPUT_PATHS["registry_json"]).name,
        "registry_csv": output_dir / Path(OUTPUT_PATHS["registry_csv"]).name,
        "stage_report": output_dir / Path(OUTPUT_PATHS["stage_report"]).name,
    }
    unresolved = [row for row in ISSUES if row["evidence_status"] == UNRESOLVED]
    blocking = [row for row in ISSUES if row["blocking_for_v4"]]
    registry_payload = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": STAGE_ID,
        "source_commit": source_commit,
        "records": sorted(ISSUES, key=lambda row: row["failure_id"]),
    }
    report = {
        "stage_id": STAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "actual_input_paths": [str(CONTRACT_PATH).replace("\\", "/")]
        + sorted({row["evidence_source_path"] for row in ISSUES if row["evidence_source_path"]}),
        "actual_output_paths": list(OUTPUT_PATHS.values()),
        "source_commit": source_commit,
        "source_tree_status": stable_tree_status(project),
        "pathology_firewall": contract["pathology_firewall"],
        "model_sequence": contract["model_sequence"],
        "split_policy": contract["split_policy"],
        "checkpoint_selection_policy": contract["checkpoint_selection_policy"],
        "agent_boundary": contract["agent_boundary"],
        "protected_paths_observed": contract["protected_artifacts"],
        "documented_issue_count": len(ISSUES),
        "unresolved_issue_count": len(unresolved),
        "blocking_issue_count": len(blocking),
        "non_blocking_issue_count": len(ISSUES) - len(blocking),
        "blocking_issue_ids": [row["failure_id"] for row in blocking],
        "unresolved_issue_ids": [row["failure_id"] for row in unresolved],
        "stage81a0_pass": True,
        "scientific_wording": "This stage freezes a new self-supervised model-development contract. It does not establish improved biological representation, causal regulation, therapeutic validity, druggability, spatial interaction, or experimental validation.",
    }
    write_json(actual_files["registry_json"], registry_payload)
    write_csv(actual_files["registry_csv"])
    write_json(actual_files["stage_report"], report)
    paths = list(actual_files.values())
    ensure_portable(paths)
    for path in paths:
        print(f"Wrote: {path.relative_to(project) if path.is_relative_to(project) else path.name}")
    print(f"documented_issue_count={len(ISSUES)}")
    print(f"unresolved_issue_count={len(unresolved)}")
    print(f"blocking_issue_count={len(blocking)}")
    print("stage81a0_pass=True")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Stage81A0 v4 failure registry and compact report.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else None
    build(project, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
