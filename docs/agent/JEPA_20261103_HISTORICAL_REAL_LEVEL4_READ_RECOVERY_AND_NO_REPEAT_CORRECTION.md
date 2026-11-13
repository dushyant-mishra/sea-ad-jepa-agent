# Historical real source reads recovered — no-repeat correction to November 3 Level-4 proposal

**Date:** 2026-11-03. **Type:** owner-prompted historical evidence recovery and append-only plan correction. **Priority:** supersedes the *execution-next* instruction in `JEPA_OWNER_DELEGATED_NARROW_QC_AND_SINGLE_LEVEL4_DECISION_20261103.md` and its machine companion, **not** the owner's limited scope delegation or any original experiment/receipt. Never alter original PR #59/#69/#314/#492/#513 artifacts.

## Executive correction

The prior instruction, "Macha should select and execute one first eligible SEA-AD reader_fit Level-4 block", was **premature and redundant as a default**. The project already conducted substantial authenticated real Level-4 reads. **No new block read is assigned or required as the next action.** The previously delegated one-block permission remains a maximum possible scope only **if** an exact retrospective field-gap inspection proves that an essential CaseBundle value cannot be obtained or derived lawfully from previously completed execution and if pre-execution source/rights gates are accepted. Absent that proof, **STOP_NO_NEW_READ__REUSE_EXISTING_EVIDENCE**.

### 1. Actual raw Level-4 read executed September 22 — PR #59

