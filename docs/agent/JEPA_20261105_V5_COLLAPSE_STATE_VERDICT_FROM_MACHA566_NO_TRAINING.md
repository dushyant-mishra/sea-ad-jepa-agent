# #566 repair: collapse verdict belongs to the measured state, not a failed step

**Scope:** Simulated, self-reported V5 checkpoint receipts only, no model, optimizer, GPU, RNA or training. This draft is stacked directly on the original, unchanged Macha #566 test-only head `c03f388845b3e2adf585c8aeece7e351148a4c2a`, test blob `60a16378c22b35ec5d52837c7c641cf6a59e0935`. Original #557 and #560 RED files remain identical.

**Corrected account:** A completed optimizer+EMA step (all three reported completion flags true) can be followed by a `CELL_CONSTANT`, `IDENTITY_ONLY_GENE_TOKENS` or `EXPRESSION_RESPONSE_ZERO` STOP verdict with `success=False` because **the resulting state is rejected**. A no-step pre-next-step probe of the previously completed state remains a distinct verdict. Both record `probed_state_update` and never make the collapsed state resumable. Inconsistent optimizer/EMA/presentation claims refuse. A mechanical failure still must not claim a completed step.

**Last healthy is UNKNOWN by default.** Prior completed *mechanical* updates are not proof of passed biological probes; `verify_capture_inventory` exposes `last_healthy_state_update=None` and `last_neurally_healthy_state_proved=False`. Its old `last_valid_completed_update` remains an explicitly mechanical count for unchanged historical tests, not a healthy model recovery point.

**Runtime abort:** `RUNTIME_ABORT` explicitly carries a reported exception class, execution stage and SHA of traceback, never called collapse or a completed optimizer state. Fields are caller-supplied. For an exception during optimizer/EMA the physical partial-step state remains **unknown**, never assumed healthy.

**Exact stop equality:** `exact_distinct_row_witness` is an illustrative equality-only witness that counts distinct rows from already supplied values, without naive float32 mean/subtraction roundoff. This avoids falsely treating bit-identical float32 constant rows as tiny-positive nonzero. A positive difference, however small, is never called exact collapse. The V1 validator still receives `observed` and panel SHA as *self-reported values*; it cannot certify that a true encoder used this method, that the state digest matches the checkpoint or that the u0 reference was frozen. A future physically measured/state-hash-bound sentinel must replace this diagnostic.

**Held next work:** Connect this schema to the #565 disk bridge, then adopt one prospective every-attempt V2 journal with actual `ATTEMPT_BEGIN`, `UPDATE_COMMITTED`, `STATE_COLLAPSED`, `ATTEMPT_FAILED`, `ATTEMPT_ABORTED`, and `RUN_CLOSED`, full state bytes, every-success checkpoint, outside-directory independent journal copy, all-trainable-tensor gradient evidence, fixed same-panel controls and future RT1–RT8 authorized replay. Existing #565 cannot be considered repaired by these receipt-only tests.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
