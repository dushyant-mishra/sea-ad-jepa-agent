# JEPA V25 — detailed next-chat execution instructions (audit-corrected)

Prepared 2026-09-24. Continue `dushyant-mishra/sea-ad-jepa-agent`. This is an **execution handoff**, not a proposal to redesign JEPA. All commit IDs below are audited snapshots and must be refreshed from live GitHub before any change. V25 on `main` incorporates the independent documentation audit via PR #110.

## 1. The first action — read the authority, then fetch live heads

Open `START_HERE.md` **first** on `main`. Read these exact files in order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260924_V25_RESULTS_DATA_SCRIPTS.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260924_V25.json`
4. `docs/agent/JEPA_RUNTIME_ASSET_MANIFEST_20260924_V25.md`
5. **This file**: `docs/agent/JEPA_NEW_CHAT_TAKEOVER_INSTRUCTIONS_20260924_V25.md`
6. `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`
7. For existing formulas/heavy-data authority, follow the pointers to `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`, `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md` and V24/V23 **as history**, not as live results.

Use the connected GitHub repository, not an unauthenticated local copy. Re-fetch `main`, experimental PR #77, any relevant review PR and their checks. Compare the live head with the last audited PR #77 head `67981c8ef6e158d865470e70bca81cbe289be3dd`. If Claude has added commits, inspect the precise changes and update this plan before editing. Do not presume GitHub commit distance; the original 58 MB data commit `52f20a7a` is an ancestor, and no numerical distance is needed. Verify ancestry with the GitHub compare endpoint if useful.

Last audited experimental branch: `analysis/perturbation-etl-gse301119-claude-20260923`, draft PR #77, based on `analysis/therapeutic-perturbation-etl-20260923`. **Nine CI workflows succeeded** at `67981c8ef6e158d865470e70bca81cbe289be3dd`; that establishes code/CI status, not biological confirmation. The main branch contains governance/handoff documents; the new experimental output binaries remain on PR #77. The PR #110 audit corrections are already merged on `main`. Do not repeat them.

## 2. Working agreement and permanent STOPs

**No project restart, no architecture redesign, no redoing completed historical audits.** Preserve the full results and chronology. Patch demonstrated defects in the smallest versioned component. Do not mix historical Stage81a3/smaller runs, placeholders, synthetic outcomes or stale branch artifacts into FULL104.

Scientific authority order: `DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`.

Permanent status until separately qualified:

`TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF`.

Never inspect protected/pathology/DEV/SEALED JEPA outcomes or use them to tune a design. Never convert a synthetic CI PASS, a descriptive culture experiment or a same-experiment reference comparison into a scientific qualification. Do not let project documentation or a receipt silently unlock N1 or training.

FULL104 scientific substrate: 4,553,407 adult human brain cells; 104 donors; 42 operators; 41,238 molecular addresses; 17,186 common-core addresses; 8,915 Level-4 feature blocks. Teacher/student/EMA machinery already exists. The corrected FULL104 adapter and its red-team were consolidated into the N1 parent, but **all-104 Level-4 raw-count reaggregation and real N1 remain unproved/unauthorized**. Target-address Stage-A semantics, masking, teacher-target binding and production-geometry qualification remain core prerequisites; do not restart those lines of work.

The >30 GB full physical dataset is on Claude's GPU laptop/external drive, not automatically available in this chat. Prefer GitHub-committed evidence, CPU/static work and small safe artifacts here. Give Claude exact SHA-bound commands for any task genuinely requiring the GPU disk; never fabricate physical execution or demand a fresh 221-million-spot SRA download when the archived counts suffice.

## 3. Existing data and science — do not regenerate it

Source root on the **experimental** branch: `analysis/therapeutic_perturbation_etl/`. Inspect `outputs/README.md`, `GSE178317_RECOVERY_QUALIFIED_20260924.md`, `BENCHMARK_BASELINE_INTEGRATION_20260924.md`, producer scripts and `evidence/gse178317_recovery/`.

Committed results: approximately 58 MB of GSE178317 and CRISPRbrain outputs. GSE178317 SRA recovery read 221,434,278 spots and produced 58,302 called cells by 81 guides and 18,006,495 deduplicated guide UMIs. The preserved count artifact `outputs/gse178317/gse178317_cell_guide_umi_counts_v2.npz` is 3,121,266 bytes and has exact SHA-256:

`170a16797d681124a9083eb4170794b0f377b8a64ec3603e63b3435567fe3b4c`

Its V2 **development-calibrated** caller assigns 11,775 cells across 39 targets; 37 targets meet the matched-well support gate; 39/39 measured target engagement point estimates are negative; median log2FC -0.7146. Four 10X wells are technical capture partitions of one pooled iTF-Microglia preparation, **not independent donors or differentiations**. Biological uncertainty is NOT estimable. The call threshold was calibrated after inspecting a bounded smoke run, so this is DEVELOPMENT, not prospective confirmation. Independent guide-identity validation is also not established.

CRISPRbrain catalogue: 54 screens, nine transcriptomic screens, 352 distinct perturbation targets. **Five** compressed microglia tables are committed in `outputs/crisprbrain/`; **four** neuron/iPSC tables are deliberately regenerate-on-demand, with full SHA-256 and exact sizes in `outputs/README.md`. The latter are not missing scientific work, and do not need to bloat Git history. The Day-8 CRISPRbrain reference derives from the SAME GSE178317 reads. Historical 35-target direction agreement (35/35), Spearman ~0.720 and 3.07-fold median magnitude ratio are **not** a support-qualified, independent replication or in-brain result.

## 4. First executable work package — CPU-first, parallel where independent

### A. Compute the real 33-target matched-well support-qualified comparison

Inputs are already committed: `outputs/gse178317/gse178317_vs_crisprbrain_engagement_v1.csv` and `evidence/gse178317_recovery/gse178317_guide_assignment_receipt_v2_lanegate.json`. Examine their actual schemas first. The reviewed 35-target historical comparison includes **AARS** and **LSM6**, which do not meet the matched-well support gate; they must be excluded using the authenticated per-target support receipt, not by manually hardcoding an arbitrary favored set.

Write a small versioned V2 producer and adversarial tests. Join by verified unique target identities, fail on missing/duplicated identifiers and contradictory support, independently recompute the exact 33-target set and its direction agreement, Spearman, Pearson, median magnitudes/ratios and count of published significant/nonsignificant reference targets. Do not copy the 35-target values, guess that 33/33 will agree or silently drop a target. Emit a clearly named **DEVELOPMENT / SAME-EXPERIMENT / MATCHED-WELL-SUPPORT-QUALIFIED** CSV, JSON receipt and provenance digest. Keep the original V1 CSV and both V1/V2 reference receipts immutable for historical comparison.

Avoid any biological SE, replication or prospective confirmation language. Explicitly report that support qualification here is technical comparison feasibility, not independent biological replication.

### B. Audit every downstream consumer of the corrected CRISPRbrain receipt

The already committed correction is `evidence/gse178317_recovery/gse178317_crisprbrain_reference_comparison_receipt_v2.json`. It explicitly records shared raw-read origin, `independent_validation=false`, `independent_biological_replication=false` and DEVELOPMENT scope. Historical `gse178317_crisprbrain_validation_receipt_v1.json` still includes the superseded "share no intermediate" and `PASS` statements. **Do not waste time publishing another correction receipt.**

Search source, analysis scripts, notebooks, workflow jobs, generated reports, README files and machine manifests for V1 receipt references, `external validation`, `independent`, `PASS` and 35-target claims. Mark each reference historical-only or migrate its consumer to V2; enforce this in regression tests. Correct `outputs/README.md` and any current report that calls the 3.07x magnitude difference an **expected consequence of stricter guide calling**. That is an untested mechanistic hypothesis. A separate caller-sensitivity analysis, holding the count matrix and processing otherwise fixed, is needed to test it; do not assert it as causally demonstrated. Do not rewrite valid historical receipts.

### C. Publish an actually verifiable complete binary integrity manifest

The V25 human-readable asset manifest has full SHA for the legacy NPZ but only **truncated prefixes for several committed binaries**. Find any existing full-digest producer/receipt before creating a new one. If incomplete, create a machine-readable JSON/CSV inventory with **exact repo-relative path, exact size, full 64-character SHA-256, source commit/tree and origin or regeneration script for every committed output binary** (GSE178317 NPZ/CSVs/gz and five CRISPRbrain gz tables). Compute hashes from the actual bytes on a checked-out copy; a Git blob SHA is NOT the file's SHA-256 and a 16-character prefix is NOT an exact digest. CI should independently hash all listed files, detect both omissions and extra unlisted binary files, verify size and digest, and fail closed. Do not duplicate 58 MB of binaries or infer any digest from its prefix.

The four uncommitted reference screens have exact **raw CSV** hashes and regeneration commands in `outputs/README.md`; keep a separate regenerate-on-demand record rather than falsely listing them as physically committed.

### D. Inspect the baseline workflow's real numeric development output

Code already integrated from the reviewed #84 -> #88 -> #90 line includes `benchmark_target_holdout_v1.py`, `benchmark_screen_profile_baselines_v1.py`, `outcome_exposure_ledger_v1.py`, the CRISPRbrain runner, tests and three CI workflows. The retrospective workflow ran on an already-inspected Day-8 reference screen, but **its numeric report was not independently reviewed in the V25 handoff**. Retrieve its actual action artifact or reproducibly rerun on the SHA-matched committed table; record exact sample/feature counts, per-target and macro scores, folds and comparators. The available same-screen baselines are zero predicted log2FC and the mean profile of **other training targets**. Five deterministic target-disjoint folds must stay disjoint. Never include each target's own perturbed gene in downstream scoring; do not substitute zero for structurally missing measurements; macro-average over targets, not thousands of genes or technical cells.

Confirm the exposure ledger marks GSE178317 engagement, its transcriptome-wide effects and the same experiment's CRISPRbrain reference as **INSPECTED/DEVELOPMENT**. Do not claim any method beats chance or JEPA from green CI alone. No independent biological error bar exists for this study.

### E. Reissue the already recovered count NPZ in safe format — no SRA re-extraction

`scripts/reissue_gse178317_safe_counts_v2.py` is implemented and its adversarial synthetic CI passed. Its physical conversion is **not yet recorded as executed/committed** in the audited PR #77. The legacy artifact uses pickle-backed identity arrays; the converter intentionally permits one narrowly scoped pickle read **only after** verifying the exact SHA above and authenticated full count-stage receipt. It checks array and lane census parity, writes integer/plain-string NPZ, validates `allow_pickle=False` and records conversion-only provenance.

If the existing 3 MB binary can be obtained safely in this execution environment, run with:

```bash
python analysis/therapeutic_perturbation_etl/scripts/reissue_gse178317_safe_counts_v2.py \
  --legacy-npz analysis/therapeutic_perturbation_etl/outputs/gse178317/gse178317_cell_guide_umi_counts_v2.npz \
  --legacy-count-receipt analysis/therapeutic_perturbation_etl/evidence/gse178317_recovery/gse178317_count_stage_receipt_v2.json \
  --out-dir <NEW_UNOCCUPIED_VERSIONED_DIRECTORY>
