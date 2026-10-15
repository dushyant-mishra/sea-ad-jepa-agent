# JEPA successor first 24 hours checklist V1 — 2026-10-14

Status: `READ_FIRST__NO_REAUDIT_BY_DEFAULT__NO_AUTHORITY`

## Rule zero

Do **not** begin by auditing the whole project again.

Before opening a new audit, search PR #322 custody surfaces and classify the claim as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

A new audit is justified only if the claim is absent, the governing bytes changed, or the scientific input/authority context changed.

## Standing operating requirement for every successor

Every future agent inheriting this lane must continue the same iterative owner process. This is not optional handoff advice; it is the standing work discipline for the lane.

For every substantive task, perform multiple rounds of implementation/review rather than a single pass:

1. classify and recover historical evidence first;
2. write discriminating RED/hostile checks for genuinely open or changed interfaces;
3. make the smallest lawful implementation or repair;
4. run focused GREEN plus inherited regression;
5. perform a hostile self-audit for scientific semantics, leakage, authority, custody and reproducibility;
6. repair any findings and repeat the audit/fix cycle until clean;
7. obtain independent review where the qualification contract requires independence;
8. freeze exact accepted identities and receipts.

Every future agent must also continuously update the durable GitHub audit and handoff surfaces with the work needed for takeover and no-repeat custody: historical audits, exact decisions, scripts, tests, small/public reproducibility data and fixtures, machine ledgers, results/receipts, negative findings, superseded states, exact heads, workflow evidence, unresolved questions and next lawful actions.

Large/private/controlled/local-only data must remain hash/path/provenance-custodied rather than being duplicated into public Git. Protected data must never be opened just to improve documentation.

The purpose is explicit: **a future successor should be able to continue from durable repository state without starting historical audits or project archaeology again, while still being able to detect and repair genuine errors.**

Read `JEPA_ITERATIVE_OWNER_AUDIT_AND_CUSTODY_PROTOCOL_V1_20261015.md` as a controlling process document and carry this requirement forward into every later handoff version.

## First 30 minutes

1. Re-fetch PR #322, #323, #380, #381 and #382 live heads.
2. Read `JEPA_NEW_AGENT_TAKEOVER_MANIFEST_V1_20261014.md` on PR #322.
3. Read `JEPA_ITERATIVE_OWNER_AUDIT_AND_CUSTODY_PROTOCOL_V1_20261015.md`.
4. Read `JEPA_MERGED_LANE_MASTER_AUDIT_INDEX_V1_20261014.md`.
5. Read `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` before searching old branches manually.
6. Read `MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md`.
7. Read the downstream reuse-first evidence matrix and unresolved-work ledger.

Do not infer authority from a branch name, PR title, or prose status. Re-fetch exact heads and machine receipts.

## First state check

Expected current stop state must always be refreshed from live PRs before acting. Do not rely on stale prose snapshots.

Current known state at this update:

- original Task 0 candidate `c80d7398b41f10208ec1622bc52599383b940be6` was independently rejected on B1–B5;
- repaired Task 0 candidate is PR #384 exact head `db92f80d128c37b99aa7d2c169eaf44447fa2164`;
- controller exact-head B1–B5 verification, original Task 0 migration audit and inherited unified synthetic integration are GREEN on the repaired candidate;
- independent Macha B1–B5 re-check is still required before Task 0 freeze;
- old synthetic Tasks 1–2 substrate remains `ff597faf2182522a320ec5322f8db9b67c9c6094` and must be adapted/wrapped into the merged workflow rather than treated as completion of unified tasks;
- old Tasks 3–4 remain stopped with requirements migrating only;
- old Tasks 5–12 have no independent continuation;
- Unified Task 1 remains blocked until Task 0 independent acceptance.

If any head moved, stop and reconcile before using old receipts.

## Macha

Treat Macha as two roles:

- GPU execution agent on the project GPU laptop;
- independent hostile reviewer/scientific custodian.

Do not collapse those roles into self-qualification. A Macha GPU run is execution evidence. Promotion still requires logically separate adjudication.

## Historical audits that should NOT be restarted absent a concrete defect

