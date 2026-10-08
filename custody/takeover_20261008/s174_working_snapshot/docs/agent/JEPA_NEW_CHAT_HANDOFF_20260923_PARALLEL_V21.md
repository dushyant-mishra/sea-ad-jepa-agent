# JEPA new-chat handoff — September 23, 2026 — parallel scientific/engineering lanes (V21)

**Navigation authority:** `START_HERE.md` → `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json` → this handoff → `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md`. This handoff supersedes older *operational status*, not historical evidence or independently frozen scientific contracts. Always fetch the live GitHub heads before editing; SHA records below are an **as-observed 2026-09-23 snapshot**, not eternal branch pins.

**Current boundaries:** `JEPA_TRAINING=OFF`; `AUDIT_B_N1=UNOPENED`; `RARE_TAIL_MOLECULAR=UNOPENED`; `D_SHARED_G5=UNOPENED`; `PROTECTED_FULL104_OUTCOMES=UNOPENED`; `THERAPEUTIC_RANKING=OFF`.

## 1. Scientific mission and history: do not restart completed work

Goal: learn measurement-robust molecular cell states from authenticated, corrected FULL104 observational single-cell data; independently test whether those states improve the prediction of *measured* perturbation responses in genetically and environmentally perturbed myeloid systems. Keep the observational foundation encoder separate from the prospective intervention-response model. Repeated historical errors to prevent: (a) zero student gradients in past T1/C2 training, (b) source/measurement/target-identity shortcuts mistaken for biology, (c) QID matched-null versus actual wrong-query semantic mismatch, (d) incorrect FULL104 source-label derivative, (e) historical small-run/synthetic artifacts entering newer physical products, (f) outcome exposure or guide duplicates silently interpreted as independent replication.

