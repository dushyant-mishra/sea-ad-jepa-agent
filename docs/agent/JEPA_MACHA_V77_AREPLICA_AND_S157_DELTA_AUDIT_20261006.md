# JEPA Macha/V77 — A_REPLICA provenance + S157 delta audit

Date: 2026-10-06
Parent audit head before write: `3164c43f34036592f632e2802aa93dc983b9a583`
Macha branch observed current head: `74ef9dad7f370338471c1f19023f8b56a50e1b48`
Prior audited Macha head: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Delta: 8 commits ahead, additions focused on S157 challenge/receipts/tests/workflow plus small bridge additions.
Status: `DOCUMENTATION_ONLY__TRAINING_OFF__NO_SCIENTIFIC_AUTHORITY_PROMOTION`

## 1. Branch advancement reconciled

The working Macha branch advanced eight commits after the prior handoff. The delta adds the S157 paired identifiability challenge, its preregistration/build/score/context/crosswalk receipts, challenge tests, a focused CI workflow, and small observer/bridge extensions. No training authorization, target choice, representation choice, estimand choice or Stage-4 authorization is introduced.

The current-head commit states the challenge remains `V77_SYNTHETIC_WORLD_QUALIFICATION` and the seed-7302 realization remains development/calibration.

## 2. A_REPLICA first-run PASS predates the S146/S147 support repair

Historical A_REPLICA result:

`results/v77/V77_AREPLICA_CONTROL_FIRST_RUN_V1.json`

was committed in:

`d76631b6d5f2f6cbf9ae57e202d9b38c4c400b32`

at 2026-10-06 16:21 UTC.

The S146/S147 structural-support repair was committed later in:

`954cee9e2a2e818b1ee712569bdd71715890853b`

at 2026-10-06 21:57 UTC.

The repair commit explicitly states that every canonical V2 world built before that repair carried swapped HVS/SEA-AD support and double-counted structural missingness.

The A_REPLICA result JSON itself does not bind:

- world/root identity;
- structural-support rule;
- observer manifest digest;
- source commit;
- input/world hashes.

Therefore the historical PASS cannot be promoted to current repaired-support evidence.

Current classification:

`A_REPLICA_FIRST_RUN_PASS = PRE_S146_S147__HISTORICAL_CONTROL_RESULT_ONLY`

The **control design** remains useful: unsupervised PCA must recover RNA-driving latents and reject ATAC-only/inert latents. Its frozen thresholds should not be changed after seeing later results. But the control should be rerun on a freshly rebuilt repaired-support world, with provenance binding the exact world, support rule, source commit and hashes, before it is cited as current qualification evidence.

## 3. S157 challenge design audit

The paired challenge was prospectively recorded before challenge worlds existed and includes four worlds:

- NULL;
- BIO;
- TWIN_EXACT — same observable arithmetic as BIO but technical interpretation;
- TWIN_OPERATOR — operator-linked technical process.

The exact-twin rule is scientifically important: if biology and nuisance generate identical allowed observations, no RNA-only gate may claim to distinguish them.

The committed score receipt reports all RED checks passing, including byte-identical BIO/TWIN_EXACT model-facing structures and bitwise-identical scores. This supports:

`SAME_OBSERVABLE_LAW__BIOLOGY_VS_TECHNICAL_SEMANTICS_CAN_BE_NON_IDENTIFIABLE`

It does not select a representation or target.

## 4. Observation context result

For BIO versus TWIN_OPERATOR:

- evidence alone recovers both biology and nuisance strongly;
- visible depth + measurable-address count do not separate them;
- raw source/operator identity separates the operator twin, but is explicitly an exploratory positive control rather than an authorized learned covariate.

Most importantly, `n_measured` identifies the operator for 95.6% of test cells by lookup, despite low linear identity-leakage R2.

Biological interpretation: a seemingly innocent measurement descriptor can function as a study/operator barcode for a nonlinear model.

Classification:

`MEASURABLE_ADDRESS_COUNT = LEGITIMATE_MEASUREMENT_FACT__HIGH_SHORTCUT_CAPACITY__NOT_AUTOMATICALLY_SAFE_LEARNED_CONTEXT`

This strengthens, rather than weakens, the earlier audit warning about study information in measurement masks/support patterns.

## 5. S149 representation in this challenge is incomplete

The current lineage crosswalk correctly records S149 as only partially represented. The challenge models study-specific support, but its biology is independent of operator, so the real study-composition confounding documented by S149 is absent.

Therefore this challenge cannot establish that an observation-context strategy safely preserves biology under the actual S149 setting.

## 6. Remote test evidence qualification

The earlier synthetic plumbing checkpoint's GitHub Actions run `37560117041` was independently re-fetched and is genuinely completed/successful at SHA `3ae2b9b53eda5a80c46fbd5551127456b00e7103`.

That run validates the 55-test plumbing checkpoint, including registry restoration by hash. It does **not** remotely qualify the later eight-commit S157 delta. The current S157 head `74ef9dad...` has no check runs at the time of this audit.

Thus:

`A3E272/3AE2B9 PLUMBING_REMOTE_TEST_EVIDENCE = VERIFIED`

`74EF9DAD S157_DELTA_REMOTE_TEST_EVIDENCE = NOT_PRESENT_AT_AUDIT_TIME`

The S157 evidence currently rests on committed receipts, provenance checks and the included tests, not a fresh remote run of that delta.

## 7. Authority unchanged

- TRAINING OFF
- Stage A OFF
- Stage 4 NOT AUTHORIZED
- TEST sealed
- Morabito protected
- 500K NOT AUTHORIZED
- no target winner
- no representation winner
- no selected estimand
- S157 remains synthetic identifiability/anti-cheat qualification only
