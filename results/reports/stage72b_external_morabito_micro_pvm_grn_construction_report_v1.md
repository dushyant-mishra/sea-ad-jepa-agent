# Stage72B external Morabito Micro-PVM candidate GRN construction

## Purpose

Stage72B builds a bounded, reproducible candidate regulatory coactivity graph
from the public GSE174367 microglia snRNA resource acquired in Stage72A. The
goal is to create a context-specific graph candidate for later Graph-JEPA
diagnostics without claiming validated regulation.

## Inputs and subset

| subset | n_microglia_cells_matched | n_samples | min_cells_per_sample | max_cells_per_sample |
| --- | --- | --- | --- | --- |
| GSE174367 snRNA microglia | 4126 | 18 | 141 | 372 |
| GSE174367 snATAC microglia | 12232 | 20 |  |  |

## Gene coverage

| gene_role | sum | count |
| --- | --- | --- |
| target | 42 | 42 |
| tf | 20 | 20 |
| tf_and_target | 2 | 2 |

## Edge construction

Edges were computed from sample-level microglia snRNA pseudobulk among
predeclared TF candidates and rare-tail target genes. Each candidate edge uses
Spearman coactivity across microglia samples plus bootstrap sign stability.

Passed candidate edges: 541

Top edge rows:

| source_tf | target_gene | edge_type | n_samples | spearman_rho | spearman_pvalue | bootstrap_median_rho | bootstrap_sd_rho | bootstrap_sign_stability | tf_mean_microglia_expressed_fraction | target_mean_microglia_expressed_fraction | atac_peak_support_status | motif_support_status | edge_candidate_pass | claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BACH1 | LAPTM5 | microglia_snrna_sample_coactivity | 18 | 0.913313 | 1.21822e-07 | 0.899791 | 0.0510019 | 1 | 0.718296 | 0.468564 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NRF1 | AP1G1 | microglia_snrna_sample_coactivity | 18 | 0.902993 | 2.89752e-07 | 0.90089 | 0.087943 | 1 | 0.419087 | 0.272449 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NFKB1 | FCER1G | microglia_snrna_sample_coactivity | 18 | 0.888545 | 8.39466e-07 | 0.870266 | 0.0605774 | 1 | 0.34772 | 0.132211 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| ELF1 | AP1G1 | microglia_snrna_sample_coactivity | 18 | 0.878225 | 1.64827e-06 | 0.88315 | 0.0888625 | 1 | 0.619348 | 0.272449 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| ELF1 | FCER1G | microglia_snrna_sample_coactivity | 18 | 0.874097 | 2.12313e-06 | 0.877745 | 0.0889129 | 1 | 0.619348 | 0.132211 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| ELF1 | APOE | microglia_snrna_sample_coactivity | 18 | 0.872033 | 2.40176e-06 | 0.871169 | 0.0780088 | 1 | 0.619348 | 0.344691 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| SPI1 | AP1G1 | microglia_snrna_sample_coactivity | 18 | 0.859649 | 4.828e-06 | 0.859377 | 0.102298 | 1 | 0.313258 | 0.272449 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| PPARG | FCER1G | microglia_snrna_sample_coactivity | 18 | 0.857585 | 5.38926e-06 | 0.828361 | 0.0784978 | 1 | 0.234489 | 0.132211 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NRF1 | PLD3 | microglia_snrna_sample_coactivity | 18 | 0.857585 | 5.38926e-06 | 0.854243 | 0.0872788 | 1 | 0.419087 | 0.209777 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NFKB1 | AP1G1 | microglia_snrna_sample_coactivity | 18 | 0.855521 | 6.00563e-06 | 0.848881 | 0.088913 | 1 | 0.34772 | 0.272449 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NRF1 | PSAP | microglia_snrna_sample_coactivity | 18 | 0.855521 | 6.00563e-06 | 0.840419 | 0.0959909 | 1 | 0.419087 | 0.506479 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| SPI1 | FCER1G | microglia_snrna_sample_coactivity | 18 | 0.853457 | 6.68154e-06 | 0.842133 | 0.0827672 | 1 | 0.313258 | 0.132211 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| STAT3 | AP1G1 | microglia_snrna_sample_coactivity | 18 | 0.853457 | 6.68154e-06 | 0.852391 | 0.086147 | 1 | 0.554014 | 0.272449 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| SPI1 | APOE | microglia_snrna_sample_coactivity | 18 | 0.851393 | 7.42169e-06 | 0.8375 | 0.0879902 | 1 | 0.313258 | 0.344691 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |
| NFKB1 | LAPTM5 | microglia_snrna_sample_coactivity | 18 | 0.851393 | 7.42169e-06 | 0.842717 | 0.0858495 | 1 | 0.34772 | 0.468564 | not_gene_mappable_from_processed_peak_matrix | not_available | True | candidate TF-target coactivity edge; not validated regulation |

## ATAC support audit

| resource | exists | n_peaks | n_cells | feature_format | n_first_1000_interval_like | n_first_1000_gene_like | gene_mappable_without_external_annotation | motif_annotation_available | usable_for_tf_peak_gene_edges_stage72b | limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSE174367_snATAC_peak_matrix | True | 219070 | 143401 | genomic_interval | 1000 | 0 | False | False | False | processed peak matrix contains genomic intervals but no bundled gene/motif annotation; use as resource availability only until a peak-to-gene/motif map is added |

The snATAC matrix is useful as an acquired multiomic resource, but its processed
feature names are genomic intervals. No bundled motif table or peak-to-gene map
was found, so Stage72B does not claim TF-peak-gene regulation.

## Readiness decision

- stage72b_run_pass: True
- candidate_graph_ready: True
- ready_for_stage73_graph_benchmark: True
- validated_tf_peak_gene_grn: False

## Claim boundary

Allowed language: candidate microglia TF-target coactivity graph; candidate
regulon-like prior for downstream diagnostics; requires motif/peak-to-gene
mapping and independent validation.

Disallowed language: validated GRN, causal regulator, therapeutic target,
gene-ablation result, clean external validation, or disease-modifying mechanism.
