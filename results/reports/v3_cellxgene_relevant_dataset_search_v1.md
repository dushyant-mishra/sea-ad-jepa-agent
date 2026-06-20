# v3 CELLxGENE relevant dataset search v1

## 1. Executive summary

Stage 26C searched CELLxGENE Census metadata using Census release `stable`.
Dataset metadata rows scanned: 1845. Candidate dataset rows emitted: 700.
No expression matrices/H5AD payloads were downloaded. No v3 training, graph neural model, external validation, model selection, evidence-level change, or manuscript prose was run.

## 2. Search method

The script loaded `census['census_info']['datasets']` and queried human and mouse obs metadata for brain/CNS tissues, microglia/CNS macrophage or immune cell labels, and neurodegenerative disease labels.
Broad `normal`/`control` disease-only queries were not used as standalone filters to avoid pulling unrelated whole-Census normal/control metadata; control/normal labels are reported when present among matched brain/cell-type/disease records.
- Homo sapiens: 53740242 matched obs rows using `(tissue in ['brain', 'cerebral cortex', 'prefrontal cortex', 'frontal cortex', 'temporal cortex', 'entorhinal cortex', 'hippocampus', 'central nervous system'] or tissue_general in ['brain', 'cerebral cortex', 'prefrontal cortex', 'frontal cortex', 'temporal cortex', 'entorhinal cortex', 'hippocampus', 'central nervous system'] or cell_type in ['microglial cell', 'central nervous system macrophage', 'macrophage', 'monocyte'] or disease in ['Alzheimer disease', 'dementia', 'Parkinson disease', 'multiple sclerosis', 'neurodegenerative disease'])`
- Mus musculus: 4913958 matched obs rows using `(tissue in ['brain', 'cerebral cortex', 'prefrontal cortex', 'frontal cortex', 'temporal cortex', 'entorhinal cortex', 'hippocampus', 'central nervous system'] or tissue_general in ['brain', 'cerebral cortex', 'prefrontal cortex', 'frontal cortex', 'temporal cortex', 'entorhinal cortex', 'hippocampus', 'central nervous system'] or cell_type in ['microglial cell', 'central nervous system macrophage', 'macrophage', 'monocyte'] or disease in ['Alzheimer disease', 'dementia', 'Parkinson disease', 'multiple sclerosis', 'neurodegenerative disease'])`

## 3. Best human AD/dementia brain candidates

- collection_name=Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution; dataset_title=MSSM_Cohort; matched_cell_count=4140453; n_microglia_or_cns_macrophage_cells=202952; relevance_score=26; recommended_role=clean_external_holdout_candidate
- collection_name=Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution; dataset_title=RADC_Cohort; matched_cell_count=693682; n_microglia_or_cns_macrophage_cells=30764; relevance_score=26; recommended_role=clean_external_holdout_candidate
- collection_name=Molecular Signatures of Resilience to Alzheimer’s Disease in Neocortical Layer 4 Neurons; dataset_title=all cells; matched_cell_count=424528; n_microglia_or_cns_macrophage_cells=5071; relevance_score=26; recommended_role=clean_external_holdout_candidate
- collection_name=Brain vascular single-cell multi-omics elucidates disease risk associations; dataset_title=Brain vascular single-cell multi-omics elucidates disease risk associations - snRNA-seq; matched_cell_count=65479; n_microglia_or_cns_macrophage_cells=10092; relevance_score=26; recommended_role=clean_external_holdout_candidate
- collection_name=Deciphering glial contributions to CSF1R-related disorder via single-nuclear transcriptomic profiling; dataset_title=Full Dataset; matched_cell_count=61747; n_microglia_or_cns_macrophage_cells=2018; relevance_score=26; recommended_role=clean_external_holdout_candidate
- collection_name=Single-soma transcriptomics of tangle-bearing neurons in Alzheimer’s disease; dataset_title=Single-soma transcriptomics of tangle-bearing neurons in Alzheimer’s disease - Excitatory; matched_cell_count=96129; n_microglia_or_cns_macrophage_cells=0; relevance_score=22; recommended_role=external_projection_stress_test
- collection_name=Deciphering glial contributions to CSF1R-related disorder via single-nuclear transcriptomic profiling; dataset_title=Oligodendrocytes; matched_cell_count=24342; n_microglia_or_cns_macrophage_cells=0; relevance_score=22; recommended_role=external_projection_stress_test
- collection_name=Deciphering glial contributions to CSF1R-related disorder via single-nuclear transcriptomic profiling; dataset_title=Astrocytes; matched_cell_count=18890; n_microglia_or_cns_macrophage_cells=0; relevance_score=22; recommended_role=external_projection_stress_test
- collection_name=Deciphering glial contributions to CSF1R-related disorder via single-nuclear transcriptomic profiling; dataset_title=Microglia; matched_cell_count=1621; n_microglia_or_cns_macrophage_cells=1621; relevance_score=22; recommended_role=clean_external_holdout_candidate
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Whole Taxonomy - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD); matched_cell_count=1395601; n_microglia_or_cns_macrophage_cells=42486; relevance_score=21; recommended_role=already_used_plausibility_only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Whole Taxonomy - MTG: Seattle Alzheimer's Disease Atlas (SEA-AD); matched_cell_count=1378211; n_microglia_or_cns_macrophage_cells=40000; relevance_score=21; recommended_role=already_used_plausibility_only
- collection_name=Cross-dementia human brain snRNA-seq (Rexach et al 2024); dataset_title=All Cells - snRNA-seq; matched_cell_count=432555; n_microglia_or_cns_macrophage_cells=21575; relevance_score=21; recommended_role=already_used_plausibility_only

