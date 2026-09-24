# JEPA V25 — detailed new-chat handoff: committed perturbation data, scripts and safeguards

Date: 2026-09-24. Status: current docs handoff. This supersedes V24 as startup guidance, not as a replacement for its historical evidence.

## First read / exact authority

1. `START_HERE.md`
2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
3. This V25 handoff
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260924_V25.json`
5. `docs/agent/JEPA_RUNTIME_ASSET_MANIFEST_20260924_V25.md`
6. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
7. V24, V23 and frozen formula/heavy-asset references for historical scope.

Re-fetch live GitHub heads and verify receipts/physical assets before any action. Never equate a CI PASS, committed binary, paper agreement, or descriptive effect with scientific confirmation.

## Current live GitHub state at this handoff

- `main` contains the V25 governance/handoff docs after PR #109, but **not** the new experimental physical binaries; those remain on experimental PR #77.
- Active experimental PR **#77**, branch `analysis/perturbation-etl-gse301119-claude-20260923`, audited head **`67981c8ef6e158d865470e70bca81cbe289be3dd`**, DRAFT, base `analysis/therapeutic-perturbation-etl-20260923`. Re-fetch before editing. The latest head differs from the prior code head by one new versioned comparison receipt only. At audit completion its CI rerun had **9 SUCCESS, 0 FAILED**. Re-check live heads before acting because later commits may supersede this snapshot. New integration after the earlier audit: previously reviewed PR #84 -> #88 -> #90 baseline/exposure code was integrated from PR #99; see benchmark section below.
- Claude's 58 MB data commit `52f20a7a` is an ancestor of that head (12 commits behind, zero divergent commits). Physical output binaries, receipts and producers are already on GitHub under `analysis/therapeutic_perturbation_etl/`. Do not re-upload duplicate binaries or merge development results into main merely to make them accessible.
- PR #83 plus #85 red-team merged into its parent at `64148023740d57777666faff15395262d4b0e3da`. N1 remains unauthorized.
- PR #105 domain-transfer and gene-authority design merged into experimental PR #77. PR #104 count binding was closed as superseded because its source/test/workflow blobs were already integrated by Claude. PR #99's previously reviewed benchmark/exposure chain was selectively integrated as byte-exact code/tests/workflows; do not merge the old PR wholesale. PR #100 superseded by #102.
- Independent open reviews: #86 GSE254205 assay-detection/schema V2; #91 GSE301119 donor-guide support; #92 GSE311359 duplicate-BIN1 STOP; #94 GSE240609 GEO source-identity V2. Re-fetch each live head before merging.

## Permanent project boundaries

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`.

`TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF`.

FULL104: 4,553,407 human brain cells; 104 donors; 42 operators; 41,238 addresses; 17,186 common-core addresses; 8,915 Level-4 feature blocks. Do not confuse historical Stage81a3 corrected TRAIN or T1 checkpoints with full current FULL104. All-104 Level-4 raw-count reaggregation and real N1 are not proved. Current target-address Stage-A qualification, target semantics, masking and production teacher/student binding remain prerequisites for training; the architecture is not being restarted.

## GSE178317 — what is now physically recovered

Raw SRA extraction: 221,434,278 spots; 58,302 called cells in four 10X capture wells; 81/81 guides in every well; 18,006,495 deduplicated guide UMIs. This took about 47 minutes and is preserved as a 3,121,266-byte count NPZ in GitHub.

The development-calibrated V2 caller assigns 11,775 cells; 39/39 perturbation targets represented; 800 NTC cells; 37 targets meet the **matched within-lane** support gate (>=40 total cells, >=3 wells with >=10 target cells AND >=10 same-well NTC cells). The 39 measured engagement point estimates are negative; median target log2FC -0.7146. Only 37 have descriptive technical-well spread; **zero have estimable biological uncertainty**. Four capture wells are technical partitions of one pooled day-eight iTF-Microglia preparation, not independent donors/differentiations.

Compared with the depositors' CRISPRbrain analysis of the SAME experiment: 35/35 comparable targets agree in direction, Spearman ~0.720; 18 reference-nonsignificant targets show median magnitude ratio 2.37 versus 3.07 overall. This is **pipeline/reference agreement, NOT independent replication or proof of false-positive control**. The 18 null-labeled targets are reference FDR>=0.05, not known biological nulls. The V2 z=5/minimum support thresholds were chosen after an inspected bounded smoke run: **DEVELOPMENT ONLY**.

