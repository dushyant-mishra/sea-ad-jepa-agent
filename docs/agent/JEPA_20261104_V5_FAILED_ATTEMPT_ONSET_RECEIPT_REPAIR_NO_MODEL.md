# Failed-onset checkpoint telemetry — Macha #557 F1 scoped repair

**Only synthetic V5 prefreeze receipt mechanics, no V5 neural training.**

Macha's [unchanged test-only #557](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/557) identified that the original [#553](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/553) `verify_capture_inventory` accepted exactly N *passing* updates and refused any extra failed attempt. A model dying at update 13 could not retain the offending dead-gradient or skipped AMP record even if the last good full checkpoint was at update 12. The owner explicitly wants to capture the **onset of collapse**, not discard it.

This draft is stacked on **#557's exact test head**, preserving the original `tests/test_jepa_synth2048_checkpoint_failed_attempt_macha_red.py` **byte-identically**. The prefreeze validator now distinguishes:

- `horizon=N` means **N completed/presumed-good updates**, with the original checkpoint grid and exactly N successful self-reported update receipts.
- Optionally, one **last failed attempt N+1** may be captured, retaining negative gradient/Adam, AMP skip, nonfinite, query leakage or other STOP evidence without treating that attempt as completed, authorizing EMA, or requiring a false resumable `u(N+1)` checkpoint.
- A missing prior good record, reordered onset, fabricated success/EMA on failed attempt, uncommitted failure record, or two attempted failures is **refused**. Onset is returned explicitly as `FAILED_ATTEMPT_RETAINED_AS_UNTRUSTED_STOP_EVIDENCE`. A hypothetical plan for retries/more than one failure is **not** covered: **STOP on first fail**.
- New CI includes Macha's unchanged original RED test file by name to prevent silent omission (the omission happened in #553), plus extra hostile cases and the original 63 prefreeze tests on both pinned Python versions.

**Critical unresolved F2/F3/F4:** Every receipt still consists of caller-supplied booleans and integer counts. **They are untrusted testimony, not physically validated unscaled gradients, Adam moments, weight movement or exact EMA equation.** The new validator does not yet create a durable atomic failed-attempt journal; the byte-writer [#555](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/555) only writes completed-step opaque snapshots and retains its own unchanged source and reviewed CI. A separate source integration must persist the failed attempt **before** declaring STOP and preserve pre-update raw state/gradient evidence in durable safe owner storage. A crash before telemetry is committed still loses the candidate onset measurement. The future builder should implement physically measured unscaled 48 gradient norms and both Adam moments, before/after weights, actual EMA formula, raw CELL and gene-token counterfactuals, fixed train-panel every-attempt monitoring, and **verified** replay from last valid checkpoint; all reviewed and precommitted before any optimizer run.

**Historical control:** loss decrease and caller-positive status never demonstrate learned biology. Current #547 can only support generic C2/C3 state and no hidden controller is opened; no learned C1–C6 success. #554 T1 exact gene-token fix is accepted at scoped failure and Macha #556 has additional T2–T5 RED evidence. Task4 #541 remains HOLD, Task3 #551 public forgery needs owner-approved separate successor, #525 and #533 selection remain blocked.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
