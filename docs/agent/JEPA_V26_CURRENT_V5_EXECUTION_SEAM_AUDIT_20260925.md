# V26 read-only V5 execution-seam audit — 2026-09-25

Status: **ACTIVE IMPLEMENTATION REVIEW; NO REAL TRAINING AUTHORIZATION.** This note is a successor audit, not a modification of PR #123, V25 main, the frozen partitions, or the FULL104 raw store.

## Exact live source lineage audited

- PR #77 head observed at audit: `9a2a30e4c4c99be2a8f948aba680524c786d2737` (`analysis/perturbation-etl-gse301119-claude-20260923`), a direct 218-commit descendant of `integrate/v5-full104-gpt-claude-20260921`. The checked training-module Git blobs on these two refs matched.
- Historical V4 runtime: `src/sea_ad_jepa/v4/teacher_student_runtime.py`, Git blob `9053d157e8132c1b671037b2db197533a6c06677`. It exposes `production_update` with the historical `PRODUCTION_CONFIG` equality check, its own uniform target-block sampling, fixed frozen backbone/predictor registry, and its own optimizer/EMA chronology. Its signature does **not** accept current V5 scientific cell weights, current V5 receipt, or current V5 optimizer guard.
- V5 preexecution: `src/sea_ad_jepa/v5/current_trainer_preexecution_contract_v2.py`, blob `bc5615e402ff74fd4b675cb7397d553eee2a4f8f`: schema and authority-root validation, explicitly training-off.
- V5 issuance: `src/sea_ad_jepa/v5/current_training_authority_v1.py`, blob `aff515aecec36e07cb31fabfdcc53f27495fc090`: V2 closure/receipt/critical-test/runtime-source issuance interface. Unit tests use synthetic authority stubs; a passing stub test is not a physical authority.
- V5 optimizer gate: `src/sea_ad_jepa/v5/qualified_optimizer_guard_v3.py`, audited original blob `7aad89061cb2dd4b5c804d2b4d2b58d3f8a6b85e`.
- V5 inactive mechanics: `src/sea_ad_jepa/v5/inactive_update_reference.py`, blob `3dc61b629c1d4723e7df058f72c1497c4b4c6c20`. It handles synthetic/CPU mechanics and scientific cell weights, explicitly `training_authorized=False`; it is **not** a production entrypoint.
- V5 current runtime source authority requires entrypoint policy `CURRENT_V5_ENTRYPOINT_ONLY__NO_V4_PRODUCTION_UPDATE_V1`. The corresponding tests verify the policy string; that is not an executed current-V5 training lane.

**Observed seam:** the reviewed modules exist but the audit has not established one runnable current V5 entrypoint that binds all of them to the authenticated FULL104 reader, scientific-weight law, current target/mask, physically proved parameter movement/Adam moments/EMA, and atomic checkpoint in the same step. Do not claim integrated V5 training from individual passing unit tests or relabel V4 `production_update` as V5. The source does contain an expressly separate inactive V5 mechanics reference.

## New narrow guard repair: one-use step proofs and contiguous cursors

Red-team inspection of the original V5 optimizer guard found an additional independent safety gap: `assert_step_completed(cursor)` could return the same successful hook receipt more than once, and `arm_for_step` could reset the consumed receipt and accept an identical, skipped or backward cursor. The guard alone did not enforce schedule chronology, so a future caller that omitted a separate chronology check could silently repeat a presentation.

On this isolated branch the guard now:
1. Consumes a completed post-hook receipt exactly once.
2. Refuses to arm a subsequent cursor until the preceding post-hook receipt is explicitly acknowledged.
3. Requires the next armed cursor to equal the last acknowledged cursor + 1; an aborted **unstepped** cursor can be retried.
4. Rejects proof assertions after close. A successful hook receipt remains **hook-level evidence only**, not proof that gradients, parameters, Adam moments, EMA, or an atomic checkpoint are healthy.

Three new adversarial regression tests cover proof replay, duplicate/backward/skipped cursors, premature rearm, abort/retry and mismatched cursor. These are synthetic/fake-optimizer tests, not real training. The existing runtime-closure workflow should separately exercise the change in GitHub CI, and a test must not be reported as passed merely because a job exists.

## Runtime asset reconciliation (local, read-only)

The ten physically mounted files in the current chat runtime were independently byte-hashed on September 25. **All ten matched** their exact size/SHA-bound names in `docs/agent/JEPA_RUNTIME_LOCAL_ASSETS_SHA256_20260925.json` on handoff PR #123: the foundation calibration ZIP, both discovery-expression ZIP parts, their checksum CSV, both text notes, historical `checkpoints.zip`, `expression.zip`, the T1 u0200 ZIP, and the 1.5 MB unidentified NPZ. No full expression file was extracted, no pickle object array loaded, no protected outcome opened. The 29-item GitHub manifest is an inventory, not evidence that all 29 were mounted in this chat.

**Quarantine remains:** the local `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` is SHA256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`; V26 reports conflict with an older expected `14734303...`. Do not relabel this NPZ as an authenticated FULL104 operator-address artifact. Historical T1 checkpoints are not current V5 healthy resume weights. This runtime has none of the authenticated >30 GB GPU-laptop FULL104 raw store.

## Exact next execution boundary

The next *development-only* scientific action requires a separately named diagnostic authorization, one prospectively fixed current target and mask, authenticated 104-`reader_fit` donor inputs and sampler/importance weights (`p_i = 1 / (104 n_{d(i)})`, exact `p_i / q_i` correction under any unequal proposal), and a current-V5 source-bound update/checkpoint path that **does not call** historical V4 `production_update`. Mechanically check gradients, update beyond weight decay, both Adam moments, teacher eval/no-grad and post-step EMA before accepting a healthy step. Freeze evaluation on DEVELOPMENT `reader_fit` donor-held-out folds and matched source/support/depth attacks; compare to the authenticated 94-donor historical Layer-2 linear proxy **only with population/estimand scope disclosed**. Stop if an upstream current masking/teacher-target authority remains unqualified; do not bypass a production stop to show a convenient learning curve.

Reader-validation 22, oracle 23, foundation development 24, sealed foundation holdout 24 and whole-study Siletti remain outside this work. No N1, D_shared, protected inspection, perturbation-effect promotion or therapeutic ranking was opened by this audit or guard patch. No real-data JEPA run was claimed.

## Audit/review boundary

Review this branch as a **small stacked code fix on PR #77**, not as a merge of divergent historical work and not as the complete V5 execution-seam integration. The prior PR #123 V26 handoff remains the successor navigation package. Do not merge or expand scientific execution permissions on the strength of these tests.
