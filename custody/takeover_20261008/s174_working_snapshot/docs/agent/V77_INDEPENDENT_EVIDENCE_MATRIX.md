# V77 independent-evidence matrix: adversarial, analysis only

**Status:** ANALYSIS_ONLY. Selects no evidence object, target, estimand, weighting or threshold. Classes describe capability and current project status, not preference, and are not a ranking

**Scope:** every Phase 5 candidate, tested against the S157, V48 and V63 twins. Sub-rows separate instances whose answer differs: same nuclei or donors versus external resources, and the query RNA versus other data

**Query:** the RNA whose program is being interpreted: the cells, libraries and donors of a qualification query. In the V77 challenge it is the student evidence; a real query cohort is the deciding lane's choice and is not made here

## The constraint that decides most rows

- **P0_TAXONOMY.** The V50 mandatory nuisance classes (N0 to N2H) remain the project's taxonomy. The twins below map onto it; none replaces it.
- **P1_QUERY_MATCHING.** Against TW_EXACT only a measurement on the query's own samples (the same nuclei, cells, libraries or donors) can identify. An external or static object takes the same value whichever process generated the query RNA: if the object is fixed and the RNA law is identical, the joint law of RNA and object is identical. It can change plausibility, never the likelihood ratio between BIO and TW_EXACT.
- **P2_OBJECT_NUISANCE.** An object that shares a physical process with the RNA (nucleus, droplet, tissue quality, perturbation stress) can be keyed by that process (TW_ANCHOR). Its own nuisance must be measured or ruled out.
- **P3_CONSTRUCTION.** An object whose features, cell groupings, region sets, regulator choices or labels use the query RNA inherits the query's covariance, biological or not.
- **P4_COUNTING.** Objects that share a selection (expression or activity) or a physical process remove one alternative, not several: resource count is not evidence-independence count.
- **P5_LOCALITY.** A twin broken in one dataset is broken there. Transfer to another dataset is a separate claim.
- **P6_STATIC_LIMITS.** Static evidence can still reject nuisances whose gene membership it predicts differently (V63 E2), but V63 Task 8 shows a latent capture factor correlated with the target surviving the declared margin, and an anchor-keyed nuisance passing unless anchor frequency is matched.

## Twin catalogue

| Twin | Lineage | Definition | Status |
|---|---|---|---|
| TW_EXACT | V48; V63 NEG5 and NEG_SEMANTIC_TWIN; S157 TWIN_EXACT | a hidden measurement process with the same joint law as the biology over every permitted query observable, acting on the same genes in the same cells | NON_IDENTIFIABLE_BY_DESIGN from same-assay RNA under every context, raw identity included (S157 T1) |
| TW_OPERATOR | V47; S157 TWIN_OPERATOR; V50 nuisance class N2G_source_lab_fingerprint | gene-specific capture tied to the measurement operator or library | lawful depth and support descriptors do not remove it (S157 T3); raw identity removes most of it as an exploratory positive control only (S157 T2); V47: only an oracle hidden-capture covariate removed it |
| TW_TARGET_CAPTURE | V63 Task 8 NEG_TECH_2 | a latent capture factor correlated with the target | the binding failure of the V63 external-link criterion: margin LCB95 0.00768 against a declared 0.010, gate_may_proceed = false on FAIL__TECH |
| TW_ANCHOR | V63 Task 8 NEG_ANCHOR_1; V58/V59; S157 handoff T3; its nucleus-quality form is V50 nuisance class N2A_hidden_nucleus_quality | a nuisance keyed to the independent object itself, so it moves the RNA and the object together | passes an external-anchor test unless anchor frequency is matched (V63 Task 8: -0.08186 without anchor matching); V58/V59: an anchor-keyed twin passed an external-anchor benchmark perfectly |
| TW_MODELLED | V63 E2 NEG1-NEG4 | measured technical, hidden quality, activity confound and geometry confound nuisance classes | rejected with an external link, for the tested classes only (V63 E2 ALL_TESTED_NEGATIVES_REJECTED); a nuisance not simulated is not tested |
| TW_ASSAY | not a lineage twin; named here for adversarial completeness | an artefact of the assay class itself, reproduced in every dataset of that assay, for example droplet single-nucleus capture of these genes in this cell type | untested |
| TW_PROPERTY | not a lineage twin; named here for adversarial completeness | capture keyed to transcript properties: length, GC, 3' end, intron content, expression level | untested |
| TW_PROCESS_PROGRAM | V50 nuisance class N2B_handling_exAM; V49 (the exAM signature does not track recorded PMI); not represented in any synthetic world | a genuine regulatory program induced by the handling process (ex vivo dissociation response, agonal state, postmortem interval) rather than by the in vivo state; ambient RNA is the analogous pure-capture case | untested in synthetic worlds; V50: handling induces apparent activation, homeostatic loss and chromatin changes not captured by PMI. Every regulatory evidence object supports it, because it is regulation |

## Classification rule

Declared before any row was filled; precedence runs top to bottom.

1. CIRCULAR_WITH_CURRENT_RNA: construction uses the RNA being explained
2. PROTECTED_OR_NOT_AVAILABLE: no lawful, available instance in the project, or restricted from use as an input
3. SUPPORTIVE_BUT_NOT_IDENTIFYING: even fully qualified it cannot change the likelihood ratio between BIO and any lineage twin (TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ANCHOR); it may still reject V63 E2 modelled classes
4. UNQUALIFIED: it could break a named lineage twin, an instance is available and not circular, but controls in column 9 are missing
5. CAN_BREAK_A_SPECIFIC_TWIN: it could break a named lineage twin and no blocking control is missing

`class_if_qualified`: what the row becomes once column 9 is satisfied; never UNQUALIFIED. It describes capability, not preference, and is not a ranking.

## Summary

