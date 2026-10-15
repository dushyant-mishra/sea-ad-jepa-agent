# JEPA successor first 24 hours checklist V1 — 2026-10-14

Status: `READ_FIRST__NO_REAUDIT_BY_DEFAULT__NO_AUTHORITY`

## Rule zero

Do **not** begin by auditing the whole project again.

Before opening a new audit, search PR #322 custody surfaces and classify the claim as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

A new audit is justified only if the claim is absent, the governing bytes changed, or the scientific input/authority context changed.

## First 30 minutes

1. Re-fetch PR #322, #323, #380, #381 and #382 live heads.
2. Read `JEPA_NEW_AGENT_TAKEOVER_MANIFEST_V1_20261014.md` on PR #322.
3. Read `JEPA_MERGED_LANE_MASTER_AUDIT_INDEX_V1_20261014.md`.
4. Read `JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` before searching old branches manually.
5. Read `MACHA_GPU_EXECUTION_ENVIRONMENT_AND_RUNTIME_CUSTODY_V1_20261014.md`.
6. Read the downstream reuse-first evidence matrix and unresolved-work ledger.

Do not infer authority from a branch name, PR title, or prose status. Re-fetch exact heads and machine receipts.

## First state check

Expected current stop state:

- Task 0 review candidate: `c80d7398b41f10208ec1622bc52599383b940be6`
- Task 0 focused GREEN: `38645994312`, job `116132861396`, 29 pass
- Task 0 inherited GREEN: `38645994388`
- old synthetic Tasks 1–2 substrate: `ff597faf2182522a320ec5322f8db9b67c9c6094`
- controller review focused GREEN: `38644641042`, job `116128364543`, 332 pass
- controller review inherited GREEN: `38644640881`
- old Tasks 3–4: stopped; requirements migrate only
- old Tasks 5–12: no independent continuation
- unified Task 1: not started; blocked on fresh independent Macha acceptance

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

Proceed one task at a time.

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

After every meaningful accepted repair or qualification:
- append/update PR #322 audit/custody state;
- publish a concise new version on PR #323;
- include exact head, tests/runs, what changed, what did not change, authority ceiling, unresolved dependencies and next lawful action.

Never rely on chat history as the only custody surface.

## Binding terminal

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