Read `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` before auditing any old issue. Label each task `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN` or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`. Do NOT silently promote historical T0/T1, Stage81A3 smaller TRAIN, six-donor preflight, synthetic gate tests, self-certified approval hashes, prior project forecasts or stale archived checkpoints to FULL104 or experimental production authority.

## 2. FULL104 — corrected derivative and real N1 adapter

Observational substrate: 4,553,407 cells; 104 donors; 42 operators; 41,238 addresses; 17,186 strict-core addresses; 8,915 blocks; four outer folds (28/26/25/25). Corrected source derivative physical-file SHA-256 `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b`. Original erroneous derivative SHA `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae` **QUARANTINED**. Frozen pass1 complete NPZ SHA `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1` is mandatory whole-file pin. The exhaustive all-cell metadata correction proves donor/source identity, **not** all-104 raw-count reaggregation.

PR chain: #69 corrected derivative → #73 adversarial qualification → #74 physical requalification → #76 whole-file pass1 → #78 crash-safe synthetic integration → #80 independent hardening → #83 physically qualified adapter @ `6ff12edb8f97287ae994f41b5217350a453e6d77` → #85 independent physical-authority red-team @ `0bccba8ce62d9006539b8d7a0f649faf906255fd`. #79 superseded by #78/#80. #83 tested real metadata preflight: three physical inputs authenticated by byte digest, zero source invariants violated, N1 execution gate **actually rejected** authority with `STOP_N1_NOT_AUTHORIZED`, 23 tests passed twice/zero skips as reported by producer; four associated hosted workflows green. #85 closes forged N1-grant and overwriteable receipt fields and pins reviewed receipt files; hosted tests/workflows green. **Adapter qualification != real N1 authorization**; the physical burden stream remains unopened; all-104 raw-count reaggregation unresolved.

Next FULL104: independent physical review of #85 successor; decide whether Level-4 raw-count reaggregation is necessary and implement any missing physical burden stream checks. No N1 or training without separately reviewed explicit authority.

## 3. Experimental collection — authenticated 8 studies, 16 assets

All 16 source assets passed historical physical-file authentication, but authentication is NOT effect qualification. Claude works heavyweight datasets on a separate GPU Windows laptop, with outputs under its local `D:/` project disk. This current chat environment lacks the same complete heavy inputs; avoid inventing paths and DO NOT reclassify synthetic CI as physical execution.

* **GSE301119**, primary human macrophage CRISPRi/a: initial ETL, count parity and RAW integer guide×donor pseudobulk **PASS**. Isolated R 4.6.1 and SeuratObject 5.4.0 accessed exact original Assay5 counts in both objects, with metadata cross-check over 52,050 cells; PR #81 reviewed script physically rerun. CRISPRa 23,584 cells, 19,162 genes; CRISPRi 28,466 cells, 36,601 genes; CRISPRa features exact subset of CRISPRi; structural nonoverlap is NEVER zero-filled. 2,098/2,137 guide×donor groups; normalized logCPM reproduced bit-identically from saved integer counts; engagement matched earlier committed rows within declared tolerance. **Transcriptome-wide guide/donor-aware differential effects still NOT_EXECUTED/await latest Claude update.** Two biological donors only; do not imply population transport.
* **GSE293118**, HMC3 noncoding CRISPRi: verified separate protospacer/matrix barcode containment; 64,148 singly assigned cells; six same-name measurable genes; remaining noncoding variants/deletions lack independently nominated cis-targets. Need transcriptome-wide downstream effects; NEVER fabricate cis targets.
* **GSE254205**, iPSC microglia amyloid ± GNE-317: 9-sample bulk arm (3 per group) and three measured contrasts processed; only bulk arm initially qualified. Current V1 incorrectly calls 22,278 assay-present but undetected genes 'unmeasured' among 58,395 assayed; draft PR #86 V2 corrects mask/label without overwriting old results, updates exposure ledger; 4 focused tests passed. **V2 physical reexecution pending**. Three other physically authenticated assets (single-nucleus RNA, ATAC, LD-sort) unprocessed. No rescue/clinical efficacy claim.
* **GSE311359**, iPSC microglia CRISPRi Perturb-seq with capture and gene features in same seven matrices: Claude's V1 producer reported 105,509 cells, 381 guide features, 36,601 gene features, dominance rule ≥5 top-guide UMI and ≥70% fraction, 27,737 assigned cells, target engagement rows. **CRITICAL NEW INDEPENDENT RED-TEAM STOP (PR #92)**: SHA-pinned lightweight V1 identity CSV contains 381 rows but only 379 unique guide labels; `BIN1` appears THREE TIMES. The V1 producer keys its guide/sample pseudobulk dictionaries by label, collapsing those three feature rows. Independent metadata/guide-level effects **NOT fully qualified**; keep 70-target headline as historical V1 producer claim, not a confirmation score. Draft PR #92 @ `bc09c0f432db6e17bec3047baeb0812975043937` adds early-stop duplicate guide-label/feature-ID guard, compares all seven samples' exact feature IDs/names/types/order, refuses overwriting old V1 results; 7 hosted tests passed zero skipped. Claude must inspect exact physical three BIN1 feature IDs, separate library/protospacer reference, then build an independently reviewed V2 source-ID-addressed producer, regenerate all affected results and red-team the corrected output. DO NOT simply append suffixes or treat three same-named entries as known independent guides.
* **GSE178317** direct Kampmann iPSC-microglial CRISPRi/a platform: **guide-to-cell STOP**, fully documented in PR #77 @ `f34fae312a3006e9eefaa1dfb85749037de9dddd` document `analysis/therapeutic_perturbation_etl/GSE178317_GUIDE_JOIN_STOP_20260923.md`. Empirical lane matching via barcode containment PASS, but the deposited four 'sgRNA enrichment' matrices have 33,538 gene-expression features and ZERO CRISPR guide-capture features; cell-to-guide identity cannot be recovered from available files. Do not infer from filenames. Separate 18-sample bulk differentiation/LPS asset is a **legitimate cellular-context** dataset, not a genetic-perturbation benchmark. Reopen CRISPR only if independently authenticated guide feature matrices, protospacer-call table, author-approved cell-guide assignments or Day-8 CRISPR bulk arms are obtained.
* **GSE175721** engineered organoid microglia: physical file auth PASS, original guide-to-cell assignment unresolved; retain organoid as replicate, not cells.
* **GSE241858** TREM2 R47H ± LPS/IFNγ: authenticated; bulk genotype × inflammatory-context ETL pending. NOT CRISPR.
* **GSE240609** APOE3 Christchurch coculture: authenticated; bulk/context ETL pending; do not assume cell-autonomous perturbation.

## 4. Independently implemented parallel PRs — do not lose or conflate authorities

All listed code PRs remain drafts unless GitHub's CURRENT live state proves otherwise. Re-fetch before changing bases.

| PR | Observed head | Purpose and exact status |
|---|---|---|
| #77 | `f34fae312a3006e9eefaa1dfb85749037de9dddd` | Claude's working experimental ETL: GSE301119 RAW PASS, GSE293118 initial, GSE254205 bulk, GSE311359 V1 producer **now subject to #92 STOP**, GSE178317 guide join STOP. |
| #81 | see live GitHub | Independently reviewed Seurat count-parity and raw-pseudobulk R script. Physical run PASS under R4.6.1/SeuratObject5.4.0. |
| #82 | `d65c45745ba36ff93c384d435af1edcc99982453` | Reject self-approved physical roots, forged production hash and overwritable receipt provenance; 46 hosted tests passed. Gate-level; actual R/Python producers must separately wire it in. |
| #84 → #88 → #90 | `4c350e0b...` → `03c5ff97...` → `3669e5c2a9f3e9466ce269efcbd696c4c28746b2` | Target-heldout CPU benchmark and strong descriptive baselines; independent donor-balanced guide scoring (not guide-pseudoreplicated); append-only known historical outcome-exposure floor and fail-closed retrospective-vs-heldout guard. 13/16/9 focused hosted tests (last respective heads) passed, zero skips. Synthetic/metadata mechanics ONLY; no physical benchmark outcomes opened here. |
| #86 | `0ffb62cac6ea3d6e0e1b9cef3fa3e95f2d581e91` | GSE254205 assay-present vs undetected V2 correction; updates stale readiness and exposure prose; 4 focused tests passed. Physical re-execution pending. |
| #87 → #89 | `52ed6e27205ef72ac7f0c7c6f8dbdad059806220` → `06c2b498d13d289382e804340d98baa736dea3ee` | Explicit HGNC/Ensembl feature mapping contract with a single per-operation frozen-annotation validation rather than O(features × mapping size). 10/14 focused hosted tests passed. **NO real annotation file qualified.** |
| #91 | `56600f66492b18af20edcfe5d11761d2cdca9383` | Actual committed SHA-authenticated GSE301119 LIGHTWEIGHT guide×donor metadata census only; 7 tests passed; workflow uploads metadata-only support receipt artifact. Both modalities have 206 targets in both donors; ≥2 guides each donor: 205 CRISPRa / 206 CRISPRi; ≥3: 200/203. CRISPRa HEXA: 1 guide in each donor, guide variance unestimable. Not gene-expression analysis. |
| #92 | `bc09c0f432db6e17bec3047baeb0812975043937` | NEW GSE311359 duplicate BIN1 name red-team STOP; 7 tests passed zero skipped. Source-corrected physical V2 pending. |

## 5. Near-term sequencing across genuinely independent lanes

1. **Claude heavy experimental lane**: independently authenticate the three duplicate BIN1 source feature IDs and the actual protospacer library. If independently resolvable, run versioned ID-keyed GSE311359 V2 and reproduce unafflicted results; if not resolvable, preserve stop and retain legitimate limited/context analyses. Then continue physical GSE301119 transcriptome-wide guide×donor effects using biological-donor-aware uncertainty, GSE175721 guide join, GSE241858/GSE240609 bulk contexts, remaining GSE254205 arms. GSE178317 CRISPR stop remains unless external guide authority arrives.
2. **Independent CPU/statistics lane**: cross-check actual response producers against pseudoreplication and measurement-missingness; repair and integrate #82 gate into real production entrypoints. Use #84/#88 target-heldout baseline only on appropriately authenticated real output, and #90 known-exposure guard BEFORE any benchmark execution. Do not allow GSE311359 V1 ambiguous guide results to become benchmark authority.
3. **Cross-study feature lane**: obtain a REAL separately authenticated/frozen annotation release; apply #87/#89 mapping with collision/release/order tests, published unmapped and ambiguous-ID exclusions. Do not silently merge HGNC/Ensembl or pretend all eight assays measure identical genes.
4. **FULL104 lane**: review #85 successor with actual physical receipt and Level-4 reaggregation gaps, then separately propose future N1 authorization. Do not open N1, D_shared, rare-tail RNA, protected outcomes or V5 training here.
5. **Governance/integration lane**: dependency-order review + merge of accepted PRs, avoid overlapping/superseded branches. Update `START_HERE.md`, pointer, state and this handoff *together*, never only stale prose. Distinguish `PASS` actual physical checks, `PASS_SYNTHETIC`, `STOP`, and `NOT_EXECUTED`.

## 6. Exact startup and code/data references

Repository: `dushyant-mishra/sea-ad-jepa-agent`. Read `START_HERE.md` FIRST; then newest pointer, this handoff, Sep15 historical audits index; fetch live PR heads and compare to snapshot above.

Important physically authenticated GSE301119 light metadata producer SHA pins:
* CRISPRa rawPB guide×donor CSV `e13c3bb2741824139d5adb91b22ad725956078ede98f59cf74a5c1abe96e3397`
* CRISPRi rawPB guide×donor CSV `ce96daa64413a238173b485a91037df02824e85bc071e715292aa800dee7abe8`
* GSE311359 V1 guide-identity CSV `1eeb4e40f14ec2ebe7472d7bb80769ae35bdb8df8ccbf4308493c8441eb363b5` (contains 3× BIN1).

Scripts:
* `analysis/therapeutic_perturbation_etl/scripts/r/extract_intervention_effects_v1.R` (PR #81)
* `analysis/therapeutic_perturbation_etl/scripts/build_gse311359_intervention_effects_v1.py` (PR #77); #92's review successor adds mandatory early STOP; V2 source-ID addressed producer UNBUILT.
* `src/sea_ad_jepa/perturbation/execution_authority_v1.py` (#82)
* `src/sea_ad_jepa/perturbation/benchmark_target_holdout_v1.py` (#84, #88 successor)
* `src/sea_ad_jepa/perturbation/outcome_exposure_ledger_v1.py` (#90)
* `src/sea_ad_jepa/perturbation/cross_study_feature_contract_v1.py` (#87, #89 successor)
* `src/sea_ad_jepa/perturbation/gse301119_support_audit_v1.py` (#91)
* `analysis/therapeutic_perturbation_etl/scripts/build_gse254205_drug_response_v2.py` (#86).

Physical source and large derivative paths remain on Claude's GPU machine; use the exact current PR #77 and #83 manifests, verify full bytes, and copy only lightweight manifests to GitHub. **No heavy asset in this chat may be assumed to substitute for Claude's physically authenticated source.** Absence of a file is STOP, not a request to synthesize its bytes.

## 7. Takeover guardrail

Next agent MUST NOT report GSE311359 as globally guide-level PASS based solely on V1 target-engagement counts, or GSE178317 as a CRISPR-response dataset. Do not automatically infer an individual gene's cis-target from a noncoding perturbation label. Do not count cells as biological replicates or artificially boost guide-level support by duplicating within-donor guides. Never call synthetic or metadata-only receipts a completed real molecular experiment. Do not authorize prospective heldout confirmation using a self-declared untouched flag. Do not merge draft PRs solely because CI passed: verify parentage and scientific authority before acceptance.
