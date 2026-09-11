# CURRENT AUTHORITY INDEX — JEPA PROJECT

Date: 2026-09-11
Status: `CURRENT_T0_V21_DRAFT_EXTERNAL_REVIEW_PENDING_EXECUTABLE_REVIEW__V5_HARDENING__NO_TRAINING_AUTHORITY`

## Canonical startup/governance

`main` is the canonical governance/startup branch. Branch names do not confer scientific or training authority.

Read first, in order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_T0_V21_EXTERNAL_REVIEW_V5_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json`
4. live `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` on the V21 branch
5. `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
6. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
7. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
8. this file and `docs/agent/CURRENT_SUPERSESSION_MAP.md`

Always re-fetch live heads before acting.

## T0 V20 — immutable historical authority

Branch/head:
`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

Primary terminal:
`BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`

Historical broad-state result:
- beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- one-sided p ~0.0210
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

Rare-tail terminal:
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT`

Step 4 result:
`4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`

Step 4 showed that 1:1 QC matching removed Q_DEPTH/Q_DETECT imbalance but simultaneously destroyed held-out-statistic detectability, while a size-matched confound-retaining control also collapsed. Therefore a clean matched null is not causal proof that biology was only confounding.

General successor rule: rejection-capable QC/anti-cheat gates must demonstrate sensitivity/specificity at the exact geometry they create. Cross-cell technical association alone is warning-level evidence.

V20 must not be modified or retrospectively retuned.

## T0 V21 — live draft only

Branch:
`t0/v21-prospective-design-20260910`

Observed live head before 2026-09-11 governance commits:
`11e76d36ace556ac48cdd2992995e63c1e35df18`

File:
`docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`

Status:
`DRAFT_FOR_REVIEW_NOT_FROZEN`

No fresh AT8 value has been opened. `reader_validation` is closed. `reader_oracle` is sealed. Estimator selection has not run. The power gate has not run. V21 has not executed.

Current donor hierarchy:

- 28 discovery donors — all method/estimator/ridge/QC/power choices;
- 18 spent historical-validation donors — development/internal sensitivity only;
- 12 fresh `reader_validation` donors — one single-shot T1 confirmation only after power gate + freeze + store closure;
- 10 `reader_oracle` donors — sealed final reserve.

The design now records:

- closed S0–S4 estimator family;
- deterministic admissibility/ranking/tie-break rule written before selection;
- deterministic ridge bracketing with endpoint STOP;
- all-28 LODO functional-stability envelope, maximum per metric, no averaging;
- nested outer-LODO / inner-LODO OOF power construction;
- one HC3 regression across the assembled 28 OOF donor predictions;
- conservative jackknife-minimum standardized effect across 28 influence refits with a directional-consistency STOP;
- minimum projected power 80% at alpha=0.025 for n=12 before `reader_validation` can open;
- zero power credit for the later 46-donor refit;
- T2 decoupled from T1 freeze;
- MTG retained as primary confirmation tissue;
- cross-region analysis frozen separately as secondary generalisation, never independent confirmation.

**External-review boundary:** `11e76d36` changes the design document only. The latest review blockers are addressed in prose, but the executable estimator-selection and nested OOF power-gate implementation has not yet been independently verified against that contract. Do not run the single-shot S0–S4 selection until executable review and adversarial tests close.

Mandatory implementation review checks include:

- held-out donor absent from both beta fit and lambda choice;
- exactly one OOF prediction per discovery donor;
- one HC3 regression across the assembled OOF vector, not one regression per fold;
- correct residual df and nuisance design;
- jackknife influence refits standardized using their actual sample size/statistic;
- sign reversal -> `STOP_EFFECT_DIRECTION_NOT_CONSISTENT`;
- no AT8 outcome from the spent 18 in the power gate;
- exact implementation of candidate admissibility/ranking/tie-break;
- fail-closed handling of missing/duplicate folds and provenance mismatch.

