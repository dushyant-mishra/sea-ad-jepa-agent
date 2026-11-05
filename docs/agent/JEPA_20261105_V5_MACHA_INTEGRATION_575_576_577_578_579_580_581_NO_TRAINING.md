# V5 journal V2 integration of #575, #576, #577/#579/#580, #578 and #581 (Macha, NO TRAINING)

Synthetic only: fake opaque bytes and tiny fake CPU tensors with manually set Adam slots. No forward or backward pass, optimizer step, EMA update, GPU, RNA, sealed controller or merge.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Inputs (exact heads)

| Input | Head | What it adds |
|---|---|---|
| Sol #576 (contains Sol #575) | `227a957c6997dc0e99233b1e4eedff3e9bb0f683` | Structured CPU state checked before each commit; the forensic reader refuses a state whose own probe evidence is damaged |
| Macha #580 (contains Sol #579, Macha #577) | `63bf1bdc8eea276d144e5f33a5828c137fe3217f` | Racily-clean cache; live-writer guard for recovery and reconcile; failures recordable over damaged history; attempt-thread ownership; no completion mirror over damage |
| Macha #581 (on Sol #575) | `86d96fc1450038c1482d4cfd8389682d0f085d62` | The model/optimizer structure must stay u0's at every commit |
| Macha #578 (on Sol #571) | `9cfe01c4fea40100e0f837cf8ece88392efd93db` | The EMA teacher must mirror the online tensors, including `value_encoder` |

**Merge order:** #576 + #580, then + #581, then + #578.

There was exactly one conflict: an add/add of `scripts/v5/jepa_v5_full_state_readonly_audit_v1.py`. #575 carries #571's original blob `fea60030`, and #578 repairs that same blob. It was resolved to #578's blob `ae79cd1b`. The build script also checked that every file #578 changed keeps #578's blob.

No original Macha or Sol test was modified.

## Cross-component tests

`tests/test_jepa_v5_journal_integration_macha_v1.py`:
1. **Forensic reads.** A structured state whose own probe telemetry is damaged is not returned; later states are.
2. **First collapse over damage.** A collapse is recorded over a damaged older *structured* checkpoint. Its bytes stay readable as a collapse, never as a probe pass.
3. **Reader vs report under random damage.** 12 seeded random accident patterns (flip or delete state, flip telemetry, delete one record copy). The #576 reader and the #572/#577 report always agree. Every readable state returns its exact committed bytes.
4. **Incomplete teacher.** Teacher-incomplete bytes are refused through the integrated bridge (#578's cause), before any file is written.
5. **Crash before the commit record.** A structured commit that crashes before its record becomes ATTEMPT_ABORTED, with its state and telemetry quarantined. It never becomes a success, and the run cannot continue.
6. **Writer ownership.** A sibling thread cannot recover a live structured attempt. Forked DataLoader workers cannot commit or recover.
7. **I/O.** The structured writer reads each new checkpoint about once (≤ n+3 reads for 5 updates).

**Local evidence** (WSL2 Python 3.11.15, torch 2.7.0 on CPU):
- 19/19 integration tests pass;
- all synth2048, #571/#578 state, #575/#581 preflight and integration suites: 406 passed, 9 skipped.

Hosted CI on both Pythons: see the PR.

## Not tested

- Real model measurements.
- Physical gradient origin, real Adam moments or EMA arithmetic.
- The frozen-panel CELL and gene-token probes.
- A complete RNG, cursor or AMP state.
- Restore and RT1–RT8.
- Windows-native execution and exFAT.
- Same-process recovery when the thread that began an attempt hands the step to another thread and then calls recovery itself. That is refused only when the beginning thread is still alive and is not the caller.

Caller-reported probes, fabricated Adam moments and successful hashing are not evidence of a healthy biological representation.
