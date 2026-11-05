# V5 #561 E2: preserve last healthy bytes after interrupted write

**Scope:** draft successor stacked on original unchanged Macha #561 test-only branch `f59f9f8fd9fec198c1b84501d78591e7a6e90820`; original #559 `38880f2c196b950a4f672aaf9fd480c7297662c5`. This is only the **E2** recoverability half of Macha #561. All original negative tests remain byte-identical.

## Implemented
The existing strict `verify_storage`, `save_opaque_bytes` and `save_failed_attempt_evidence` still reject ANY unfinished/orphaned bytes. **They cannot resume.**

For read-only forensics only, `read_verified_bytes` and new `inspect_verified_prefix_read_only` independently verify the SHA-linked completed checkpoint prefix, while describing an orphaned next checkpoint payload, failure evidence without its commit-last receipt, or interrupted `.uncommitted-<hex>` temp file by its byte count and SHA-256, always `UNCOMMITTED_UNVERIFIED`. No orphan is promoted, deleted, repaired, opened as model state or treated as a valid attempted update. A corrupted committed prefix, missing middle checkpoint, unexpected filename/symlink or receipt-only orphan still refuses.

The existing Macha #561 **E2 three parameterized scenarios** are named individually in CI and must pass unchanged. New hostile E2 tests check hashes, zero-length temp, tampering, gaps, symlinks, strict writer refusal, and a false resume claim.

## Still known failing — do NOT claim full #561 repair
**E1 (two Macha RED tests) remains open.** A fully erased *tail* cannot be detected by the writer's internal mutable SHA chain. A separate **out-of-process externally committed monotonic attempt counter and head SHA** is essential. No internal file, in-process variable, same-directory log or auto-adopted orphan solves E1. `inspect_verified_prefix_read_only` says `external_head_authenticated:false`, `full_history_completeness_proved:false`, and `resume_authorized:false` even on a clean directory.

Every-attempt write-ahead intent, telemetry, #558/#562 typed cause integration, physical 48-gradient/Adam/EMA evidence, full V5 state checkpoint, restart parity, owner permissions, and all learned C1–C6 qualification also remain unimplemented. Windows-native writers unsupported; POSIX Linux/WSL only.

**No training, GPU, human RNA, sealed controller access or actual neural checkpoint.** Author CI is not Macha independent acceptance.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