## 4. Best human normal brain/microglia pretraining candidates

- collection_name=A human cell atlas of fetal gene expression; dataset_title=Survey of human embryonic development; matched_cell_count=2843334; n_microglia_or_cns_macrophage_cells=8975; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=A multi-region single nucleus transcriptomic atlas of Parkinson’s disease; dataset_title=Parkinson's disease; matched_cell_count=2096155; n_microglia_or_cns_macrophage_cells=118515; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=An integrated transcriptomic cell atlas of human neural organoids; dataset_title=HNOCA Extended: The Human Neural Organoid Atlas; matched_cell_count=1920454; n_microglia_or_cns_macrophage_cells=60; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=An integrated transcriptomic cell atlas of human neural organoids; dataset_title=The Human Neural Organoid Atlas; matched_cell_count=1767346; n_microglia_or_cns_macrophage_cells=60; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution; dataset_title=HBCC_Cohort; matched_cell_count=1486324; n_microglia_or_cns_macrophage_cells=66567; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Population-scale cross-disorder atlas of the human prefrontal cortex at single-cell resolution; dataset_title=Aging_Cohort; matched_cell_count=1332155; n_microglia_or_cns_macrophage_cells=66294; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Human Brain Cell Atlas v1.0; dataset_title=All non-neuronal cells; matched_cell_count=871787; n_microglia_or_cns_macrophage_cells=91838; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=A human cell atlas of fetal gene expression; dataset_title=Survey of human embryonic development (1 million cells subset); matched_cell_count=700346; n_microglia_or_cns_macrophage_cells=2265; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Single-cell analysis of prenatal and postnatal human cortical development; dataset_title=Single-cell analysis of prenatal and postnatal human cortical development; matched_cell_count=690693; n_microglia_or_cns_macrophage_cells=15957; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Single cell atlas of the human optic nerve; dataset_title=snRNA-seq of human optic nerve and optic nerve head - all cells; matched_cell_count=616465; n_microglia_or_cns_macrophage_cells=48062; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=Human developing neocortex by area; dataset_title=Second Trimester Human Developing Brain Regions and Cortical Areas; matched_cell_count=457965; n_microglia_or_cns_macrophage_cells=6864; relevance_score=21; recommended_role=self_supervised_pretraining_candidate
- collection_name=HYPOMAP: A comprehensive spatio-cellularmap of the human hypothalamus; dataset_title=Human HYPOMAP single-nucleus data; matched_cell_count=433369; n_microglia_or_cns_macrophage_cells=23651; relevance_score=21; recommended_role=self_supervised_pretraining_candidate

## 5. Mouse auxiliary candidates

- collection_name=A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation; dataset_title=Single-cell RNA-seq for all cortical & hippocampal regions (10x); matched_cell_count=1169213; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=A transcriptomic atlas of the mouse cerebellum reveals regional specializations and novel cell types; dataset_title=A transcriptomic atlas of the mouse cerebellum; matched_cell_count=611034; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=An integrated transcriptomic and epigenomic atlas of mouse primary motor cortex cell types; dataset_title=An integrated transcriptomic and epigenomic atlas of mouse primary motor cortex cell types; matched_cell_count=406187; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=HypoMap – a unified single cell gene expression atlas of the murine hypothalamus; dataset_title=HypoMap – a unified single cell gene expression atlas of the murine hypothalamus; matched_cell_count=384925; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Developmental trajectories of thalamic nuclei revealed by single-cell transcriptome profiling and Shh perturbation; dataset_title=Atlas of the developing mouse thalamus; matched_cell_count=249071; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Thyroid hormone remodels cortex to coordinate body-wide metabolism and exploration; dataset_title=Single-nucleus RNA sequencing of M2: WT-THR vs DN-THR; matched_cell_count=205722; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Cellular development and evolution of the mammalian cerebellum; dataset_title=snRNA-seq data for mouse cerebella from 9-12 developmental stages; matched_cell_count=115282; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Thyroid hormone remodels cortex to coordinate body-wide metabolism and exploration; dataset_title=Single-nucleus RNA sequencing of M2: T3 vs control; matched_cell_count=107742; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Molecular and spatial signatures of mouse brain aging at single-cell resolution; dataset_title=BrainAgingSpatialAtlas_snRNAseq; matched_cell_count=79667; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=A taxonomy of transcriptomic cell types across the isocortex and hippocampal formation; dataset_title=Single-cell RNA-seq for all cortical & hippocampal regions (SMART-Seq v4); matched_cell_count=73347; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Tabula Muris Senis; dataset_title=All - A single-cell transcriptomic atlas characterizes ageing tissues in the mouse; matched_cell_count=33659; relevance_score=11; recommended_role=mouse_auxiliary_only
- collection_name=Tabula Muris Senis; dataset_title=All - A single-cell transcriptomic atlas characterizes ageing tissues in the mouse - Smart-seq2; matched_cell_count=24082; relevance_score=11; recommended_role=mouse_auxiliary_only

