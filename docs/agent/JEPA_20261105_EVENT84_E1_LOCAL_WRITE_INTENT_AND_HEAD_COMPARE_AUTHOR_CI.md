# Event84 — PR #564 E1 scoped local write-intent barrier + external-expected-head comparison (NO TRAINING)

**2026-11-05 UTC.** This is a scoped **author-side test** result, NOT a complete E1 repair, NOT independently accepted, and NOT authorization.

**Original lineage:** Macha original test-only #561 head `f59f9f8fd9fec198c1b84501d78591e7a6e90820`, test blob `be259ab4cdcf035d7bf05134f68b6fe8d09f8833` byte-identical; E2-only draft PR #563 `0acbf16407f63560bbd8a1cc81030cf232068c71`; new E1-scoped draft [PR #564](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/564) exact head `5cd20a418c360a6cb9b532a70ec48cf5e3a58dc7`.

**Actual source:** `scripts/v5/jepa_synth2048_atomic_checkpoint_bytes_v1.py` Git blob `15f4f0e3a309e206db4a52034b1be548f8410fa8`; new hostile tests `tests/test_jepa_synth2048_write_intent_e1_scoped_v1.py` blob `c8ed0b1627d2b4768f7151bfabff237dd1414997`; workflow blob `61a8b1bf45cecfe03aad4bcea9edf068b9e4cf8c`; limitations doc blob `95c8c0bb9bb7e4ec9dc9d279758c76af530da968`.

**What was done:** Each POSIX *storage operation* fsyncs a local write-ahead intent identifying its run lock, kind, index and previous receipt; committed checkpoint and STOP receipts require their matching intent. Thus deleting the two failure files, or deleting the last checkpoint+receipt but not intent, is no longer silently accepted (Macha #561 E1 local examples). The existing PR563 E2 forensic reader continues to return only a SHA-verified committed prefix and labels partial intent or other orphan `UNCOMMITTED_UNVERIFIED`. A new local-head proposal (run digest, counter, checkpoint/failure tail SHA) can be checked against an **independently retained** expected head/count. Match never claims external authentication or model resume.

**Exact-head hosted CI:** [41976065000](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41976065000), two Python jobs **126 passed each**. All **five** cases in original unchanged Macha #561 E1/E2 tests were executed. Old #555/#559/#563 tests also inherited without changes.

**Critical still-open E1:** If an attacker deletes the **local intent too**, the same-writer history still verifies clean. New tests reproduce this negative and show detection only when the earlier expected head was retained separately. There is **no** out-of-process append-only custodian, verified external signer, signer key, trusted attestation, or authenticated monotonically increasing head currently connected. The comparison accepts caller-supplied inputs and expressly reports `independent_custody_verified:false`. Therefore **E1 is NOT closed**. Local intent precedes *storage*, not a true optimizer update. True pre-update intent and durable every-attempt physical evidence are still absent.

**Next exact work:** Independent Macha review of PR #564 head; owner-selected access-controlled external custody actor and freshness/authority proof; only then integrate with the still-separate #562 failed-onset cause and every-attempt telemetry. Full V5 encoder/predictor/teacher/Adam/RNG checkpoint and fresh-process next-update replay are absent. No real training, GPU, sealed truth, new source read, C1–C6 scientific qualification or Stage4.

**Existing decisions untouched:** #547 C2/C3 generic-only, #554 T1-only, #556 T2–T5, Task4 #541 HOLD, Task3 #551 signed successor owner decision, L04 and #525/#533 open. Avoid repeating completed TD/Stage81/R5/V79/V80 work.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
