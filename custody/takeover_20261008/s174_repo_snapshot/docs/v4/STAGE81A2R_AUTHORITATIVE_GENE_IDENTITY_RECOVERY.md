# Stage81A2R Authoritative Gene-Identity Recovery

**PROVISIONAL - NOT FROZEN - AUTHORITATIVE MAPPING RECOVERY**

Stage81A3R/global-state work remained paused. This audit used exact release-pinned Ensembl/HGNC evidence only; it performed no model training and opened no DEV RNA, SEALED RNA, or pathology.

## Accounting

1. Previous current-exact candidate: **37,346**
2. Previously unresolved source records: **106,118**
3. Previously unresolved unique symbols: **17,607**
4. Source records newly resolved: **93,547**
5. Unique symbols newly resolved: **15,370**
6. Support-only recovered source records: **73,975**
   - Existing genes gaining support in one or more additional matrices: **10,665**
7. Genuinely new current Ensembl genes recovered: **4,219**
8. Final provisional current exact address-space size: **40,422**
9. Exact historical/legacy Ensembl identities without unique projection: **773**
   - Source records preserving those identities: **4,845**
10. Remaining unresolved source records: **10,264**
11. Remaining unresolved unique symbols: **2,011**
12. Within-matrix canonical collisions: **11,435**
13. New semantic hash: `d0d0affeb92b33cd520846da0e16723c2672638f669a88cbef3aa98421ba372b`

## Preserved Biological Identity Classes

- Current canonical Ensembl genes: **40,422** unique genes across **284,447** source rows.
- Legacy exact Ensembl genes: **773** unique IDs across **4,845** source rows.
- Alternative-authority exact features: **0** unique anchors across **0** source rows.
- Source-native coordinate/transcript/biological features: **219** source-scoped features across **219** rows.
- Symbol-only unresolved: **2,010** unique symbols across **10,257** rows.
- Technical/non-biological: **0** unique features across **0** rows.

Absence from Ensembl/HGNC is not a biological-exclusion criterion. Source-native biological evidence is preserved in a separate registry and remains subject to a human A2R encoder-address-space decision. It is never merged across datasets without exact shared identity.

Source-row counts are not gene counts. Support-only recovery improves legitimate matrix measurement evidence without increasing the biological address space.

## Remaining Reasons

- `SYMBOL_ONLY_UNRESOLVED`: 10,257
- `AMBIGUOUS_ALIAS_MULTIPLE_TARGETS`: 7

## Recovery By Source

| source | source_rows | prior_exact | prior_unresolved | newly_recovered_source_rows | support_only_recovered_rows | new_gene_recovered_rows | alternative_authority_exact_rows | source_native_biological_rows | symbol_only_unresolved_rows | technical_feature_rows | remaining_unresolved_rows | legacy_exact_rows | duplicate_canonical_collision_rows | measured_current_exact_genes_after_recovery |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HVS_COMMON | 18736 | 18717 | 19 | 19 | 2 | 17 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 18735 |
| NPH52::Astro_data_arranged_updatedId_final_batches.qs | 35028 | 19773 | 15255 | 13460 | 10671 | 2789 | 0 | 35 | 1446 | 0 | 1447 | 664 | 530 | 32279 |
| NPH52::Endo_data_arranged_updatedId_final_batches.qs | 32373 | 19147 | 13226 | 11779 | 9901 | 1878 | 0 | 23 | 1085 | 0 | 1086 | 610 | 464 | 30128 |
| NPH52::ExN_data_arranged_updatedId_final_batches.qs | 37477 | 20409 | 17068 | 14935 | 11118 | 3817 | 0 | 39 | 1867 | 0 | 1868 | 694 | 562 | 34237 |
| NPH52::InN_data_arranged_updatedId_final_batches.qs | 35964 | 20050 | 15914 | 13991 | 10862 | 3129 | 0 | 34 | 1604 | 0 | 1605 | 680 | 537 | 33031 |
| NPH52::MG_data_arranged_updatedId_final_batches.qs | 33441 | 19437 | 14004 | 12378 | 10164 | 2214 | 0 | 27 | 1265 | 0 | 1266 | 634 | 488 | 30961 |
| NPH52::OPC_data_arranged_updatedId_final_batches.qs | 33761 | 19416 | 14345 | 12687 | 10314 | 2373 | 0 | 26 | 1306 | 0 | 1307 | 623 | 492 | 31245 |
| NPH52::Oligo_data_arranged_updatedId_final_batches.qs | 36394 | 20126 | 16268 | 14288 | 10942 | 3346 | 0 | 35 | 1684 | 0 | 1685 | 680 | 552 | 33364 |
| SEA_AD_COMMON | 36601 | 36571 | 19 | 10 | 1 | 9 | 0 | 0 | 0 | 0 | 0 | 259 | 7810 | 35527 |
| aggregate::SEA_AD | 36601 | 36571 | 19 | 10 | 1 | 9 | 0 | 0 | 0 | 0 | 0 | 259 | 7810 | 35527 |
| aggregate::HVS | 18736 | 18717 | 19 | 19 | 2 | 17 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 18735 |
| aggregate::NPH52 | 244438 | 138358 | 106080 | 93518 | 73972 | 19546 | 0 | 219 | 10257 | 0 | 10264 | 4585 | 3625 | 34790 |

