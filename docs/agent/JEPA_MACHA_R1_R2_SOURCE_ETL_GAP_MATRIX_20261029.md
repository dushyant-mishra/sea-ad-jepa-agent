# R1 / R1D / R2 source and ETL gap matrix — Macha, 2026-10-29

**Scope.** Identity, grouping and code evidence only. No count values, no pathology, no reader_validation/reader_oracle rows, no DEV/SEALED data, no BAM/FASTQ. This is an append-only delta, so no frozen evidence is rewritten.

**Builds on ChatGPT #492** (`79d2f936`; source/ETL audit) **and #505** (historic archive aggregate). Their custody, residual and grouping numbers are cited, not recomputed.

**New numbers come from one committed probe:**
- `scripts/v5/review_probes/macha_20261029/r1_r2_source_gap_probe.py`
- output `results/target_discovery/unified_qualification_v1/JEPA_MACHA_R1_R2_SOURCE_GAP_PROBE_20261029.json`

The probe asserts the SHA-256 of every pinned input before reading it.

**Classes:**
- **AUTHENTICATED** — established from byte-bound project artifacts or depositor-supplied identifiers, within the stated scope. This is never physical provenance unless the row says so.
- **CONTRADICTED** — bound evidence shows the requirement fails. "Candidate-level" means the identity evidence was deliberately left unaccepted by the authority.
- **UNAVAILABLE** — no bound evidence is reachable under current policy. The row names the smallest route that would close it.

**Evidence kinds:** code (tested or source-read behavior), source-backed (bound artifact or depositor identifier), inference (reasoning on those), unavailable.

## 0. Correction to #492 §6–§7: the all-feature decision table is bound and in GitHub
#492 says the final `stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz` has no SHA-256 in GitHub history, so it is "not acceptable by name alone". **Contradicted:**
- **The binding.** `docs/history/JEPA_COMPLETE_PRESERVATION_MANIFEST_20260902.csv` line 5536 binds this exact path to SHA-256 `e3106248ac77…c773` and 17,002,348 bytes. The row is marked decision-bearing and review-safe, and it was committed in `2c000ecc` (2026-09-02).
- **The bytes.** They are also in git at `docs/history/exact_bytes/results/v4/stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz`.
- **Where.** Both are on `origin/main` and on #492's own head `79d2f936`.
- **Consequence.** The full source-feature accounting and the off-ledger alias audit that #492 lists as blocked can run in any environment holding the repository, with no new acquisition.

## 1. Gap matrix

