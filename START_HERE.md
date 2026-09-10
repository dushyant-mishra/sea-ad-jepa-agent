# START HERE — JEPA PROJECT

Date: 2026-09-10
Status: `CURRENT_T0_V21_DRAFT_V5_HARDENING__NO_TRAINING_AUTHORITY`

## Start with the current 2026-09-10 handoff

Use `main` for project-current governance/startup context. Read these first, in order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_T0_V21_V5_CURRENT.md`
3. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260910_T0_V21_V5_CURRENT.json`
4. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
5. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
6. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
7. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

Before writing, re-fetch live heads for:

- `main`
- `t0/v20-pathology-blind-materialization-20260908`
- `t0/v21-prospective-design-20260910`
- `planning/v5-full-population-cheat-proofing-20260909`

Branch names do not confer authority.

## Current project boundary

Authenticated production population:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / 42 matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic data may be used for unit/mechanics tests only. It may not set production biology, dimensions, schedules, thresholds, or training authority.

## T0 V20 remains immutable

Frozen V20 branch:
`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

Primary broad-state terminal:
`BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`

Historical broad-state result:

- p_upper ~0.021
- beta ~124.945
- HC3 SE ~65.489
- t ~1.9079
- composition sensitivity p ~0.019
- measurement sensitivity p ~0.030

Rare-tail terminal:
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT`

The binary rare tail remains unresolved. Do not retrospectively alter V20.

## T0 diagnostic arc and V21

Step 4 commit:
`4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`

Step 4 established that 1:1 matching can remove Q_DEPTH/Q_DETECT imbalance while also destroying the held-out statistic's power. A size-matched confound-retaining control also collapsed, so the matched result cannot adjudicate confounding in either direction.

General rule: a rejection-capable gate must demonstrate sensitivity and specificity at the exact geometry it creates.

V21 draft branch:
`t0/v21-prospective-design-20260910 @ e770f6dc83c44a36232d15541d3529e71c7611c9`

Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`; nothing executed.

Highest-value next T0 action:
`PATHOLOGY_BLIND_FRESH_DONOR_FEASIBILITY_AUDIT_ONLY`

The audit may inspect availability/eligibility and authenticated population membership, but must not read AT8 values or use confirmation outcomes to choose methods. V20 remains immutable.

## Historical T1/C2 mechanics

Historical u10–u205 remain `TRAINING_MECHANICS_DEFECT_INHERITED`.

The corrected successor established that the historical 128×8 failure was not OOM; it involved protected-gradient/identity mechanics. Mandatory successful update chain:

`FP16_FORWARD → BACKWARD_AUTOCAST_DISABLED → UNSCALE → PROTECTED_48_GRADIENT_GATE → OPTIMIZER_STEP_PROVED_BEYOND_DECAY → ADAM_EXP_AVG_PROVED → ADAM_EXP_AVG_SQ_PROVED → EMA_UPDATE → SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE → ATOMIC_CHECKPOINT_TELEMETRY_COMMIT`

This never authorizes production training by itself.

## V5 current engineering state

Live prospective branch observed at the current handoff:
`planning/v5-full-population-cheat-proofing-20260909 @ 5668e3d71c720219ec823d5ff089f246091f2be2`

Key hardening now present on that branch:

- biological objectives/checkpoint selection consume `z_bio`; nuisance/measurement information belongs in `z_obs`;
- cross-cell QC association is warning-only;
- complete same-cell intervention family is required for QC qualification;
- pre-execution and learned-checkpoint/post-qualification evidence are separated;
- all learned evidence binds to exact checkpoint and design context;
- aggregate QC/power artifacts bind to their exact child artifacts;
- every rejection-capable gate requires two-sided calibration: accept minimally valid control and reject minimally invalid control at exact adjudication geometry;
- trainer entry is bounded qualification only, not production-training authority;
- production-geometry GPU evidence is required.

## V5 unresolved blockers

Production dimensions remain unresolved:

- `D_shared`
- `D_private`
- `D_total = D_shared + D_private`
- `D_obs`
- `d_gene` as separate neural/token capacity

Historical 5/96/160/224/320/512 values are not production dimension authority.

Current real-data blocker:
`STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`

Need exact binding of all 42 corrected TRAIN counts/meta shard pairs from:
`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Frozen loader-manifest SHA-256:
`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Required closure terminal:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Other open blockers include production dimension derivation, prospective numerical thresholds, proposal-weight invariance, packing/order/restart invariance, production-geometry GPU Gate-2 evidence, clean bounded qualification, and independent review.

## Small real-data V5 smoke

A tiny real-data smoke test is allowed and useful if the runtime assets verify. It must be labeled `REAL_DATA_SMOKE_NON_AUTHORITY`.

It may test data-path identity, V5 reader compatibility, query masking/leakage firewall, forward mechanics, a bounded protected-gradient mechanics step if supported, same-cell perturbation mechanics, and packing/order identity.

It may not set production dimensions, biology thresholds, schedule thresholds, scientific conclusions, or training authority.

## Execution remains closed

Do not run V5 production training, protected reader-validation/oracle, DEV/SEALED, pathology-guided tuning, or any route that treats smoke/unit/mechanics PASS as scientific authority.

## Heavy assets

Do not ask the user to re-upload recoverable immutable assets merely for handoff. Use the current handoff plus:
`docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`

Verify path and SHA before use; never silently substitute a smaller/different dataset.

## Permanent scientific rule

A teacher/student checkpoint does not qualify because loss decreases.

It qualifies only after mechanics health, exact data identity, prospective shortcut superiority, held-out biology, same-cell robustness, collapse checks, power/discrimination controls, donor-level inference, proposal/packing invariance, production-geometry hardware evidence, and independent review all close.

**Training remains OFF.**
