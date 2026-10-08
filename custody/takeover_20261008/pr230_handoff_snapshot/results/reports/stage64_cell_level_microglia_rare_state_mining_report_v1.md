# Stage64 cell-level microglia rare-state mining

## Bottom line

Stage64 reframes the problem from donor-average prediction to rare/high-tail Micro-PVM disease-program mining. It uses pathology-blind frozen module scores and thresholds, then tests donor-level pathology associations after feature construction. Outputs are hypothesis-generating and intended for Stage65 external support.

## Dataset schema

| dataset | path | n_cells | n_genes | donor_col | state_col | n_donors | n_states |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MTG | C:\Users\dushy\Desktop\Jepa project\data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad | 40000 | 2977 | Donor ID | Supertype | 89 | 8 |
| DLPFC | C:\Users\dushy\Desktop\Jepa project\data\sea_ad\stage45\cellxgene\h5ad_assets\100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad | 42486 | 35483 | donor_id | Supertype | 83 | 6 |

## Gene availability

| dataset | module | requested_genes | present_genes | missing_genes | n_present | usable |
| --- | --- | --- | --- | --- | --- | --- |
| MTG | dam_lipid_trem2_apoe | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD |  | 8 | True |
| MTG | lysosomal_endolysosomal | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;PSAP | GBA | 7 | True |
| MTG | complement_phagocytosis | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 | C1QA;C1QB;C1QC;TYROBP;CTSS | FCER1G;AIF1 | 5 | True |
| MTG | antigen_presentation | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M |  | 6 | True |
| MTG | interferon_inflammatory | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG | NFKBIA;IRF8;STAT1;IL27RA;SLC6A12;BSG | IFITM3 | 6 | True |
| MTG | oxidative_stress_gene_preserved | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP | SOD2;TXNIP | HMOX1;NQO1;SOD1;GPX4;PRDX1 | 2 | True |
| DLPFC | dam_lipid_trem2_apoe | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD | APOE;TREM2;LPL;APOC1;TYROBP;CST7;LGALS3;CTSD |  | 8 | True |
| DLPFC | lysosomal_endolysosomal | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;GBA;PSAP | CTSD;CTSB;LAPTM5;NPC2;LAMP2;CTSS;PSAP | GBA | 7 | True |
| DLPFC | complement_phagocytosis | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 | C1QA;C1QB;C1QC;TYROBP;FCER1G;CTSS;AIF1 |  | 7 | True |
| DLPFC | antigen_presentation | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M | CD74;HLA-DRA;HLA-DRB1;HLA-DPA1;HLA-DPB1;B2M |  | 6 | True |
| DLPFC | interferon_inflammatory | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG | NFKBIA;IRF8;STAT1;IFITM3;IL27RA;SLC6A12;BSG |  | 7 | True |
| DLPFC | oxidative_stress_gene_preserved | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP | HMOX1;NQO1;SOD2;SOD1;GPX4;PRDX1;TXNIP |  | 7 | True |

## Strongest mean/tail target associations

| dataset | feature | metric | target | spearman | n_donors |
| --- | --- | --- | --- | --- | --- |
| DLPFC | lysosomal_endolysosomal | variance | NeuN | -0.5109704641350211 | 80 |
| MTG | lysosomal_endolysosomal | variance | NeuN | -0.4892173736964666 | 84 |
| MTG | disease_program_score | variance | NeuN | -0.4713576997063887 | 84 |
| MTG | dam_lipid_trem2_apoe | top_10pct_mean | AT8 | 0.4612129189025008 | 84 |
| MTG | dam_lipid_trem2_apoe | top_5pct_mean | AT8 | 0.458681785967399 | 84 |
| MTG | oxidative_stress_gene_preserved | q90 | NeuN | -0.4575883365394351 | 84 |
| MTG | dam_lipid_trem2_apoe | q90 | AT8 | 0.45343727852586824 | 84 |
| MTG | dam_lipid_trem2_apoe | fraction_high_global_q95 | AT8 | 0.45308196996167466 | 84 |
| MTG | dam_lipid_trem2_apoe | q95 | AT8 | 0.44790928419560594 | 84 |
| MTG | oxidative_stress_gene_preserved | mean | NeuN | -0.4464108534980257 | 84 |
| MTG | dam_lipid_trem2_apoe | mean | AT8 | 0.4441429583881745 | 84 |
| MTG | interferon_inflammatory | fraction_high_global_q95 | AT8 | 0.4409031082312444 | 84 |
| MTG | lysosomal_endolysosomal | q90 | 6e10/A_beta | 0.4366305558367926 | 84 |
| MTG | complement_phagocytosis | variance | GFAP | 0.4346461476156727 | 84 |
| DLPFC | lysosomal_endolysosomal | top_1pct_mean | AT8 | 0.4338490389123301 | 80 |