### A. Physical nucleus vs matrix row (R1)
| # | Requirement | Class | Evidence |
|---|---|---|---|
| A1 | Each reader-fit row is one deposited count-matrix row with a stable key | **AUTHENTICATED** (deposited-row scope) | **Code:** HVS/SEA-AD rows are enumerated from H5AD obs of SHA-verified assets (`build_full104_production_adapter_metadata.py:268-288`); NPH52 rows come from a fresh-process-verified reader_fit derivative. **Source-backed:** #492 §4, 4,553,407 reader_fit rows. |
| A2 | Count values are integers before normalization | **AUTHENTICATED** (50k sample bytes) | **Source-backed:** #492 §2. All 246,702,069 nonzero log1p10k values invert to integers within 2.2e-11. Whether those integers are uncorrected UMI counts (no ambient or other correction by the depositor) is **UNAVAILABLE**. |
| A3 | One row = one physical nucleus (not a doublet, empty droplet or merged barcode) | **UNAVAILABLE** | Needs read/barcode-level data (BAM/FASTQ, prohibited) or depositor doublet/ambient calls. None of the recorded metadata carries them (#492 §9–10). |
| A4 | Cell keys are unique across sources and libraries | **AUTHENTICATED** at project scope only (`selection_row`, `canonical_cell_id`) | **Fixture code (#481):** raw barcodes repeat across libraries, and the fixture fails closed. A real producer must key cells by (source, matrix, row). |

### B. Donor vs specimen or pseudodonor (R1D)
| # | Requirement | Class | Evidence |
|---|---|---|---|
| B1 | Donor IDs denote distinct people | **UNAVAILABLE** | ID strings are disjoint across sources and partitions (#492 §4), but string disjointness is not identity. No external crosswalk is bound. The stage81a2 donor↔sample crosswalk `a555da96…` is for other studies (#492 §10). |
| B2 | Donor = replication unit = specimen | **CONTRADICTED** for SEA-AD | **Probe:** all 46 SEA-AD reader-fit donors appear in more than one of the 11 region matrices (ang, caudate, fi, hip, itg, lec, mec, mtg, pfc_a9, stg, v1c), median 10 regions per donor. Each region is a separate dissection, so specimens are nested in donors. The region is recoverable from `matrix_id`; tissue block and `sample_id` are **UNAVAILABLE** in the reader SQLite (in the upstream obs for 10/11 matrices, per #492 §10). |
| B3 | Specimen identity for HVS and NPH52 | **UNAVAILABLE** | **Probe:** HVS has 41 donors in 24 matrices (median 23 per donor); NPH52 has 16 of 17 donors in all 7 matrices. These matrices are dataset or cell-type partitions, not specimens (NPH52 objects are Astro/Endo/ExN/InN/MG/OPC/Oligo). No sample field exists upstream (#492 §10). |
| B4 | Pseudodonor and pooling exclusion | **UNAVAILABLE** | No multiplexing or pooling metadata is bound. |

### C. Full source-feature and query-alias accounting (R2 semantic precondition)
Bound inputs:
- the decision table `e3106248…`;
- provenance `df0cb60f…`;
- the operator state matrix `852cb3ec…`, with `state_names` asserted in the file.

| # | Requirement | Class | Evidence (probe) |
|---|---|---|---|
| C1 | Every deposited source feature has exactly one disposition | **AUTHENTICATED** (bound table) | 299,775 features in 9 feature sets. **HVS** 18,736 = the declared H5AD width in all 24 matrices. **SEA-AD** 36,601 = the declared width in all 11. **NPH52** 32,373–37,477 per cell-type object. |
| C2 | No off-ledger feature carries an addressed gene's molecules: **HVS, SEA-AD** | **AUTHENTICATED** by complete accounting (depositor Ensembl IDs) | Both sources map **every** feature (0 off-ledger). HVS has 0 collision-blocked features. In SEA-AD, 1,525 features per matrix are collision-blocked into 710 collision-unresolved addresses, never into a measured-scalar address (consistent with the 11,449 collision pairs recorded by #505, all collision-unresolved in Macha's 10-28 census). **So no off-ledger alias route exists in these two sources.** |
| C3 | Same requirement, **NPH52** | **CONTRADICTED (candidate-level)** | Each object has 1,085–1,867 off-ledger features (all but one per object `SYMBOL_ONLY_UNRESOLVED`), and 943–1,547 of them have no Ensembl anchor at all. The other off-ledger identities reach **348 ledger addresses**; 341 of 347 distinct symbols equal the reached address's symbol. In the same operator, 260 of those addresses are measured-scalar (the count may be partial), **95 are labelled structurally unmeasured** although a same-operator feature resolves to them, and 4 are collision-unresolved. **Under #492's fail-closed rule (symbol-only features cannot clear), no NPH52 operator can be cleared for any query.** |
| C4 | No in-ledger alias (two addresses sharing one gene's molecules) | **CONTRADICTED (candidate-level)**, small and enumerable | 46 mapped features (40 NPH52, 6 SEA-AD) sit on legacy addresses whose Ensembl ID has multiple current replacements, at least one of which is another address. That gives 18 address pairs and **11 current addresses at risk** (listed in the probe JSON). Under D1 this is the route that leaks: a base-right holder would carry query molecules into the depth (#481 C). |
| C5 | Query identity is the molecular address ID, never the symbol | **CONTRADICTED** for symbol keys | 275 duplicated symbols over 551 addresses (#492 §5; reproduced). |

### D. Residual and physical-library-total provenance
| # | Requirement | Class | Evidence |
|---|---|---|---|
| D1 | `source_library` is the whole deposited row, summed before mapping | **AUTHENTICATED** (code) | `materialize_full104_phase2_expression.py:222`. |
| D2 | Residual composition per source | **AUTHENTICATED** for HVS and SEA-AD; **UNAVAILABLE** per row for NPH52 | HVS: 0 off-ledger + 0 blocked, which explains #492's 0.0000% exactly. SEA-AD: 0 off-ledger, so the whole residual (#492: 4.0065% pooled) is collision mass of collision-unresolved addresses. NPH52: off-ledger + collision mass. A per-row split needs feature-level counts from the NPH reader-fit derivative, which is expression access (not executed here). |
| D3 | The library total is a whole-transcriptome physical total | **CONTRADICTED** for HVS; **UNAVAILABLE** for SEA-AD and NPH52 | The HVS deposit (18,736 features) has **no** source feature for ACTB, RPL13, RPS18, RPL10, RPS12 or RPL23, among the most abundant transcripts in any nucleus. All six are present in SEA-AD and in every NPH52 object. So HVS's total omits abundant molecules, and structurally unmeasured there means "not deposited", not "not captured". SEA-AD's 36,601 matches the standard 10x GRCh38-2020-A gene set (external knowledge, inference). NPH52's per-object widths differ. |
| D4 | V2's conservation gate (total == Σ mapped) holds on real rows | **CONTRADICTED** except HVS | Every SEA-AD and NPH52 operator has collision-blocked or off-ledger features (probe). V2 and #502 therefore refuse any real row carrying that mass. A real D1 issuer must not gate on conservation; D1 needs no total (#491). |

### E. Query-dependent QC and cell selection
| # | Requirement | Class | Evidence |
|---|---|---|---|
| E1 | Our selection uses no expression or QC statistic | **AUTHENTICATED** (code) for HVS and SEA-AD | **Code:** all deposited obs rows of a reader-fit donor are admitted (`build_full104_production_adapter_metadata.py:280-288`), and Phase 2 uses keyed identity hashes and per-donor caps (`build_full104_phase2_metadata_selection.py`). |
| E2 | Same requirement, NPH52 | **CONTRADICTED** (selection imported) | **Code:** a cell is eligible only if it has exact membership in the depositor's final annotation (`stage81a3_rebuild_nph_disposition_cache.R:81-87`, "no QC cause inferred"). 22,715 reader-fit cells are quarantined (`build_full104_production_adapter_metadata.py:32`). We apply the depositor's post-QC and annotation selection ourselves. **The excluded cells' bytes are held**, so the selection effect is measurable, but only by opening quarantined expression. That needs explicit authorization. |
| E3 | Depositor QC rule is independent of the query | **UNAVAILABLE** | Rules are not recorded (#492 §9, negative scan). The upstream obs QC columns (mito fraction, genes detected, UMI count) can be recovered metadata-only (#492 §10). All 154 QC-entangled addresses (MT-, RPS/RPL, MALAT1, NEAT1) are never collision-unresolved. 114 (SEA-AD), 124 (HVS) and 131 (NPH52) are measured-scalar in every operator, so they are mechanically observable but selection-entangled. |
| E4 | Query observability is independent of the query's expression | **CONTRADICTED** (inference, NPH52) | NPH52 operators are depositor cell-type objects with different feature sets from one assay: measured-scalar addresses 30,294–34,405 per operator, against 18,736 uniform in HVS and 35,076 uniform in SEA-AD. A gene missing from one cell-type object is most plausibly a per-object expression filter, so which cell types can serve a query depends on the query's own expression. The depositor's per-object gene rule is **UNAVAILABLE**. |

### F. Rights issuer (R2 issuer half)
| # | Requirement | Class | Evidence |
|---|---|---|---|
| F1 | A real issuer binds address rights, ladder and query to a view | **UNAVAILABLE** | Only process-local fixture custody exists (#502). See Macha #507: a teacher-view oracle, and a receipt that does not commit to the enforced policy. |

## 2. Decision-relevant consequences (scientific inference; for the deciding lane)
1. **D1 (#491) changes what the alias audit protects.** Off-ledger aliases (C3) no longer leak into the depth, because D1 excludes the residual. They do still mean:
   - NPH52 measured-scalar counts for up to 260 addresses may be partial teacher values;
   - 95 NPH52 structurally-unmeasured labels are not established.

   In-ledger aliases (C4) do leak under D1. **Rights should be assigned per alias class** (the 18 pairs), or the 11 at-risk addresses excluded as queries.
2. **HVS and SEA-AD are alias-closed by accounting today**, relative to depositor Ensembl IDs. NPH52 is not, and under the strict rule never will be. The alias rule needs a decision: either symbol-level clearance against the query's HGNC symbol set, or NPH52 excluded from query issuance.
3. **Specimen nesting (B2) means SEA-AD replication cannot be counted by donor alone.** Region matrices give a recoverable specimen layer, which HVS and NPH52 lack.
4. **NPH52 selection (E2, E4) is imported from depositor annotation and per-cell-type gene filters.** Its effect can be measured from held bytes only under an explicit authorization to open quarantined reader-fit expression. Until then, NPH52 queries carry an unquantified selection condition.
5. **D1 depth is source-geometry dependent.** The base-visible address sets differ (HVS 18,736; SEA-AD 35,076; NPH52 30–34k), so cross-source D1 comparability needs operator conditioning or a common base set.

## 3. Smallest closing actions (none acquires BAM/FASTQ)
| Gap | Action | Data access |
|---|---|---|
| C3 | Decide the symbol-level clearance rule, then run it with the bound decision table | identity only |
| C4 | Freeze the 18 alias pairs as rights-sharing classes | identity only |
| B2/B3/E3 | Recover upstream obs columns (`sample_id`, QC columns) for reader-fit rows | metadata only |
| D2/E2/E4 | Authorize or refuse a per-feature NPH52 reader-fit read (residual split and selection effect) | expression; needs explicit authority |
| A3/B1/B4 | Depositor statements (doublet calls, donor identity, pooling) | external |

No claim here grants calibration, target, training, Stage 4 or G7 authority.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
