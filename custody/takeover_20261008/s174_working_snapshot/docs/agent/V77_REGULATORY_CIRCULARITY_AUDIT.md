# V77 SCENIC+ and regulatory-evidence circularity audit

**Status:** ANALYSIS_ONLY. Classifies constructions; selects no evidence object, network, target or threshold

**Question:** Can regulatory evidence tell true regulatory biology from a capture or measurement process that generates the same RNA covariance? Answered separately for (a) SCENIC+ built partly from the same RNA, (b) SCENIC+ built with independent chromatin plus RNA, and (c) links supported by evidence physically independent of the query RNA

**Answer:** (a) is circular with the query RNA; (b) is circular with the assay class and static with respect to the query; (c) is static. None can break a lineage twin in the query. Only measurements on the query's own nuclei, cells or donors can: among available objects the matrix's R1, R2a and R7a (R8a and R10a are not available), not SCENIC+ as such. No SCENIC+ network exists in the project yet

## Circularity classes

| Class | Meaning |
|---|---|
| C0_QUERY_MATCHED_INDEPENDENT | measured on the query's own nuclei, cells or donors and constructed without the query RNA; can change the likelihood ratio between biology and a lineage twin, given its controls |
| C1_STATIC_INDEPENDENT | constructed without any RNA of the query and fixed with respect to it; supportive only (matrix P1) |
| C2_ASSAY_CLASS_CIRCULAR | constructed from other RNA of the same assay class; not circular with the query values, but it absorbs whatever artefact the assay class produces everywhere (TW_ASSAY) |
| C3_QUERY_CIRCULAR | constructed from the query RNA; any agreement with the query's covariance is guaranteed |

SELECTION_COUPLED: constructed without RNA values but selected on expression or activity (active promoters, H3K27ac enhancers, regulators chosen from query correlations, panels chosen from RNA markers). A modifier, not a class: it needs selection-matched controls and is never counted as independent of expression

## Where the query RNA enters a SCENIC+-style pipeline

| Step | Query RNA | Consequence |
|---|---|---|
| S1 cell grouping for chromatin (metacells, pseudobulks, labels) | LEAKS if labels or metacells come from the query RNA, including joint RNA-ATAC embeddings | peaks, topics and differential regions inherit the RNA's partition, biological or not |
| S2 peak calling and consensus region universe (iterative overlap, blacklist) | LEAKS when pseudobulks are RNA-defined; independent when groups come from chromatin alone | the region universe itself encodes the RNA partition |
| S3 topics and differentially accessible regions | chromatin only, unless contrasts are between RNA-defined groups | region sets selected by RNA contrasts are RNA-derived |
| S4 motif enrichment (cisTarget rankings, differential motif enrichment) | sequence only; inherits S3's region sets | annotation supply and GC structure need the PR #179 controls |
| S5 TF-to-gene importance (gradient boosting on expression) | USES the RNA directly | a TF gene inside a capture-affected module becomes its regulator |
| S6 region-to-gene importance (accessibility against expression across cells or metacells) | USES the RNA; with unpaired data the pairing itself comes from RNA-derived integration | the only step where independent same-nucleus chromatin can disagree with an RNA-confined twin; with unpaired data it is circular |
| S7 eRegulon assembly (TF to motif-bearing regions to linked genes, sign filters) | combines S4 to S6; sign filters use TF-gene correlation in the RNA | membership mixes circular and independent evidence without separating them |
| S8 activity scoring (gene-based AUC on RNA, region-based AUC on chromatin) | gene-based scores are functions of the query RNA | identical under TW_EXACT; region-based scores are per-nucleus chromatin (the R1 object) |
| S9 triplet ranking and specificity scores | uses S5, S6 and S8 | rankings inherit every leak above |

## The three settings

### A_SAME_RNA: SCENIC+ built partly from the same RNA being explained

- **Circularity class:** `C3_QUERY_CIRCULAR`; verdict `CIRCULAR_WITH_CURRENT_RNA`; matrix rows R5a, R5c.
- **Can it tell regulation from a capture process producing the same RNA covariance?** No, from the RNA side: S5, S6's RNA input, S8 gene-based and S9 are functions of the query RNA, identical under TW_EXACT. The only discriminating content is per-nucleus accessibility (S1 to S4 and region-based S8) when it is same-nucleus and built without the RNA; that is the R1 object, and it should be tested as R1 directly, with R1's controls, not through eRegulon presence, which mixes it with circular evidence. With unpaired chromatin the S6 pairing is RNA-derived, so nothing escapes the circularity
- **Twins it can break:** none. **Twins it absorbs or passes:** TW_EXACT, TW_OPERATOR, TW_TARGET_CAPTURE, TW_ASSAY, TW_PROPERTY.

### B_INDEPENDENT_CHROMATIN_PLUS_RNA: SCENIC+ built with independent chromatin plus RNA (another dataset), applied to the query

