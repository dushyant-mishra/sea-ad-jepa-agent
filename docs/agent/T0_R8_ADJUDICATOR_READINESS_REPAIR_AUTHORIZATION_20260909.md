# T0 R8 adjudicator-readiness repair authorization — 2026-09-09

Status: `AUTHORIZE_R8_ADJUDICATOR_READINESS_REPAIR__CONFIRMATION_NUMERIC_AT8_STILL_CLOSED`

This file records the owner/reviewer decision after Stage 2 discovery completed and replayed at head `237427c734bfdf7d00f286ceeae63692b3075d49` on branch `t0/v20-pathology-blind-materialization-20260908`.

## Basis

Stage 2 discovery terminal:

```text
DISCOVERY_STAGE_DONE_AND_REPLAYED__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN
```

Discovery AT8 access was limited to the 28 discovery donors through the R7-gated frozen conclusion path. The discovery object was fitted and replayed from disk. Confirmation numeric AT8 remains unopened.

Important discovery roots/status:

```text
r7_package_root_sha256: a7e25e515f8e9cb4ec43e1e3bf09798adca6a573059d4b7ca0b61483c5c96c09
r7_readiness_root_sha256: a75581dfc5e7ea88609a9ef62f54765b9a495a7dbdc5c09152ba7fb76d1488ae
discovery_target_package_root_sha256: b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe
discovery_provenance_root_sha256: 15d13dd3e733e0ea90b199cf981b03ccd94bc67fbd19660ef88861e3ae1a37c2
discovery_authority_package_root_sha256: 9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7
endpoint_identity_sha256: 95870f7dd32101983ff710f7b394fcca4177da1525cc2a87342eb1a285155f89
endpoint_values_sha256: 4cfb572798ab3f48c08aaa74a841e4cb92c01cfc69303f0f3a45c006a81c671a
```

Important scientific caveat: the pre-registered LOODO ridge grid selected the maximum exponent `2.0`, the most regularized endpoint. This does not invalidate the discovery run, because the grid was frozen and not changed, but it is weak-signal evidence that must be visible before confirmation adjudication.

## R8 authorization

Authorized now:

```text
R8_ADJUDICATOR_READINESS_REPAIR_AUTHORIZED = true
```

Goal:

```text
Supersede the two execution-input-authority loaders in a repo-side v2 whose only behavioural difference is the readiness value check, justified by the V20 contract's own production_requires_real_execution_ready: true.
```

R8 must repair the adjudicator path that still contains the same readiness contradiction at `t0_adjudicator_v2` lines 34 and 48. R8 may not alter the scientific design, donor roles, endpoint, discovery object, discovery fit, or confirmation procedure.

## Still closed during R8

```text
CONFIRMATION_NUMERIC_AT8_AUTHORIZED = false
DEV_AUTHORIZED = false
SEALED_AUTHORIZED = false
PROTECTED_POPULATIONS_AUTHORIZED = false
TRAINING_AUTHORIZED = false
SUCCESSOR_U0_AUTHORIZED = false
TD60_AUTHORIZED = false
BIOLOGICAL_SWEEPS_AUTHORIZED = false
```

Opening confirmation AT8 against an adjudicator that cannot conclude would spend the holdout for nothing. R8 must stop before confirmation numeric AT8 if the repaired adjudicator path is not replayed and externally reviewable.

## Required R8 terminal

```text
PASS_R8_ADJUDICATOR_READINESS_REPAIR__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN
```

Required evidence:

- exact starting head `237427c734bfdf7d00f286ceeae63692b3075d49`;
- R8 code diff restricted to adjudicator/readiness-loader semantics;
- no discovery refit;
- no confirmation numeric AT8 read;
- all R7 and Stage 2 discovery roots consumed unchanged;
- live replay proving the repaired adjudicator readiness path is satisfiable;
- tests demonstrating old contradiction remains reproducible and new v2 gate is the only production path;
- explicit shut-gate report for DEV, SEALED, protected populations, training, successor-u0, TD60, and biological sweeps.
