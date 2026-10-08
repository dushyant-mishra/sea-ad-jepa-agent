# Stage68 rare-tail cell extraction and expression contrast

## Bottom line

Stage68 joins the frozen Stage64 rare/high-tail scoring definitions back to the local SEA-AD MTG and DLPFC H5AD expression rows. Because the Stage64 cell table is a capped top-cell export, Stage68 recomputes the same frozen module scores over the full local H5ADs before selecting q95 high-tail and q50 low-reference cells. It then compares high-tail cells with low-reference cells within donor. This is a diagnostic expression/state contrast, not a new model, benchmark, external validation, causal claim, therapeutic claim, validated biomarker, or new microglia subtype.

## Join audit

| dataset | path | exists | x_shape | n_genes | donor_column | state_column | stage64_dataset_present | stage64_export_rows | stage64_row_index_compatible | full_h5ad_cells_scored_for_stage68 | requested_genes | present_requested_genes | missing_requested_genes | missing_genes_sample |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MTG | C:\Users\dushy\Desktop\Jepa project\data\processed\sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad | True | (40000, 2977) | 2977 | Donor ID | Supertype | True | 5000 | True | 40000 | 57 | 48 | 9 | GBA;FCER1G;AIF1;IFITM3;HMOX1;NQO1;SOD1;GPX4;PRDX1 |
| DLPFC | C:\Users\dushy\Desktop\Jepa project\data\sea_ad\stage45\cellxgene\h5ad_assets\100c6145-7b0e-4ba6-81c1-ffebed0d1ac4.h5ad | True | (42486, 35483) | 35483 | donor_id | Supertype | True | 5000 | True | 42486 | 57 | 56 | 1 | GBA |

## Rare-cell selection summary

| dataset | n_cells_scored_full_h5ad | high_tail_threshold | low_reference_threshold | n_high_tail_cells | n_low_reference_cells | n_donors | n_high_tail_donors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DLPFC | 42486 | 1.3129036476682465 | -0.07733010387095274 | 2125 | 21243 | 83 | 81 |
| MTG | 40000 | 1.144890521198029 | -0.01229429577441319 | 2000 | 20000 | 89 | 81 |

## Top high-tail expression contrasts

