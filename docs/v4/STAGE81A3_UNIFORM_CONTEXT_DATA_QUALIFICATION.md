# Stage81A3 Uniform Context Data Qualification

## A. What biological evidence do we actually have?

This read-only audit separates broad same-entity spatial truth, high-plex cell-resolved truth, targeted cell-resolved context, spot context, molecular references, and regional references. Role assignment describes what can be tested; it does not establish context benefit.

## B. How many independent people?

Exact people are counted only through the acquisition exact-identity graph. Repeated sections and regions are not added as independent donors; fuzzy `8667` / `Br8667` identity remains rejected.

## C. What can each dataset actually prove?

| Dataset | Role | Donors | Region | Technology | Entity | 4096 support | Direct counts | Physical geometry | Same-entity truth | A3 use |
|---|---|---:|---|---|---|---:|---|---|---|---|
| HPA_human_brain_StereoSeq | ACCESS_TRACE_ONLY | 0 | frontal cortex and cerebellum | Stereo-seq | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |
| GSE280460 | CELL_RESOLVED_MINIMAL_PANEL_CONTEXT | 8 | hypothalamus | 10x Xenium | see role matrix | 0.012 | see measurement table | see geometry table | see pairing table | supportive |
| GSE325489 | CELL_RESOLVED_TARGETED_CONTEXT | 4 | nucleus accumbens | 10x Xenium | see role matrix | 0.012 | see measurement table | see geometry table | see pairing table | supportive |
| doi:10.5061/dryad.x3ffbg7mw | CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT, QUARANTINED_PENDING_GOVERNANCE | 4 | MTG, STG | MERFISH | see role matrix | 0.233 | see measurement table | see geometry table | see pairing table | core |
| CELLxGENE:283d65eb-dd53-496d-adb7-7570c7caa443 | MOLECULAR_REFERENCE_ONLY | 4 | approximately 100 adult human brain dissections | 10x 3' v3 snRNA-seq | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | reference/review |
| CELLxGENE:d0941303-7ce3-4422-9249-cf31eb98c480 | MOLECULAR_REFERENCE_ONLY | 11 | hypothalamus | 10x 3' v3 snRNA-seq | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | reference/review |
| GSE264624 | MOLECULAR_REFERENCE_ONLY | 10 | hippocampus | 10x snRNA-seq | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | reference/review |
| GSE307587 | MOLECULAR_REFERENCE_ONLY | 10 | nucleus accumbens | 10x snRNA-seq | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | reference/review |
| GSE248545 | MULTIDONOR_SPOT_CONTEXT | 4 | dentate gyrus / hippocampus | 10x Visium | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | supportive |
| GSE264692 | MULTIDONOR_SPOT_CONTEXT | 10 | hippocampus | 10x Visium | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | supportive |
| GSE278848 | MULTIDONOR_SPOT_CONTEXT | 7 | hypothalamus | 10x Visium CytAssist v2 | see role matrix | 0.960 | see measurement table | see geometry table | see pairing table | supportive |
| GSE280316 | MULTIDONOR_SPOT_CONTEXT | 8 | hypothalamus | 10x Visium | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | supportive |
| GSE307586 | MULTIDONOR_SPOT_CONTEXT | 10 | nucleus accumbens | 10x Visium | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | supportive |
| 10x_Xenium_healthy_cortex_preview | QUARANTINED_PENDING_GOVERNANCE | 0 | cortex | 10x Xenium | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |
| CosMx_WTX_human_hippocampus | QUARANTINED_PENDING_GOVERNANCE | 0 | hippocampus | CosMx SMI WTX | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |
| CosMx_human_frontal_cortex_6K | QUARANTINED_PENDING_GOVERNANCE | 0 | frontal cortex | CosMx SMI | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |
| SCP2167 | QUARANTINED_PENDING_GOVERNANCE | 1 | prefrontal cortex | Slide-tags / snRNA-seq | see role matrix | 1.000 | see measurement table | see geometry table | see pairing table | reference/review |
| HPA_Zhong_PFC_RNA | REGIONAL_REFERENCE_ONLY | 0 | 20 PFC/reference cortical regional categories | bulk RNA-seq | see role matrix | 0.987 | see measurement table | see geometry table | see pairing table | reference/review |
| HPA_regional_human_brain_RNA | REGIONAL_REFERENCE_ONLY | 0 | 193 anatomical brain subregions | bulk RNA-seq | see role matrix | 0.987 | see measurement table | see geometry table | see pairing table | reference/review |
| spatialDLPFC | UNRESOLVED | 10 | DLPFC | 10x Visium and 10x snRNA-seq | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |
| spatialLIBD_classic_DLPFC | UNRESOLVED | 3 | DLPFC | 10x Visium | see role matrix | 0.000 | see measurement table | see geometry table | see pairing table | reference/review |

## D. What remains unidentifiable?

Opaque R objects and archive-only representations retain explicit implementation exceptions where continuous count-distribution metrics could not be inspected without extraction or schema-specific tooling. Optional CosMx and direct HPA Stereo-seq resources remain unresolved but do not block qualification of acquired data.

A generic SCP2167 `disease=normal` value was incidentally displayed during a pre-audit terminal schema preview. It was quarantined and not used. The audited reader blocks pathology-like columns, but governance-compliant completion is therefore reported as NO.

## E. Three identifiability decisions

- **BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE: NO**
- **CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE: PARTIAL_TARGETED_ONLY**
- **CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE: NO**

Final scientific classification: **REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE**

These are identifiability decisions, not experimental results. No neighbor graph, context model, optimizer update, or architecture change was performed.

STAGE81A3 UNIFORM CONTEXT DATA QUALIFICATION COMPLETE: NO

STAGE81A3 FROZEN: NO

READY FOR STAGE81B: NO
