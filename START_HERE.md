# START HERE — JEPA PROJECT

Date: 2026-09-11
Status: `CURRENT_POST_CLAUDE_REVIEW_REPAIR_HANDOFF__NO_TRAINING_AUTHORITY`

## Read first

Use `main` for project-current governance/startup context unless a later pointer supersedes this. Read in this order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_POST_CLAUDE_REPAIR_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json`
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md`
5. `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` on the live V21 branch
6. `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
7. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
8. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
9. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
10. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

The earlier `JEPA_NEW_CHAT_HANDOFF_20260911_T0_V21_EXTERNAL_REVIEW_V5_CURRENT.md` and `JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md` remain useful historical context, but startup is now superseded by the post-Claude repair handoff.

Before writing or executing, re-fetch live heads for:

- `main`
- `review/integrated-target-v5-repairs-20260911`
- `repair/v5-qualified-target-guard-20260911`
- `repair/t0-v21-authority-hardening-20260911`
- `t0/v20-pathology-blind-materialization-20260908`
- `t0/v21-prospective-design-20260910`
- `planning/v5-full-population-cheat-proofing-20260909`

Branch names do not confer scientific authority.

## Current post-Claude review update

Claude reviewed these heads:

- `repair/t0-v21-authority-hardening-20260911 @ a36fd209b40aa9c28cd3d6790bda1fe5054a1923` — `PASS_WITH_MINOR_NOTES`
- `repair/v5-qualified-target-guard-20260911 @ 7a2bdfb051e0173c2a6d6bfa50cf57fd110278e0` — `MAJOR_REVISION`
- `review/integrated-target-v5-repairs-20260911 @ f493e531402e8a1148e9abb7011641a7bbbdcda3` — `PASS`

After that review, this chat pushed V5 guard repairs to:

- `repair/v5-qualified-target-guard-20260911 @ a3427815b803382c939cd9741ab7332513ad4a9d`

V5 local focused verification before push:

```bash
cd /mnt/data/v5_patch
PYTHONPATH=src pytest -q tests/test_v5_qualified_target_optimizer_guard_v1.py
# 12 passed in 1.96s
```

The V5 repair keeps the optimizer guard resident, requires the schedule cursor at `optimizer.step` time, burns stale authorization after skipped steps, blocks post-entrypoint direct optimizer mutation, and binds the observed installed target root before mutation. `production_training_authorized` remains false.

T0 V21 wrapper note fixes were verified locally in `/mnt/data/v21_patch` but still require live branch recheck/push if the live branch does not already contain them:

```bash
cd /mnt/data/v21_patch
PYTHONPATH=scripts/v4 pytest -q scripts/v4/test_t0_v21_authority_v1.py scripts/v4/test_t0_v21_measurement_and_freeze_v1.py
# 23 passed in 0.15s
```

Those V21 local fixes cross-check declared ridge metadata against all fold records and enumerate allowed `effect_estimand` values, excluding HC3/t-over-sqrt-n transport until a derivation exists.

## Integrated production-review boundary

For production authority, target discovery and V5 are one scientific chain:

`raw SEA-AD substrate → discovery population/masks → target discovery → target statistical qualification/freeze → teacher target → V5 student/teacher training → downstream evaluation`

A V5 anti-cheat review by itself is not a complete production-pipeline review. A technically strong V5 model can still learn a circular, confounded or leakage-derived target. Conversely, a valid biological target can still fail if V5 finds identity, technical or same-cell shortcuts.

Current target-discovery external-review status:

`IN_PROGRESS_NOT_YET_END_TO_END_EXTERNAL_CODE_EVIDENCE_REVIEW_COMPLETE`

Training remains OFF.

## Current project boundary

Authenticated production population:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / 42 matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic data may be used for unit/mechanics tests only. It may not set production biology, dimensions, schedules, thresholds or training authority.

## T0 / target discovery

Frozen V20:
`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

V20 remains immutable:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- training unauthorized

V21 live draft observed before this handoff:
`t0/v21-prospective-design-20260910 @ 11e76d36ace556ac48cdd2992995e63c1e35df18`

Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`.

No fresh AT8 value has been opened, no protected partition has been opened, estimator selection has not run, the power gate has not run, and V21 has not executed.

The design records:

- 28 discovery donors for all method/estimator/ridge/power choices;
- 18 spent historical-validation donors for development/internal sensitivity only;
- 12 fresh `reader_validation` donors for one single-shot T1 confirmation only after a passing power gate and complete freeze;
- 10 `reader_oracle` donors sealed as final reserve;
- T2 decoupled from the T1 freeze;
- MTG retained as the T1 confirmation tissue;
- cross-region work is secondary generalisation, not independent confirmation;
- S0-S4 estimator family closed and ranking/tie-break rules written prospectively;
- nested outer-LODO/inner-LODO OOF power design and conservative jackknife influence envelope written into the draft.

**Critical boundary:** V21 is a design/document/wrapper-hardening lane, not executable discovery authority. The S0-S4 implementation, nested OOF/HC3 construction, jackknife power implementation, raw discovery lineage and frozen target→V5 lineage have not yet closed external code/evidence review.

Do **not** run S0-S4 selection until that external/adversarial executable review closes.

Do **not** open fresh `reader_validation` or `reader_oracle` while any confirmation result could change a design choice.

Standing rule:
`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

## V5

Current V5 guard-repair branch after this handoff:
`repair/v5-qualified-target-guard-20260911 @ a3427815b803382c939cd9741ab7332513ad4a9d`

The prior V5 planning branch remains:
`planning/v5-full-population-cheat-proofing-20260909`

V5 remains unauthorized for production training. Next review must test exact live post-repair heads and cover unguarded post-entrypoint step, stale AMP-skip authorization, target-root mismatch, forged ridge metadata, and HC3/free-text effect-estimand acceptance.

The uploaded corrected TRAIN cache exactly closes only:

- 42/42 corrected TRAIN counts/meta shard pairs;
- 4,726 physical TRAIN rows;
- 41,238 addresses;
- terminal `PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY`.

It is **not** the 4,553,407-cell FULL104 reader-fit expression store.

Current expression blocker:
`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

Required separate historical substrate:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 41,238 addresses
- 8,915 Level-4 blocks
- manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

Required closure:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

The real full-population proposal-weight, affine-order, packing and restart replay is closed:

- H = 5,267,086 presentations
- terminal `PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY`
- presentation-stream SHA-256 `08a1df725b3803d049cf6a0a75811c1863b4bd0b537ed2ecaf70445380f02f74`

This creates no FULL104 expression, production-dimension, GPU, biological, postqualification or training authority.

Production dimensions remain unresolved; historical 5/96/160/224/320/512 are not production authority.

## Runtime boundary

Major discovery/calibration/checkpoint assets under `/mnt/data` are documented in `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json` and the canonical integrated handoff.

`/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` remains `PROVENANCE_MISMATCH_DO_NOT_USE`.

## Permanent rules

A decreasing loss, passing unit test/CI, branch name, smoke test, design-document closure or mechanically healthy checkpoint is not biological/training authority.

Target discovery must be independently qualified and frozen before V5 can claim a production teacher target. V5 must then be shown unable to bypass that frozen target lineage or its anti-cheat gates.

**Training remains OFF** until exact production expression identity, target-discovery qualification, prospective anti-cheat/QC/power gates, donor-level evidence, production dimensions, production-geometry GPU qualification, bounded qualification, postqualification and a fresh integrated independent review all close.