- **Circularity class:** `C2_ASSAY_CLASS_CIRCULAR`; verdict `SUPPORTIVE_BUT_NOT_IDENTIFYING`; matrix rows R5b.
- **Can it tell regulation from a capture process producing the same RNA covariance?** No lineage twin: the network is fixed with respect to the query (P1), and its activity on the query is a function of the query RNA. Its own RNA side absorbs the source dataset's covariance, including any assay-class capture structure. It can argue against TW_ASSAY only where its region evidence shows the program coupled to chromatin in the source dataset
- **Twins it can break:** none. **Twins it absorbs or passes:** TW_ASSAY.

### C_PHYSICALLY_INDEPENDENT_LINKS: regulatory links supported by evidence physically independent of the query RNA: motif sequence, enhancer-promoter contacts, histone marks, perturbation responses, eQTL and caQTL

- **Circularity class:** `C1_STATIC_INDEPENDENT`; verdict `SUPPORTIVE_BUT_NOT_IDENTIFYING`; matrix rows R3, R4, R6, R8b.
- **Can it tell regulation from a capture process producing the same RNA covariance?** Not against a twin acting on the same genes: a fixed link set takes the same value whichever process generated the query RNA. It can reject nuisances whose gene membership it predicts differently (V63 E2 classes, TW_PROPERTY) given matched controls, but V63 Task 8 failed on a latent capture factor correlated with the target, and an anchor-keyed nuisance passed unless anchor frequency was matched. A handling-induced program (TW_PROCESS_PROGRAM) is genuine regulation and passes every link test
- **Twins it can break:** TW_MODELLED, TW_PROPERTY. **Twins it absorbs or passes:** TW_PROCESS_PROGRAM.

## Not only ATAC

| Evidence | Circularity class | Selection-coupled | Matrix row | Note |
|---|---|---|---|---|
| enhancer-promoter contacts (Nott PLAC-seq) | C1_STATIC_INDEPENDENT | yes | R3 |  |
| TF motifs and cisTarget rankings | C1_STATIC_INDEPENDENT | no | R4 |  |
| perturbation responses in an external system | C1_STATIC_INDEPENDENT | yes | R6 |  |
| external eQTL and caQTL catalogues | C2_ASSAY_CLASS_CIRCULAR | no | R8b | discovered on RNA of other cohorts; capture-altering variants in those cohorts are absorbed |
| query-donor genotypes with allele-resolved query RNA | C0_QUERY_MATCHED_INDEPENDENT | no | R8a |  |
| same-nucleus accessibility at a region universe fixed without RNA | C0_QUERY_MATCHED_INDEPENDENT | no | R1 |  |
| spatial in situ data from the query donors | C0_QUERY_MATCHED_INDEPENDENT | yes | R7a |  |
| protein in the same cells or the query donors | C0_QUERY_MATCHED_INDEPENDENT | yes | R10a |  |
| donor and sample handling covariates | C0_QUERY_MATCHED_INDEPENDENT | no | R9d | breaks no lineage twin; the only object addressing TW_PROCESS_PROGRAM |

## Project evidence folded in