## New Current Genes By Biotype

| broad_biotype | new_current_gene_count | recovered_source_record_count | source_families | source_objects |
| --- | --- | --- | --- | --- |
| TCR | 4 | 28 | NPH52 | NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs |
| immunoglobulin | 1 | 6 | NPH52 | NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs |
| lncRNA | 201 | 1358 | HVS\|NPH52\|SEA_AD | HVS_COMMON\|NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs\|SEA_AD_COMMON |
| mitochondrial | 11 | 77 | NPH52 | NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs |
| other | 52 | 336 | NPH52 | NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs |
| other_ncRNA | 945 | 3693 | HVS\|NPH52 | HVS_COMMON\|NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs |
| protein_coding | 256 | 1667 | HVS\|NPH52\|SEA_AD | HVS_COMMON\|NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs\|SEA_AD_COMMON |
| pseudogene | 2749 | 12813 | HVS\|NPH52\|SEA_AD | HVS_COMMON\|NPH52::Astro_data_arranged_updatedId_final_batches.qs\|NPH52::Endo_data_arranged_updatedId_final_batches.qs\|NPH52::ExN_data_arranged_updatedId_final_batches.qs\|NPH52::InN_data_arranged_updatedId_final_batches.qs\|NPH52::MG_data_arranged_updatedId_final_batches.qs\|NPH52::OPC_data_arranged_updatedId_final_batches.qs\|NPH52::Oligo_data_arranged_updatedId_final_batches.qs\|SEA_AD_COMMON |

No protein-coding or other biotype filter was applied.

## Highest-Frequency Unresolved Symbols

| raw_symbol | source_row_count | terminal_reason |
| --- | --- | --- |
| AC000003.2 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC002321.2 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC002395.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC002472.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC002477.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC002553.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC003043.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004016.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004017.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004257.3 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004410.3 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004447.2 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004812.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004840.9 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004878.7 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC004878.8 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC005027.3 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC005082.1 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC005152.2 | 7 | SYMBOL_ONLY_UNRESOLVED |
| AC005229.1 | 7 | SYMBOL_ONLY_UNRESOLVED |

The complete tail is preserved in `stage81a2r_authoritative_unresolved_features_candidate.csv.gz`; it is not hidden behind these aggregates.

## Collision Boundary

Collision rows are evidence only. No expression rows were summed, dropped, duplicated, or otherwise materialized. Any reported collision requires a later human materialization policy.

## Governance

**STOP FOR HUMAN A2R ADDRESS-SPACE AND PROTECTED-IDENTITY REVIEW**

A2R is not frozen. Freeze1 is not declared. Do not proceed into A3R automatically.
