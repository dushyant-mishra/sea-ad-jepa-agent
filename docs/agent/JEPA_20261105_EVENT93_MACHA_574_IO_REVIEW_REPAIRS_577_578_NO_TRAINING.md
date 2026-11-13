# Event93 — Macha independent review of #572/#573/#574/#571, repairs #577 and #578, measured laptop I/O (NO TRAINING)

**Date:** 2026-11-05 (US Eastern).

**Author:** Macha (independent reviewer and repair engineer).

**Scope:** fake opaque bytes and fake CPU tensors only. No model forward or backward pass, no optimizer step, GPU, RNA, sealed controller or merge.

**Branches:** append-only on #322, mirrored byte-identically on #460. Events 1–92 are unchanged.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Scoped verdicts (Macha)

| PR | Exact head | Verdict | Basis |
|---|---|---|---|
| #573 PID-bound writer | `98b6e61327396c73c66676d73b82ae7381002e40` | **ACCEPT_SCOPED** | A forked child can no longer advance the parent's run. Sol's RED passes. All combined suites pass. A thread in the opening process remains a writer, by design. |
| #574 incremental I/O cache | `42cb0efe89882b066d9e123523ecfc5f9b2a9d85` | **REPAIR_REQUIRED → repaired in draft #577** | The design is right and delivers 48× fewer checkpoint bytes. Defects: same-tick change trusted; metadata trust unlabelled; "O(n)" claim wrong. |
| #572 (Macha's own) | `c4286f4b5fde761b16226b911054d085a3a97aef` | **REPAIR_REQUIRED, self-identified, repaired in #577.** No self-acceptance. | Two of its own gaps: recovery did not check that the writer was dead, and failures and recovery refused over unrelated damaged old evidence. |
| #571 read-only state audit | `8656adcf7e96b1e9c52a598beb844f8f8f548644` | **REPAIR_REQUIRED (teacher completeness) → repaired in draft #578**; otherwise ACCEPT_SCOPED for its claims | A bundle whose EMA teacher lacks `value_encoder`, or has other shapes, dtypes or unrelated tensors, verified. Sol's #575 preflight independently checks teacher/online equality at the journal bridge; #578 puts the guard inside #571 itself. |
| #575 / #576 | `41e7c556…` / `227a957c…` | **Not reviewed this cycle** | Combined with #577 by a local merge: 364 passed, 9 skipped across all synth2048 and v5 suites. No merge conflicts. |

## Repairs

**Draft #577** (base #574):
- RED `f7843637f3e7a0dd275f7eeeb12e87b2a478768e`;
- repair `b9f5be9790405dfb2873b2a754541c4fe8de43c5`.

What it changes:
1. **Racily-clean cache.** Metadata is trusted only if the file's ctime is strictly older than a filesystem-clock sample taken before hashing. A new file waits at most 30 ms, once, so it needs no second read.
2. **Labels.** Writer results carry `historical_evidence_check`. Reports and close carry `evidence_integrity_basis = FRESH_SHA256…`.
3. **Live-writer guard.** The opener holds a shared flock on `run.lock.json` for its life. Recovery by another process, or by a fork, is refused while the opener lives.
4. **Failures over damaged history.** Collapse, failed-attempt and runtime-abort outcomes, crash recovery and reconcile tolerate damage to *earlier* evidence, which is listed. A success, or the close of a completed run, still refuses over damage.

Blobs:
- journal `d75c57e91d4be88aa6b70f9ed81a3402829e4cd5`;
- RED `7ea018084b6aa96abe61d57b62a091120df10a89`;
- controls `c053e38503cd7ae3e5bc15fd8ea4992951ebdbb1`;
- tool `f7d4d01d1f5445c2de108b8e937a674acce3bc24`;
- measurements `9ae56f13dee241cf5f4823afedea96a8eba1f09c`.

**Draft #578** (base #571):
- RED `124c9eff179c59022adf6afa120ef14754d32ffd`;
- repair `9cfe01c4fea40100e0f837cf8ece88392efd93db`.

The teacher must mirror the online encoder's tensor names, shapes and dtypes. Blobs: source `ae79cd1b705d33d29c7d28b5481dd0b91ee19ba9`, test `ddf377fe6b167a5f7fa8e868429574c3932da135`.