The existing 3.0 MB `gse178317_cell_guide_umi_counts_v2.npz` has legacy pickle-backed identity arrays. It is a committed development artifact, not compliant with the new safe-count runtime contract. `scripts/reissue_gse178317_safe_counts_v2.py` now provides a SHA-gated, one-time **format-only** reissue from the reviewed legacy NPZ + count receipt, with source/lane census parity and `allow_pickle=False` for the resulting artifact. CI exercises synthetic adversaries but **the physical safe-format reissue is not shown committed at the audited head**. Do not claim it ran, or rerun 221M SRA reads unnecessarily. Next: execute that reissue on the known committed blob in a new output directory, preserve SHA/receipt/provenance, then rerun the V2 caller on the safe NPZ and compare assignment/effect parity.

IMPORTANT RECEIPT CAVEAT: the original `evidence/gse178317_recovery/gse178317_crisprbrain_validation_receipt_v1.json` still contains a historical, **superseded** phrase that the two analyses 'share no intermediate' and a generic PASS. A versioned correction now exists at `evidence/gse178317_recovery/gse178317_crisprbrain_reference_comparison_receipt_v2.json`. The V2 receipt explicitly records same experiment/shared raw-read origin, no independent biological replication, no independent validation, and DEVELOPMENT-only scope. Preserve V1 as history but machine consumers should use V2.

## Committed output inventory

See `docs/agent/JEPA_RUNTIME_ASSET_MANIFEST_20260924_V25.md` and the authoritative source `analysis/therapeutic_perturbation_etl/outputs/README.md` on PR #77.

`outputs/gse178317/` includes the full 58,302 x 81 count NPZ, gzipped 11,775 assignments, target engagement, gzipped top effects, and reference comparison. `outputs/crisprbrain/` includes **five gzipped microglia screens** (~48 MB). Four neuron/iPSC CRISPRbrain tables (~347 MB raw, ~131 MB gzipped) are NOT committed; exact size/full SHA-256 and producer command are in the output README. Do not inflate Git history merely to duplicate quickly regenerable tables; if offline reproducibility is required, put them in versioned external object storage with SHA-bound manifest.

## Eight-study perturbation status and unresolved biological design

- GSE301119: guide identity/effects qualified within stated two-donor limits. Independent PR #91 checks guide-by-donor support; next donor-aware transcriptome-wide effects and no false biological replication.
- GSE293118: six currently measurable nominated target engagements qualified; regulatory-locus causality is not automatically established.
- GSE311359: **STOP** for guide-level benchmark authority. 381 capture features have only 379 unique guide labels; three BIN1 features collide. Need exact feature-ID -> protospacer/library -> target mapping and physical V2 rerun, not name-keyed aggregation. PR #92.
- GSE254205: bulk GNE-317 arm available. PR #86 schema/detection correction is CPU-reviewed but requires physical V2 rerun; three other assays remain.
- GSE241858: TREM2 R47H x cytokine; two independent iPSC clones per genotype. Replicate cultures within clone are not independent biological replicates. Effects descriptive with clone-aware uncertainty limits.
- GSE240609: CD11b-purified microglia **after** neuron coculture; 2x2 APOE3ch x neuron genotype, one biological sample per factorial cell; descriptive only, no biological SE/CI. PR #94 physical V2 pending.
- GSE178317: recovered and development-usable with the strict scope above, but no biological error bar, no independent replication, no prospective confirmation, no independent guide-identity validation.
- GSE175721: STOP for guide->cell assignment. Guide reference exists, but no deposited per-cell guide mapping. Do not infer from coincidental GEX gene names.

## CRISPRbrain benchmark and culture-vs-brain transport

Claude acquired 54 CRISPRbrain screens, including nine transcriptomic screens and 352 distinct perturbation targets. Five microglia screens are committed; four neuron/iPSC tables are regenerate-on-demand. Some screens may share experiments/targets; do not sum per-screen target counts as independent genes. The Day-8 GSE178317 reference table is the SAME study, never a held-out external cohort.

The core FULL104 data are adult human brain, whereas CRISPRi benchmarks are predominantly cultured/iPSC-derived cells. The integrated `benchmark_domain_contract_v1.py` explicitly refuses direct in-brain causal generalization from matched context labels alone; external in-brain evidence is required. This is a **validation/transport** problem, not a reason to redesign JEPA. Measure untreated control-state similarity to matched FULL104 cell types on the **frozen shared gene space**, stratify benchmark performance by tissue/culture/donor/cell line and similarity distance, and keep the domain claim descriptive until external brain perturbation evidence exists. Baseline similarity is NOT yet measured as an authenticated result.

A FULL104-vs-CRISPRbrain overlap receipt measured gene-space coverage, but donor/cell-line and cell-barcode overlap remain NOT_CHECKED. Source-family naming is not proof of independence.

## Gene-ID harmonization — existing work, not a restart

