# Discovery Scorecard v2 Negative Controls

## Executive Summary

- Null universe: 2,676 graph-connected feature genes.
- Random nulls per tested set: 1,000.
- Degree-matched nulls per tested set: 1,000.
- Degree matching uses graph-degree quantile bins and the nearest populated bin when an exact bin has no eligible decoy.

Interpretation counts:

- `too_few_genes`: 13
- `enriched_vs_degree_matched_null`: 6
- `not_enriched`: 2
- `broad_shift_confounded`: 1

## Evidence Tier 1: Strongest Set Tests

These comparisons are the most meaningful because the tested groups were nominated independently of the specific null draw.

### Prior Candidate Set

| test_set | null_type | n_genes | primary_metric | median_therapeutic_like_percentile | median_tau_lowering_percentile | median_neuron_preservation_percentile | median_gliosis_penalty_percentile | median_broad_shift_percentile | empirical_p_value | z_score_vs_null | FDR | evidence_tier | interpretation | comparison_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| prior_candidate_set | degree_matched | 24 | therapeutic_like | 49.645 | 83.371 | 54.185 | 71.954 | 77.41 | 0.55844 | -0.14038 | 0.64662 | strongest_independent_set_test | not_enriched |  |
| prior_candidate_set | high_degree_hub_control | 24 | therapeutic_like | 49.645 | 83.371 | 54.185 | 71.954 | 77.41 | 0.005994 | 3.0166 | 0.005994 | strongest_independent_set_test | not_enriched |  |
| prior_candidate_set | random | 24 | therapeutic_like | 49.645 | 83.371 | 54.185 | 71.954 | 77.41 | 0.51848 | -0.052543 | 0.60035 | strongest_independent_set_test | not_enriched |  |

The prior set is tested against random, degree-matched, and high-degree hub controls. Degree matching is the primary graph-aware comparator; hub-control enrichment alone does not override failure against random and degree-matched backgrounds.

### Cleaner Therapeutic-Like Classes Versus Broad-Reactive Reference

| test_set | null_type | n_genes | primary_metric | median_therapeutic_like_percentile | median_tau_lowering_percentile | median_neuron_preservation_percentile | median_gliosis_penalty_percentile | median_broad_shift_percentile | empirical_p_value | z_score_vs_null | FDR | evidence_tier | interpretation | comparison_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cleaner_therapeutic_like_classes | broad_reactive_reference | 99 | therapeutic_like | 96.45 | 94.806 | 82.922 | 39.537 | 78.662 | 0.000999 | 141.62 | 0.000999 | strongest_direct_cleaner_vs_broad_test | enriched_vs_degree_matched_null | cleaner_than_broad_reference |

The `comparison_interpretation` field is the direct gate: `cleaner_than_broad_reference` or `not_cleaner_than_broad_reference`.

## Evidence Tier 2: Class Calibration

