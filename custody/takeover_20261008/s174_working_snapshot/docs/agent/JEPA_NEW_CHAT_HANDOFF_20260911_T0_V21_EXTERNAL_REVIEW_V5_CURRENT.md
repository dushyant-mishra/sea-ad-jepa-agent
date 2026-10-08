# JEPA NEW-CHAT HANDOFF — 2026-09-11 — T0 V21 EXTERNAL REVIEW + V5 CURRENT

Status: `CURRENT_HANDOFF__T0_V21_DRAFT_EXTERNAL_REVIEW_PENDING_EXECUTABLE_REVIEW__V5_HARDENING__NO_TRAINING_AUTHORITY`

**Training remains OFF.** Nothing in this document authorizes production training, opening `reader_validation`, reading fresh AT8 outcomes, modifying frozen V20, or treating a design-document change as executable scientific authority.

## 0. New-chat startup order

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Read in this order:

1. `START_HERE.md`
2. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
3. **this handoff**
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json`
5. `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` on the live V21 branch
6. `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
7. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
8. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
9. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
10. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

Before any write, re-fetch live heads. Observed immediately before this handoff:

- `main`: `6f0209c1bcd950ef056f0ae96a35aa5b3ee079b9`
- frozen V20: `d5d67e21398da92e39095afd864b4fb9ebe3da02`
- V21 draft: `11e76d36ace556ac48cdd2992995e63c1e35df18`
- V5 engineering: `1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`
- T0 Step 4: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`

Branch names do not confer scientific authority.

## 1. Division of labor

- **Claude lane:** T0/V21 only unless the owner explicitly changes scope.
- **This ChatGPT lane:** V5 teacher/student anti-cheat and production qualification framework.
- Keep the lanes logically independent. Do not use V21 confirmation outcomes to tune V5, and do not use V5 learned outcomes to rewrite V21 confirmatory rules.

## 2. Authenticated production population

Current reader-fit authority:

- 4,553,407 cells
- 104 donors
- 42 matrices/operators
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic data is mechanics/unit-test only. It cannot set production biology, dimensions, schedules, thresholds or training authority.

---

# PART A — T0

## 3. V20 is immutable

Branch/head:
`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

Frozen terminals:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- training unauthorized

Historical broad-state donor-level result:

- beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- one-sided p ~0.0210
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

Step 4 (`4d95355e...`) showed that 1:1 QC matching removed Q_DEPTH/Q_DETECT imbalance but destroyed held-out-statistic detectability; a size-matched confound-retaining control collapsed too. Therefore a clean matched null did **not** prove the biology was only confounding. General rule: any rejection-capable gate must prove discrimination/power at the exact geometry it creates.

Do not modify or retrospectively reinterpret V20.

## 4. V21 live state

Branch:
`t0/v21-prospective-design-20260910`

Observed head:
`11e76d36ace556ac48cdd2992995e63c1e35df18`

Status:
`DRAFT_FOR_REVIEW_NOT_FROZEN`

At this head:

- no fresh AT8 value has been opened;
- `reader_validation` has not been opened;
- `reader_oracle` remains sealed;
- nothing has been fitted under V21;
- estimator selection has not run;
- the V21 power gate has not run;
- V21 has not executed.

**Critical external-review note:** commit `11e76d36` modifies only `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` (198 additions / 59 deletions). It addresses the latest external-review blockers **in the design document**, but it does not itself implement or test the new nested OOF estimator-selection/power-gate machinery. The next reviewer must inspect executable code before authorizing Step 1.

## 5. V21 donor hierarchy

Owner-approved four tiers:

1. **28 discovery donors** — target/estimator/ridge/QC/power method choices.
2. **18 spent historical-validation donors** — internal sensitivity/development only; not fresh confirmation.
3. **12 fresh `reader_validation` donors** — one single-shot T1 confirmation only after power gate + full freeze + validation-store closure.
4. **10 `reader_oracle` donors** — untouched final reserve.