| dataset | gene | mean_high_minus_low | median_high_minus_low | mean_log1p_high_minus_low | n_donors | total_high_cells | total_low_cells | median_rank_sum_p | bh_q_median_p_within_dataset | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DLPFC | APOE | 2.2697402222515786 | 2.2968368530273438 | 0.9036681154002882 | 73 | 2117 | 17985 | 3.984358973442875e-08 | 1.7834346743119745e-06 | higher_in_high_tail |
| DLPFC | C1QC | 1.5932018177150047 | 1.6581751108169556 | 0.7453054553025389 | 73 | 2117 | 17985 | 6.369409551114194e-08 | 1.7834346743119745e-06 | higher_in_high_tail |
| DLPFC | B2M | 1.5771457258969137 | 1.6365962028503418 | 0.6660193568223143 | 73 | 2117 | 17985 | 7.060878479454356e-07 | 6.590153247490732e-06 | higher_in_high_tail |
| DLPFC | C1QB | 1.495737664911845 | 1.557098388671875 | 0.6422788541610926 | 73 | 2117 | 17985 | 1.0698832101238953e-07 | 1.9971153255646045e-06 | higher_in_high_tail |
| DLPFC | CD74 | 1.475834951825338 | 1.4878032207489014 | 0.5665873570801461 | 73 | 2117 | 17985 | 6.249330593279787e-07 | 6.590153247490732e-06 | higher_in_high_tail |
| DLPFC | HLA-DRA | 1.4456616921784127 | 1.4958988428115845 | 0.7106868051094551 | 73 | 2117 | 17985 | 2.803749399475537e-07 | 3.925249159265752e-06 | higher_in_high_tail |
| MTG | APOE | 1.3390667469073565 | 1.364324927330017 | 0.5927115969168835 | 78 | 1994 | 17762 | 2.719596015967374e-08 | 1.3054060876643394e-06 | higher_in_high_tail |
| DLPFC | HLA-DRB1 | 1.308822846575959 | 1.3394088745117188 | 0.6536181846710101 | 73 | 2117 | 17985 | 6.6776831348486445e-06 | 4.674378194394051e-05 | higher_in_high_tail |
| DLPFC | C1QA | 1.262109398841858 | 1.259609341621399 | 0.6684145653901035 | 73 | 2117 | 17985 | 7.66905734504834e-06 | 4.771857903585634e-05 | higher_in_high_tail |
| MTG | C1QC | 1.2182033222455244 | 1.2480645775794983 | 0.5899551736238675 | 78 | 1994 | 17762 | 4.3441382994250383e-07 | 1.0425931918620092e-05 | higher_in_high_tail |
| MTG | HLA-DRA | 1.1602287903810158 | 1.1737547516822815 | 0.5829730049157754 | 78 | 1994 | 17762 | 8.752433659800835e-07 | 1.4003893855681336e-05 | higher_in_high_tail |
| DLPFC | TYROBP | 1.097228079217754 | 1.1393176317214966 | 0.6306004658953784 | 73 | 2117 | 17985 | 4.887905060657048e-06 | 3.9103240485256385e-05 | higher_in_high_tail |
| MTG | C1QA | 1.089191962702152 | 1.1115508675575256 | 0.5783300441809189 | 78 | 1994 | 17762 | 1.735633009707763e-06 | 1.6662076893194527e-05 | higher_in_high_tail |
| MTG | TYROBP | 1.0673159158382661 | 1.0802529454231262 | 0.604685800961959 | 78 | 1994 | 17762 | 9.488562179484098e-06 | 5.693137307690459e-05 | higher_in_high_tail |
| MTG | HLA-DRB1 | 1.0612144088133788 | 1.0695990324020386 | 0.5384919192546453 | 78 | 1994 | 17762 | 1.1706835676749714e-05 | 6.243645694266514e-05 | higher_in_high_tail |
| DLPFC | PSAP | 1.0598719160850734 | 1.0787525177001953 | 0.433890553369914 | 73 | 2117 | 17985 | 9.205326450404517e-05 | 0.0004686348011115027 | higher_in_high_tail |
| MTG | B2M | 1.0299312869707744 | 1.0651004314422607 | 0.46153133458051926 | 78 | 1994 | 17762 | 4.158274627956682e-06 | 2.8513883163131534e-05 | higher_in_high_tail |
| MTG | C1QB | 1.024305108265999 | 1.057289183139801 | 0.4616824231850795 | 78 | 1994 | 17762 | 2.320423318151434e-06 | 1.8563386545211473e-05 | higher_in_high_tail |
| DLPFC | HLA-DPA1 | 0.9739557741439506 | 0.9948514103889465 | 0.575669623401067 | 73 | 2117 | 17985 | 3.408157327909083e-05 | 0.00019085681036290866 | higher_in_high_tail |
| MTG | CD74 | 0.9650768920397147 | 0.9347404539585114 | 0.39039596685996425 | 78 | 1994 | 17762 | 1.424667933063005e-06 | 1.6662076893194527e-05 | higher_in_high_tail |
| MTG | CTSD | 0.9641736684701382 | 0.9768776297569275 | 0.5504410219116088 | 78 | 1994 | 17762 | 1.734281158060747e-05 | 8.324549558691586e-05 | higher_in_high_tail |
| MTG | HLA-DPA1 | 0.9622292239696552 | 0.9377152919769287 | 0.5541852955252696 | 78 | 1994 | 17762 | 0.00017953748148811995 | 0.0007834362828572506 | higher_in_high_tail |
| DLPFC | CTSD | 0.9577037222581367 | 0.9360094666481018 | 0.5559640643123078 | 73 | 2117 | 17985 | 0.0001468818092087621 | 0.0006327216396685137 | higher_in_high_tail |
| DLPFC | APOC1 | 0.8532760833224206 | 0.8336020112037659 | 0.5325502860423637 | 73 | 2117 | 17985 | 0.0011977306031348616 | 0.004192057110972015 | higher_in_high_tail |
| DLPFC | HLA-DPB1 | 0.8527467003832124 | 0.8849666118621826 | 0.49526899011984266 | 73 | 2117 | 17985 | 0.00011724770683949763 | 0.000547155965250989 | higher_in_high_tail |

_Showing 25 of 30 rows._

## Module-level signature summary

| dataset | module | n_present_module_genes | mean_gene_high_minus_low | median_gene_high_minus_low | n_genes_higher_in_high_tail | n_genes_lower_in_high_tail | top_higher_genes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DLPFC | antigen_presentation | 6 | 1.2723612818339645 | 1.41360604763031 | 6 | 0 | B2M;CD74;HLA-DRA;HLA-DRB1;HLA-DPA1 |
| DLPFC | complement_phagocytosis | 7 | 1.072208491644281 | 1.1393176317214966 | 7 | 0 | C1QC;C1QB;C1QA;TYROBP;AIF1 |
| DLPFC | dam_lipid_trem2_apoe | 8 | 0.7460996876191667 | 0.6777730882167816 | 7 | 1 | APOE;TYROBP;CTSD;APOC1;TREM2 |
| DLPFC | lysosomal_endolysosomal | 7 | 0.745150379749077 | 0.7356610298156738 | 7 | 0 | PSAP;CTSD;LAPTM5;CTSB;CTSS |
| DLPFC | oxidative_stress_gene_preserved | 7 | 0.3968259162495528 | 0.4241599142551422 | 7 | 0 | TXNIP;GPX4;SOD2;PRDX1;HMOX1 |
| DLPFC | interferon_inflammatory | 7 | 0.10694843777473616 | 0.06356784701347351 | 7 | 0 | IFITM3;NFKBIA;BSG;IRF8;STAT1 |
| MTG | complement_phagocytosis | 5 | 1.0356232576263256 | 1.0802529454231262 | 5 | 0 | C1QC;C1QA;TYROBP;C1QB;CTSS |
| MTG | antigen_presentation | 6 | 0.9829392510219517 | 1.0014078617095947 | 6 | 0 | HLA-DRA;HLA-DRB1;B2M;CD74;HLA-DPA1 |
| MTG | oxidative_stress_gene_preserved | 2 | 0.706385931907556 | 0.6823415011167526 | 2 | 0 | TXNIP;SOD2 |
| MTG | lysosomal_endolysosomal | 7 | 0.6631637566719518 | 0.7034757137298584 | 7 | 0 | CTSD;CTSS;PSAP;NPC2;LAPTM5 |
| MTG | dam_lipid_trem2_apoe | 8 | 0.6170833487573337 | 0.645564541220665 | 8 | 0 | APOE;TYROBP;CTSD;APOC1;TREM2 |
| MTG | interferon_inflammatory | 6 | 0.08516451337152862 | 0.06344073638319969 | 6 | 0 | NFKBIA;BSG;STAT1;IRF8;IL27RA |

