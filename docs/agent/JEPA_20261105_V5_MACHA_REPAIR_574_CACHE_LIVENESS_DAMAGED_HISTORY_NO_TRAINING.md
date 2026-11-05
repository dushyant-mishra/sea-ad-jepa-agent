# Macha repair of #574 (with #572/#573): cache timing, live-writer recovery, failures over damaged history — NO TRAINING

Fake opaque bytes and caller-reported probes only. No model, optimizer step, GPU, RNA or controller truth. Not merged; no authority change.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## What #574 gets right

Sol's cache removes the quadratic checkpoint re-reading.

- At 205 updates × 23 MiB, the writer now makes 878 checkpoint reads (19.7 GiB) instead of 42,436 (953 GiB).
- Every report, the close and a fresh process re-hash the bytes.
- Any change to inode, size, link count, mtime or ctime forces a re-hash.
- I confirmed each of these with new control tests.

## Defects found and repaired here

| # | Defect (present at #574 head `42cb0efe`) | Repair |
|---|---|---|
| 1 | **Same-tick change accepted as unchanged.** The cache trusted stat fields captured right after hashing. A same-size change inside the same timestamp tick leaves every stat field identical. On this laptop's WSL2 ext4 (CONFIG_HZ=100) this happened in 38 of 200 raw writes; on exFAT, in 199 of 200. Practical risk through the public API is low: 0 of 300 real API trials, because the record writes outlast one tick. The RED test reproduces it deterministically. | git's racily-clean rule. Metadata is trusted only if the file's **ctime** is strictly older than a filesystem-clock sample taken before hashing. A new file waits at most 30 ms (once per file) for the tick to pass, so no extra read is needed. |
| 2 | **Metadata confidence not distinguished from SHA integrity.** | Writer results now carry `historical_evidence_check`: either `FULL_SHA256_OF_EVERY_REFERENCED_FILE` or `METADATA_UNCHANGED_SINCE_SHA_IN_THIS_PROCESS__NOT_FRESH_PROOF`. They also carry per-file counts. Reports and close carry `evidence_integrity_basis = FRESH_SHA256_OF_EVERY_REFERENCED_FILE_AT_THIS_READ`. |
| 3 | **Any process could "recover" a live run.** A second process, or a forked child, calling `recover_interrupted_attempt` during a live training step wrote ATTEMPT_ABORTED. The live writer could then not record its real outcome, possibly a collapse. | The opener holds a shared `flock` on `run.lock.json` for its lifetime. Recovery from any other process is refused (`WRITER_PROCESS_STILL_ALIVE__RECOVERY_REFUSED`) until the opener and all its forks have exited. The opener may still recover after one of its own calls failed. Verified on ext4 and on C: NTFS. |
| 4 | **A damaged unrelated old checkpoint blocked the first collapse.** `record_collapsed_state`, `record_failed_attempt`, `record_runtime_abort`, `recover_interrupted_attempt` and `reconcile_one_unmirrored_record` all refused when any older payload or telemetry was damaged. The collapse bytes and cause were then lost. | Failures and their recovery tolerate damage to *earlier evidence*, which is listed in `historical_evidence_damaged_sequences`. The record chain stays strict. A **success is still never recorded**, and a **completed run is never closed**, over damaged history. A stopped run closes with `…__HISTORICAL_EVIDENCE_DAMAGED`. |
| 5 | **The "O(n)" claim was wrong.** The 32-update full scrub is still quadratic, about n²/64 checkpoints: 32 times smaller, not linear. | Comment corrected. Cost measured and projected below. |

## Tests

New `tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py`: **9 tests**. All fail at #574 for their named reasons:

- `DID NOT RAISE` ×2: same-tick change to the state or the telemetry;
- `KeyError 'historical_evidence_check'`;
- `RECOVERED_A_LIVE_RUN`;
- `UNSAFE_CHILD_ABORTED_LIVE_PARENT`;
- `STATE_PAYLOAD_CORRUPT` ×4: collapse, failed attempt and runtime abort recorded over damage, and crash recovery over damage.

New `…_io_cache_macha_controls.py`: **11 tests**. All pass both at #574 and after the repair:

- success refused over damaged history;
- a completed run is not closable over damage;
- bit rot between scrubs is caught by inspect, forensic, a fresh process and the update-32 scrub;
- an interrupt during the scrub leaves no files, and the retry re-scrubs;
- a removed or altered outside copy is refused;
- a restored mtime is caught via ctime;
- identical bytes under a new inode are accepted;
- a coarse clock gives no false refusal;
- a dead writer's run is recoverable;
- a future mtime neither stalls the writer nor hides a later edit.

Local evidence (WSL2, Python 3.11.15):