- FULL104 population/support census and authenticated registry;
- Macha real-data hostile audit;
- PR #314 spent corrected replay;
- G8/G6/geometry/R1/G2/G7/R4-C6-C4/G12 mechanics audits and repairs;
- V79/Q00–Q11 historical audits;
- T1/C2 gradient mechanics;
- optimizer-before-EMA chronology;
- checkpoint/RNG/resume mechanics;
- target-identity-shortcut discovery;
- correlated-gene masking shortcut discovery;
- V5 6-block/48-tensor/128x8 carryover discovery;
- semantic carryover (`z_bio`, common core, native support, estimand, rank ceiling);
- V5 inactive one-update mechanics;
- Layer-2 cross-view shortcut audit;
- donor-primary target/proposal separation.

Use the exact-asset and historical-test ledgers instead.

## What the successor may work on before Task 0 acceptance

Only non-authorizing work:
- custody corrections;
- missing exact historical asset recovery;
- schema/design analysis;
- evidence-reuse mapping;
- hostile-test design;
- handoff/audit maintenance.

Do not start unified implementation Task 1.
Do not open candidate outcomes, reader_validation, or reader_oracle.

## After Task 0 acceptance

Proceed one task at a time and keep the iterative audit/fix cycle active.

1. Freeze acceptance at exact Task 0 head.
2. Start unified Task 1 RED-first.
3. Reuse old synthetic Task 1 canonical primitives only where compatible; do not equate old Task 1 with unified Task 1.
4. Implement Task 2 manifest/access law independently; old synthetic Task 2 mainly feeds sealed-custody/RNG infrastructure, not unified Task 2.
5. Continue prerequisite/registry/custody chain before known-truth qualification.
6. Only later bind downstream through exact `TARGET_QUALIFICATION_BUNDLE_V1`.

## Downstream program

Use reuse-first A–T map. Historical mechanics are evidence, not current authority.

High-priority open/changed-input units include:
- exact TQB target consumption;
- current teacher evidence/target construction;
- student restrictions/recoverability;
- target-address identity shortcut qualification;
- masking authority;
- current scientific weighting/proposal schedule;
- representation/subspace transfer scope;
- normalization/library/support channels;
- multimodal provenance;
- joined current optimizer/gradient/EMA runtime;
- EMA timescale;
- current checkpoint/runtime/source provenance;
- current model/protected registry;
- GPU packing/RNG/kernel equivalence;
- collapse/stability;
- complete falsifier regression;
- downstream certification;
- runtime eligibility;
- independent training eligibility;
- explicit owner training authorization.

## GPU execution checklist when that stage is reached

Before any current GPU qualification run:
- freeze source/config/TQB/model/protected-registry identities;
- re-detect hardware, driver, CUDA and PyTorch;
- record environment variables and any compatibility workaround;
- prove physical microbatch/accumulation preserves selected cells and scientific mass;
- prove one optimizer step per effective update;
- prove EMA occurs exactly once after an accepted step;
- preserve RNG/packing scientific-coordinate identity;
- emit checkpoint/resume and source/runtime receipts;
- independently adjudicate before promotion.

## No-repeat decision rule

When considering a new audit, answer these in writing:

1. What exact scientific claim is being qualified?
2. Is it present in the historical audit index or downstream reuse matrix?
3. Are the relevant bytes identical to already audited bytes?
4. Did the scientific input, target, support, TQB, population, model geometry, runtime or authority context change?
5. What exact new failure mode is not covered by historical hostile tests?

If 2 is yes and 3 is yes and 4 is no, the default answer is: **reuse the prior audit; do not repeat it.**

## Update discipline

After every meaningful audit, repair, implementation, qualification, rejection or newly discovered blocker:
- append/update PR #322 audit/custody state;
- update PR #323 successor/navigation handoff;
- preserve relevant scripts, tests, machine ledgers, results and receipts;
- record exact head, tests/runs, what changed, what did not change, authority ceiling, unresolved dependencies and next lawful action;
- update no-repeat classifications so settled work is not rediscovered later;
- carry this iterative-audit and continuous-custody requirement explicitly into every future handoff.

Never rely on chat history as the only custody surface.

## Binding terminal

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
