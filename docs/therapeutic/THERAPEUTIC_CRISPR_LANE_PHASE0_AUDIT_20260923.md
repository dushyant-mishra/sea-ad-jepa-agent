# Therapeutic CRISPR lane: historical audit and Phase-0 contract (2026-09-23)

**Status:** METADATA_ONLY / NO NEW RNA READ / NO JEPA TRAINING / NO THERAPEUTIC CLAIM.

This lane is separate from the V5 FULL104 scientific-authority, N1, rare-tail and TD60 branches. Branch parent is main c8898923fc10ffa5ef0662b04908b0d94bcb158b. The newer V19 handoff lives at d565f37714a79195844336977852fc0921b2d087 and is a read-only dependency here, not ancestry to merge. Live PR69 reports a canonical source derivative pending independent review; PR70 reports native Windows gateway test closure. They are parallel and do not authorize training.

## Historical material audited

Sources: START_HERE.md; docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md; docs/v4/STAGE81A1C_P_PERTURBATION.md; docs/v4/PRE_STAGE81A2_HARMONIZATION.md; docs/v4/STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md; results/v4/stage81a1c_p_{acquisition_report.json,download_hashes.csv,perturbation_identity_registry.csv,seurat_object_audit.csv}; results/v4/pre_stage81a2_perturbation_readiness_registry.csv; docs/external_perturbation_benchmarks.md; scripts/benchmark_kampmann_deg_alignment.py; results/tables/kampmann_deg_jepa_alignment_{input_erasure,predictive}.csv; Stage74 and Stage77 perturbation reports; Stage47-49 drug tables; September 23 V19 handoff; prior project conversation and uploaded historical handoffs.

**Already audited acquisition, not training readiness:** Stage81A1C-P records eight official GEO studies and 16 processed, historical hash/format-verified assets. All 16 are explicitly perturbation_training_ready=False in pre-Stage81A2. The acquisition report says no controller trained, no model trained, no raw sequencing/microscopy downloaded and no pathology values used. A historical checksum receipt does not establish that the corresponding bytes currently reside on the GPU laptop.

**GSE301119 is first engineering study, not adult-microglia validation:** The audited CRISPRa Seurat object has 23,584 cells/19,162 features; CRISPRi has 28,466 cells/36,601 features; each reports 207 target genes, two donors, audited guide/NT-control metadata. Explicit Ensembl/source-feature alignment and distinct measurement masks remain blockers, and two donors do not establish broad transport.

**GSE178317 is microglial calibration after guide qualification:** Four GEX and matched sgRNA enrichment lanes were acquired. The final per-cell assignment is not the downloaded RNA feature matrix; reconstruct/validate the author-defined guide-calling join, or use published target DEG vectors strictly as supporting evidence. Do not invent target assignments. It is already a historical development source, not a clean validation holdout.

**Other source roles, requiring independent readiness:** GSE175721, engineered organoid microglia in amyloid context, is a conditional validation candidate if a prior-use/leakage audit permits; GSE293118 HMC3 noncoding CRISPRi is regulatory stress; GSE311359 iPSC microglia MS-risk CRISPRi is context stress; GSE254205 APOE/genotype/amyloid/compound-treatment data are possible later genetic–chemical bridging material, not guide-labelled pooled CRISPR; GSE241858 and GSE240609 are bulk isogenic genotype/context comparisons. Historical 1,989,578-cell K562 GWPS is engineering data, not adult microglia biology.

**Historical negative/partial intervention tests must remain in scope:** The prior flat-vector JEPA vs published GSE178317 DEG table gave poor agreement for CSF1R, TGFBR2 and CDK8 and partial agreement for CDK12. The archived method computes log1p-normalized baseline gene means and then multiplies them by 2^log2FC; this is a scale-mixing implementation problem. These results are historical diagnostics, NOT calibrated biological effect-size estimates and NOT V5 architecture authority. Stage74 reports no causal validation. Stage77 runs only synthetic one-hop expression perturbations with no JEPA inference and clips 2,642 of 8,000 compared input values (33%); do not reinterpret it as measured gene control, disease reversal or therapy.

**Historical drug tables are hypothesis-only:** Stage47's candidate/drug rows have no validated drug compounds or directions. Stage49 ChEMBL broad target-search metadata includes APOE rows pointing to Apolipoprotein B and other unrelated targets, so substring/description matches are forbidden as compound–target evidence. MorphOptim/JUMP morphology is external method inspiration; its 259 features and U2OS context are not directly comparable to our RNA state, and no JUMP Cell Painting image corpus appears in the 16 acquired studies.

**Foundation boundary:** FULL104 (4,553,407 cells, 104 donors, 42 operators) and candidate VALUE_ONLY_256 are distinct from experimental perturbations. Stage81A3 TRAIN-cache, 50K discovery, historical PCA160 and v3 JEPA checkpoint are not V5 training or biological-authority substitutes. V19's TD60, rare-tail molecular, protected/pathology, D_shared and N1 outcomes remain unopened; current training stays OFF.

## Phase 0 — newly implemented metadata gate

A standalone standard-library read-only script, scripts/therapeutic/audit_legacy_perturbation_inventory.py, compares the four existing acquisition/readiness/Seurat metadata inputs. It verifies unique asset/study/path identities, manifest counts, historical checksum syntax, no unearned readiness, and safety boundaries. Its default JSON output reports physical bytes as NOT_INSPECTED, not as present. Optional size probing is not hash verification; optional per-file streaming SHA-256 verifies local assets without opening RNA matrices. Even SHA-matched assets remain UNQUALIFIED_FOR_TRAINING pending study-specific scientific contracts. Focused tests must be run with python -m unittest discover -s tests/therapeutic -v.

## Next gates — these are plans, not completed claims

1. On the GPU laptop, verify the existing asset bytes against the preserved download SHA ledger. Do not re-download or substitute data until actual missing bytes are established. Fail closed on wrong size or hash.
2. GSE301119: read-only recovery of exact gene IDs, donor/batch/guide/control structure and non-targeting matchability. Separate CRISPRi/a gene universes with measurement masks. GSE178317: independent author-faithful cell–guide join audit.
3. Precommit discovery/calibration/held-out study roles before expression results are inspected. A study reused for development is never called independent validation. Keep pathology and full-model protected outcomes sealed.
4. Build observed perturbation effects from real matched guides vs controls using biological-unit-aware pseudobulk, guide concordance, depth/viability/confounding negatives; compare raw RNA, differential expression and PCA baselines BEFORE claims of JEPA added value.
5. Only after a separately frozen lawful JEPA encoder exists, test donor/target/study-held-out observed latent perturbation transport against exactly the same baselines; no V5 training or objective tuning here.
6. Connect validated genetic-response signatures to independently qualified compound-response profiles using stable compound/target identities, dose and context, not cross-modality raw-vector cosine. Functional phenotypes and target engagement are mandatory before therapeutic interpretation.

**Terminal status:** THERAPEUTIC_LANE_METADATA_ONLY__HISTORICAL_ASSETS_NOT_YET_REQUALIFIED__V5_TRAINING_OFF.

No changes to current V19 branches, protected outcomes, models or existing historical manifest bytes are authorized by this document.
