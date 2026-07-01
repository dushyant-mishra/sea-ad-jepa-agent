# Stage 37B-rev1 PI reuse recommendation summary v1

## Short answer

Several datasets are reasonable to reuse, but none are currently approved for the strongest clean external-validation claim unless explicit approval evidence is added later.

## Top recommended reuse datasets

| dataset_id | dataset_name | revised_claim_level | allowed_use_now | recommended_next_action |
| --- | --- | --- | --- | --- |
| GSE138852 | GSE138852 / Grubman-Leng | external_biological_support_candidate | directional smoke-test; external biological support; projection/signature support | use as support only unless upgraded by manual review |
| GSE174367 | GSE174367 / Morabito | conditional_clean_validation_candidate | conditional validation candidate after contamination check; secondary projection/stress-test support | manual contamination and metadata review |
| GSE157827 | Candidate public external brain snRNA/scRNA dataset | conditional_clean_validation_candidate | manual metadata review and possible conditional validation planning | prioritize metadata/access/readout review |
| GSE160936 | GSE160936 | external_biological_support_candidate | external biological support and manual metadata review for possible conditional validation | request metadata/readouts and independence review |
| ROSMAP_AMP_AD | ROSMAP / AMP-AD | conditional_clean_validation_candidate | manual metadata review and possible conditional validation planning | prioritize metadata/access/readout review |

## How each should be used

| dataset_id | support_type | allowed_analysis_type | priority |
| --- | --- | --- | --- |
| GSE138852 | external_biological_support_candidate | directional smoke-test; external biological support; projection/signature support | medium |
| HBCC | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | medium |
| HBCA | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | medium |
| PUBLIC_CELLXGENE_MICROGLIA | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| LU_2026_SIGNATURES | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| PIG_WGCNA_RESOURCES | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| GSE181279 | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| b165f033-9dec-468a-9248-802fc6902a74 | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | low |
| 5c97eeeb-7e52-44b3-b010-b832b1f5424c | robustness_only | robustness/provenance/context only, with explicit non-clean-validation label | low |
| Olah_live_microglia | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| ac0c6561-7a48-4185-af6f-af799f699172 | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| Tabula_Sapiens_immune | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| Tabula_Sapiens_myeloid | projection_or_signature_support_candidate | projection/signature support; mechanism concordance | medium |
| GSE160936 | external_biological_support_candidate | external biological support and manual metadata review for possible conditional validation | high |

## Manual checks needed

| dataset_id | review_priority | minimum_metadata_to_request | exact_question_for_pi_or_manual_reviewer |
| --- | --- | --- | --- |
| GSE138852 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE174367 | high | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| PUBLIC_CELLXGENE_MICROGLIA | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| LU_2026_SIGNATURES | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| PIG_WGCNA_RESOURCES | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE157827 | high | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE147528 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE203206 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE181279 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| 37a17b78-4864-4a42-b67b-31c00962795a | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| 5e57cd50-8e42-42d6-940d-5c1660d06864 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| cff99df2-4904-44f7-9173-ff837f95606e | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| 203025fe-fa99-4d57-81da-458ed8f0c334 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| 0a2d7e87-c3c0-4ed2-86df-ae18811fcc16 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| fe2eecbc-977a-4aec-9196-f89c3281d11c | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| Olah_live_microglia | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| ac0c6561-7a48-4185-af6f-af799f699172 | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| Tabula_Sapiens_immune | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| Tabula_Sapiens_myeloid | medium | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| GSE160936 | high | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |
| ROSMAP_AMP_AD | high | donor/sample metadata; pathology/mechanism readouts; gene/module measurements; batch/provenance; licensing/access; prior-use independence | Can this resource be approved for the proposed bounded claim level, and if clean validation is desired, does it satisfy every Stage 36E/37A independence and readout rule? |

## Stage 37C gate

| stage37c_clean_external_validation_allowed | reason | approved_datasets | conditional_candidates | recommended_next_stage | claim_boundary |
| --- | --- | --- | --- | --- | --- |
| False | No dataset has explicit complete approval evidence in the repo. |  | GSE174367;GSE157827;GSE147528;ROSMAP_AMP_AD | Stage37C_external_support_first_pass_or_manual_metadata_review | Stage 37B-rev1 reclassifies claim levels only; it does not complete validation. |

## Safe lab-meeting language

reasonable to reuse; conditional validation candidate; external biological support; stress-test support; projection/signature support; manual metadata review required; not currently approved for clean external validation; missing evidence is not rejection

Avoid: validated; clean validation proven; external validation completed; causal regulator; therapeutic target; disease-modifying target