Original [PR #59](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/59) exact head `1bdff2a8f12d7971652dcf92b5b81ca45c37a933`, original receipt `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i/DONOR_UMI_INDEPENDENT_QUALIFICATION_V1.json` (Git blob `e3a0926a81a278f49f155906a11c1eb35baa95cb`), original execution script `analysis/v5_full104_information_channel_redteam_20260920/scripts/qualify_donor_umi_independent_v1_20260922.py` (blob `4193cfed494bf5c18968d813ee3553a41adb84db`):

- **387 actual raw-count Level-4 blocks read and SHA-checked**, over six prospectively SHA-salted selected donors; **all 8,915 block metadata files SHA-verified**; **4,553,407 cells accounted exactly once** in metadata; original Level-4 manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
- Across six donor × **17,186 strict-core molecular addresses**, independently computed `donor_nnz` (number of cells with nonzero counts) and `donor_umi` (sum of actual integer counts) exactly match existing heavy sufficient-statistics artifact `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`, without numerical tolerance. Original frozen verdict `DONOR_UMI_INDEPENDENTLY_QUALIFIED` **at six-donor scope only**; not all 104 donors, not new target/teacher/CaseBundle.
- Note raw count blocks were read for sampled donors; the 8,915 metadata count **is not** proof all 8,915 count blocks were read, and 4,553,407 cell coverage is metadata/cell-identity coverage, **not** 4.55m per-cell q-level truth checks.
- The script's input metadata includes `source_library` and it re-authenticates selection row and donor identity. Its emitted qualifying result is **donor-aggregated strict-core counts**, not a persisted, separately qualified CaseBundle per-cell q/physical-total pairing.

### 2. Crucial historical source-label correction: PR #69 (DO NOT REPEAT #59)

Original [PR #69](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/69) head `83b85382f22a7672a5beb1ef9154e5b8bf36e16f`, receipt `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i/SIX_DONOR_SUCCESSOR_QUALIFICATION_V1.json` (Git blob `28418462bf4e4ddab0794bc8d7c759d121b67476`) and source derivative `CANONICAL_SOURCE_DERIVATIVE_MANIFEST_V1.json` (blob `0ad8521c82b1d590362016011efe6faf8237cdde`):

- The original #59 numeric array is exact but **four original source labels are transposed**: donor codes 64/76 (H20.33.043 / H21.33.028) are **SEA_AD**, not NPH52; donor codes 94/96 (human_NPH_896 / human_NPH_906) are **NPH52**, not SEA_AD. HVS original labels were correct. Original source_names stored `[HVS,SEA_AD,NPH52]`, corrected canonical order `[HVS,NPH52,SEA_AD]`.
- All six `donor_nnz` and `donor_umi` numerical rows are unchanged, with per-row value SHA checks; 33/35 derivative array values were identical, only two source-code arrays corrected. PR #69 explicitly records `raw_reaggregation_proved_for_all_104_donors=false`, `re_run_of_six_donor_raw_comparison_required=false`.
- **Do not cite #59's original swapped labels as biology**, do not require Macha to rerun the 387-block raw comparison, and do not treat #69's metadata-only repair as a new raw count read.

### 3. Other already-executed real-data reads with different authority

| Historical record | What was already observed | Scope limit |
|---|---|---|
| [PR #492](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/492) `79d2f9364970c0e5b678caae94b92a803ff03623` | Frozen 50,000-cell × 41,238-address sample, 246,702,069 nonzero transformed expression values inverted to integer raw counts (max residual ≤ 2.2e-11); source-specific 50k support/depth residual aggregates | Archived 50k sampled expression, **not** all Level-4 cells or source-verified per-cell q-right release |
| [PR #314](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/314) `c6899a2910244a0352c0c57e7aea6e3026191da1` | Authorized real corrected TD56/TD57B/TD57C/TD59 scientific replay **executed once, spent**, observed broad/meso PASS and fine-local TD57C FAIL | Real experiment exhausted; not a CaseBundle issuer or right to rerun |
| [PR #513](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/513) `0b1af4f06ba423753899e7c564d3b16ce609ac6a`, with [#528 correction](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/528) `1a4fda758936a3cc3868948b44d25694de216bd9` | QC metadata `Doublet score`, `is_primary_data`; 4,118,213 SEA-AD same-deposit matrix/UMI totals equal; HVS deposited full-library ratio median 0.915 (unknown cause); 35 matrix admission receipts | #513 probe expressly states **count matrices not read** in that operation; same-deposit totals ≠ independent external provenance; QC output does not qualify q-independence |
| [PR #147](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/147) `9f7818472bdf515680b85eddbbf761eae2208020` | 104/104 donor and 4,553,407-cell pass1→calibration histogram count bridge physically executed | Explicitly **0 raw Level-4 count blocks opened**, no per-cell q proof; don't conflate with #59 |

## Revised next action: exact existing-receipt coverage audit, no numeric source opening

1. Locate original PR #59 raw-count qualification source, raw SHA roots and #69 corrected-label receipt; #492 50k sampled-expression audit; #513/#528 depositor/QC receipts and source feature/rights tables. **Do not recompute, redownload, rerun or open a new block.** The source files are already in the project/GPU custody.
2. Build a **field-by-field source→CaseBundle coverage matrix** over existing receipts for: source/matrix/block/selection row, donor/library, physical per-cell source total, molecular-address raw count, measured/structural/collision support, query alias class/right, withheld q-excluded student D1, parent/source/task2 access receipt, private CaseBundle output. Status each `EXISTING_PHYSICALLY_EVIDENCED`, `PRESENT_BUT_UNQUALIFIED`, `NOT_RETAINED_IN_OLD_RECEIPT`, or `NOT_ESTIMABLE`. The original six-donor aggregate comparisons **cannot be silently substituted for per-cell CaseBundle truth**.
3. If an existing source-bound actual per-cell CaseBundle candidate/producer is discovered on any accepted branch, use it. Otherwise implement only missing **offline code/adapter using synthetic hostile fixtures** first. No new read merely to test code.
4. Only if a specific indispensable per-cell count or source-denominator field **cannot be verified from retained artifacts** and has no accepted derivation, may the original narrow single-block owner-delegated scope be considered. Freeze **a new no-outcomes precommit and independent reviewed source-read plan** using current source rights and explicitly cite the confirmed missing field. A prior approval is a **ceiling**, not a mandate to spend or recollect the block. Check any existing already-read SEA_AD block coverage before proposing a new one.
5. No additional QC read by default: #513 aggregate results already exist, and #528 software `REPLAY_HOLD` remains effective. The owner-delegated QC-only allowlist resolves the narrow governance question but does not imply a rerun.

**Decision now:** `REUSE_EXISTING_LEVEL4_SOURCE_EVIDENCE__NO_NEW_READ_ASSIGNED__CASEBUNDLE_FIELD_GAP_AUDIT_FIRST`. Historical owner-delegated permission is **not withdrawn**, but the instruction to select/execute one fresh SEA_AD block as an immediate next step **is superseded and suspended**. The prior proposed block has **not** been selected/committed or read in this new plan.

**Authority unchanged:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