## MTG/DLPFC signature overlap

| feature | target | datasets_tested | n_datasets | same_direction_across_datasets | max_abs_tail_spearman | mean_tail_beats_mean_delta |
| --- | --- | --- | --- | --- | --- | --- |
| dam_lipid_trem2_apoe | AT8 | DLPFC;MTG | 2 | True | 0.458681785967399 | 0.08694592574460522 |
| interferon_inflammatory | AT8 | DLPFC;MTG | 2 | True | 0.4409031082312444 | 0.0024316319990453916 |
| lysosomal_endolysosomal | AT8 | DLPFC;MTG | 2 | True | 0.4338490389123301 | 0.14922515401053127 |
| lysosomal_endolysosomal | NeuN | DLPFC;MTG | 2 | True | 0.42810595405532115 | 0.12796148130680599 |
| lysosomal_endolysosomal | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.42490849908663864 | 0.1369668955011653 |
| lysosomal_endolysosomal | GFAP | DLPFC;MTG | 2 | True | 0.4174951908474233 | 0.07094058964646303 |
| disease_program_score | NeuN | DLPFC;MTG | 2 | True | 0.4044952920927407 | 0.23814080204803184 |
| dam_lipid_trem2_apoe | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.4016401741419459 | 0.04076693256734343 |
| disease_program_score | AT8 | DLPFC;MTG | 2 | True | 0.4014376835071378 | 0.113308533214516 |
| disease_program_score | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.3879720562923965 | 0.05359114601392728 |
| disease_program_score | GFAP | DLPFC;MTG | 2 | True | 0.38063847082570673 | 0.09357592774969355 |
| lysosomal_endolysosomal | Iba1 | DLPFC;MTG | 2 | True | 0.36898734177215187 | 0.02604920859435561 |
| dam_lipid_trem2_apoe | GFAP | DLPFC;MTG | 2 | True | 0.3673585096689278 | 0.0926339296839167 |
| oxidative_stress_gene_preserved | AT8 | DLPFC;MTG | 2 | True | 0.3648513197647743 | -0.03737616320734559 |
| complement_phagocytosis | GFAP | DLPFC;MTG | 2 | True | 0.3563025210084033 | 0.08019651796800596 |
| oxidative_stress_gene_preserved | Iba1 | DLPFC;MTG | 2 | True | 0.3418424753867792 | -0.01566110325244882 |
| oxidative_stress_gene_preserved | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.32538549546565426 | -0.016869849000238538 |
| interferon_inflammatory | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.3141237217778678 | 0.027900548998343017 |
| complement_phagocytosis | 6e10/A_beta | DLPFC;MTG | 2 | True | 0.30887921433633697 | 0.01245048152282452 |
| oxidative_stress_gene_preserved | GFAP | DLPFC;MTG | 2 | True | 0.3064493267186393 | 0.02284501145619483 |
| interferon_inflammatory | GFAP | DLPFC;MTG | 2 | True | 0.3011238230231852 | -0.00021151632496491102 |
| oxidative_stress_gene_preserved | NeuN | DLPFC;MTG | 2 | True | 0.28549154601599674 | -0.10087690643674817 |
| dam_lipid_trem2_apoe | NeuN | DLPFC;MTG | 2 | True | 0.27641819034224097 | 0.14998247430739872 |
| interferon_inflammatory | Iba1 | DLPFC;MTG | 2 | True | 0.26322081575246137 | -0.007898798446394635 |
| dam_lipid_trem2_apoe | Iba1 | DLPFC;MTG | 2 | True | 0.2527894983591186 | -0.0004724235618026873 |

