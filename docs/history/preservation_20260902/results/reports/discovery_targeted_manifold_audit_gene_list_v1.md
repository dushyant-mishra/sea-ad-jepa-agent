# Discovery Targeted Manifold Audit Gene List v1

This is the bounded, pre-specified candidate list used for the targeted manifold audit. Audit results are reported separately in `results/reports/discovery_targeted_manifold_audit_v1.md`.

Graph-neighborhood evidence is carried only as penalty/context. No gene is selected because of positive 1-hop graph support, because no coherent cleaner neighborhood survived FDR.

## Group counts

- `top20_tier1`: 20
- `prior_anchor`: 11
- `broad_state_caution_control`: 9
- `special_review`: 12
- unique genes after deduplication: 45

## Candidate list

| gene | audit_priority | audit_groups | audit_selection_reason | final_tier | therapeutic_like_score_percentile | deprioritization_reason | graph_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UGCG | priority_1_top_tier1 | top20_tier1/special_review | top-20 Tier-1 therapeutic-like percentile; pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 99.626 | none | isolated_high_score_no_fdr_supported_neighborhood |
| SLC38A9 | priority_1_top_tier1 | top20_tier1/special_review | top-20 Tier-1 therapeutic-like percentile; pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 99.29 | none | isolated_high_score_no_fdr_supported_neighborhood |
| MDM2 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 99.253 | none | isolated_high_score_no_fdr_supported_neighborhood |
| SMARCA4 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 99.178 | none | isolated_high_score_no_fdr_supported_neighborhood |
| AP1G1 | priority_1_top_tier1 | top20_tier1/special_review | top-20 Tier-1 therapeutic-like percentile; pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 99.141 | none | isolated_high_score_no_fdr_supported_neighborhood |
| TLR2 | priority_1_top_tier1 | top20_tier1/prior_anchor | top-20 Tier-1 therapeutic-like percentile; pre-specified prior biological anchor | scorecard_supported_isolated_hypothesis | 99.103 | none | isolated_high_score_no_fdr_supported_neighborhood |
| NEMF | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 99.066 | none | isolated_high_score_no_fdr_supported_neighborhood |
| BAZ1A | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.879 | none | isolated_high_score_no_fdr_supported_neighborhood |
| GMDS | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.729 | none | isolated_high_score_no_fdr_supported_neighborhood |
| BTBD9 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.692 | none | isolated_high_score_no_fdr_supported_neighborhood |
| ARHGEF7 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.655 | none | isolated_high_score_no_fdr_supported_neighborhood |
| LRCH3 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.617 | none | isolated_high_score_no_fdr_supported_neighborhood |
| KIF1B | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.58 | none | isolated_high_score_no_fdr_supported_neighborhood |
| RAD51B | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.543 | none | isolated_high_score_no_fdr_supported_neighborhood |
| PI4KA | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.468 | none | isolated_high_score_no_fdr_supported_neighborhood |
| PTPRE | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.43 | none | isolated_high_score_no_fdr_supported_neighborhood |
| STARD13 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.393 | none | isolated_high_score_no_fdr_supported_neighborhood |
| SARAF | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.244 | none | isolated_high_score_no_fdr_supported_neighborhood |
| MSR1 | priority_1_top_tier1 | top20_tier1/special_review | top-20 Tier-1 therapeutic-like percentile; pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 98.206 | none | isolated_high_score_no_fdr_supported_neighborhood |
| NCOA2 | priority_1_top_tier1 | top20_tier1 | top-20 Tier-1 therapeutic-like percentile | scorecard_supported_isolated_hypothesis | 98.169 | none | isolated_high_score_no_fdr_supported_neighborhood |
| SLAIN2 | priority_2_special_review | special_review | pre-specified special-review gene | broad_state_caution | 100 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| GSK3B | priority_2_special_review | special_review | pre-specified special-review gene | unsupported_or_deprioritized | 99.888 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| FIP1L1 | priority_2_special_review | special_review | pre-specified special-review gene | broad_state_caution | 99.851 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| ERC1 | priority_2_special_review | special_review | pre-specified special-review gene | broad_state_caution | 99.664 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| KIF2A | priority_2_special_review | special_review | pre-specified special-review gene | broad_state_caution | 99.552 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| PTPN18 | priority_2_special_review | special_review | pre-specified special-review gene | unsupported_or_deprioritized | 98.804 | gliosis_penalty | isolated_high_score_no_fdr_supported_neighborhood |
| PLD3 | priority_2_special_review | special_review | pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 96.861 | none | isolated_high_score_no_fdr_supported_neighborhood |
| CD74 | priority_2_special_review | special_review | pre-specified special-review gene | scorecard_supported_isolated_hypothesis | 95.74 | none | isolated_high_score_no_fdr_supported_neighborhood |
| CD4 | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 89.91 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| CTSD | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 87.332 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| C3 | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 68.161 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| PLCG2 | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 65.658 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| C1QA | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 64.723 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| TREM2 | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 55.792 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| CSF1R | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 51.719 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| APOE | priority_2_prior_anchor | prior_anchor/broad_state_caution_control | pre-specified prior biological anchor; broad-state/gliosis/neuron-risk caution control | broad_state_caution | 51.196 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| TYROBP | priority_2_prior_anchor | prior_anchor | pre-specified prior biological anchor | biological_anchor_prior_candidate | 50.71 | prior_candidate_not_globally_enriched | no_supportive_one_hop_enrichment |
| APP | priority_2_prior_anchor | prior_anchor/broad_state_caution_control | pre-specified prior biological anchor; broad-state/gliosis/neuron-risk caution control | broad_state_caution | 1.2332 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| PAFAH1B1 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 99.963 | high_score_but_broad_shift_penalized | isolated_high_score_no_fdr_supported_neighborhood |
| RC3H1 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 6.3154 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| HECTD1 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 3.6996 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| SMG1 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 0.33632 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| DLG1 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 0.26158 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| POLK | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 0.14948 | broad_shift_penalty | no_supportive_one_hop_enrichment |
| HDAC8 | priority_3_caution_control | broad_state_caution_control | broad-state/gliosis/neuron-risk caution control | broad_state_caution | 0.074738 | neuron_risk_penalty | no_supportive_one_hop_enrichment |

## Required boundaries

- The full feature-wide graph-connected screen is the official pathology-delta ranking.
- The full run skipped nearest-neighbor manifold checking because of the Windows sklearn/threadpoolctl failure.
- The successful pilot supports feasibility and manifold safety for the pilot subset only.
- This candidate-list artifact defines the audit scope; it does not itself report targeted manifold-audit results.
- No current result proves causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.
