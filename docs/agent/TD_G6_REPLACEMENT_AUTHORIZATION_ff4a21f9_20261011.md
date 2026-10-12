# Real TD G6 Replacement Authorization — ff4a21f9 — 2026-10-11

Status: **OWNER + RUNTIME AUTHORIZED FOR REPLACEMENT G6 ONLY**

This record follows external audit acceptance of the fresh qualification evidence for PR #282 exact executable head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Qualification evidence:

- branch `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- evidence commit `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused suite: `219 passed / 0 failed`
- authenticated Sample-A schema/global-row gate: `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- Sample-A rows: 25,000; SEA_AD 22,561; NPH52 1,310; HVS 1,129
- PR #259 compatibility: `1 passed / 0 skipped / 0 failed`
- exact head clean before and after
- no H5AD value read during qualification
- no G6/G7 execution during qualification

The only implementation delta from failed qualification head `7e482cf50f73a5cecda16482777129dd3ca725a6` is a test-only fixture repair in two test files. Production common/G6/G7 code is unchanged from that repaired implementation lineage.

## Authority objects

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Bound implementation identities:

- implementation commit: `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`
- common: `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6: `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7: `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

PR #259 pins remain:

- preflight driver: `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt: `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

## Operational authorization

The next allowed real-TD action is a **single replacement G6 execution** at exact head `ff4a21f9...` in a fresh, never-used namespace.

The historical `G6_OUT_fafd4309` namespace remains immutable evidence and must not be reused, edited, removed, or renamed in place.

Before execution, materialize the two authority files byte-for-byte from this audit branch, verify their physical SHA-256 values above, verify the exact executable worktree head and clean status, and recheck all frozen small-input/CSR pins.

The successor performs metadata/schema/global-row/TD50/CSR compatibility checks before its immutable start marker. If any such pre-spend check fails, preserve evidence and stop without creating a replacement G6 attempt marker.

Once the new `G6_EXECUTION_START.json` exists, preserve every outcome. Do not repair or rerun in place.

Expected successful terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected success namespace contains exactly five files:

- `G6_EXECUTION_START.json`
- `G6_RECEIPT.json`
- `MANIFEST.json`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected accounting semantics:

- HVS+SEA physical reread: 23,690 rows
- NPH52 authenticated historical pass-through: 1,310 rows
- total Sample A: 25,000 rows

**STOP AFTER G6. G7 is not operationally authorized until external audit accepts the replacement G6 namespace.**

Still unauthorized:

- G7 execution before external G6 audit
- corrected TD56/57B/57C/59 replay
- TD60
- target selection
- representation selection in this lane
- Stage4
- training

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
