# E1 scoped repair: durable local write intent and independent-head comparison (NO TRAINING)

**Source:** original #559 failed-onset journal `38880f2c196b950a4f672aaf9fd480c7297662c5`, Macha's unchanged #561 RED `f59f9f8fd9fec198c1b84501d78591e7a6e90820` / original test blob `be259ab4cdcf035d7bf05134f68b6fe8d09f8833`, and #563 E2 forensic-prefix recovery `0acbf16407f63560bbd8a1cc81030cf232068c71`.

**Actual scope implemented:** Before each **storage operation** (checkpoint or failed-onset evidence), the POSIX writer fsyncs a write-once local intent bound to the run, attempted index, kind and previous checkpoint receipt. The verifier checks those intents against each committed receipt. Removing only the two failed evidence files no longer launders failed u4 as a checkpoint; removing just the last checkpoint/receipt also refuses because its intent remains. Forensic-only reads report an interrupted trailing write-intent as `UNCOMMITTED_UNVERIFIED`; strict writes/verification still refuse any orphan.

Added read-only `read_local_head_proposal` and `compare_independent_expected_head`. A proposed head contains the exact run lock digest, receipt head, fail-stop receipt, record counter and update number. If an external party **independently saves** that pair, later deletion or rollback can be detected by comparison. The validator cannot establish that the provided expected head was externally issued, fresh, immutable or signed. A match returns `independent_custody_verified: false`, `training_authorized: false`, and `resume_authorized: false`.

## Critical limitation: not full E1 closure

A party able to delete **all** current-run files can also delete the local write-intent. The tests deliberately reproduce this and show that a wholly self-consistent truncated run still passes the local verifier. It is detected **only when checked against a genuinely independent prior head**; our current tests simulate retaining that head in separate memory and **do not** implement an out-of-process custodian, digital signature or append-only external store. Therefore DO NOT call the journal tamper-proof, independently authenticated or training-ready.

The local intent precedes *disk persistence*, **not an actual neural optimizer attempt**. A full future system must record a trusted begin-attempt before the update, commit every attempt's actual physical gradient/Adam/EMA/biology witness, and atomically pin the monotonic external head with an owner-controlled separate actor. The full #562 failure-cause schema is still on a different PR; #563 E2 forensics remain read-only. Complete V5 model/optimizer/RNG serialization and restart parity remain unimplemented.

All original #555/#559/#561 tests must remain unchanged, including the full #561 E1/E2 tests now in CI. If the original E1 tests pass, that establishes only the two **specified local deletion** attacks are blocked. Independent reviewer Macha must still review exact head. No neural run, GPU, real RNA, sealed controller, Stage4 or biological qualification.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
