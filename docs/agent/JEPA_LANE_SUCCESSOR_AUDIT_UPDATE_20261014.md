# JEPA lane successor audit update — 2026-10-14

Status: `HISTORICAL_AUDITS_CONSOLIDATED__CURRENT_GATE_IMPLEMENTATIONS_CUSTODIED__PHASE2_AUTHORIZED_ONCE_NOT_EXECUTED__REAL_TD_OFF`

This is the current read-first audit addendum for PR #322. It exists so a successor does **not** repeat historical archaeology, revive closed experiments, or re-derive the current G6/G7/G8/R1 mechanics from chat.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No real-data TD, target selection, representation selection, TD60, Stage 4, production EMA selection, multimodal training, or JEPA training is authorized by this audit surface.

## 1. Current canonical surfaces

- PR #322 — historical/audit custody: `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`.
- PR #323 — read-first takeover/handoff: `handoff/jepa-lane-takeover-20261013`.
- PR #329 — exact phase-2 controller authorization only: `science/td-phase2-controller-authorization-20261013` at `9663c3b45e8ea58bfc5624ff9cb4ed7a67e4d0f7`.
- PR #341 — real blocked-gate design/history lane: `design/td-real-blocked-gates-resolution-v1-20261013` at `8ae96cbddfc29749c72ec1bbceef9ff6a40f2fe4`.
- PR #343 — G8 measurement reference: source head `82d17bfb1650d97a95d5424160126791f09d7494`, Actions run `38489523630`, `11 passed`.
- PR #345 — G6 teacher-information diagnostic: source head `f16ba70f7066db2928e31f31b7785831a8fc10f2`, Actions run `38489595232`, `10 passed`.
- PR #346 — G7 evidence-ladder contract: source head `5a314bdeda9078d5f65e995e49d2ebf5274751f6`, Actions run `38490004001`, `9 passed`.
- PR #347 — repaired R1 relational manifest: source head `877242a6c8206ea35a73ebf111cb6b52bbe79109`, Actions run `38490456813`, `13 passed`.

The implementation PR heads above remain the exact source identities for their original blobs and CI evidence. Copies on this audit branch are custody/convenience copies; if byte identity matters, compare against the listed source head/blob.

## 2. Historical audits now consolidated here

The existing PR #322 audit already carries the robust-pipeline audit, historical architecture decision ledger, gene-identity reclassification, downstream implementation-readiness audit, phase-1 receipt audit, post-TD harness custody, validators, hostile tests and machine mirrors.

This update adds:

- `TD_REAL_BLOCKED_GATE_HISTORY_CROSSCHECK_20261014.md` — gate-by-gate historical classification for G6/G7/G8/G9/S1/S2/G11/G12 and standing history-check rule.
- `TD_REAL_RELATIONAL_HISTORY_CROSSCHECK_20261014.md` — preserves TD56/57B/57C/59 scope, graph/rare control history and the current R1/R4 interpretation boundary.
- exact phase-2 governance documents from PR #329: authorization, execution packet, independent audit checklist, and downstream decision tree.

Historical interpretation that must not be re-litigated without changed inputs/contracts:

- TD57B historical scale-free triplet order = strong historical incumbent, not current biological authority.
- TD57C nearest-third fine-local recurrence = historically closed FAIL; do not reopen/mine on the same evidence.
- TD59 nearest-half = historical mesoscale prior only, not production constant.
- old graph/STRING/GRN failures do not imply relational or rare biology is absent.
- Stage69–71 rare/graph results are internal/scoped; they can constrain controls but cannot become current target authority.
- source-specific failure stays source-specific; scale-specific failure stays scale-specific; `NOT_ESTIMABLE` is not FAIL.
- pre-repair cross-source/NPH gene-semantic results cannot become current biological authority unless repaired address binding is established.
- semantics-free mechanics may remain reusable across the gene-ID incident.

## 3. Current implementation custody added to PR #322

### G8 measurement reference

Custodied paths:
- `scripts/v5/td_real_measurement_reference_v1.py`
- `tests/v5/test_td_real_measurement_reference_v1.py`
- `.github/workflows/td-real-measurement-reference-v1.yml`

Source qualification: PR #343 / run `38489523630`, `11 passed in 0.16s`.

Frozen meaning: technical count-thinning calibration only; displacement and support are protected jointly; family alpha 0.01 across 3 depths x 2 endpoints gives `alpha_eff=0.01/6` and minimum `n=599` calibration realizations per depth/reference unit. Count thinning is measurement, not biological-evidence convergence.

### G6 teacher-information diagnostic

Custodied paths:
- `scripts/v5/td_real_teacher_information_probe_v1.py`
- `tests/v5/test_td_real_teacher_information_probe_v1.py`
- `.github/workflows/td-real-teacher-info-probe-v1.yml`

Exact source qualification: PR #345 / source head `f16ba70f7066db2928e31f31b7785831a8fc10f2` / run `38489595232`, `10 passed in 4.04s`.