Standing rule:
`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## 6. What V21-T1 is trying to test

Primary confirmatory question:

> Does the broad immune expression state in MTG associate with AT8 pathology in genuinely fresh donors?

MTG remains the primary tissue. MEC/PFC etc. reuse the same reader-fit donors and are **cross-region generalisation**, not independent confirmation. The separate cross-region analysis is secondary and must not alter T1 after freeze.

T2 rare/continuous biology is now a separate exploratory track. It inherits T1's frozen estimator/infrastructure and may not alter any T1 quantity after T1 freezes.

## 7. Estimator family and selection contract

Closed family:

- `S0`: frozen V20 score baseline
- `S1`: detected-set matched offset
- `S2`: S0 on common measured core
- `S3`: S1 on common measured core
- `S4`: weighted within-cell ranks on the core

No dropout-model candidate is added before selection.

Selection is discovery-only and single-shot.

Frozen selection logic at `11e76d36`:

1. **Admissibility:** preserve held-out biology within `S0`'s own LODO envelope. This prevents a trivially flat/noisy score from winning merely because it is measurement-stable.
2. **Rank admissible candidates:** worst-case standardized same-cell displacement across all frozen retention levels/draws; maximum, not average.
3. **Tie handling:** ties relative to the LODO envelope of the ranking quantity break to earliest declared candidate in `S0 < S1 < S2 < S3 < S4` (fewest modifications first).
4. Publish the complete candidate table.

`LODO/LOODO` means leave one donor out. Each held-out donor must not influence the fit or hyperparameter choice used to score that donor.

## 8. Ridge identification contract

Ridge uses deterministic discovery-only bracketing/refinement rather than a guessed wider fixed grid.

Near-optimal lambda set is defined from paired donor-level LOODO loss differences.

Functional stability is checked per metric using all 28 leave-one-donor-out refits:

- beta-direction displacement;
- cell-score rank/geometry displacement;
- donor-summary displacement.

Envelope = maximum LODO displacement **per metric**, with no averaging. Lambda-induced displacement must remain inside its own envelope for all metrics. Any metric exceeding its envelope -> `STOP_RIDGE_SELECTION_NOT_IDENTIFIED`.

A flat CV surface can be flagged without rejection if the resulting estimator is functionally stable.

## 9. Correct V21 power-gate construction

The target fit is AT8-supervised (`fit_discovery_target_v2` uses donor metadata containing `AT8`; lambda is selected on predictive loss for that outcome). Therefore a 46-donor refit cannot supply an independent effect estimate for deciding whether to spend the fresh 12.

The gate must use the 28 discovery donors only.

### Nested OOF construction

For each of the 28 discovery donors:

1. hold that donor out;
2. fit beta on the other 27;
3. choose ridge inside those 27 using its own inner LOODO procedure;
4. generate exactly one out-of-fold (OOF) donor predictor for the held-out donor.

After all 28 folds, assemble the 28 OOF donor scores and fit **one** donor-level HC3 regression with frozen nuisance design:

`[1, age_c, age_c^2, sex]`

For n=28, residual df = 28 - 5 = 23.

The prior wording "HC3 evaluated on the held-out donors" was invalid because one held-out donor cannot support a donor-level regression.

### Conservative effect for power projection

The draft now proposes a jackknife/worst-case construction:

- recompute the OOF HC3 effect 28 times, each time omitting one donor from the assembled OOF vector;
- all influence refits must agree in direction, otherwise `STOP_EFFECT_DIRECTION_NOT_CONSISTENT`;
- use the minimum standardized effect across those 28 influence refits;
- project to n=12 at alpha=0.025 using a noncentral-t model with residual df 7;
- the 46-donor refit's expected sharpening receives **zero** power credit.

Draft shorthand:

`delta = t / sqrt(n)`

`projected_n12_signal = delta_min * sqrt(12)`

Power is then computed from the noncentral t at df = 12 - 5 = 7.

### Mandatory re-review point before execution

The executable implementation must make the jackknife standardization explicit. Each influence regression contains 27 donors, so the reviewer must verify that each standardized effect uses the actual sample size/statistic of that influence refit (rather than accidentally reusing the n=28 scaling). This is not yet verified in code because `11e76d36` is documentation-only.

Gate requirement:

- projected power >= 80% at alpha = 0.025 -> T1 may proceed to validation-store build/freeze sequence;
- otherwise `reader_validation` stays sealed and V21-T1 remains a methodology/development result.

## 10. V21-T1 remaining sequence

Before T1 freeze:

1. **External executable re-review** of the selection/power implementation against the frozen draft. Do not skip this merely because the prose blockers were addressed.
2. Run estimator selection once on the 28 discovery donors.
3. Run the nested-OOF conservative power gate on the selected estimator.

Only if the power gate passes:

4. Create a new `T0_V21_VALIDATION_POPULATION_AUTHORITY` for `partition='reader_validation'`; do not amend V20.
5. Build the op31 validation expression store.
6. Extend age/sex authority for the fresh donors.
7. Re-run population, identity, completeness, physical-read-plan and provenance closure.
8. Freeze the complete V21-T1 contract.
9. Explicitly record owner-authorized opening of `reader_validation`; `reader_oracle` remains sealed.
10. Open fresh AT8 outcomes once and run the single confirmatory T1 test.

No retuning after the 12 are opened.

---

# PART B — V5 TEACHER/STUDENT ANTI-CHEAT LANE

## 11. V5 live state

Branch:
`planning/v5-full-population-cheat-proofing-20260909`

Observed head:
`1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

