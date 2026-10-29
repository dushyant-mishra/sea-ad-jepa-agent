# Macha source qualification delta — 2026-10-30 (append-only; stacked on #509)

**Scope.** Metadata and source-feature identity only.
- **Not read:** count matrices, quarantined NPH52 cells, reader_validation/reader_oracle rows, DEV/SEALED data, pathology or disease columns, BAM/FASTQ.
- **Data handling:** every probe asserts its input SHA-256 pins before reading, and emits aggregates only, with no donor, sample or cell identifiers.

**Controlling rule:** reuse earlier verification, and re-hash only small files.

**Probes and outputs** (all under `scripts/v5/review_probes/macha_20261030/` and `results/target_discovery/unified_qualification_v1/`):

| Probe | Output | Section |
|---|---|---|
| `etl_reuse_ledger_probe.py` | `JEPA_MACHA_ETL_REUSE_LEDGER_20261030.json` | §0 |
| `alias_class_adjudication_probe.py` | `JEPA_MACHA_ALIAS_CLASS_ADJUDICATION_20261030.json` | §2A |
| `specimen_and_depositor_qc_probe.py` | `JEPA_MACHA_SPECIMEN_AND_DEPOSITOR_QC_20261030.json` | §2B–C |

The machine-readable gap-matrix delta is `JEPA_MACHA_SOURCE_QUALIFICATION_DELTA_20261030.json`.

## 0. ETL verification reuse ledger
322 artifact rows, taken from the existing authority manifests. Files up to 256 MB were re-hashed (730 MB in total). Larger files were stat'ed only and rely on their existing receipt. The 8,915 FULL104 blocks were counted, never hashed.