Frozen meaning: matched donor-held-out finite ridge diagnostic only. It does not define the target. Teacher and student differ only by prospectively declared evidence rights. A negative human result is operational and cannot be promoted to information-theoretic absence.

### G7 biological-evidence ladder

Custodied paths:
- `scripts/v5/td_real_evidence_ladder_contract_v1.py`
- `tests/v5/test_td_real_evidence_ladder_contract_v1.py`
- `.github/workflows/td-real-evidence-ladder-contract-v1.yml`

Source qualification: PR #346 / run `38490004001`, `9 passed in 0.03s`.

Frozen meaning: static nested evidence-rights contract only. Count/depth thinning is forbidden. At least three lawful levels are required or the gate is `NOT_ESTIMABLE`; strict adjacent monotonicity is not required.

### R1 repaired relational manifest

Custodied paths:
- `scripts/v5/td_real_relational_manifest_v1.py`
- `tests/v5/test_td_real_relational_manifest_v1.py`
- `.github/workflows/td-real-relational-manifest-v1.yml`

Source qualification: PR #347 / run `38490456813`, `13 passed in 0.04s`.

Frozen meaning: static relational identity/provenance only. Candidate = C2; relation family = `SCALE_FREE_TRIPLET_ORDER`; scale = `GLOBAL_SCALE_FREE`; required sources exactly HVS/NPH52/SEA_AD; every relation unit uses three unique `REPAIRED_41K_ADDRESS_BOUND` molecular addresses; no fine-locality mining or graph-topology claim is authorized.

## 4. Phase-2 status correction

PR #329 now provides a narrow authorization that did not exist when the original PR #322/#323 text was written.

Current state:

`PHASE2_CONTROLLER_ADJUDICATION_AUTHORIZED_ONCE__NOT_YET_EXECUTED_IN_THIS_LANE`

Exactly one V4 `adjudicate` invocation is authorized against the frozen phase-1 receipt and certified controller identities. The V4 runner must authenticate receipt bytes and all frozen fit-engine identities before controller read. Output must be frozen and independently audited; no rerun for an inconvenient PASS/FAIL/NOT_ESTIMABLE result.

This authorization qualifies the **TD test only**. It creates no human biological authority.

## 5. External/private data and result custody

`docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv` is now mirrored onto this audit branch. Large/private binaries remain external by design; exact hashes/sizes/classifications are sufficient custody and avoid turning the public audit branch into an uncontrolled data store.

Key identities include:

- repaired 41K archive: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- expression metadata bundle: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`;
- historical defective checkpoint bundle: `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`;
- T1 u0200 transport: `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`;
- program NPZ: `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`;
- phase-1 package: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`;
- phase-1 blinded receipt: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`;
- controller archive: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`;
- raw controller manifest: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`.

Defective T1 checkpoints remain forensic-only and must never be resumed. The repaired 41K archive is useful for address-bound smoke/historical proxy work but is not target/training authority.

## 6. Do not duplicate these investigations

Do not restart the following merely because a new agent did not personally witness them:

- historical architecture audit and closure classification;
- gene-ID provenance incident/reclassification;
- phase-1 synthetic blind-fit structural/custody audit;
- post-TD teacher/student/EMA harness qualification;
- visibility/QC-as-observation-state finding;
- measurement shortcut audit at the tested model class;
- distinction between biological-evidence restriction (G7) and count thinning (G8);
- graph-topology history versus scale-free relational recurrence;
- TD56/57B/57C/59 scope classification;
- closed PR #314 corrected replay;
- defective PROD41K T1 checkpoint forensics.

Reopen only when underlying bytes, provenance bindings, estimand, or genuinely relevant new evidence changes.

## 7. Legitimately unresolved work

The following remain open and should be continued, not rediscovered from scratch:

- execute the single authorized phase-2 adjudication independently, then audit the frozen receipt;
- real-data TD remains unauthorized pending separate authority after synthetic test qualification;
- G2 meaningful biological magnitude still requires an exact effect/noise-relative criterion; do not use donor-refit biological sampling variability as if it were technical noise;
- R4/C6/C4 increment margins remain unresolved in the same sense and must preserve non-compensation;
- G9/S1/S2 require target-geometry-specific alignment/recurrence metrics and cannot inherit historical `0.50` cutoffs;
- G11 needs the frozen candidate x transfer-stratum applicability map;
- G12 needs a pre-outcome biological claim/coverage envelope;
- exact human teacher-target semantics remain open; G6 mechanics must not define the target while testing it.

## 8. Successor starting rule

Read this document, the two 2026-10-14 history cross-checks, the machine custody state, and the PR #323 successor update before new work. Then verify source PR heads/CI. **Do not start another historical audit unless a specific contradiction or changed input is identified.**

Terminal:

`AUDIT_CUSTODY_REFRESHED__HISTORY_ALREADY_CLASSIFIED__G6_G7_G8_R1_IMPLEMENTATIONS_CUSTODIED__PHASE2_ONE_SHOT_AUTHORIZED_NOT_EXECUTED__REAL_TD_OFF__TRAINING_OFF`