## 6. Peripheral immune candidates

- collection_name=Tabula Sapiens; dataset_title=Tabula Sapiens - All Cells; matched_cell_count=95235; relevance_score=10; recommended_role=peripheral_immune_plausibility
- collection_name=Tabula Sapiens; dataset_title=Tabula Sapiens - Immune; matched_cell_count=95235; relevance_score=10; recommended_role=peripheral_immune_plausibility
- collection_name=Tabula Sapiens; dataset_title=Tabula Sapiens - Eye; matched_cell_count=651; relevance_score=10; recommended_role=peripheral_immune_plausibility
- collection_name=Cell Types of the Human Retina and Its Organoids at Single-Cell Resolution; dataset_title=Periphery - Cell Types of the Human Retina and Its Organoids at Single-Cell Resolution; matched_cell_count=471; relevance_score=10; recommended_role=peripheral_immune_plausibility
- collection_name=Cell Types of the Human Retina and Its Organoids at Single-Cell Resolution; dataset_title=Fovea - Cell Types of the Human Retina and Its Organoids at Single-Cell Resolution; matched_cell_count=309; relevance_score=10; recommended_role=peripheral_immune_plausibility
- collection_name=Mapping the developing human immune system across organs; dataset_title=HSC/immune cells (all hematopoietic-derived cells); matched_cell_count=152073; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Mapping the developing human immune system across organs; dataset_title=Full dataset of single-cell RNA-seq profiles from 9 developmental tissues across gestation (4-17 pcw); matched_cell_count=152073; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Mapping the developing human immune system across organs; dataset_title=Myeloid cells; matched_cell_count=148771; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Azimuth meta-analysis of human scRNA-seq datasets; dataset_title=Human - Lung v2 (HLCA); matched_cell_count=138373; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Single cell atlas of large B-cell lymphoma; dataset_title=Single cell atlas of LBCL (LME); matched_cell_count=136373; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Multimodal profiling reveals tissue-directed signatures of human immune cells altered with age; dataset_title=Immune aging project - all cells; matched_cell_count=124931; relevance_score=6; recommended_role=peripheral_immune_plausibility
- collection_name=Multimodal profiling reveals tissue-directed signatures of human immune cells altered with age; dataset_title=Immune aging project - myeloid cell subset; matched_cell_count=118259; relevance_score=6; recommended_role=peripheral_immune_plausibility

## 7. Datasets to avoid or review

- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Whole Taxonomy - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=21; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Whole Taxonomy - MTG: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=21; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=Cross-dementia human brain snRNA-seq (Rexach et al 2024); dataset_title=All Cells - snRNA-seq; relevance_score=21; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Microglia-PVM - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=19; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Microglia-PVM - MTG: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=19; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=Live Human Microglia Single-cell RNA-seq; dataset_title=Olah et al (2020) Single-cell Human Microglia; relevance_score=19; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Oligodendrocyte - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=Oligodendrocyte - MTG: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=Molecular characterization of selectively vulnerable neurons in Alzheimer's Disease; dataset_title=Molecular characterization of selectively vulnerable neurons in Alzheimer’s Disease: Superior frontal gyrus; relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=Molecular characterization of selectively vulnerable neurons in Alzheimer's Disease; dataset_title=Molecular characterization of selectively vulnerable neurons in Alzheimer’s Disease: Entorhinal Cortex; relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=OPC - MTG: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only
- collection_name=SEA-AD: Seattle Alzheimer’s Disease Brain Cell Atlas; dataset_title=OPC - DLPFC: Seattle Alzheimer's Disease Atlas (SEA-AD); relevance_score=17; recommended_role=already_used_plausibility_only; notes=resembles already-used v1/v2 provenance; plausibility only

## 8. Recommended downloads

Metadata/schema should remain the first download step. H5AD download should be limited to top-ranked candidates after role approval. Clean holdout candidates should stay untouched until v3 architecture/training decisions are frozen.

## 9. Recommended integration plan

- Preserve clean human AD/dementia brain candidates as external holdouts unless intentionally reclassified.
- Use mouse datasets only as auxiliary/pretraining resources with ortholog mapping, never as human validation.
- Use peripheral immune datasets only for plausibility/auxiliary context, not direct brain microglia validation.
- Keep already-used or provenance-unclear datasets out of clean validation.

## 10. Role-freezing rules

No CELLxGENE dataset found in this audit is allowed for model selection. Training/pretraining permissions are role-specific and must be frozen before any matrix download or integration.
