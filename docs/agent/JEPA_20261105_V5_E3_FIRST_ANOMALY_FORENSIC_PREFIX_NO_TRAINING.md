# #567 E3 repair: recover mechanically intact checkpoint prefix up to first damage

**Scope:** Non-training opaque byte forensics, stacked directly on immutable Macha test-only #567 head `55aba0cfe4df492c18e5b268081cebbc6ac0e33e`. The original Macha test `tests/test_jepa_synth2048_last_healthy_recoverability_macha_red.py` blob `c513693fa11b2c0ef72b68601ca83dcd5a0a5b2f` is unchanged. #561 E1/E2 test blob `be259ab4cdcf035d7bf05134f68b6fe8d09f8833` also unchanged.

Owner decision D4: forensic reading may return the **maximal SHA-verified ancestor prefix** even when later files are corrupt, missing, orphaned or inconsistent. An anomaly inventory identifies the damaged index and lists suspect tail artifacts as `UNCOMMITTED_UNVERIFIED`, including name/length/hash when safe. Strict `verify_storage`, all writers and any future resume loader **still refuse**. A forensic byte reader MUST NEVER be used for model resume.

A single damaged last payload or receipt at u3 does not hide intact u2 bytes; a damaged u2 still makes u2/u3 unverified. Recovery after a failed storage write at u43 with last u40 sparse checkpoint remains readable because the forensic reader **does not pretend to validate a pending intent at u41**. It treats pending u43 intent as suspect/unfinished evidence, not a committed success. All incomplete files and unknown artifacts are reported without mutating the directory.

The original author-side tests from #563/#564 that demanded whole-directory refusal after any anomaly were updated **only where they contradicted the owner-selected forensic policy**. The original independent Macha #561/#567 tests are unmodified. Regression tests still enforce strict storage refusal.

**Safety and limitations:** The receipts prove byte hashes in a linked committed prefix, **not neural-health, a physical successful optimizer step, a real collapsed state, signed external custody or complete history**. Erasing the whole tail and all intents can still create a locally consistent shorter run. An external head copy is still needed for accidental whole-group deletion. The existing checkpoint cadence is sparse after u40, despite the owner's every-update direction; that is future journal V2 work. No real RNA, GPU, sealed controller, optimizer, EMA, Stage4 or training.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