## State enrichment among high-tail cells

| dataset | state_label | mean_high_minus_low_fraction | median_high_minus_low_fraction | n_donors | total_high_cells | total_low_cells |
| --- | --- | --- | --- | --- | --- | --- |
| MTG | Micro-PVM_3-SEAAD | 0.16617043133452156 | 0.1409533935849725 | 78 | 1994 | 17762 |
| MTG | Micro-PVM_2 | 0.11674705032247495 | 0.1275121704785524 | 78 | 1994 | 17762 |
| DLPFC | Micro-PVM_3-SEAAD | 0.09526941139385048 | 0.037772606739940776 | 68 | 1990 | 17189 |
| DLPFC | Micro-PVM_1_1-SEAAD | 0.04084577018925887 | 0.004193073426797261 | 45 | 1507 | 11570 |
| MTG | Monocyte | 0.007576622368348534 | -0.00421360695333298 | 48 | 1443 | 11721 |
| MTG | Micro-PVM_1 | 0.003000243196342488 | -0.010262936207074684 | 78 | 1994 | 17762 |
| MTG | Micro-PVM_4-SEAAD | 0.0016380025581448875 | -0.004706116844576339 | 34 | 920 | 8953 |
| DLPFC | Micro-PVM_2_1-SEAAD | -0.015468074112464225 | -0.009209226046550745 | 34 | 880 | 9039 |
| DLPFC | Micro-PVM_1 | -0.021291969260593915 | -0.021739130434782608 | 67 | 1883 | 16997 |
| MTG | Micro-PVM_2_1-SEAAD | -0.02604772626244591 | -0.014981483559645382 | 34 | 978 | 7872 |
| DLPFC | Micro-PVM_2 | -0.042888069629794634 | 0.01388888888888884 | 73 | 2117 | 17985 |
| DLPFC | Micro-PVM_2_2-SEAAD | -0.04618677271485568 | -0.02243444561880316 | 70 | 2088 | 17549 |
| MTG | Lymphocyte | -0.056412033659722347 | -0.03237410071942446 | 73 | 1925 | 16689 |
| MTG | Micro-PVM_2_3-SEAAD | -0.22714424806583594 | -0.19393435665275516 | 78 | 1994 | 17762 |

## Legacy overlay feasibility

| legacy_artifact | artifact_stage_guess | n_rows | has_cell_identifier_column | has_donor_identifier_column | direct_overlay_probable | recommended_use |
| --- | --- | --- | --- | --- | --- | --- |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_01_r007_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_02_r007_cov001_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_03_r010_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_04_r010_cov002_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_05_r012_cov001_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_06_r015_cov001_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_01_r0035_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_02_r0035_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_03_r004_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_04_r004_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_05_r0045_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_bridge_06_r0045_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_loose_01_r005_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_loose_02_r005_cov001_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_loose_03_r010_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_loose_04_r010_cov002_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_loose_05_r020_cov001_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_01_r003_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_02_r003_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_03_r005_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_04_r005_cov00075_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_05_r008_cov00025_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_06_r008_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_narrow_07_r008_cov00075_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_safety_01_r00475_cov0004_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_safety_02_r00475_cov0005_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_safety_03_r005_cov00035_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_fine_safety_04_r005_cov0004_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_upgrade_01_projector_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |
| C:\Users\dushy\Desktop\Jepa project\results\archive\old_stage_c_sweeps\tables\stage_c_upgrade_02_projector_pathology_epoch_005_coordinates.csv |  |  | True | True | True | overlay Stage68 rare-cell labels on legacy embedding/trajectory coordinates |

_Showing 30 of 242 rows._

## Claim boundary

| stage68_run_is_cell_extraction_and_expression_contrast_only | full_h5ad_scores_recomputed_from_frozen_stage64_definitions | stage64_capped_export_used_only_as_anchor_not_low_reference | no_new_model_run | no_benchmark_claim | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_validated_biomarker_claim | no_new_microglia_subtype_claim | raw_expression_matrix_not_written | raw_h5ad_not_committed | cell_labels_are_hypothesis_generating | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | True |