**Unchanged original RED and test blobs:**
- Macha #557 `bfa53457`, #560 `3ab6c208`, #561 `be259ab4`, #566 `60a16378`, #567 `c513693f`;
- #572 RED `34e0cf82` and controls `9d56478f`;
- Sol V2 `25bf5c07`, #573 fork `9c0a116c`, #574 I/O `0d79a438`;
- #571 original `3247a0de`.

## Test evidence

| Evidence | Result |
|---|---|
| Local, #574 head, all synth2048 suites | 288 passed, 9 skipped |
| Local, new RED file against #574 | 9 failed for their named reasons |
| Local, #577, all synth2048 suites (ext4) | 308 passed, 9 skipped |
| Local, #577, journal suites on C: NTFS | 71 passed |
| CI #577 (Python 3.11.9 and 3.12.7) | 8/8 jobs SUCCESS. Runs: `42096392485` (20 + 51 passed + read budget), `42096392223` (248), `42096392113` (1 + 49), `42096392363` (7 + 44) |
| Local, #578 | 6 RED failed at #571; 35 passed repaired |
| CI #578 | `42096400546`: 35 passed per Python, 2/2 jobs |

## Measured laptop I/O

**Hardware:** i9-11980HK, 31 GiB WSL RAM, WSL2 kernel 5.15 with HZ=100. The RTX 3080 was not used.

| | Pre-cache #573 | #574 = #577 |
|---|---|---|
| Writer checkpoint reads, 23 MiB × 33 | — | 66 (1.48 GiB), 6.8 s ext4 / 33 s C: NTFS |
| Pause at the u32 full scrub (23 MiB) | — | 0.64–0.82 s ext4 / 3.3 s NTFS |
| Projected writer reads, 205 × 23 MiB | 42,436 = **953 GiB** | 878 = **19.7 GiB**, plus 4.6 GiB at close |
| Checkpoint writes, 205 updates | 4.6 GiB | 4.6 GiB |
| Peak RSS | — | 114–136 MiB |
| Journal-record scan overhead, 205 updates | — | 28 s ext4 (measured); ~12 min C: NTFS (fitted from a measured 100-update run, 189 s) |

### Filesystem facts

| Filesystem | Hard links | Same-tick change invisible to stat |
|---|---|---|
| WSL ext4 | yes | 38/200 |
| C: NTFS (via 9p) | yes | 0/200 |
| D: exFAT (WD My Book; the project drive) | **refused** | 199/200 |

**The journal cannot run on exFAT.** It fails closed at the first link.

### Recommendations

- Keep run directories on WSL ext4.
- A device-separated outside copy needs an owner decision (D1).

## Smallest changes to connect physical evidence (none executed)

1. **Model-measured probe.** A forward-only function computes, on the frozen TRAIN panel and the exact checkpoint:
   - the CELL exact distinct-row count;
   - centred energy in float64 of float32;
   - gene-token cross-cell variance;
   - the expression-shuffle delta;
   - a **gene-identity-only** delta;
   - **teacher-target variance**.

   The journal accepts this only under a versioned probe schema and a new measurement origin. It never asserts health.
2. **Gradients.** Use #571 `inspect_existing_trainable_gradients`, with a CUDA path, between backward and `optimizer.step` (after `GradScaler.unscale_`). Store the per-tensor report, including `value_encoder`, in commit telemetry. A missing or nonfinite tensor becomes a failure outcome.
3. **Adam and EMA.** After the step and the EMA update, run `validate_live_adam(completed_updates=u)` and record the per-tensor EMA residual and EMA count. Teacher completeness is enforced as in #578 and #575.
4. **Complete state.** Extend the #571 bundle with:
   - Python, NumPy, CUDA and masking RNG;
   - the data/presentation cursor;
   - the LR schedule;
   - the AMP scaler.

   Then `to_verified_bytes` becomes the journal's `state_bytes`, and the probe's `state_payload_sha256` is that SHA. Add a restore and bitwise-compare API.
5. **Execution.** RT1–RT8 and any optimizer step stay **withheld pending separate owner authorization**.

**Falling loss is not biology. A completed update is not a healthy state.**

## Open

- Sol to cross-review #577 and #578.
- Macha review of #575/#576.
- Owner decision D1 (signed or device-separated outside head; exFAT-safe publish).
- Record-scan overhead on NTFS.
- RT1–RT8 authorization.
- V80 controller escrow before 2026-11-13 03:01:58 UTC.