| test_set | null_type | n_genes | primary_metric | median_therapeutic_like_percentile | median_tau_lowering_percentile | median_neuron_preservation_percentile | median_gliosis_penalty_percentile | median_broad_shift_percentile | empirical_p_value | z_score_vs_null | FDR | evidence_tier | interpretation | comparison_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| class::amyloid_lowering_candidate | degree_matched | 153 | amyloid_lowering | 82.324 | 83.969 | 62.892 | 33.819 | 78.849 | 0.000999 | 11.962 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::amyloid_lowering_candidate | random | 153 | amyloid_lowering | 82.324 | 83.969 | 62.892 | 33.819 | 78.849 | 0.000999 | 11.388 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::broad_reactive_state_shift | degree_matched | 80 | broad_shift | 3.2698 | 12.818 | 91.966 | 97.739 | 97.646 | 0.000999 | 6.1952 | 0.002442 | calibration_not_independent_validation | broad_shift_confounded |  |
| class::broad_reactive_state_shift | random | 80 | broad_shift | 3.2698 | 12.818 | 91.966 | 97.739 | 97.646 | 0.000999 | 9.2078 | 0.002442 | calibration_not_independent_validation | broad_shift_confounded |  |
| class::dual_pathology_lowering_neuron_preserving | degree_matched | 41 | therapeutic_like | 97.235 | 95.628 | 85.164 | 45.067 | 87.444 | 0.000999 | 6.3377 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::dual_pathology_lowering_neuron_preserving | random | 41 | therapeutic_like | 97.235 | 95.628 | 85.164 | 45.067 | 87.444 | 0.000999 | 6.2086 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::gliosis_inflating | degree_matched | 152 | gliosis_penalty | 8.8378 | 31.857 | 65.527 | 93.629 | 85.65 | 0.000999 | 9.9248 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::gliosis_inflating | random | 152 | gliosis_penalty | 8.8378 | 31.857 | 65.527 | 93.629 | 85.65 | 0.000999 | 11.274 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::mixed_or_unclear | degree_matched | 1925 | therapeutic_like | 54.522 | 47.048 | 50.934 | 44.993 | 37.818 | 0.000999 | 14.65 | 0.002442 | calibration_not_independent_validation | not_enriched |  |
| class::mixed_or_unclear | random | 1925 | therapeutic_like | 54.522 | 47.048 | 50.934 | 44.993 | 37.818 | 0.000999 | 7.5388 | 0.002442 | calibration_not_independent_validation | not_enriched |  |
| class::neuron_risk | degree_matched | 267 | neuron_preservation | 19.507 | 43.61 | 5.0075 | 61.659 | 67.9 | 0.000999 | -19.124 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::neuron_risk | random | 267 | neuron_preservation | 19.507 | 43.61 | 5.0075 | 61.659 | 67.9 | 0.000999 | -15.942 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::tau_lowering_neuron_preserving | degree_matched | 58 | therapeutic_like | 95.516 | 94.226 | 77.672 | 26.345 | 71.655 | 0.000999 | 7.4836 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |
| class::tau_lowering_neuron_preserving | random | 58 | therapeutic_like | 95.516 | 94.226 | 77.672 | 26.345 | 71.655 | 0.000999 | 7.0938 | 0.002442 | calibration_not_independent_validation | enriched_vs_degree_matched_null |  |

Class-level tests are calibration checks, not independent validation: the classes were defined from these same scorecard percentiles. Enrichment of a class on its defining metric is expected and only confirms that the classification rules partitioned the feature-wide universe as designed.

## Supporting Cleaner and Broad Null Context

| test_set | null_type | n_genes | primary_metric | median_therapeutic_like_percentile | median_tau_lowering_percentile | median_neuron_preservation_percentile | median_gliosis_penalty_percentile | median_broad_shift_percentile | empirical_p_value | z_score_vs_null | FDR | evidence_tier | interpretation | comparison_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| class::broad_reactive_state_shift | degree_matched | 80 | broad_shift | 3.2698 | 12.818 | 91.966 | 97.739 | 97.646 | 0.000999 | 6.1952 | 0.002442 | calibration_not_independent_validation | broad_shift_confounded |  |
| class::broad_reactive_state_shift | random | 80 | broad_shift | 3.2698 | 12.818 | 91.966 | 97.739 | 97.646 | 0.000999 | 9.2078 | 0.002442 | calibration_not_independent_validation | broad_shift_confounded |  |
| cleaner_therapeutic_like_classes | broad_reactive_reference | 99 | therapeutic_like | 96.45 | 94.806 | 82.922 | 39.537 | 78.662 | 0.000999 | 141.62 | 0.000999 | strongest_direct_cleaner_vs_broad_test | enriched_vs_degree_matched_null | cleaner_than_broad_reference |
| cleaner_therapeutic_like_classes | degree_matched | 99 | therapeutic_like | 96.45 | 94.806 | 82.922 | 39.537 | 78.662 | 0.000999 | 10.716 | 0.002442 | supporting_null_context | enriched_vs_degree_matched_null |  |
| cleaner_therapeutic_like_classes | random | 99 | therapeutic_like | 96.45 | 94.806 | 82.922 | 39.537 | 78.662 | 0.000999 | 9.9537 | 0.002442 | supporting_null_context | enriched_vs_degree_matched_null |  |

