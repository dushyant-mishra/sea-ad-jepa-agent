# JEPA new-chat handoff — FINAL4 addendum

Date: 2026-09-10
Status: `HANDOFF_ONLY_NO_TRAINING_AUTHORITY`

This is the final consistency addendum for this chat. Read it after `START_HERE.md`, `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, and `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_FINAL_CURRENT.md`.

The canonical detailed handoff remains authoritative for the full narrative, formulas, T0 Steps 1–4, V21 draft direction, V5 architecture, heavy-asset hashes, and blocker list. Where an older observed SHA appears inside that long canonical file, this FINAL4 addendum and the machine-readable state/pointer take precedence for current branch locations.

## Live heads pinned immediately before FINAL4

- `main` before FINAL4 governance commit: `ab95ad91c9bc5584172de042744a30da7acc2ad6`
- frozen T0 V20: `t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`
- T0 Step 4 result: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`
- T0 V21 draft: `t0/v21-prospective-design-20260910 @ e770f6dc83c44a36232d15541d3529e71c7611c9`
- V5 live branch: `planning/v5-full-population-cheat-proofing-20260909 @ 495e88971909ad5aeb8c93639af85000481a8f41`
- V5 engineering-content state referenced by its lane-local handoff: `5668e3d71c720219ec823d5ff089f246091f2be2`; `495e889...` adds the lane-local machine-readable handoff pointer.

Branch names never confer scientific or training authority.

## T0 state

V20 is immutable:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- `training_authorized: false`

Step 4 showed that 1:1 matching can remove Q_DEPTH/Q_DETECT imbalance while simultaneously destroying the held-out statistic's detectability; a size-matched confound-retaining control also collapsed. Therefore the matched null does not establish that the held-out program was a QC confound.

V21 is still `DRAFT_FOR_REVIEW_NOT_FROZEN`; nothing has executed under it.

The next T0 action remains exactly:

`PATHOLOGY_BLIND_FRESH_DONOR_FEASIBILITY_AUDIT_ONLY`

Rules for that audit:

- inspect only pathology availability/eligibility metadata and authenticated population fields needed by the unchanged eligibility predicate;
- never read AT8 values;
- identify unused donors with authenticated MTG immune cells and exact usable-cell counts;
- determine whether they require a new V21 population authority;
- do not run weighting, fit an estimator, run power analysis, or perform another confirmation diagnostic during the audit;
- standing rule: if looking at confirmation data could change a design choice, do not look.

Claude remains on T0 unless the user explicitly moves Claude to V5.

## V5 state

Authenticated production scope remains:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Structural hardening now includes:

- `z_bio`/`z_obs` representation firewall;
- warning-only cross-cell QC association;
- full same-cell technical-intervention family;
- pre-execution versus learned-checkpoint/postqualification phase separation;
- exact checkpoint and design-context binding;
- parent/child and cross-artifact dependency closure;
- two-sided rejection-gate calibration at exact adjudication geometry;
- shortcut-superiority and student/teacher collapse guards;
- proposal-weight packing and packing/order/restart invariance gates;
- bounded qualification separated from production training;
- historical C2 receipts prevented from satisfying V5 production-GPU authority;
- production dimension authority tied to exact FULL104 real-data closure.

Dominant real-data blocker remains:

`STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`

Required source cache on the local project machine:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Frozen loader-manifest SHA-256:

`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Required success terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Historical dimensions such as 5/96/160/224/320/512 are not production authority. Production `D_shared`, `D_private`, `D_total`, `D_obs`, and `d_gene` remain to be derived from authenticated full real data.

## Small real-data V5 smoke

The next chat is explicitly allowed to run a tiny deterministic real-data smoke labelled:

`REAL_DATA_SMOKE_NON_AUTHORITY`

Only use hash/manifest/provenance-verified real inputs. The smoke may validate real-data reader compatibility, observation-state/query-self masking, representation firewall behavior, forward/update mechanics, same-cell perturbation wiring, packing identity, and telemetry/checkpoint mechanics.

It may not set production dimensions, thresholds, schedule authority, biology conclusions, shortcut-superiority authority, postqualification, or training authority.

The smoke was **not executed in this chat**.

Do not use `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`; current status is `PROVENANCE_MISMATCH_DO_NOT_USE` until reconciled.

Hash-verified runtime assets and exact hashes are recorded in `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json` and `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`.

## New-chat startup order

1. Open `START_HERE.md` first.
2. Read `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`.
3. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_FINAL_CURRENT.md`.
4. Read this FINAL4 addendum.
5. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260910_FINAL_CURRENT.json` and runtime-asset status.
6. Re-fetch `main`, frozen V20, V21 draft, and V5 live heads before any write.
7. Keep training OFF.
8. T0: only the fresh-donor availability/eligibility audit unless the user changes direction.
9. V5: continue iterative structural audit and, if useful, run the tiny deterministic real-data smoke under the non-authority restrictions above.

## Permanent boundary

A decreasing loss, passing unit test, smoke test, convenient subset, branch name, or mechanically healthy checkpoint is not scientific or training authority.

`training_authorized: false`