V5 currently contains:

- `z_bio`/`z_obs` representation firewall;
- fail-closed representation-gradient routes;
- warning-only cross-cell QC association;
- complete same-cell intervention-family qualification;
- two-sided exact-geometry valid/invalid control calibration for rejection-capable gates;
- exact checkpoint/design-context binding;
- pre-execution vs learned-checkpoint/postqualification separation;
- dependency-closed evidence bundles;
- bounded qualification separate from production training;
- production-GPU authority separate from historical C2 mechanics;
- real full-population schedule/proposal/packing/restart replay.

## 12. Corrected TRAIN-cache result

Uploaded runtime asset:
`/mnt/data/stage81a3r_corrected_real_train.zip`

It exactly binds the corrected TRAIN cache:

- 42/42 counts/meta shard pairs;
- 4,726 physical TRAIN rows;
- 41,238 addresses;
- loader-manifest SHA-256 `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`;
- terminal `PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY`.

This is **not** FULL104 closure.

Current production-expression blocker:
`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

The required separate historical Phase2/FULL104 Level-4 materialization is:

- 4,553,407 cells;
- 104 donors;
- 42 operators/matrices;
- 41,238 addresses;
- 8,915 blocks, nominally 512 rows/block;
- historical root `outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`;
- block-manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.

Binder:
`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Required terminal:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

No TRAIN cache, 50K subset, synthetic fixture, validation/oracle partition, or different-byte replacement may satisfy this without prospective re-authorization.

## 13. Real schedule / proposal / packing / restart closure

From authenticated full-reader metadata:

- unique cells = 4,553,407
- donors = 104
- total presentations H = 5,267,086
- proposal `q_i = m_i / H`
- target `p_i = 1 / (D n_d)`
- exact importance weight `w_i = H / (D n_d m_i)`
- canonical presentation-stream SHA-256 `08a1df725b3803d049cf6a0a75811c1863b4bd0b537ed2ecaf70445380f02f74`

Production-scale replay terminal:
`PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY`

It includes exact affine order, exact packing replay at physical batch sizes 128 and 576, and exact full-horizon restart replay. It creates no expression, dimension, GPU, biology, postqualification or training authority.

## 14. V5 remaining blockers

Still unresolved:

1. recover/rebind the separate 8,915-block FULL104 expression store (or prospectively rebuild an exact-authorized equivalent);
2. close `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
3. derive production dimensions from the exact full real expression stream:
   - `D_shared`
   - `D_private`
   - `D_total = D_shared + D_private`
   - `D_obs`
   - `d_gene` as neural/token capacity;
4. freeze/derive remaining production numerical gate authorities for collapse, shortcut superiority, same-cell stability and discrimination where not already fixed structurally;
5. obtain production-geometry CUDA Gate-2 evidence;
6. run a clean bounded qualification;
7. obtain learned-checkpoint shortcut-superiority/collapse/same-cell robustness evidence;
8. build the dependency-closed postqualification bundle;
9. independent review;
10. only then consider production training authorization.

Historical dimensions 5/96/160/224/320/512 are **not** production authority.

## 15. V5 anti-cheat scientific rule

Historical teacher/student systems repeatedly found shortcuts. Therefore:

- low loss is not enough;
- above-chance performance is not enough;
- technical-variable predictability alone is not causal evidence;
- `z_bio` must beat prospectively frozen shortcut baselines on held-out units by a prospectively frozen increment;
- same-cell perturbations must show biological conclusions are stable to measurement changes;
- donor recurrence/inference is required;
- training remains off until the exact production evidence graph closes.

---

# PART C — RUNTIME ASSETS AVAILABLE IN THIS CHAT

## 16. `/mnt/data` assets observed immediately before handoff

Present:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` (~392 MB)
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` (~290 MB)
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` (~290 MB)
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `checkpoints.zip` (~69 MB)
- `t1_checkpoint_u0200.zip` (~223 MB)
- `expression.zip` (~3.5 MB)
- `stage81a3r_corrected_real_train.zip` (~49 MB)
- `JEPA_NEW_CHAT_HANDOFF_FINAL4_20260910.zip`
- `WSL execution issue.txt`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` (~1.5 MB)

The last NPZ remains `PROVENANCE_MISMATCH_DO_NOT_USE` until reconciled.

Historical verified hashes that remain relevant:

- Foundation calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- Foundation 41K discovery expression assembled stream: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- discovery part001: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- discovery part002: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`

See `JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json` and the heavy-asset ledger before treating any runtime file as authority.

---

# PART D — IMMEDIATE NEXT ACTIONS

## 17. Claude / T0 next action

**Do not run estimator selection yet until executable external review closes.**

The next chat/reviewer should:

1. inspect the actual implementation that will execute S0–S4 selection;
2. confirm the nested outer-LODO / inner-LOODO separation;
3. verify every held-out donor is absent from both beta fit and lambda selection;
4. verify the single HC3 regression is across the assembled OOF donor scores, not inside folds;
5. verify jackknife influence standardization uses the actual influence-refit sample/statistic and direction rule;
6. verify no 18-donor spent AT8 outcome enters the power gate;
7. verify selection admissibility/ranking/tie-break exactly matches the frozen prose and cannot be changed after results;
8. add adversarial tests for leakage, fold identity, duplicated/missing OOF predictions, wrong nuisance df, wrong jackknife n, sign reversal, and fail-open paths.

Only after those pass should Claude run Step 1 once.

## 18. This environment / V5 next action

Continue V5 work that does not falsely substitute the TRAIN cache for FULL104. Highest-value actions:

- search/recover the historical 8,915-block Level-4 store or its exact provenance/manifest path;
- if unavailable, harden a prospectively authorized deterministic rebuild contract rather than faking closure;
- continue metadata-only/pre-expression qualification work that does not require learned full-corpus geometry;
- keep production dimensions and learned biological thresholds unresolved until FULL104 expression identity closes.

## 19. Permanent fail-closed rules

- V20 immutable.
- No fresh AT8 before V21-T1 complete freeze and power gate PASS.
- `reader_oracle` stays sealed.
- No result-driven changes after opening fresh confirmation.
- No historical/synthetic dimensions promoted to production.
- TRAIN-cache PASS != FULL104 PASS.
- Smoke PASS != biological authority.
- Unit tests/CI PASS != training authority.
- Decreasing loss != biological qualification.
- Never treat prose design closure as executable closure without code/tests.

**Training remains OFF.**
