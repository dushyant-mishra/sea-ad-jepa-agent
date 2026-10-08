# Stage81A2R Project-Wide Source Identity Audit

**PROVISIONAL - NOT FROZEN - STOP FOR HUMAN REVIEW**

Original source feature metadata was inspected before authority fallback. No expression values, pathology labels, DEV biology, or SEALED biology were analyzed.

- Feature universes audited: **396**
- Materialized unique-universe feature rows: **4,118,465**
- Source-row-equivalent features across all matrix contracts: **12,627,696**
- Source-exact source-row equivalents: **10,797,139**
- Source-era exact source-row equivalents: **1,224,334**
- Authority-reconstructed source-row equivalents: **321,207**
- Legacy exact source-row equivalents: **80,462**
- Symbol-only/unresolved source-row equivalents: **281,811**

Repeated identical ordered feature universes are materialized once per dataset and linked to every source matrix through the provenance ledger. Source-row-equivalent counts retain the full matrix-level denominator.

The source-native NPH rowData discovery supersedes the historical symbol-only NPH assumption. Source-native biological features remain preserved but are not automatically admitted as universal encoder addresses.

## Dataset Compatibility

dataset,intended_role,modality,matrix_count,source_feature_count,source_row_equivalent_count,materialized_unique_universe_rows,unique_feature_universes,exact_current_identifiers,historical_identifiers_recovered,unresolved_identifiers,alternative_authority_exact_identifiers,source_native_biological_identifiers,symbol_only_unresolved_identifiers,technical_nonbiological_identifiers,duplicate_canonical_mappings,genome_annotation_build,exact_genes_in_foundation_space,exact_genes_outside_foundation_space,dataset_to_foundation_addressable_percent,foundation_to_dataset_measurement_percent,status
10x_Xenium_healthy_cortex_preview,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,0,0,0,0,0,0,0,0,0,0,0,0,0,unknown,0,0,0.0,0.0,SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER
CosMx_WTX_human_hippocampus,downloaded_unregistered_role_requires_review,spatial RNA,0,0,0,0,0,0,0,0,0,0,0,0,0,unknown,0,0,0.0,0.0,SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER
CosMx_human_frontal_cortex_6K,downloaded_unregistered_role_requires_review,spatial RNA,0,0,0,0,0,0,0,0,0,0,0,0,0,unknown,0,0,0.0,0.0,SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER
Fang_MERFISH_human_cortex_4000,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,30,39990,39990,3999,1,3499,0,493,0,5,489,0,2,unknown,3472,27,99.22835095741641,8.589382019692247,MATERIALIZATION POLICY NEEDED
GSE133357,downloaded_unregistered_role_requires_review|regional_primary_microglia_reference,gene-level RNA,1,9126,9126,9126,1,8936,0,179,0,11,173,0,0,unknown,8872,64,99.28379588182632,21.948443916679036,IDENTITY COMPATIBLE
GSE134577,living_csf_external_validation_only,gene-level RNA,18,603684,603684,33538,1,32481,734,0,0,0,0,0,545,unknown,32290,191,99.41196391736707,79.8822423432784,MATERIALIZATION POLICY NEEDED
GSE146639,aged_primary_microglia_validation|downloaded_unregistered_role_requires_review,gene-level RNA,27,450785,450785,417247,26,40771,2548,0,0,0,0,0,1279,unknown,34513,6258,84.65085477422677,85.38172282420464,MATERIALIZATION POLICY NEEDED
GSE175721,amyloid_context_validation|downloaded_unregistered_role_requires_review,gene-level RNA,2,65476,65476,32738,1,30309,705,0,0,0,0,0,483,unknown,30196,113,99.62717344683098,74.7018950076691,MATERIALIZATION POLICY NEEDED
GSE178317,downloaded_unregistered_role_requires_review|primary_microglial_perturbation_training,gene-level RNA,16,536608,536608,33538,1,32481,734,0,0,0,0,0,545,unknown,32290,191,99.41196391736707,79.8822423432784,MATERIALIZATION POLICY NEEDED
GSE181279,living_blood_independent_validation_only,gene-level RNA,1,32738,32738,32738,1,30309,705,0,0,0,0,0,483,unknown,30196,113,99.62717344683098,74.7018950076691,MATERIALIZATION POLICY NEEDED
GSE200164,living_csf_immune_adapter_and_validation_candidate,gene-level RNA,2,39378,39378,39378,1,16113,0,7064,0,38,7044,0,44,unknown,16109,4,99.97517532427233,39.85206075899263,MATERIALIZATION POLICY NEEDED
GSE226267,living_peripheral_regulatory_adapter_candidate,ATAC/chromatin|gene-level RNA,2,1001432,1001432,500716,1,0,0,0,0,500716,0,0,0,source R object; release metadata not supplied,0,0,0.0,0.0,IDENTITY COMPATIBLE
GSE226602,living_peripheral_immune_rna_adapter_candidate,gene-level RNA,2,44930,44930,44930,1,17525,0,9760,0,46,9744,0,70,source R object; release metadata not supplied,17518,7,99.96005706134095,43.33778635396566,MATERIALIZATION POLICY NEEDED
GSE240609,downloaded_unregistered_role_requires_review|mechanistic_bulk_validation,gene-level RNA,4,108616,108616,108616,4,2,0,108443,0,0,108443,0,8,unknown,2,0,100.0,0.004947800702587699,MATERIALIZATION POLICY NEEDED
GSE241858,downloaded_unregistered_role_requires_review|genotype_context_validation,gene-level RNA,2,56792,56792,56792,1,3,0,56786,0,0,56786,0,0,unknown,3,0,100.0,0.0074217010538815496,IDENTITY COMPATIBLE
GSE243292,aged_normal_and_pathology_context_validation|downloaded_unregistered_role_requires_review|future_use_role_from_download_registry,gene-level RNA,1,26423,26423,26423,1,19636,0,6687,0,53,6672,0,44,unknown,19632,4,99.97962925239356,48.56761169660086,MATERIALIZATION POLICY NEEDED
GSE248545,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,4,146404,146404,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE254205,downloaded_unregistered_role_requires_review|genotype_context_validation,ATAC/chromatin|gene-level RNA,1,33538,33538,33538,1,23356,0,10027,0,73,10010,0,77,encoding-version=0.1.0,23332,24,99.89724267854085,57.72104299638811,MATERIALIZATION POLICY NEEDED
GSE264624,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA,26,951626,951626,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE264692,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,42,1537242,1537242,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE270454,living_whole_blood_secondary_validation_candidate,gene-level RNA,1,27663,27663,27663,1,24496,0,2886,0,211,2870,0,68,unknown,22821,1675,93.16214892227302,56.45687991687695,MATERIALIZATION POLICY NEEDED
GSE278848,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,9,162765,162765,18085,1,18070,6,0,0,0,0,0,1,unknown,18070,0,100.0,44.70337934787987,MATERIALIZATION POLICY NEEDED
GSE280316,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,10,366010,366010,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE280460,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,13,7033,7033,1082,2,364,0,4,0,350,4,0,0,unknown,364,0,100.0,0.9004997278709613,IDENTITY COMPATIBLE
GSE292141,living_nph_blood_csf_context_and_adapter_candidate,gene-level RNA,20,732020,732020,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE293118,downloaded_unregistered_role_requires_review|regulatory_element_perturbation,gene-level RNA,2,37139,37139,37139,2,35527,897,0,0,0,0,538,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE301119,downloaded_unregistered_role_requires_review|myeloid_auxiliary_training,gene-level RNA,2,55763,55763,55763,2,24017,0,12567,0,76,12550,0,103,source R object; release metadata not supplied,24004,13,99.94587167423076,59.38350403245757,MATERIALIZATION POLICY NEEDED
GSE302937,living_olfactory_neural_immune_adapter_candidate,gene-level RNA,22,839307,839307,75207,2,37589,1923,0,0,0,0,0,1540,unknown,35582,2007,94.66067200510788,88.02632229973777,MATERIALIZATION POLICY NEEDED
GSE305625,living_biofluid_mirna_secondary_validation_candidate,miRNA,2,258,258,258,2,0,0,258,0,0,258,0,0,unknown,0,0,0.0,0.0,NON-RNA / SEPARATE FEATURE AUTHORITY
GSE307586,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,38,1390838,1390838,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE307587,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA,20,732020,732020,36601,1,35527,897,0,0,0,0,0,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE311359,downloaded_unregistered_role_requires_review|microglial_auxiliary_training,gene-level RNA,7,258874,258874,36982,1,35527,897,0,0,0,0,381,710,unknown,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
GSE325489,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,4,2164,2164,541,1,366,0,0,0,175,0,0,0,unknown,366,0,100.0,0.905447528573549,IDENTITY COMPATIBLE
GSE97930,downloaded_unregistered_role_requires_review|future_use_role_from_download_registry|normal_training_reference,gene-level RNA,3,113084,113084,113084,3,27212,0,39474,0,212,39420,0,169,unknown,22390,4822,82.27987652506248,55.390628865469296,MATERIALIZATION POLICY NEEDED
GSE99074,aged_primary_microglia_reference|downloaded_unregistered_role_requires_review,gene-level RNA,1,28981,28981,28981,1,27517,359,0,0,0,0,0,228,unknown,23488,4029,85.35814223934295,58.10697145118995,MATERIALIZATION POLICY NEEDED
HPA_Zhong_PFC_RNA,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA,2,225703,225703,225703,2,20158,7,0,0,205541,0,0,3,HPA source release,19866,292,98.5514435955948,49.14650437880362,MATERIALIZATION POLICY NEEDED
HPA_human_brain_StereoSeq,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,0,0,0,0,0,0,0,0,0,0,0,0,0,unknown,0,0,0.0,0.0,SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER
HPA_regional_human_brain_RNA,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA,2,225703,225703,225703,2,20158,7,0,0,205541,0,0,3,HPA source release,19866,292,98.5514435955948,49.14650437880362,MATERIALIZATION POLICY NEEDED
HVS,future_use_role_from_download_registry,gene-level RNA,24,449664,449664,449664,1,18735,0,0,0,0,0,0,0,encoding-version=0.1.0,18735,0,100.0,46.34852308149028,COMPATIBLE WITH LEGACY FEATURES
HYPOMAP_snRNA_reference,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA,1,36924,36924,36924,1,36922,1,0,0,0,0,0,1,encoding-version=0.1.0,27362,9560,74.10757813769568,67.69086141210232,MATERIALIZATION POLICY NEEDED
LIBD_spatialDLPFC,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,1,28916,28916,28916,1,28239,616,0,0,0,0,0,431,source R object; release metadata not supplied,28239,0,100.0,69.86047202018703,MATERIALIZATION POLICY NEEDED
NPH52,foundation_training_candidate|future_use_role_from_download_registry,gene-level RNA,7,244438,244438,244438,7,34790,4525,10264,0,219,10257,0,3625,source R object; release metadata not supplied,34790,0,100.0,86.06699322151304,MATERIALIZATION POLICY NEEDED
SCP2167_slidetags_PFC,context_qualification_or_reference|downloaded_unregistered_role_requires_review,gene-level RNA|spatial RNA,3,109803,109803,73202,2,35554,897,12420,0,56,12407,0,811,unknown,35541,13,99.96343590032063,87.92489238533472,MATERIALIZATION POLICY NEEDED
SEA_AD,downloaded_unregistered_role_requires_review|future_spatial_training_and_evaluation_source|microglia_specialization_candidate|multiregion_foundation_or_replication_candidate_pending_stage81a2|primary_foundation_candidate|regional_replication_candidate|regulatory_prior_source,ATAC/chromatin|gene-level RNA|spatial RNA,17,659604,659604,659604,5,35527,10764,40,0,218882,40,0,8520,encoding-version=0.1.0,35527,0,100.0,87.8902577804166,MATERIALIZATION POLICY NEEDED
Siletti_HBCA,context_qualification_or_reference|downloaded_unregistered_role_requires_review|future_use_role_from_download_registry,gene-level RNA,3,174696,174696,116464,1,58218,14,0,0,0,0,0,14,encoding-version=0.1.0,39572,18646,67.97210484729808,97.89718470140022,MATERIALIZATION POLICY NEEDED
_acquisition,downloaded_unregistered_role_requires_review,gene-level RNA,0,0,0,0,0,0,0,0,0,0,0,0,0,unknown,0,0,0.0,0.0,ADMINISTRATIVE INVENTORY / NO MOLECULAR FEATURE CONTRACT
spatialLIBD_classic_DLPFC,context_qualification_or_reference|downloaded_unregistered_role_requires_review,spatial RNA,1,33538,33538,33538,1,32481,734,0,0,0,0,0,545,source R object; release metadata not supplied,32290,191,99.41196391736707,79.8822423432784,MATERIALIZATION POLICY NEEDED


A2R is not frozen. Stage81A3R is not started. Future datasets contributed zero genes to the foundation candidate.