```

Inspect the script flags from the live head before using this command. Verify all cell/guide identities, all array elements, 58,302 × 81 geometry, 18,006,495 guide UMIs, every lane's counts and exact-source SHA. Commit the **versioned safe NPZ, new count receipt and provenance** without overwriting legacy outputs. Rerun the V2 caller on the new safe NPZ; verify 11,775 assignment identities and downstream descriptive effect parity or explicitly characterize any discrepancy. This is authenticated **format conversion only**, not new extraction, independent guide evidence, new biological replication or confirmation. If this environment cannot retrieve the binary, give Claude the exact executable command and required receipt paths; do not mark it physically done.

Independent CPU tasks A–D can run in parallel or on separate short-lived review branches; do not race two writers against the same file or PR #77 while Claude is also pushing.

## 5. Next scientific qualification after the first work package

**Gene nomenclature:** Reuse `src/sea_ad_jepa/perturbation/cross_study_feature_contract_v1.py`. Canonical cross-study key is unversioned human Ensembl gene ID; original namespace/ID and missingness state are preserved. Authenticate the actual official HGNC/Ensembl snapshot **bytes, releases and full SHA-256** before constructing a frozen crosswalk. The authority document proposes release candidates but the files are not yet authenticated; verify exact releases instead of assuming. Map all eight study sources with per-study counts of unique/mapped/unmapped/ambiguous/aliases and `STRUCTURALLY_UNMEASURED` vs `ASSAYED_UNDETECTED` vs `ASSAYED_DETECTED` masks. Do not hand-map the eight stale aliases or let duplicate symbols silently collapse.

**Cultured cells versus human brain:** Reuse the already integrated `benchmark_domain_contract_v1.py`; matching coarse labels alone never authorizes adult-brain causal generalization. Design an **outcome-blind untreated/control-state** domain-distance analysis on a frozen shared Ensembl-gene set, matched cell types, controlled assay depth/QC/source/donor/line and predeclared metrics. Use independent donors/clones as units when available. Baseline similarity cannot prove perturbation-effect transport. Report cultured CRISPR results as development benchmarks; independent in-brain perturbation evidence is still required for direct adult-brain causal claims. FULL104 donor/cell-line and barcode overlap with benchmark cohorts are currently NOT CHECKED.

**Study-specific remaining work:** GSE301119 uses real two-donor identities (review PR #91); proceed donor-aware but report limitations. GSE293118 has six measurable nominated target engagements. GSE311359 remains **STOP**: 381 feature entries, 379 unique guide labels and three BIN1 label collisions; require authenticated feature ID -> protospacer -> library -> target mapping and physical V2 before guide-level analysis (PR #92). GSE254205 requires corrected assay-detection/source schema physical V2 and three other assays (PR #86). GSE241858 has two clones per genotype; do not count culture repeats as independent clones. GSE240609 is purified microglia **after** neuron coculture with one biological sample per 2x2 cell; descriptive-only physical V2 pending (PR #94). GSE175721 remains **STOP** without authentic guide-to-cell assignment. Never promote a study just because a script runs.

**Core JEPA track:** In parallel with CPU perturbation validation, continue the established FULL104 Stage-A structural qualification, scientifically authorized target semantics, masking, independent anti-cheating checks, production geometry and teacher/student/EMA binding. Verify current full-data lineage, not Stage81a3 historical archives. Do not reopen T0/T1/C2, QID archaeology or generic Layer-2 shortcut discovery without material new evidence. Training remains OFF until all required already-defined qualification gates actually close.

## 6. Branch management, red-team and done criteria

Re-fetch live PR/branch heads: PR #77 is the active experimental parent. PR #105 domain/gene contract and PR #102 matched-well support were integrated. PR #104 was closed as byte-identical/superseded. PR #99 was only **selectively** integrated; **do not merge it wholesale**. PR #100 is superseded. PRs #86, #91, #92 and #94 are separate drafts with unresolved source/physical work. The V25 audit-document repairs from PR #110 are already merged into `main`. Reconcile any new commits first.

For each change: write the exact testable scientific claim and data scope; enumerate source paths and existing code; implement a minimal versioned fix; run unit and adversarial tests with **zero unexpected skips**; reproduce on committed physical inputs where possible; inspect CI logs, job counts and actual artifacts; independently red-team leakage, key collisions, lane pairing, missingness, stale reference consumption, format/pickle safety and accidental older-run spillover. Maintain SHA-bound inputs/outputs and immutable historical results. Clearly distinguish `CODE_TEST_PASS` from `PHYSICAL_DATA_VERIFIED` from `BIOLOGICAL_REPLICATION` from `PROSPECTIVE_CONFIRMATION`.

If working alongside Claude, isolate changes on a new branch based on a freshly fetched parent; do not overwrite Claude's moving PR #77 head. Merge only after reviewing the exact diff, ancestry, no accidental binary/source churn, and all relevant completed checks. Use docs-only PRs for governance updates. Any data or code PR remains development-scope unless a separate scientific authority gate approves it.

**Deliverables for the new chat:** (1) a live GitHub head/CI and asset audit; (2) completed, tested first-package work A–D to the extent inputs are accessible, with exact PRs/commits and concrete physical versus synthetic qualification; (3) if the 3 MB NPZ is accessible, the safe-format conversion and parity receipts; (4) an evidence-backed prioritized backlog for genuinely remaining gene mapping, brain/culture transport, study-specific blockers and core FULL104 qualification; (5) update `START_HERE` and the latest pointer only when substantive new authority is actually established. Never invent a result, performance score, full hash, independent replicate or future completion.

Begin now with the live-head check, source/receipt review and the 33-target comparison. **Do not ask to restart the project or to re-upload already committed data.**