_Showing 25 of 35 rows._

## External handoff

| signature_type | signature_name | target_context | evidence_summary | handoff_status | allowed_claim | recommended_next_stage | disallowed_claim |
| --- | --- | --- | --- | --- | --- | --- | --- |
| module_tail_or_composite | dam_lipid_trem2_apoe | AT8 | max_abs_tail_spearman=0.459; tail_minus_mean=0.087; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | interferon_inflammatory | AT8 | max_abs_tail_spearman=0.441; tail_minus_mean=0.002; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | lysosomal_endolysosomal | AT8 | max_abs_tail_spearman=0.434; tail_minus_mean=0.149; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | lysosomal_endolysosomal | NeuN | max_abs_tail_spearman=0.428; tail_minus_mean=0.128; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | lysosomal_endolysosomal | 6e10/A_beta | max_abs_tail_spearman=0.425; tail_minus_mean=0.137; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | lysosomal_endolysosomal | GFAP | max_abs_tail_spearman=0.417; tail_minus_mean=0.071; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | disease_program_score | NeuN | max_abs_tail_spearman=0.404; tail_minus_mean=0.238; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | dam_lipid_trem2_apoe | 6e10/A_beta | max_abs_tail_spearman=0.402; tail_minus_mean=0.041; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | disease_program_score | AT8 | max_abs_tail_spearman=0.401; tail_minus_mean=0.113; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | disease_program_score | 6e10/A_beta | max_abs_tail_spearman=0.388; tail_minus_mean=0.054; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | disease_program_score | GFAP | max_abs_tail_spearman=0.381; tail_minus_mean=0.094; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | lysosomal_endolysosomal | Iba1 | max_abs_tail_spearman=0.369; tail_minus_mean=0.026; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | dam_lipid_trem2_apoe | GFAP | max_abs_tail_spearman=0.367; tail_minus_mean=0.093; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | oxidative_stress_gene_preserved | AT8 | max_abs_tail_spearman=0.365; tail_minus_mean=-0.037; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | complement_phagocytosis | GFAP | max_abs_tail_spearman=0.356; tail_minus_mean=0.080; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | oxidative_stress_gene_preserved | Iba1 | max_abs_tail_spearman=0.342; tail_minus_mean=-0.016; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | oxidative_stress_gene_preserved | 6e10/A_beta | max_abs_tail_spearman=0.325; tail_minus_mean=-0.017; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | interferon_inflammatory | 6e10/A_beta | max_abs_tail_spearman=0.314; tail_minus_mean=0.028; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | complement_phagocytosis | 6e10/A_beta | max_abs_tail_spearman=0.309; tail_minus_mean=0.012; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | oxidative_stress_gene_preserved | GFAP | max_abs_tail_spearman=0.306; tail_minus_mean=0.023; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | interferon_inflammatory | GFAP | max_abs_tail_spearman=0.301; tail_minus_mean=-0.000; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | oxidative_stress_gene_preserved | NeuN | max_abs_tail_spearman=0.285; tail_minus_mean=-0.101; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | dam_lipid_trem2_apoe | NeuN | max_abs_tail_spearman=0.276; tail_minus_mean=0.150; same_direction=True | candidate_for_external_support | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | interferon_inflammatory | Iba1 | max_abs_tail_spearman=0.263; tail_minus_mean=-0.008; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |
| module_tail_or_composite | dam_lipid_trem2_apoe | Iba1 | max_abs_tail_spearman=0.253; tail_minus_mean=-0.000; same_direction=True | manual_review_required | hypothesis-generating rare/high-tail microglia signature | Stage65_external_rare_microglia_signature_support_v1 | validated biomarker; causal mechanism; therapeutic target; clean external validation completed |

_Showing 25 of 60 rows._