The current `src/sea_ad_jepa/perturbation/cross_study_feature_contract_v1.py` already uses **unversioned human Ensembl gene ID** as the canonical cross-study key, retaining original HGNC approved symbol / versioned Ensembl / Entrez ID and source namespace, rejecting ambiguous collisions, and distinguishing structurally unmeasured from assayed-undetected (zero is not missing). Do not reimplement or hand-map aliases.

`docs/agent/CROSS_STUDY_GENE_ID_AUTHORITY_20260924.md` freezes the planned authority: HGNC archived complete snapshot (proposed 2026-07-07) + Ensembl human release 116 GRCh38.p14, **proposed until actual source files are downloaded and hashed**. Build a SHA-bound versioned crosswalk, report mapped/unmapped/ambiguous/alias counts per study, use reviewed unique aliases only, and never treat a symbol guess as a gene-identity PASS. The eight stale aliases (including ATP5A1 -> ATP5F1A) must go through this frozen authority, not manual substitutions.

## Newly integrated retrospective benchmark and exposure safeguards (latest PR #77)

At `67981c8ef6e158d865470e70bca81cbe289be3dd`, the reviewed #84 -> #88 -> #90 code/tests/workflows were integrated from PR #99 without wholesale merging its stale branch. `analysis/therapeutic_perturbation_etl/BENCHMARK_BASELINE_INTEGRATION_20260924.md` documents the integration.

- `src/sea_ad_jepa/perturbation/benchmark_target_holdout_v1.py`: target-heldout benchmark framework with donor-aware components only when real independent donors exist; GSE178317 10X wells must NEVER be relabeled donors.
- `src/sea_ad_jepa/perturbation/outcome_exposure_ledger_v1.py`: immutable outcome-exposure accounting. GSE178317 target engagement, DE and same-experiment CRISPRbrain reference are **INSPECTED/DEVELOPMENT**, never untouched confirmation.
- `src/sea_ad_jepa/perturbation/benchmark_screen_profile_baselines_v1.py` and `analysis/therapeutic_perturbation_etl/scripts/run_crisprbrain_target_profile_baselines_v1.py`: two simple same-screen retrospective comparators, zero predicted log2FC and mean profile of OTHER training targets. Five deterministic target-disjoint folds, exclude each target's own gene from scoring, intersect measured genes rather than imputing missing as zero, macro-average targets. No invented biological error bars.
- `.github/workflows/perturbation-screen-profile-baselines.yml`, `perturbation-target-heldout-benchmark.yml`, `perturbation-outcome-exposure.yml` plus strict test suites. **Nine** workflows SUCCESS at the audited head, including a DEVELOPMENT-only baseline report on the already-inspected committed Day-8 CRISPRbrain screen. The report's numeric results are not copied into this handoff because the workflow artifact has not been independently inspected here. Do not invent a performance result.
- Source published uncompressed Day-8 screen SHA-256 required by baseline: `41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39`. It is the SAME experiment as GSE178317, not an independent train/test cohort.

## Next exact work, ordered

1. Re-fetch live PR #77 and read its `outputs/README.md`, producer scripts, physical receipts and six CI workflow results.
2. Run the **safe-format count reissue** on the committed legacy NPZ with exact SHA + receipt, verify parity and commit the versioned safe artifact/receipt/provenance without overwriting the legacy record. Do not re-stream SRA.
3. Audit the legacy CRISPRbrain comparison receipt's stale independence claim and publish an explicit versioned correction so machine consumers cannot accidentally read it as external validation.
4. Freeze/physically authenticate the HGNC/Ensembl mapping source files, build and test the actual crosswalk, apply to all eight studies, report missing/collision/assay masks.
5. Build an outcome-blind baseline brain-vs-culture control-state distance audit, with frozen shared genes, covariate/QC stratification and donor/cell-line disjointness checks. Do not open protected JEPA outcomes.
6. **Baseline infrastructure is now integrated and tested** (see section below). Inspect the generated DEVELOPMENT report, validate score/holdout/exposure semantics and run actual benchmarks only on qualified screen inputs. Add further non-JEPA comparators and study/target/donor-aware validation only where independent biological units exist.
7. Physically rerun GSE254205 and GSE240609 corrected V2, process remaining GSE254205 assays, resolve GSE311359 feature identity, and retain GSE175721 STOP.
8. Continue FULL104 Stage-A target semantics/masking/production geometry qualification; training remains OFF until those existing gates are actually closed.

Do not redo T0/T1/C2, QID archaeology, Layer-2 generic shortcut discovery or old smaller-run archaeology without changed evidence. Do not silently carry Stage81a3 or exploratory results into FULL104. Keep branch work and historical findings in perspective.