| Run | Result |
|---|---|
| #574 head, all `tests/test_jepa_synth2048_*` | 288 passed, 9 skipped |
| Repaired, all `tests/test_jepa_synth2048_*` on ext4 | **308 passed**, 9 skipped |
| Repaired, journal suites with basetemp on C: NTFS | **71 passed** |
| New workflow test list | 51 passed |
| Read-budget tool | Passes for #574 and the repair; **fails (`READ_BUDGET_EXCEEDED`) for pre-cache #573** |

Original Macha RED blobs are unchanged: #557 `bfa53457`, #560 `3ab6c208`, #561 `be259ab4`, #566 `60a16378`, #567 `c513693f`, #572 `34e0cf82`. Sol's #573 and #574 tests are unchanged.

## Measured I/O on the recorded laptop

**Hardware:** i9-11980HK (8/16 cores), 31 GiB WSL RAM, RTX 3080 Laptop (not used).

**Record:** `JEPA_20261105_V5_MACHA_574_JOURNAL_IO_MEASUREMENTS.json`. **Tool:** `scripts/v5/measure_attempt_journal_v2_io_no_training.py`.

| Run (ext4 unless stated) | Writer checkpoint reads | Bytes read | Writer time |
|---|---|---|---|
| pre-cache #573, 1 MiB × 40 | 1,681 (= 1 + n(n+1) + n) | 1.64 GiB | 5.8 s |
| #574 / repair, 1 MiB × 40 | 73 (= 1 + n + 32) | 0.071 GiB | 4.1 / 4.2 s |
| pre-cache #573, 23 MiB × 12 | 169 | 3.80 GiB | 4.7 s |
| #574 / repair, 23 MiB × 33 | 66 | 1.48 GiB | 6.8 / 6.8 s |
| #574 / repair, 23 MiB × 33, C: NTFS | 66 | 1.48 GiB | 34.4 / 33.3 s |
| #574 / repair, 1 KiB × 205 (record-scan overhead) | 878 | — | 27.6 / 28.0 s |
| repair, 1 KiB × 100, C: NTFS | 293 | — | 189 s |

Additional observations:

- **31→32 boundary** (23 MiB): BEGIN u31 0.04 s with 0 reads; **u32 0.64–0.82 s with 32 reads**; u33 0.04 s with 0 reads. On C: NTFS the same boundary is 0.56 / 3.3 / 0.58 s.
- **Peak RSS:** 114–136 MiB at 23 MiB states. It does not grow with run length.
- **Storage-level `read_bytes`** was 0: all re-reads hit the page cache, and 31 GiB RAM holds a whole run.

### Projection to 205 updates × 23 MiB (206 states with u0)

| | Pre-cache (#573) | #574 = repair |
|---|---|---|
| Writer checkpoint reads | 42,436 = **953 GiB** | 878 = **19.7 GiB** (15.1 GiB of it is the scrubs) |
| Close (full re-hash) | 4.6 GiB | 4.6 GiB |
| Read+SHA time, ext4 / NTFS | ~13 min / ~67 min | ~20 s / ~1.7 min |
| Largest single pause (scrub at u192) | — | ~4–5 s ext4 / ~20 s NTFS |
| Checkpoint writes (all versions) | 4.6 GiB | 4.6 GiB |
| Journal-record scan overhead (re-reads every small record each call) | ~28 s ext4 / ~12 min NTFS | same |

Assumptions:

- Warm reads.
- Throughput measured at 1,244 MiB/s (ext4) and 241 MiB/s (C: NTFS).
- The NTFS record overhead is fitted from the 100-update run (≈ 8.3 ms per record per call).
- Explicit `inspect_journal` and `inspect_forensic_prefix` add 4.6 GiB each when called.

**Operational conclusions:**

- **Put the run directory on the WSL ext4 disk.** On C: NTFS the remaining record-scan overhead is about 12 minutes per run.
- **The exFAT D: project drive cannot host the journal or its outside copy.** `os.link` is refused (fail-closed, nothing written). A device-separated outside copy on the My Book drive would need an exFAT-safe publish; that needs an owner decision (D1).
- **The GPU gives no benefit here.** SHA-256 on this CPU runs faster than the drive delivers bytes.

## Still not done

- All probe values are caller-reported. Nothing physically measures the model yet.
- The outside copy is unsigned and on the same device (D1).
- RT1–RT8 have not been run.
- Re-reading the journal records is still quadratic in small-file operations; this matters on NTFS.
- POSIX only.
- Bit rot that preserves metadata is caught only by the next scrub (≤32 updates), the close, or any report.
- The recovery liveness lock is local to one Linux kernel. A writer running in a different WSL instance or machine is not detected.