The `broad_reactive_reference` row compares the cleaner class union directly with bootstrap samples from broad-reactive genes.

## Evidence Tier 3: Named-Gene Descriptive Context

| test_set | null_type | n_genes | primary_metric | median_therapeutic_like_percentile | median_tau_lowering_percentile | median_neuron_preservation_percentile | median_gliosis_penalty_percentile | median_broad_shift_percentile | empirical_p_value | z_score_vs_null | FDR | evidence_tier | interpretation | comparison_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| named_gene::APOE | degree_matched | 1 | therapeutic_like | 51.196 | 98.468 | 56.652 | 90.172 | 96.151 | 0.48651 | 0.068964 | 0.59463 | descriptive_singleton_context | too_few_genes |  |
| named_gene::APOE | random | 1 | therapeutic_like | 51.196 | 98.468 | 56.652 | 90.172 | 96.151 | 0.49251 | 0.026445 | 0.60035 | descriptive_singleton_context | too_few_genes |  |
| named_gene::APP | degree_matched | 1 | therapeutic_like | 1.2332 | 98.393 | 94.955 | 99.103 | 98.43 | 0.996 | -1.6743 | 0.996 | descriptive_singleton_context | too_few_genes |  |
| named_gene::APP | random | 1 | therapeutic_like | 1.2332 | 98.393 | 94.955 | 99.103 | 98.43 | 0.99301 | -1.7098 | 0.999 | descriptive_singleton_context | too_few_genes |  |
| named_gene::CD4 | degree_matched | 1 | therapeutic_like | 89.91 | 97.384 | 89.836 | 78.139 | 92.265 | 0.086913 | 1.4576 | 0.11248 | descriptive_singleton_context | too_few_genes |  |
| named_gene::CD4 | random | 1 | therapeutic_like | 89.91 | 97.384 | 89.836 | 78.139 | 92.265 | 0.11289 | 1.3714 | 0.14609 | descriptive_singleton_context | too_few_genes |  |
| named_gene::DLG1 | degree_matched | 1 | therapeutic_like | 0.26158 | 99.888 | 99.552 | 99.888 | 99.776 | 0.97502 | -1.0177 | 0.996 | descriptive_singleton_context | too_few_genes |  |
| named_gene::DLG1 | random | 1 | therapeutic_like | 0.26158 | 99.888 | 99.552 | 99.888 | 99.776 | 0.999 | -1.736 | 0.999 | descriptive_singleton_context | too_few_genes |  |
| named_gene::ERC1 | degree_matched | 1 | therapeutic_like | 99.664 | 99.589 | 81.689 | 14.836 | 98.916 | 0.014985 | 1.8995 | 0.021978 | descriptive_singleton_context | too_few_genes |  |
| named_gene::ERC1 | random | 1 | therapeutic_like | 99.664 | 99.589 | 81.689 | 14.836 | 98.916 | 0.004995 | 1.7271 | 0.0078493 | descriptive_singleton_context | too_few_genes |  |
| named_gene::FIP1L1 | degree_matched | 1 | therapeutic_like | 99.851 | 99.626 | 98.468 | 67.825 | 97.16 | 0.004995 | 2.0731 | 0.010989 | descriptive_singleton_context | too_few_genes |  |
| named_gene::FIP1L1 | random | 1 | therapeutic_like | 99.851 | 99.626 | 98.468 | 67.825 | 97.16 | 0.004995 | 1.7699 | 0.0078493 | descriptive_singleton_context | too_few_genes |  |
| named_gene::GSK3B | degree_matched | 1 | therapeutic_like | 99.888 | 97.758 | 99.253 | 14.836 | 92.489 | 0.00999 | 2.0088 | 0.015699 | descriptive_singleton_context | too_few_genes |  |
| named_gene::GSK3B | random | 1 | therapeutic_like | 99.888 | 97.758 | 99.253 | 14.836 | 92.489 | 0.001998 | 1.7698 | 0.0043956 | descriptive_singleton_context | too_few_genes |  |
| named_gene::KIF2A | degree_matched | 1 | therapeutic_like | 99.552 | 99.253 | 96.413 | 59.641 | 96.749 | 0.025974 | 1.9338 | 0.035714 | descriptive_singleton_context | too_few_genes |  |
| named_gene::KIF2A | random | 1 | therapeutic_like | 99.552 | 99.253 | 96.413 | 59.641 | 96.749 | 0.004995 | 1.7386 | 0.0078493 | descriptive_singleton_context | too_few_genes |  |
| named_gene::PAFAH1B1 | degree_matched | 1 | therapeutic_like | 99.963 | 99.963 | 99.738 | 99.701 | 99.851 | 0.008991 | 1.914 | 0.015216 | descriptive_singleton_context | too_few_genes |  |
| named_gene::PAFAH1B1 | random | 1 | therapeutic_like | 99.963 | 99.963 | 99.738 | 99.701 | 99.851 | 0.002997 | 1.6929 | 0.005994 | descriptive_singleton_context | too_few_genes |  |
| named_gene::PTPN18 | degree_matched | 1 | therapeutic_like | 98.804 | 99.29 | 83.371 | 66.031 | 88.378 | 0.005994 | 1.6284 | 0.010989 | descriptive_singleton_context | too_few_genes |  |
| named_gene::PTPN18 | random | 1 | therapeutic_like | 98.804 | 99.29 | 83.371 | 66.031 | 88.378 | 0.013986 | 1.7004 | 0.019231 | descriptive_singleton_context | too_few_genes |  |
| named_gene::RC3H1 | degree_matched | 1 | therapeutic_like | 6.3154 | 100 | 99.925 | 99.963 | 100 | 0.76324 | -0.86861 | 0.83956 | descriptive_singleton_context | too_few_genes |  |
| named_gene::RC3H1 | random | 1 | therapeutic_like | 6.3154 | 100 | 99.925 | 99.963 | 100 | 0.93606 | -1.4771 | 0.999 | descriptive_singleton_context | too_few_genes |  |
| named_gene::SLAIN2 | degree_matched | 1 | therapeutic_like | 100 | 99.439 | 99.29 | 48.132 | 97.982 | 0.000999 | 2.0433 | 0.002442 | descriptive_singleton_context | too_few_genes |  |
| named_gene::SLAIN2 | random | 1 | therapeutic_like | 100 | 99.439 | 99.29 | 48.132 | 97.982 | 0.000999 | 1.6857 | 0.002442 | descriptive_singleton_context | too_few_genes |  |
| named_gene::TLR2 | degree_matched | 1 | therapeutic_like | 99.103 | 97.123 | 96.525 | 47.235 | 73.244 | 0.005994 | 1.7889 | 0.010989 | descriptive_singleton_context | too_few_genes |  |
| named_gene::TLR2 | random | 1 | therapeutic_like | 99.103 | 97.123 | 96.525 | 47.235 | 73.244 | 0.005994 | 1.7093 | 0.0087912 | descriptive_singleton_context | too_few_genes |  |

Singleton named-gene tests are labeled `too_few_genes`; their empirical context is descriptive and should not be treated as set enrichment.

## Degree-Matching Diagnostics

- Degree-null iterations with nearest-bin fallback: 0 / 22,000.
- Tested sets with at least one fallback gene: 0.

Nearest-bin fallback is recorded explicitly in `discovery_scorecard_v2_degree_matched_nulls.csv`. Unmatched genes cause `not_testable`; nearest-bin fallback alone does not.

## Boundary

The negative controls test whether scorecard-v2 candidate groups are enriched relative to the graph-connected feature-wide universe. They do not prove causality or experimental validity. The full feature-wide run used skipped nearest-neighbor manifold checking, so manifold safety remains supported by the successful pilot and any future targeted top-hit audits.

Biological conclusions are intentionally unchanged. The next step is scorecard-v2 interpretation and targeted top-hit manifold audit.