| Authority | Rows | Classification | Bytes today |
|---|---|---|---|
| 2026-09-02 FULL104 reuse manifest | 34 + 9 | 34 `EXACT_SHA_ALREADY_VERIFIED`; 9 `VERIFIED_AT_LIMITED_SCOPE` (engineering-pattern-only) | all identical, re-hashed |
| FULL104 metadata adapter manifest | **50** | `EXACT_SHA_ALREADY_VERIFIED` | all identical, re-hashed |
| FULL104 expression interface v8 | 124 | `EXACT_SHA_ALREADY_VERIFIED` | 122 re-hashed identical; 2 > 256 MB size-identical. Package root `28d544e8…` equals the manifest SHA. |
| FULL104 Level-4 materialization | 8 + blocks | `EXACT_SHA_ALREADY_VERIFIED` | block manifest `66f589e5…` and asset journal `d8bccf6c…` identical; **8,915/8,915** blocks present |
| Calibration bundle 2026-08-24 (#471, #492) | 97 | `EXACT_SHA_ALREADY_VERIFIED` | 95 re-hashed identical; 2 size-identical. Bundle manifest `da7c3daf…` as #492 recorded. |

**Drift: none. Missing: none.**

**Discrepancies reported, not reconciled:**
- **Adapter manifest count.** It has **50** entries, against the 47 named in the 2026-10-30 instructions.
- **Stale stored paths.** The Level-4 materialization manifest still names `_staging_expression_level4/`. Those rows resolve only through the declared rename to `expression_level4/`, and are matched by content.

**#509 inputs.** All eight inputs that #509 used are `EXACT_SHA_ALREADY_VERIFIED`, by the bundle, #492, the v8 package or the 2026-09-02 preservation manifest. Correction to #509: the address registry `7d61ed7b…` was labelled "unpinned" there, but it is #492's pinned address namespace. No input was newly verified, and none drifted.

## 1. P0 — #510 review (PR #512)
**Verdict: `REPAIR_REQUIRED`** at `ef51325d`.
- **Closed:** V2B closes the oracle for its own entry point.
- **Still open:** the #502 validator stays reachable from the V2B module and still recovers the hidden counts. The receipt binds neither the enforced roster and operator states nor the view it validated. An unhashable policy element escapes as `TypeError`.
- **Evidence:** CI run `40936356265` shows the review at 14 failed (10 new + 4 preserved #507) / 40 passed on ubuntu/windows × numpy 1.26.4/2.2.6. Repository sweeps show 14 failed / 553 passed. Inherited #510 passes everywhere.

## 2. P1 — source identity

### A. Alias adjudication of the 18 legacy/current pairs (11 query addresses)
**Rule.** It was fixed in the probe before its first run. The legacy locus comes from source-feature coordinates; current loci come from the pinned Ensembl 116 GTF (`ed992f0e…`). Locus support means same chromosome, same strand and at least 1 bp of overlap.

**Pair classifications:**
- **6 shared feature identity:** the legacy locus overlaps exactly one current gene.
- **2 ambiguous historical replacement:** it overlaps two current genes.
- **6 unsupported equivalence:** history lists the replacement, but there is no locus overlap. Example: legacy `LINC01251` (chr9) "replaced by" `CHD2` (chr15).
- **4 unresolved:** no legacy locus, because the SEA-AD-only 10x features carry no coordinates.

**Proposed query-rights equivalence table.** A constraint binds only where holder and query are both measured-scalar in the same operator:

| Query address | Symbol | Proposed action | Operators where it binds now |
|---|---|---|---|
| ENSG00000235481 | UBE2R2-AS1 | `SHARE_RIGHTS_CLASS` with legacy `ENSG00000233776` | 18 |
| ENSG00000257612 | MIR4307HG | `BLOCK_QUERY_OR_OPERATOR` (ambiguous) | 16 |
| ENSG00000257842 | LINC02588 | `BLOCK_QUERY_OR_OPERATOR` (ambiguous) | 18 |
| ENSG00000284609 / ENSG00000284680 | OR8B3 / OR8B2 | `SHARE_RIGHTS_CLASS` | 0 |
| ENSG00000286522 / ENSG00000287080 | HIST1H3B / HIST1H3C | `SHARE_RIGHTS_CLASS` | 0 |
| ENSG00000288709 / ENSG00000288722 | F8A2 / F8A1 | `BLOCK_QUERY_OR_OPERATOR` (unresolved holder) | 0 |
| ENSG00000288825 | HIST2H2AA3 | `BLOCK_QUERY_OR_OPERATOR` (unresolved) | 0 |
| ENSG00000173575 | CHD2 | no constraint from this audit (unsupported equivalence) | — |

- **Only three constraints bind today.** The other eight become live only if operator geometry changes, so they are retained.
- **NPH52 stays uncleared.** Symbol-only off-ledger features still receive no negative alias clearance, and nothing here clears them by symbol.

### B. Donor and specimen hierarchy
**SEA-AD** (reader_fit: 46 donors, 4,118,213 cells):
- **Hierarchy:** donor > brain region (= matrix, 11 regions) > [specimen/tissue block: **unavailable**] > 10x library.
- **Libraries:** 566 in total, each inside one donor, one region and one matrix. 164 of 343 donor-regions have more than one library (maximum 5).
- **`sample_id` is unique per nucleus.** It has 3,484,130 distinct values over exactly 3,484,130 cells, so **it is not a specimen key**. This **contradicts** #492 §10 and Macha #509 B2, which both treated it as recoverable specimen identity.
- **Caudate gaps.** The caudate matrix lacks `sample_id`, `method` and `cell_prep_type` (634,083 cells).
- **Replication unit.** Regional specimens are nested in donors, and the library is the finest established technical unit.

**HVS** (Johansen et al. 2023, *Science*, DOI 10.1126/science.adf2359, cited in each file's own CELLxGENE `uns`):
- **Matrices are subclass partitions.** The 24 matrices are the depositor's 24 subclass partitions of one study. Every one of the 43 libraries spans several matrices, so **operators are depositor annotation partitions, not batches**.
- **Specimen = donor.** The depositor's publication says nuclei came "from a single tissue section" per donor, consistent with a median of one library per donor (maximum 2). This is a depositor statement, not per-donor metadata.
- **No duplicated nuclei.** Every reader_fit cell has `is_primary_data = True`, and no cell key appears in two matrices.
- **Tumor infiltration.** The publication reports tumor-cell infiltration in two donors.

**NPH52:**
- **Matrices are cell-type objects**, and no specimen field exists. Specimen identity is **unavailable**.

No specimen ID has been derived from operator, matrix or cell-type names.

### C. Depositor QC and source selection
| Source | Observed selection evidence | Class |
|---|---|---|
| HVS | **Genes detected ≥ 1,000 exactly** (9 cells at the floor, 103 within 1%): a hard depositor filter, inferred from truncation (the methods are in a supplement not retrieved). UMIs ≥ 1,300. No mitochondrial ceiling (maximum 0.71). | CONTRADICTED for "selection independent of the query": a cell at the floor is included only because every detected gene, the query among them, was detected. The observed effect is small (9 of 198,718 cells at the floor). |
| SEA-AD | No hard floor (minimum 3 genes and 3 UMIs). Depositor `Doublet score` up to 0.98, so likely doublets are retained. No mitochondrial ceiling (maximum 0.73). | UNAVAILABLE (rules unrecorded). The depositor doublet score exists as metadata, but any filter on it is itself expression-derived. |
| NPH52 | Retained reader_fit library floor 601, consistent with a "> 600" filter (inference). Eligibility is final-annotation membership (22,715 reader-fit cells quarantined). Per-cell-type feature sets. | CONTRADICTED (selection imported). Effect unmeasured, because the quarantined cells were not opened. |

**Physical library total versus the depositor's UMI count:**
- **SEA-AD:** our `source_library` **equals** the depositor's `Number of UMIs` for all 4,118,213 cells. The total is **authenticated against the depositor**.
- **HVS:** our total is a median **0.915** (range 0.72–0.96) of the depositor's UMI count. So the HVS deposit omits about 8.5% of each nucleus's molecules, which quantifies #509 D3.

Proposed NPH52 quarantined-expression protocol (separate approval required; not executed): §4.

### D. D1 eligibility by source
- **HVS — eligible for D1 at source scope, with stated limits:**
  - D1 is computed over 18,736 deposited genes;
  - about 8.5% of molecules are absent from the deposit;
  - the 1,000-gene inclusion floor is a weak, quantified query-selection condition;
  - operators are subclass partitions;
  - alias-closed by accounting (#509).
- **SEA-AD — eligible for D1 at source scope:**
  - the residual is collision mass of collision-unresolved addresses (#509);
  - the total equals the depositor's UMI count;
  - the alias policy is consistent, with only the three binding constraints above;
  - no hard QC floor exists, but doublets may be present;
  - replication must count specimens nested in donors.
- **NPH52 — blocked for real query issuance** pending exact feature identity and depositor-selection qualification.

Eligibility is per source and per operator. A universal all-operators restriction would discard lawful coverage (#492 §8), and is not recommended.

## 3. P2 — smallest legitimate issuer contract (recommendation)
A V2B or G7 E3 V2 issuer must be an actor separate from the student. It must issue, under one signed and externally custodied release, the eight things below.

1. **Frozen query identity:** `molecular_address_id`, never a symbol.
2. **Alias-equivalence classes:** the table above, plus NPH52 symbol-only exclusions. A query is issued only if its whole class shares its right, otherwise it is blocked per operator.
3. **Evidence-rights ladder:** base rights and the full address→right map.
4. **Operator support:** the frozen state matrix (`852cb3ec…`), declared as source-specific.
5. **Permitted source-cell roster:** (source, matrix, row) keys, with donor and the specimen layer where known.
6. **Data custody:** the input SHA-256 set (the reuse ledger above) and storage location.
7. **Issuer provenance:** who issued, from which committed code, and when.
8. **Receipt:** the digest of each released view and a commitment to every enforced field (#512).

**Separation of quantities.** The physical library total stays private and separate from released D1. D2 stays excluded.

**Not sufficient** as evidence of external physical identity:
- a checksum;
- a matching row ID;
- a decision-table hash;
- a self-issued JSON policy.

**Still needed:**
- an external signing identity (who may issue);
- depositor specimen keys for SEA-AD tissue blocks and NPH52;
- the depositor QC methods;
- the NPH52 alias and selection protocol.

## 4. Proposed protocol for approval: NPH52 selection effect (NOT executed)
**Question.** Does annotation-based exclusion of the 22,715 quarantined reader-fit cells depend on a query's own expression? Specifically: does excluded-versus-retained status associate with a query's detection or count, beyond what library size and cell-type composition explain?

**Required access:** reader-fit NPH52 quarantined expression, for a frozen, pre-declared query list only. The list would come from issuer-eligible addresses and be fixed before any data is opened.

**Required design:**
- a frozen analysis plan;
- library-size-matched comparisons within donor;
- the stopping rule declared up front.

**Outputs:** aggregates only.

**Prohibited:** use for target choice, D selection, training or Stage 4.

**Status:** awaiting explicit approval. No bytes have been opened.

## 5. Handoff
| PR | Head | Role | Local evidence | CI evidence |
|---|---|---|---|---|
| #512 | `16b5bc6c` | #510 review | 14 RED / 553 pass (Windows ×2) | run `40936356265`, as in §1 |
| #509 | `3e5694e2` | gap matrix | — | custody-audit pass |
| this PR | (this delta) | stacked on #509 | three probes replayed byte-identically | — |
| #504 | `f52246fb` | A4 | — | accepted by ChatGPT #506 at `b66c23e5` |

**Next decisions:**
- adopt or amend the alias table;
- approve or refuse the §4 protocol;
- decide the issuer signing identity.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