| Row | Evidence object | Query matching | Lineage twins it can break | Strongest twin remaining | Class now | Class if qualified |
|---|---|---|---|---|---|---|
| R1 | Paired same-nucleus chromatin (RNA plus ATAC multiome) | SAME_NUCLEUS | TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE | TW_ANCHOR through nucleus quality tied to the state, moving RNA capture and accessibility together; TW_PROCESS_PROGRAM, since handling changes chromatin too (V50 N2B); programs without a chromatin footprint are out of reach | UNQUALIFIED | CAN_BREAK_A_SPECIFIC_TWIN |
| R2a | Separate-nucleus chromatin from the query donors | SAME_DONOR | TW_EXACT, TW_OPERATOR | TW_ANCHOR at donor level (tissue quality moving both); composition; TW_PROCESS_PROGRAM | UNQUALIFIED | CAN_BREAK_A_SPECIFIC_TWIN |
| R2b | Morabito snATAC (GSE174367) | EXTERNAL_STATIC | none | TW_EXACT and every query twin | PROTECTED_OR_NOT_AVAILABLE | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R2c | Chromatin from other external cohorts | EXTERNAL_STATIC | none | TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ANCHOR | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R3 | Nott enhancer-promoter interactome (PLAC-seq, Table S5) | EXTERNAL_STATIC | none | TW_EXACT; TW_TARGET_CAPTURE (V63 Task 8 FAIL__TECH); TW_ANCHOR keyed to contact frequency; TW_PROCESS_PROGRAM | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R4 | TF motifs and cisTarget rankings | EXTERNAL_STATIC | none | TW_EXACT; TW_PROPERTY keyed to GC; TW_PROCESS_PROGRAM | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R5a | SCENIC+ eRegulons built on the query RNA | QUERY_RNA | none | TW_EXACT, absorbed by construction | CIRCULAR_WITH_CURRENT_RNA | CIRCULAR_WITH_CURRENT_RNA |
| R5b | SCENIC+ eRegulons built on an independent multiome, applied to the query | EXTERNAL_STATIC | none | TW_EXACT; TW_ASSAY absorbed through its RNA side; TW_PROCESS_PROGRAM | PROTECTED_OR_NOT_AVAILABLE | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R5c | Stage75F regulatory edges (built with Morabito RNA) | QUERY_RNA | none | TW_EXACT, absorbed by construction | CIRCULAR_WITH_CURRENT_RNA | CIRCULAR_WITH_CURRENT_RNA |
| R6 | Perturbation with engagement (CRISPRi/a) in an external system | EXTERNAL_STATIC | none | TW_EXACT and TW_OPERATOR in the query; perturbation-keyed capture; TW_PROCESS_PROGRAM (a handling-induced program is also perturbable) | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R7a | Spatial in situ transcriptomics from the query donors | SAME_DONOR | TW_EXACT, TW_OPERATOR | TW_ANCHOR through tissue RNA integrity moving both chemistries; agonal and postmortem forms of TW_PROCESS_PROGRAM; program genes absent from the panel | UNQUALIFIED | CAN_BREAK_A_SPECIFIC_TWIN |
| R7b | Spatial in situ transcriptomics from other donors | EXTERNAL_STATIC | none | TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ANCHOR | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R8a | Query-donor genotypes with allele-resolved query RNA | SAME_DONOR | TW_EXACT, TW_TARGET_CAPTURE | allele-keyed capture (the TW_ANCHOR analogue); low 3' coverage; few donors | PROTECTED_OR_NOT_AVAILABLE | CAN_BREAK_A_SPECIFIC_TWIN |
| R8b | External eQTL and caQTL catalogues | EXTERNAL_STATIC | none | TW_EXACT and every query twin | PROTECTED_OR_NOT_AVAILABLE | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R9a | Spike-ins or external RNA standards in the query libraries | SAME_LIBRARY | TW_OPERATOR | TW_EXACT with gene-specific, state-linked capture that spike-ins do not report | PROTECTED_OR_NOT_AVAILABLE | CAN_BREAK_A_SPECIFIC_TWIN |
| R9b | Library descriptors derived from the query RNA (depth, measurable-address count, zero fraction) | QUERY_RNA | none | TW_OPERATOR and TW_EXACT stay | CIRCULAR_WITH_CURRENT_RNA | CIRCULAR_WITH_CURRENT_RNA |
| R9c | Protocol metadata and raw source or operator identity | SAME_LIBRARY | TW_OPERATOR | TW_EXACT; biology confounded with study | PROTECTED_OR_NOT_AVAILABLE | CAN_BREAK_A_SPECIFIC_TWIN |
| R9d | Donor and sample process covariates (postmortem interval, agonal state, RNA integrity, handling time) | SAME_DONOR | none | TW_EXACT, TW_OPERATOR | SUPPORTIVE_BUT_NOT_IDENTIFYING | SUPPORTIVE_BUT_NOT_IDENTIFYING |
| R10a | Protein in the same cells or nuclei (antibody-derived tags) | SAME_CELL | TW_EXACT, TW_OPERATOR | TW_ANCHOR through size or quality moving tags and RNA; poor RNA-protein coupling | PROTECTED_OR_NOT_AVAILABLE | CAN_BREAK_A_SPECIFIC_TWIN |
| R10b | Donor-level proteomics of the query donors | SAME_DONOR | TW_EXACT, TW_OPERATOR | composition; tissue quality (donor-level TW_ANCHOR) | PROTECTED_OR_NOT_AVAILABLE | CAN_BREAK_A_SPECIFIC_TWIN |

## Rows in full

### R1. Paired same-nucleus chromatin (RNA plus ATAC multiome)

Candidate 1; query matching SAME_NUCLEUS.