Standing rule:
`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## Historical C2 / mechanics authority

Historical u10–u205 remain:
`TRAINING_MECHANICS_DEFECT_INHERITED`

Historical 128x8 was not primarily OOM-limited. The failure class included exact-zero/invalid protected gradients and identity/pandas mechanics.

Mandatory successful update chain:

`FP16_FORWARD -> BACKWARD_AUTOCAST_DISABLED -> UNSCALE -> PROTECTED_48_GRADIENT_GATE -> OPTIMIZER_STEP_PROVED_BEYOND_DECAY -> ADAM_EXP_AVG_PROVED -> ADAM_EXP_AVG_SQ_PROVED -> EMA_UPDATE -> SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE -> ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

Corrected mechanics are necessary but never sufficient for training authority.

## Authenticated V5 production population

- 4,553,407 reader-fit cells
- 104 donors
- 42 matrices/operators
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Production-scale values must come from the authenticated real substrate or prospectively frozen risk/error rules. Synthetic fixtures may test mechanics only.

## V5 current state

Branch/head observed before 2026-09-11 governance commits:
`planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

Structural hardening includes:

- `z_bio` biology-only objective/checkpoint path;
- `z_obs` for nuisance/measurement information;
- fail-closed representation-gradient routes;
- warning-only cross-cell QC association;
- complete same-cell intervention family;
- two-sided exact-geometry valid/invalid calibration for rejection-capable gates;
- exact checkpoint/design-context binding;
- separate pre-execution and learned-checkpoint/postqualification evidence;
- dependency-closed evidence bundles;
- bounded qualification separate from broad training;
- production-GPU authority separate from historical C2 mechanics.

### Corrected TRAIN-cache authority

The uploaded corrected TRAIN cache is exact:

- terminal `PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY`;
- 42/42 counts/meta shard pairs;
- 4,726 physical TRAIN rows;
- 41,238 addresses;
- loader-manifest SHA-256 `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`.

This is not FULL104.

Current expression blocker:
`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

Required separate Phase2/FULL104 Level-4 substrate:

- 4,553,407 cells;
- 104 donors;
- 42 matrices/operators;
- 41,238 addresses;
- 8,915 blocks;
- historical manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.

Required terminal:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

No TRAIN cache, 50K subset, synthetic expression, validation/oracle source or different-byte substitute may satisfy it without prospective re-authorization.

### Real schedule/proposal/packing/restart authority

Authenticated full-reader metadata closes:

- H = 5,267,086 presentations;
- proposal `q_i = m_i/H`;
- target `p_i = 1/(D n_d)`;
- exact importance weight `w_i = H/(D n_d m_i)`;
- exact affine-order replay;
- exact packing replay at 128 and 576;
- exact full-horizon restart replay;
- canonical presentation-stream SHA-256 `08a1df725b3803d049cf6a0a75811c1863b4bd0b537ed2ecaf70445380f02f74`.

Terminal:
`PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY`

This creates no expression, production-dimension, GPU, biological, postqualification or training authority.

## V5 unresolved blockers

Still unresolved:

- 8,915-block FULL104 expression binding/identity closure;
- production dimensions `D_shared`, `D_private`, `D_total`, `D_obs`, `d_gene`;
- remaining prospective numerical gate authorities where not already structural;
- production-geometry CUDA Gate-2 evidence;
- clean bounded qualification;
- learned-checkpoint shortcut/collapse/same-cell evidence;
- dependency-closed postqualification bundle;
- independent review;
- broad production training authorization.

Historical 5/96/160/224/320/512 are not production authority.

## Training authority

All remain false:

- V5 production training
- successor-u0 production training
- V21 fresh confirmation execution before its gates
- reader_oracle execution
- DEV/SEALED/protected populations unless separately authorized
- pathology-guided tuning

## Precedence

When artifacts disagree:

1. live `main` + `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `JEPA_NEW_CHAT_HANDOFF_20260911_T0_V21_EXTERNAL_REVIEW_V5_CURRENT.md` + its state JSON
3. this index
4. `docs/agent/CURRENT_SUPERSESSION_MAP.md`
5. exact lane-specific frozen contracts/reviews and prospective drafts
6. FINAL R4 formulas/heavy-asset ledgers where not superseded
7. older historical governance

Never infer authority from a branch name, timestamp, unit-test PASS, CI PASS, smoke PASS, design-document edit, or decreasing loss.

**Training remains OFF.**