| Evidence | Where | Status | Bearing on circularity |
|---|---|---|---|
| PR #179 SCENIC+ recovery and expansion | PR #179 (open), agent-4/scenicplus-recovery-expansion-20260926 | INCOMPLETE_STOPPED: 'Do not cite any number from this branch as evidence' | no citable SCENIC+ result exists; nothing here can be counted as regulatory support |
| Stage75F edges | docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json | HYPOTHESIS_GENERATING_ONLY; 10 regulators, 96 TF-target rows; HISTORICALLY_EXPOSED; forbidden upgrade 'Stage75F hypothesis to validated GRN' | setting A for Morabito RNA (C3), and Morabito is protected |
| V50 forbidden upgrades | docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json | 'joint integration latent agreement to independent multimodal evidence'; 'same-nucleus agreement to independent cohort replication' | project law already forbids reading joint-embedding agreement as independent evidence (pipeline step S1) |
| GSE214979 in the V50 map | docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json | AUTHENTICATED_WITH_FROZEN_EXCLUSIONS; cannot address 'independent confirmation of a network trained on all of its own data' | setting A in GSE214979's own frame; setting B for any other query |
| V69 Route A/B prospective freeze on GSE214979 | claude/v74-authority-correction-20261004: results/v64/V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1.json (500a8cfd) and amendments 1-2 | pseudobulk unit donor x published microglial subcluster (Mic_0..Mic_4); 'microglial identity is taken from the published multiome annotation and cannot be re-derived from ATAC alone without circularity'; no recurrence filter on the universe 'because filtering regions by recurrence and then measuring recurrence would be circular'; TF-label permutation within annotation-supply strata, donor-fingerprint and broad-class controls frozen before any eRegulon | OPEN QUESTION: how the depositor derived Mic_0..Mic_4 is not recorded in the receipts read. If from RNA or a joint embedding, the Route-B region universe inherits the RNA partition (steps S1 and S2) for any test on the same nuclei. The freeze avoided ATAC-only circularity by accepting this dependence |
| Stage-4 synthetic qualification preserved by the V69 freeze | claude/v74-authority-correction-20261004: same freeze, SECTION_9 stage4_hidden_confound_preservation | planted biology Delta ~ +0.785; hidden within-donor metacell-varying technical confound Delta ~ +0.654; control-vs-control ~ 0 | the project's own synthetic already shows a hidden technical confound scoring close to planted biology on a regulatory-correspondence criterion (the TW_TARGET_CAPTURE pattern). V69's point that an external network has a DIFFERENT failure mode is consistent with this audit: setting B fails by absorbing the assay class (C2) rather than the query's own covariance (C3). A different failure mode is not identification |
| V74 reconciliation | claude/v74-authority-correction-20261004@733829c6 results/v74/V74_MACHA_RECONCILIATION_AUTHORITY_V1.json | Route-B fragment replay REPRODUCED_ON_RECONCILED_HEAD; blacklist ENCFF356LFX AUTHENTICATED_AND_BOUND; REMAINING_BLOCKERS: 'no SCENIC+ regulatory network exists on either route' | infrastructure only; there is no network yet, so this audit classifies constructions, not results |
| V68 coverage map | results/v64/V68_FULL104_PRIVILEGED_EVIDENCE_COVERAGE_MAP_V1.json | scenic_plus current_qualified_broad_network false; NOT_YET_QUANTIFIABLE_AGAINST_FULL104 | no qualified network to transport to FULL104 |
| V50 nuisance class N2B handling/exAM | docs/agent/V50_REGULATORY_TRIANGULATION_AND_TRANSPORT_FRAMEWORK_20260928.md | 'Handling induces apparent activation/homeostatic loss and chromatin changes not captured by PMI' | chromatin evidence cannot separate a handling-induced program (TW_PROCESS_PROGRAM); every setting passes it |
| V49 exAM and PMI | docs/agent/V49_SNRNA_UNDERDETECTS_TWO_OF_OUR_THREE_PROGRAMS_20260928.md | the exAM signature does not correlate with recorded PMI | recorded handling variables are a weak handle on TW_PROCESS_PROGRAM |
| V50 nuisance class N2E motif annotation supply | docs/agent/V50_REGULATORY_INDEPENDENCE_MAP_20260928.json | mandatory nuisance class | the motif step (S4) needs the supply-stratified TF-label permutation that V69 froze |
| Stage75F motif power | claude/v74-authority-correction-20261004: V69 freeze amendment 2 | Stage75F failed to resolve TF-specific signal at 57-91 query regions on this tissue and motif collection | motif evidence on small region sets is underpowered as well as static |
| Nott S5 re-authentication | handoff/jepa-20261006-macha-audit-successor@b1382ab4 docs/agent/JEPA_NOTT_TABLE_S5_REAUTH_AND_CELLTYPE_CONTACT_SPECIFICITY_20261006.md | 'Exact-edge specificity can reflect both biology and interaction-calling power/assay properties'; 'Nott contacts remain physical wiring evidence, not activity, causality, or state-specific expression evidence' | setting C, static: supportive only |
| V63 E2 and Task 8 | results/v63/V63_E2_IDENTIFIABILITY_BENCHMARK_V1.json; docs/agent/V63_TASK8_TOURNAMENT_RESULT_20260929.md | E2: ALL_TESTED_NEGATIVES_REJECTED, NEG5 NON_IDENTIFIABLE_BY_DESIGN; Task 8: gate_may_proceed false on FAIL__TECH; anchor family fails without anchor-frequency matching | the empirical limits of setting C |
| same-nucleus instances | handoff/jepa-20261006-macha-audit-successor@e966e05b; main@7018edea asset matrix V3 | GSE214979 VERIFIED_SAME_NUCLEUS_PAIRING__CONDITIONAL; GSE272082 NEEDS_AUTHENTICATION; SEA-AD public multiome PAIRING_QUALIFIED_BIOLOGICAL_OUTCOME_UNOPENED | the only route out of setting A's circularity is the region side measured in these nuclei (R1) |
| V77 S157 terminal | results/v77/V77_S157_TERMINAL_RECEIPT_V1.json | T1: the exact same-assay twin is observationally indistinguishable from RNA | anything computed from the query RNA alone, eRegulon activity included, is identical under TW_EXACT |

## What any use of SCENIC+ as discriminating evidence would require (not a decision)

- use only the region side measured in the query's own nuclei, tested as R1 rather than through eRegulon presence
- cell groupings, the region universe and differential contrasts built from chromatin alone, frozen before outcomes
- a region-to-gene rule fixed in advance (distance or external contacts), never fitted on the query RNA
- the PR #179 controls: annotation supply and TF-label permutation
- a planted nucleus-quality-keyed control for TW_ANCHOR
- handling covariates for TW_PROCESS_PROGRAM
- donor-level inference; exposure-ledger entries before any outcome is read

## What this does not do

- build, run or select any network
- open protected data (Morabito, DS010, DEV, SEALED, TEST)
- read any real outcome
- train, mutate or touch runtime code
