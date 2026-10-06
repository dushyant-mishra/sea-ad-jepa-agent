# JEPA external-validation asset matrix — V3 draft

Date: 2026-10-06
Status: `DRAFT_FROM_EXISTING_AUDITS__NO_TARGET_SELECTION_USE`

Purpose: consolidate already-audited external assets against the claim ladder without repeating completed work. This draft is based on repository audits/PRs #188-#199 and related authenticated lanes. Missing facts remain explicit.

No asset in this table is authorized for target selection by this document.

## Claim transitions

- R1: `RNA_REPRESENTATION -> TRANSFERABLE_BIOLOGICAL_STATE`
- R2: `TRANSFERABLE_BIOLOGICAL_STATE -> REGULATORY_SUPPORT`
- R3: `REGULATORY_SUPPORT -> CAUSAL_PERTURBATIONAL_PREDICTION`

Observational multimodal association cannot by itself close R3.

## Matrix

| Asset | Modality / unit | Pairing | Exposure / protection | Independence and defects | Potential lawful role | Cannot establish | Current classification |
|---|---|---|---|---|---|---|---|
| GSE174367 / Morabito | separate-nucleus RNA/ATAC; donor-level evidence | **SEPARATE NUCLEI** in prior audit | heavily exposed; explicitly protected from selection | donor-level only; not same-cell evidence; prior project exposure means not pristine | later held-out/supporting transport or regulatory evidence after target freeze, under separate authority | target selection; pristine independent confirmation; same-cell state correspondence; causality | `PROTECTED_NOT_AVAILABLE_FOR_SELECTION` |
| GSE214979 | paired 10x multiome; 105,332 nuclei, 15 donors in prior audit | **VERIFIED SAME-NUCLEUS RNA+ATAC** across audited rows | historically unexposed at time of authentication | two donors had sex/age and region conflicts consistent with a possible pooled-lane label swap; donor assignment inferred by demultiplexing; effective donor count is small | paired same-nucleus regulatory/representation support after prospectively frozen exclusions and target | realistic small AD donor effects; causal effects; pristine claim if exposure changes | `CONDITIONAL_EXTERNAL_SUPPORT` |
| GSE214637 | SuperSeries container for GSE214979/GSE214911 | not a separate cohort | not an independent dataset | container; using it as a second cohort would duplicate GSE214979 | provenance/navigation only | replication | `NOT_A_SEPARATE_DATASET` |
| GSE272082 | paired multiome by construction; prior audit reconstructed 9 donors / 21 region-libraries | format suggests paired, matrix-level pairing not fully verified in cited audit | historically unexposed at time of audit | microglia census/annotation unresolved in deposit; disease-label title/characteristic contradictions reported; small n | possible later study/technology transport after required authentication | current microglia-specific confirmation; robust donor-level disease effect; causality | `NEEDS_AUTHENTICATION` |
| SEA-AD processed snRNA/snATAC/spatial | public processed modalities; large project cohort | exact same-cell relationship depends on specific product; not assumed | extensively used/exposed within project | development exposure is load-bearing; some raw/IAC resources controlled; public processed data are not automatically independent | supporting transport, modality and population coverage; source-specific stress tests after freeze | pristine independent validation; causality | `DEVELOPMENT_EXPOSED_SUPPORTING_ASSET` |
| GSE173316 / Yang candidate external cis resource | public GEO series audited in V63 | not a JEPA same-cell pairing object | external candidate | audited RAW tar contained RSEM and CRISPR matrices; expected public pcHi-C interactions were not located | none until the claimed regulatory object is physically located/authenticated | regulatory-map confirmation from an unlocated artifact | `ARTIFACT_UNLOCATED` |
| DS010 / GSE308668-GSE308906 family | intended regulatory/contact + companion multiome resource | unresolved because data unavailable | embargoed/private in prior audit; development exposure status separately recorded | exact companion relationship could not be publicly resolved | future only after public release and re-authentication | current validation or target selection | `BLOCKED_BY_EMBARGO` |
| Nott Table S5 / related microglia regulatory resource | external regulatory/cis reference | not same-cell JEPA data | external source; retrieval had been blocked in one audit environment, later project custody may exist and must be checked before reacquisition | use exact authenticated table/version only; do not infer availability from historical retrieval failures | independent regulatory support after target freeze if current authenticated custody and mapping are verified | causal prediction by itself; target selection if used during development | `REQUIRES_CURRENT_CUSTODY_RECHECK` |
| Kosoy microglia regulome resources | mixed regulatory/multiomic resources | varies by product | access class mixed: some processed open-distribution; individual/raw access-governed | exact product and exposure must be named; cannot treat family name as one dataset | possible regulatory/study transport for an explicitly authenticated product | generic independent validation claim across the whole resource family | `PRODUCT_SPECIFIC__UNKNOWN_REQUIRES_AUDIT` |
| CRISPRbrain / perturbation screens | perturbational screens across microglia/neuron contexts | intervention-level, not same-cell multimodal | extensively audited/ETL-exposed within project | heterogeneous screens, target engagement and mapping limitations; historical conclusion: not benchmark truth | later causal/perturbational support under explicit per-screen reliability and exposure rules | pristine benchmark truth; direct target-selection authority | `EXPOSED_PERTURBATIONAL_SUPPORT__NOT_BENCHMARK_TRUTH` |
| Spatial datasets already inventoried in project | limited-panel spatial expression | spatial units, not same-cell full 41K | exposed/supporting | limited gene/program coverage and segmentation/detection limitations in historical audits | localization/supporting evidence for covered programs | full-state validation or 41K completeness | `SUPPORTING_LIMITED_COVERAGE` |

## Binding rules

1. **Exposure and access are different axes.** An asset can be public but heavily development-exposed, or inaccessible but already conceptually exposed.
2. **External does not mean independent.** Independence must be stated relative to FULL104, target construction, study/donor overlap and development exposure.
3. **Same-nucleus pairing is a distinct evidence class.** It must not be inferred from the word `multiome`; it requires physical/barcode/row-level authentication appropriate to the product.
4. **Separate-nucleus evidence is donor-level evidence.** Do not promote it to same-cell correspondence.
5. **Small donor n cannot be rescued by many cells.** Biological inference remains limited by donors.
6. **Previously exposed assets are not pristine confirmation.** They may still be valid supporting/transport evidence if their role is frozen prospectively.
7. **Morabito is protected.** It is unavailable for target/representation selection.
8. **Observational regulatory association is not causality.** R2 evidence cannot automatically close R3.
9. **Unknown facts remain unknown.** Do not replace `UNKNOWN_REQUIRES_AUDIT`, `ARTIFACT_UNLOCATED`, or embargo with assumptions.
10. **Use exact products, not family names.** Resource families such as SEA-AD, Kosoy, ROSMAP or DS010 can contain products with different access, pairing and exposure states.

## Required fields before an asset is used in a deciding external transition

- exact accession/product/version;
- physical data identity and digest where feasible;
- biological-unit count;
- pairing state;
- source/study/donor overlap assessment;
- prior development exposure;
- protected/sealed status;
- access class;
- target-selection prohibition status;
- claim transition requested;
- confounders/identity defects;
- predeclared exclusions;
- held-out evaluation rule;
- provenance grade.

## Non-authority statement

This matrix does not authorize opening any protected outcome, does not select a target/representation and does not promote any asset to independent validation merely by listing it.

`TRAINING=OFF`; Stage A remains prefreeze only; Morabito remains protected; TEST remains sealed.