1. **Quantity measured.** Tn5 accessibility at regulatory regions in the same nucleus whose RNA is the query
2. **Physically independent of the query RNA?** PARTLY: a different molecule and library, but the same nucleus, isolation, permeabilisation, droplet, barcode and ambient pool
3. **Construction independence.** LEAK_RISK: independent only if the region universe, peak calls, cell groupings and region-to-gene rule are fixed without the query RNA; standard multiome pipelines leak through joint embeddings, peak calling on RNA-labelled clusters, RNA-transferred labels and gene-activity scores
4. **Biological specificity.** accessibility is necessary, not sufficient; many regions are open across states; region-to-gene assignment is ambiguous. Needs state-specific accessibility at the program's regions against matched decoy regions and same-donor nuclei of other states
5. **Nuisance that can mimic it.** nucleus integrity and permeabilisation moving both libraries' yield (fragments with UMIs, FRiP, TSS enrichment); doublets; ambient DNA; Tn5 GC bias; copy number
6. **Twins it can falsify.** TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE: when the hidden process is confined to the RNA library (reverse transcription, priming, amplification, ambient RNA): biology predicts state-specific accessibility at the program's regions, such a twin predicts none. Only for programs with a chromatin footprint
7. **Stronger twin remaining.** TW_ANCHOR through nucleus quality tied to the state, moving RNA capture and accessibility together; TW_PROCESS_PROGRAM, since handling changes chromatin too (V50 N2B); programs without a chromatin footprint are out of reach
8. **Provenance and ETL already in the project.**
   - SEA-AD public multiome: PAIRING_QUALIFIED_BIOLOGICAL_OUTCOME_UNOPENED; 66,288 exact paired nuclei, MTG only, 1,594 candidate myeloid paired nuclei, 15 myeloid donors; not independent of FULL104 target discovery, the SEA-AD cohort, the nucleus or MTG (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json; results/v64/V68_FULL104_PRIVILEGED_EVIDENCE_COVERAGE_MAP_V1.json)
   - SEA-AD processed products: DEVELOPMENT_EXPOSED_SUPPORTING_ASSET; same-cell relationship depends on the product (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md)
   - GSE214979: VERIFIED_SAME_NUCLEUS_PAIRING__CONDITIONAL_DATASET__NOT_SELECTED_OR_QUALIFIED; 105,332 of 105,332 nuclei carry RNA and ATAC on one row; 15 donors, 12 after frozen exclusions; donors inferred by demultiplexing; non-overlap with FULL104 inferred, not proved (PR #182, via handoff/jepa-20261006-macha-audit-successor@e966e05b; main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md)
   - GSE272082: PAIRED_BY_DESIGN__PAIRING_AND_MICROGLIA_CENSUS_NOT_YET_AUTHENTICATED; effective donor n 9; label conflicts in 2 of 9 (handoff/jepa-20261006-macha-audit-successor@e966e05b)
   - GSE214979 fragment custody: Route-B replay REPRODUCED_ON_RECONCILED_HEAD; blacklist ENCFF356LFX AUTHENTICATED_AND_BOUND (263 of 150,561 regions removed) (claude/v74-authority-correction-20261004@733829c6 results/v74/V74_MACHA_RECONCILIATION_AUTHORITY_V1.json)
9. **Missing controls blocking use.**
   - region universe frozen before outcomes, with the blacklist gate authenticated
   - per-nucleus quality covariates and a planted nucleus-quality-keyed control (TW_ANCHOR)
   - GC- and accessibility-matched decoy regions
   - cell groupings and the region-to-gene rule fixed without the query RNA
   - donor-level inference: nuclei refine donors, they are not replicates
   - exposure-ledger entries and FULL104 donor overlap declared
   - prospective positive and negative signatures frozen before any outcome
10. **Classification now:** `UNQUALIFIED`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R2a. Separate-nucleus chromatin from the query donors

Candidate 2; query matching SAME_DONOR.

1. **Quantity measured.** donor-level or donor-by-cell-type accessibility from other nuclei of the query donors
2. **Physically independent of the query RNA?** YES: other nuclei and libraries; shared donor tissue (postmortem interval, pH, agonal state, RNA integrity), dissection and possibly isolation batch
3. **Construction independence.** LEAK_RISK: cell-type labels must come from chromatin alone or an external reference; label transfer from the query RNA leaks; donors matched by stable identifiers
4. **Biological specificity.** donor resolution only; few donors; composition differs between samples
5. **Nuisance that can mimic it.** donor-level tissue quality, composition and cohort batch; disease state co-varies at donor level (never used as a label, still a confounder)
6. **Twins it can falsify.** TW_EXACT, TW_OPERATOR: at donor resolution, when the hidden process is cell- or library-level: biology predicts that donor-level program activity tracks accessibility at its regions in separate nuclei; a library-level twin predicts no such relation
7. **Stronger twin remaining.** TW_ANCHOR at donor level (tissue quality moving both); composition; TW_PROCESS_PROGRAM
8. **Provenance and ETL already in the project.**
   - SEA-AD processed snATAC from the SEA-AD donors: DEVELOPMENT_EXPOSED_SUPPORTING_ASSET (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md)
   - rule: separate-nucleus evidence is donor-level evidence and is not promoted to same-cell correspondence (same file, binding rule 4); small donor n cannot be rescued by many cells (rule 5)
9. **Missing controls blocking use.**
   - a donor-matched chromatin instance for the query donors
   - donor-level quality covariates and composition control
   - power at the available donor count
   - exposure-ledger entries
10. **Classification now:** `UNQUALIFIED`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R2b. Morabito snATAC (GSE174367)

Candidate 2; query matching EXTERNAL_STATIC.

1. **Quantity measured.** single-nucleus accessibility in a separate cohort
2. **Physically independent of the query RNA?** YES: another cohort's nuclei
3. **Construction independence.** INDEPENDENT: independent of the query unless the query is Morabito RNA; see R5c for the edges built with that RNA
4. **Biological specificity.** donor and cell-type level in another cohort
5. **Nuisance that can mimic it.** cohort batch; selection on activity
6. **Twins it can falsify.** none: no lineage twin (P1): external to the query
7. **Stronger twin remaining.** TW_EXACT and every query twin
8. **Provenance and ETL already in the project.**
   - MORABITO_GSE174367: AUTHENTICATED_CONDITIONALLY_INDEPENDENT; 18 shared RNA/ATAC donors, 4,126 RNA and 12,232 ATAC microglia, no cell-level pairing (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
   - PROTECTED_NOT_AVAILABLE_FOR_SELECTION; heavily exposed historically (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md); PR #164 was readiness only, every biological evaluation NOT_EXECUTED (handoff/jepa-20261006-macha-audit-successor@e966e05b)
   - PR #175 (open): 37,966 of 41,238 addresses donor-level RNA/ATAC eligible: structural coverage, not biology
9. **Missing controls blocking use.**
   - protection lifted by the deciding lane, which is not requested here
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R2c. Chromatin from other external cohorts

Candidate 2; query matching EXTERNAL_STATIC.

1. **Quantity measured.** accessibility or histone marks in other donors
2. **Physically independent of the query RNA?** YES: other donors, nuclei and labs
3. **Construction independence.** LEAK_RISK: region sets or labels derived with the query RNA would leak; otherwise independent
4. **Biological specificity.** cell-type level in another cohort; no query-state resolution
5. **Nuisance that can mimic it.** cohort batch; selection on activity
6. **Twins it can falsify.** TW_MODELLED: no lineage twin (P1). Can reject V63 E2-type modelled nuisances and argue against TW_ASSAY when its own chromatin couples to the program
7. **Stronger twin remaining.** TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ANCHOR
8. **Provenance and ETL already in the project.**
   - Kosoy microglia regulome: PRODUCT_SPECIFIC__UNKNOWN_REQUIRES_AUDIT; DS010 (GSE308668-GSE308906): BLOCKED_BY_EMBARGO; GSE173316: ARTIFACT_UNLOCATED (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md)
   - GSE214979 chromatin is external to FULL104 only if the inferred non-overlap holds (R1)
9. **Missing controls blocking use.**
   - region universe and labels fixed without the query RNA
   - exposure ledger
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R3. Nott enhancer-promoter interactome (PLAC-seq, Table S5)

Candidate 3; query matching EXTERNAL_STATIC.

1. **Quantity measured.** physical 3D proximity between H3K4me3-marked promoters and distal regions, with cell-type enhancer marks, in FANS-sorted microglia, neuron and oligodendrocyte nuclei from resected cortex
2. **Physically independent of the query RNA?** YES: different tissue, donors, lab and molecule
3. **Construction independence.** LEAK_RISK: no query RNA, but selection shares expression and activity with RNA: interactions are anchored on active promoters, enhancers are defined by H3K27ac, nuclei are sorted by marker proteins
4. **Biological specificity.** three broad cell types, static, no state resolution within a type, kilobase region-to-gene resolution, non-aged surgical tissue, hg19
5. **Nuisance that can mimic it.** activity selection (highly expressed cell-type genes carry more contacts and better detection); gene length (long genes have more distal contacts and more intronic single-nucleus reads); GC and promoter CpG status
6. **Twins it can falsify.** TW_MODELLED: no lineage twin (P1): the map is identical in BIO and TW_EXACT. With length-, expression-, GC- and anchor-frequency-matched controls it can reject nuisances whose gene membership is not organised by cell-type wiring (the V63 E2 classes, TW_PROPERTY)
7. **Stronger twin remaining.** TW_EXACT; TW_TARGET_CAPTURE (V63 Task 8 FAIL__TECH); TW_ANCHOR keyed to contact frequency; TW_PROCESS_PROGRAM
8. **Provenance and ETL already in the project.**
   - Nott Table S5 re-authenticated: 36,876,140 bytes, SHA-256 81c99689...; 104,802 microglia, 93,290 neuronal and 61,895 oligodendrocyte contacts; 72.93% of microglia contacts unique to that map; NOTT_S5_AUTHENTICATED__SAME_STUDY_CONTACT_SPECIFICITY_SUBSTRATE_AVAILABLE__NO_PROGRAM_VALIDATION_PERFORMED (handoff/jepa-20261006-macha-audit-successor@b1382ab4 docs/agent/JEPA_NOTT_TABLE_S5_REAUTH_AND_CELLTYPE_CONTACT_SPECIFICITY_20261006.md)
   - hg19 coordinates; both liftover chains authenticated, the liftover itself listed as a next step (docs/agent/JEPA_NEW_CHAT_HANDOFF_20260929_V64_SINGLE_SOURCE_E2.md section 13); no completed liftover receipt found
   - 'Nott/E2 and NIH-CARD measurability share expression/activity selection; resource count is not evidence-independence count' (docs/agent/JEPA_HANDOFF_STATE_20260930_V64.json)
   - V63 E2 used an external link of this kind: ALL_TESTED_NEGATIVES_REJECTED, NEG5 NON_IDENTIFIABLE_BY_DESIGN (results/v63/V63_E2_IDENTIFIABILITY_BENCHMARK_V1.json)
9. **Missing controls blocking use.**
   - hg19 to hg38 liftover receipt
   - length-, expression-, GC-, CpG- and anchor-frequency-matched controls
   - promoter-fixed distal shuffle
   - same-study comparator contrast (neuronal, oligodendrocyte)
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R4. TF motifs and cisTarget rankings

Candidate 4; query matching EXTERNAL_STATIC.

1. **Quantity measured.** motif match scores and region rankings per TF motif: genome sequence
2. **Physically independent of the query RNA?** YES: DNA sequence and position weight matrices
3. **Construction independence.** LEAK_RISK: independent if the region set is fixed without the query RNA; regions from RNA-guided peaks or from differential accessibility between RNA-defined groups leak; motif-to-TF annotation is uneven
4. **Biological specificity.** low per TF: families share motifs, sites are common, occupancy is unknown
5. **Nuisance that can mimic it.** GC and CpG content (a GC-keyed capture or PCR bias makes GC-rich genes co-vary and enriches GC-rich motifs); annotation supply; region length; promoter versus distal composition
6. **Twins it can falsify.** TW_MODELLED: no lineage twin alone (sequence is constant across cells). Jointly with per-nucleus accessibility its power is R1's
7. **Stronger twin remaining.** TW_EXACT; TW_PROPERTY keyed to GC; TW_PROCESS_PROGRAM
8. **Provenance and ETL already in the project.**
   - V69 Route A/B prospective freeze: a custom cisTarget database per route, or a receipted fallback labelled GENERIC_REGION_DATABASE; TF-label permutation within annotation-supply strata frozen (claude/v74-authority-correction-20261004 results/v64/V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1.json and amendments)
   - Stage75F failed to resolve TF-specific signal at 57-91 query regions (same freeze, amendment 2)
   - V50 mandatory nuisance class N2E_motif_annotation_supply (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
9. **Missing controls blocking use.**
   - pinned motif collection and version
   - annotation-supply control
   - TF-label permutation control
   - GC-, CpG- and length-matched backgrounds
   - region universe frozen without the query RNA
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R5a. SCENIC+ eRegulons built on the query RNA

Candidate 5; query matching QUERY_RNA.

1. **Quantity measured.** TF-to-region-to-gene eRegulons and per-cell activities
2. **Physically independent of the query RNA?** NO: TF-to-gene importance, region-to-gene links and gene-based activity scores all use the query RNA
3. **Construction independence.** CIRCULAR: any covariance in the query RNA, biological or capture, is absorbed; a TF gene inside a capture-affected module becomes its regulator
4. **Biological specificity.** candidate networks, not causal; membership unstable without resampling controls
5. **Nuisance that can mimic it.** every query covariance, by construction
6. **Twins it can falsify.** none: none from the RNA side. Only the region-accessibility side can separate, as R1 with R1's controls
7. **Stronger twin remaining.** TW_EXACT, absorbed by construction
8. **Provenance and ETL already in the project.**
   - PR #179 (open): INCOMPLETE_STOPPED; 'Do not cite any number from this branch as evidence'
   - no SCENIC+ regulatory network exists on either route (claude/v74-authority-correction-20261004@733829c6, REMAINING_BLOCKERS)
   - V50 forbidden upgrade: 'joint integration latent agreement to independent multimodal evidence' (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
9. **Missing controls blocking use.**
   - not repairable by controls: rebuild on other data (R5b) or use the accessibility side alone (R1)
10. **Classification now:** `CIRCULAR_WITH_CURRENT_RNA`; if qualified: `CIRCULAR_WITH_CURRENT_RNA`.

### R5b. SCENIC+ eRegulons built on an independent multiome, applied to the query

Candidate 5; query matching EXTERNAL_STATIC.

1. **Quantity measured.** a network from another dataset, applied to the query as gene and region sets
2. **Physically independent of the query RNA?** PARTLY: the network comes from other nuclei; activity scores on the query are functions of the query RNA
3. **Construction independence.** LEAK_RISK: the network carries the other dataset's RNA covariance, including assay-class capture structure
4. **Biological specificity.** as R5a, plus transfer across datasets, regions and chemistries
5. **Nuisance that can mimic it.** assay-class capture structure (TW_ASSAY) learned into the network; label harmonisation
6. **Twins it can falsify.** TW_MODELLED: no lineage twin (P1). Argues against TW_ASSAY only if its own region evidence couples the program to chromatin in the source dataset
7. **Stronger twin remaining.** TW_EXACT; TW_ASSAY absorbed through its RNA side; TW_PROCESS_PROGRAM
8. **Provenance and ETL already in the project.**
   - V69 Route A/B on GSE214979: pseudobulk unit donor x published microglial subcluster (Mic_0..Mic_4); microglial identity taken from the published multiome annotation; controls frozen before any eRegulon (claude/v74-authority-correction-20261004 results/v64/V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1.json)
   - GSE214979 cannot address 'independent confirmation of a network trained on all of its own data' (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
   - scenic_plus current_qualified_broad_network false; coverage NOT_YET_QUANTIFIABLE_AGAINST_FULL104 (results/v64/V68_FULL104_PRIVILEGED_EVIDENCE_COVERAGE_MAP_V1.json)
   - no network exists on either route (claude/v74-authority-correction-20261004@733829c6)
9. **Missing controls blocking use.**
   - source data independent of the query and of FULL104 exposure
   - PR #179 controls passed
   - region universe frozen
   - stability across donors and resamples
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R5c. Stage75F regulatory edges (built with Morabito RNA)

Candidate 5; query matching QUERY_RNA.

1. **Quantity measured.** regulator-to-target edges inferred with the Morabito RNA they were meant to explain
2. **Physically independent of the query RNA?** NO: built from the same RNA
3. **Construction independence.** CIRCULAR: the edges cannot be an answer key for an RNA state of the RNA that produced them
4. **Biological specificity.** candidate edges, not causal
5. **Nuisance that can mimic it.** every covariance of the Morabito RNA, by construction
6. **Twins it can falsify.** none: none
7. **Stronger twin remaining.** TW_EXACT, absorbed by construction
8. **Provenance and ETL already in the project.**
   - STAGE75F: HYPOTHESIS_GENERATING_ONLY; 10 regulators, 96 TF-target rows; HISTORICALLY_EXPOSED; cannot address independent RNA validation (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
   - V50 forbidden upgrade: 'Stage75F hypothesis to validated GRN' (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
9. **Missing controls blocking use.**
   - not repairable by controls; Morabito is also PROTECTED
10. **Classification now:** `CIRCULAR_WITH_CURRENT_RNA`; if qualified: `CIRCULAR_WITH_CURRENT_RNA`.

### R6. Perturbation with engagement (CRISPRi/a) in an external system

Candidate 6; query matching EXTERNAL_STATIC.

1. **Quantity measured.** change in program-gene expression after perturbing a candidate regulator, against non-targeting guides in the same experiment
2. **Physically independent of the query RNA?** YES: the intervention is designed; the readout is RNA of the same assay class, and within-experiment contrasts cancel capture that does not depend on the perturbation
3. **Construction independence.** LEAK_RISK: independent unless regulators were chosen from query correlations (selection leak)
4. **Biological specificity.** high for regulator-to-gene causality in that system; lineage mismatch (iPSC microglia, macrophages), one genetic background, in vitro
5. **Nuisance that can mimic it.** perturbation-induced stress, proliferation or differentiation that shifts capture or composition; guide, MOI and Cas9 toxicity; off-target effects; weak engagement
6. **Twins it can falsify.** TW_MODELLED: no lineage twin in the query (P1). Can break TW_ASSAY: with capture held fixed the gene set responds as a regulatory unit, if engagement and off-program controls pass
7. **Stronger twin remaining.** TW_EXACT and TW_OPERATOR in the query; perturbation-keyed capture; TW_PROCESS_PROGRAM (a handling-induced program is also perturbable)
8. **Provenance and ETL already in the project.**
   - PR #77 (open): GSE301119 target engagement only; primary human macrophage, an auxiliary myeloid system
   - PR #84 (open): target-held-out benchmark machinery, synthetic-qualified; PR #90 (open): outcome-level exposure ledger
   - PR #114 (open): GSE178317 DEVELOPMENT / SAME-EXPERIMENT, 33 support-qualified targets, not independent replication
   - PR #137 (open): CRISPRbrain screens cannot be benchmark truth; joint engagement 1 of 31
   - PR #158 (open): GSE289721 QUALIFIED-FEASIBLE, PENDING GATES 1-3, not benchmark truth
   - asset class EXPOSED_PERTURBATIONAL_SUPPORT__NOT_BENCHMARK_TRUTH (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md); iPSC genotype-by-context designs GSE241858 and GSE240609 (docs/agent/JEPA_NEW_CHAT_HANDOFF_20260924_V25_RESULTS_DATA_SCRIPTS.md)
9. **Missing controls blocking use.**
   - engagement shown first
   - non-targeting and off-program controls
   - lineage match
   - capture-shift diagnostics per guide
   - regulators chosen without query outcomes
   - exposure ledger
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R7a. Spatial in situ transcriptomics from the query donors

Candidate 7; query matching SAME_DONOR.

1. **Quantity measured.** program transcripts counted in intact sections by probe hybridisation and imaging, no dissociation or droplets
2. **Physically independent of the query RNA?** PARTLY: different chemistry and no droplets; the same donors, tissue and RNA integrity
3. **Construction independence.** LEAK_RISK: cell typing by label transfer from the query RNA leaks; panels are often chosen from markers of the same atlas
4. **Biological specificity.** panel-limited (hundreds of genes), segmentation errors, region-specific
5. **Nuisance that can mimic it.** RNA integrity shared across chemistries; probe design; segmentation spill-over
6. **Twins it can falsify.** TW_EXACT, TW_OPERATOR: when the hidden process is droplet- or dissociation-specific, at donor or donor-by-cell-type resolution; also addresses the dissociation form of TW_PROCESS_PROGRAM
7. **Stronger twin remaining.** TW_ANCHOR through tissue RNA integrity moving both chemistries; agonal and postmortem forms of TW_PROCESS_PROGRAM; program genes absent from the panel
8. **Provenance and ETL already in the project.**
   - SEAAD_SPATIAL: PUBLIC_RESOURCE_NEEDS_PROJECT_AUDIT, exposure UNKNOWN_UNTIL_AUDIT (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json); inventoried spatial assets SUPPORTING_LIMITED_COVERAGE (main@7018edea docs/agent/JEPA_EXTERNAL_VALIDATION_ASSET_MATRIX_V3_DRAFT_20261006.md)
   - the homeostatic program is absent from all four panels; lipid/DAM absent in MTG, HIP and MEC, partial in CaH Xenium; microglial detection and segmentation asymmetry (docs/agent/V52_R2_R4_RECOVERY_CLOSEOUT_20260928.md)
   - the MTG MERFISH and CaH Xenium files carry protected pathology, so a firewall is required (docs/agent/JEPA_NEW_CHAT_HANDOFF_20260928_V51_REGULATORY_REDTEAM.md)
   - spatial may attack the dissociation component of N2B, subject to an access, identity and panel audit (docs/agent/V50_REGULATORY_TRIANGULATION_AND_TRANSPORT_FRAMEWORK_20260928.md)
9. **Missing controls blocking use.**
   - a same-donor spatial instance, audited
   - panels that cover the program (V52: the homeostatic program is absent from all four SEA-AD panels)
   - segmentation QC
   - RNA-integrity covariate
   - cell typing without the query RNA
   - a pathology firewall
   - exposure ledger
10. **Classification now:** `UNQUALIFIED`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R7b. Spatial in situ transcriptomics from other donors

Candidate 7; query matching EXTERNAL_STATIC.

1. **Quantity measured.** program transcripts in intact tissue of other donors
2. **Physically independent of the query RNA?** YES: other donors and chemistry
3. **Construction independence.** LEAK_RISK: as R7a
4. **Biological specificity.** as R7a, without query matching
5. **Nuisance that can mimic it.** as R7a
6. **Twins it can falsify.** TW_MODELLED: no lineage twin (P1). Can break TW_ASSAY and the dissociation form of TW_PROCESS_PROGRAM: the program exists outside droplet chemistry
7. **Stronger twin remaining.** TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ANCHOR
8. **Provenance and ETL already in the project.**
   - as R7a; spatial is supporting evidence, not a primary full-state validation axis (docs/agent/V52_R2_R4_RECOVERY_CLOSEOUT_20260928.md)
9. **Missing controls blocking use.**
   - panel coverage
   - segmentation QC
   - exposure ledger
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R8a. Query-donor genotypes with allele-resolved query RNA

Candidate 8; query matching SAME_DONOR.

1. **Quantity measured.** donor genotypes at cis variants; allele-specific expression in the query and donor-level cis effects
2. **Physically independent of the query RNA?** PARTLY: genotype is DNA; the allelic readout uses query reads, but the within-cell allele contrast cancels allele-agnostic capture
3. **Construction independence.** LEAK_RISK: variant calls from the RNA reads leak; genotypes must come from DNA or imputation
4. **Biological specificity.** cis effects at variants in the program's regulatory regions, in the program's state; needs heterozygous donors and coverage
5. **Nuisance that can mimic it.** capture-altering variants (3' UTR, poly-A signal, priming) and reference mapping bias; in 3' droplet assays observable heterozygous sites concentrate exactly where capture-altering variants act; ancestry structure
6. **Twins it can falsify.** TW_EXACT, TW_TARGET_CAPTURE: when the hidden process is allele-agnostic
7. **Stronger twin remaining.** allele-keyed capture (the TW_ANCHOR analogue); low 3' coverage; few donors
8. **Provenance and ETL already in the project.**
   - NOT_FOUND: no authorised donor-genotype access for any query cohort in the receipts searched; the genotype records found are iPSC designs (GSE241858 TREM2 R47H, GSE240609 APOE), which are external systems (R6)
9. **Missing controls blocking use.**
   - authorised genotype access
   - mapping-bias control
   - exclusion of capture-altering variants
   - power at the donor count
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R8b. External eQTL and caQTL catalogues

Candidate 8; query matching EXTERNAL_STATIC.

1. **Quantity measured.** genotype-dependent expression or accessibility in other cohorts
2. **Physically independent of the query RNA?** YES: other cohorts
3. **Construction independence.** INDEPENDENT: no query RNA; catalogues discovered in droplet single-cell RNA inherit that assay class's capture structure, including capture-altering variants (TW_ASSAY)
4. **Biological specificity.** tissue or cell-type level; linkage disequilibrium blurs the causal variant
5. **Nuisance that can mimic it.** capture-altering variants in the source cohorts; tissue composition
6. **Twins it can falsify.** TW_MODELLED: no lineage twin (P1)
7. **Stronger twin remaining.** TW_EXACT and every query twin
8. **Provenance and ETL already in the project.**
   - NOT_FOUND: no eQTL or caQTL catalogue acquired in the receipts searched. Downloadable is not licensed or acquired
9. **Missing controls blocking use.**
   - licensing and exposure
   - composition-aware matching
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R9a. Spike-ins or external RNA standards in the query libraries

Candidate 9; query matching SAME_LIBRARY.

1. **Quantity measured.** recovered counts of exogenous RNA of known input: capture efficiency per cell or library
2. **Physically independent of the query RNA?** PARTLY: an exogenous molecule measured by the same assay, which is the point
3. **Construction independence.** INDEPENDENT: known input amounts
4. **Biological specificity.** global or batch capture, not gene-specific nuclear capture; spike-ins never enter nuclei
5. **Nuisance that can mimic it.** spike-in sequence and structure differ from endogenous transcripts; dosing variance
6. **Twins it can falsify.** TW_OPERATOR: supplies the measured capture covariate that V47 and S157 showed is needed, when the operator's bias is visible to spike-ins
7. **Stronger twin remaining.** TW_EXACT with gene-specific, state-linked capture that spike-ins do not report
8. **Provenance and ETL already in the project.**
   - NOT_FOUND: no spike-in or external RNA standard in the query libraries in the receipts searched
9. **Missing controls blocking use.**
   - spike-ins present in the query libraries
   - per-library calibration
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R9b. Library descriptors derived from the query RNA (depth, measurable-address count, zero fraction)

Candidate 9; query matching QUERY_RNA.

1. **Quantity measured.** summaries of the query RNA and its support
2. **Physically independent of the query RNA?** NO: functions of the query RNA
3. **Construction independence.** CIRCULAR: computed from the query
4. **Biological specificity.** none
5. **Nuisance that can mimic it.** not applicable
6. **Twins it can falsify.** none: none: S157 T3, NOT_SEPARATED under depth, support and both; the measurable-address count is an identity proxy (S157 T4)
7. **Stronger twin remaining.** TW_OPERATOR and TW_EXACT stay
8. **Provenance and ETL already in the project.**
   - results/v77/V77_S157_CONTEXT_ABLATION_SUMMARY_V1.json (T3); results/v77/V77_S157_PAIRED_CHALLENGE_SCORE_ARMS_V1.json (T4, the 0.956 lookup)
   - V50 mandatory nuisance class N2H_feature_support_artifact (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
9. **Missing controls blocking use.**
   - not repairable by controls
10. **Classification now:** `CIRCULAR_WITH_CURRENT_RNA`; if qualified: `CIRCULAR_WITH_CURRENT_RNA`.

### R9c. Protocol metadata and raw source or operator identity

Candidate 9; query matching SAME_LIBRARY.

1. **Quantity measured.** dataset, chemistry, lab and batch identity
2. **Physically independent of the query RNA?** YES: metadata, not a process measurement
3. **Construction independence.** INDEPENDENT: identity, not values
4. **Biological specificity.** none; it names the operator
5. **Nuisance that can mimic it.** biology confounded with study composition (S149): adjusting identity removes real biology where biology differs by study
6. **Twins it can falsify.** TW_OPERATOR: S157 ARM3 cut the operator nuisance from 0.872 to 0.374, as an EXPLORATORY POSITIVE CONTROL only (T2)
7. **Stronger twin remaining.** TW_EXACT; biology confounded with study
8. **Provenance and ETL already in the project.**
   - S157 ARM3 (results/v77/V77_S157_PAIRED_CHALLENGE_SCORE_ARMS_V1.json); register addendum 2; bridge OBSERVATION_CONTEXT_RESTRICTION
   - V50 mandatory nuisance class N2G_source_lab_fingerprint (docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json)
9. **Missing controls blocking use.**
   - restricted from production inputs by decision (S157 T2, addendum 2)
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R9d. Donor and sample process covariates (postmortem interval, agonal state, RNA integrity, handling time)

Candidate 9; query matching SAME_DONOR.

1. **Quantity measured.** recorded handling and tissue-state variables of the query donors and samples
2. **Physically independent of the query RNA?** YES: recorded independently of the RNA values
3. **Construction independence.** INDEPENDENT: metadata; must not include pathology labels
4. **Biological specificity.** donor or sample level; confounded with disease course and age
5. **Nuisance that can mimic it.** disease course drives agonal state; cohort-specific recording
6. **Twins it can falsify.** none: no lineage twin. The only object here aimed at TW_PROCESS_PROGRAM, and a weak one: V49 found the exAM signature does not track recorded PMI
7. **Stronger twin remaining.** TW_EXACT, TW_OPERATOR
8. **Provenance and ETL already in the project.**
   - covariates recorded for at least one cohort include age, sex, PMI, cohort, batch, brain bank, race and ancestry (docs/agent/JEPA_NEW_CHAT_HANDOFF_20260929_V64_SINGLE_SOURCE_E2.md)
   - the exAM signature does not correlate with recorded PMI (docs/agent/V49_SNRNA_UNDERDETECTS_TWO_OF_OUR_THREE_PROGRAMS_20260928.md); handling induces chromatin changes not captured by PMI (docs/agent/V50_REGULATORY_TRIANGULATION_AND_TRANSPORT_FRAMEWORK_20260928.md, N2B)
9. **Missing controls blocking use.**
   - covariate availability and authorisation
   - separation from pathology labels
10. **Classification now:** `SUPPORTIVE_BUT_NOT_IDENTIFYING`; if qualified: `SUPPORTIVE_BUT_NOT_IDENTIFYING`.

### R10a. Protein in the same cells or nuclei (antibody-derived tags)

Candidate 10; query matching SAME_CELL.

1. **Quantity measured.** antibody-derived tag counts for program proteins in the same cell or nucleus
2. **Physically independent of the query RNA?** PARTLY: a different molecule and library; the same droplet; nuclear proteins only for nuclei
3. **Construction independence.** LEAK_RISK: panels chosen from RNA markers
4. **Biological specificity.** RNA-protein coupling varies; antibody specificity
5. **Nuisance that can mimic it.** non-specific binding scaling with cell or nucleus size; droplet quality; ambient tags
6. **Twins it can falsify.** TW_EXACT, TW_OPERATOR: when the hidden process is confined to the RNA library, at cell level
7. **Stronger twin remaining.** TW_ANCHOR through size or quality moving tags and RNA; poor RNA-protein coupling
8. **Provenance and ETL already in the project.**
   - NOT_FOUND for query cells; the CITE-seq records found are CRISPRbrain iPSC microglia screens (docs/agent/JEPA_RUNTIME_ASSET_MANIFEST_20260924_V25.md), external and not benchmark truth (PR #137)
9. **Missing controls blocking use.**
   - an instance for brain nuclei
   - isotype and ambient-tag controls
   - quality covariates
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

### R10b. Donor-level proteomics of the query donors

Candidate 10; query matching SAME_DONOR.

1. **Quantity measured.** bulk protein abundance per donor
2. **Physically independent of the query RNA?** YES: other molecule and lab; shared tissue
3. **Construction independence.** INDEPENDENT: no query RNA
4. **Biological specificity.** donor level and composition-dominated
5. **Nuisance that can mimic it.** tissue quality, composition, postmortem interval
6. **Twins it can falsify.** TW_EXACT, TW_OPERATOR: at donor resolution, when the hidden process is library-level
7. **Stronger twin remaining.** composition; tissue quality (donor-level TW_ANCHOR)
8. **Provenance and ETL already in the project.**
   - NOT_FOUND: no proteomics of query donors in the receipts searched
9. **Missing controls blocking use.**
   - a donor-matched instance
   - composition deconvolution
   - exposure ledger
10. **Classification now:** `PROTECTED_OR_NOT_AVAILABLE`; if qualified: `CAN_BREAK_A_SPECIFIC_TWIN`.

## Older statements this narrows (marked, not rewritten)

| Where | Statement | Narrowed to |
|---|---|---|
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Same-nucleus chromatin accessibility) | e.g. SEA-AD public exact pairing, GSE272082 | GSE272082 is PAIRED_BY_DESIGN with pairing and microglia census not yet authenticated, as the audit-successor lane recorded first (e966e05b); the verified same-nucleus instances are the SEA-AD public multiome pairing and GSE214979, the latter CONDITIONAL (R1) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Cell-type enhancer-promoter interactome (Nott)) | T1 if the program's genes are wired to cell-type-specific enhancers that a capture artefact would not explain | no lineage twin: the map is identical in BIO and TW_EXACT (P1). With matched controls it can reject modelled nuisances whose gene membership is not organised by cell-type wiring: the V63 E2 classes, TW_PROPERTY (R3) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, SCENIC+ eRegulons) | T1 or T2 only when built on independent data and its region evidence carries the weight | built on independent data it is static with respect to the query and breaks no lineage twin there (R5b); region evidence carries weight only when measured in the query's own nuclei (R1); built on the query RNA it is circular (R5a) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Perturbation with qualified engagement) | T1 and T2: a capture artefact should not follow knock-down of the program's regulator | in an external system the response is static with respect to the query: it can break an assay-class artefact (TW_ASSAY), not the query's TW_EXACT or TW_OPERATOR (R6) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Spatial in situ transcriptomics) | T2 and a droplet-specific T1: a dissociation or droplet capture artefact should not survive a different chemistry in intact tissue | holds for spatial data from the query's own donors only (R7a); spatial data from other donors are supportive (R7b) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Genetics) | T1, except for capture-altering variants | holds for query-donor genotypes with allele-resolved query RNA (R8a), where 3' assays put the observable sites where capture-altering variants act; external eQTL catalogues are supportive (R8b) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Separate-nucleus or donor-level chromatin) | T1 at donor level: a cell-level capture artefact should not reappear in separate nuclei | holds for the query's own donors only (R2a); other cohorts are supportive (R2c); Morabito is protected (R2b) |
| docs/agent/V77_S157_MULTIMODAL_HANDOFF_REQUIREMENTS.md (b1d8ca9f, Protein-level measurement) | T1, if the program's proteins rise with its RNA in that state | holds for the same cells or the query's own donors only (R10a, R10b) |

## What this does not do

- select or rank any evidence object
- open protected data (Morabito, DS010, DEV, SEALED, TEST)
- read any real outcome
- train, mutate or touch runtime code
- set a threshold: no number here admits or rejects an object
