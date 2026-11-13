# Event111 (part 2 of 2) — Plan for the first intentional V5 training run on DEV2048 (PLAN ONLY — NOT AUTHORIZED TO EXECUTE)

**Date:** 2026-11-13.

**Author:** Macha.

**Status:** design only. Nothing in this plan was executed: no forward, backward, optimizer step or EMA update was run while writing it. Executing any milestone needs a **separate, explicit owner authorization** (section 6).

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 0. What this pilot is for, and what it cannot show

**It can show** that the real, pinned PR224 V5 code performs one intended update correctly on our project-generated DEV2048 data, and later that a resumed run is bit-for-bit identical to an uninterrupted one. "Correctly" means:
- gradients reach every parameter;
- AdamW takes exactly one step with real moments;
- the EMA teacher follows its formula;
- no hidden query gene leaks;
- the result is recorded in a custody journal.

**It cannot show** anything about Alzheimer's biology. DEV2048 is synthetic, with the known PR547 artefacts F1–F4. For example, every SYNTH_A cell has exactly 1,988 measured addresses, so measurement support identifies the source, and donors are nested in sources. A falling loss, a successful optimizer step or healthy-looking geometry is **not** a biological result. That was the Stage81A3 lesson.

## 1. What is reused, with exact pins

| Component | Pin |
|---|---|
| Model source | PR224 guarded V5 **35-file executed closure** (blobs in `JEPA_V5_DEV2048_PIPELINE_IDENTITY_CONTRACT_V1.json`, unchanged from PR224); entry point `run_guarded_inactive_reference_update`, used through `ema_bound_runtime_proof_v1.run_presentation_ema_bound_guarded_reference_update` |
| Loaded-code check | #594 `_require_loaded_from_verified_tree`: every loaded module must be the verified file |
| Pipeline contract | #594 contract SHA-256 `590e4e66b170f7219cd77fa319fc9dc441bce8b7831cf5d44eff2968b8c3c8d6`; derived journal bindings (gene axis, source manifest, rights, Philox, config) |
| Data | PR547 public FIT artifact 13364085153, ZIP SHA-256 `87fe3ec2038305c797c439cd9780036fe22cc22b647242749b1af0bfb444c06f` (5 member SHAs in the contract); student q-excluded matrix restored to 2,048 addresses with q 1672–1675 hidden (PR548 `restore_full_address_space`) |
| Governance file | `docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json`, blob `d8d6be5f2f1d4f7f50dfc2cc38b688deff9ef1f9` (`premise_state_path` for authority issuance) |
| Initialization | PR548 / #590: `build_reference_modules`, seed 8113002, verified by the connector's exact rebuild |
| Model config | vocabulary 2,048, width 160, heads 4, blocks 6, FFN 320, dropout 0.1, gene-identity dim 48 |
| Optimizer | AdamW, one group (online, then predictor), lr 1e-4 constant, betas (0.9, 0.999), eps 1e-8, weight decay 0.01, no amsgrad/maximize/foreach/fused |
| Custody | V2 journal + preflight (#591/#594 blobs), CPU only, run directory on WSL ext4 (D: exFAT cannot host the journal) |
| Stop checks | runtime gradient gate; EMA equation check; `jepa_synth2048_collapse_sentinel_v1.evaluate_training_record` (failure-only, no invented thresholds) |

The code commit must be **one pinned commit** containing all of the above, plus the new pilot code in section 2 after it has been reviewed. Today these pieces are spread across drafts #590–#596, which are not merged; the authorization must name the exact commit.

## 2. New code required before any execution (separate review; still no training)

**(a) A dev-only post-update journal lane, separate from the u0-only journal.**
- The existing original-V5 **u0-only journal stays read-only for updates**, exactly as #591/#594 enforce. It is not relaxed, reopened or re-flagged.
- A new bridge entry, `open_dev2048_pilot_journal`, creates a **different root** whose lock carries `dev2048_pilot: true`. The lock also binds:
  - `pilot_authorization_sha256` (section 6);
  - `parent_u0_snapshot_sha256`, which must equal the u0 snapshot already recorded in the u0-only journal (cross-referenced, not copied and edited);
  - `planned_horizon` = the authorized number of updates.
- A new entry, `commit_dev2048_pilot_update`, commits update *k* only when **all** of the following hold:
  - the PR224 guarded-update **completed receipt** and persisted EMA proof exist for exactly *k*;
  - real Adam moments are consistent with step *k*;
  - the structure equals u0;
  - `k == next` and `k <= horizon`;
  - the authorization hash matches.
- Probe and telemetry records are labelled `MEASURED_BY_PILOT_DRIVER__DEV2048_MECHANICS_ONLY`, never biological.
- The legacy fake lane keeps refusing original-V5 bytes (#594).

**(b) A pilot driver,** `scripts/v5/jepa_v5_dev2048_pilot_driver_v1.py`, which does only:
1. verify the source, data and contract;
2. rebuild and capture u0 (connector);
3. issue genesis authority;
4. run **one** guarded update per call;
5. bind and persist the continuation checkpoint;
6. commit to the pilot journal;
7. write a report.

It has no loop beyond the authorized horizon, no GPU path and no real-data path.

**(c) Non-executing tests** with mocked runtime calls: refusals for a missing or wrong authorization, horizon overrun, u0-only root reuse, wrong batch rows, and q addresses in packed IDs. The tests are explicitly inventoried and statically checked (#592/#596). A real update happens only in M1 itself.

## 3. Milestone M1 — one intended update (smallest useful run)

**Inputs.** All are value-independent selections, decided before any execution.

| Item | Value |
|---|---|
| Cells | the first **16** TRAIN rows from source SYNTH_A, by row index: 1, 3, 8, 10, 28, 32, 34, 35, 49, 54, 65, 74, 79, 81, 83, 90 (rows 1 and 3 are the PR548 forward-probe rows) |
| Stable cell keys | row + 11,000,000 (PR548 convention) |
| Operators | one operator (SYNTH_A): `operator_ids = [0]*16`, `measured_tokens_by_operator = {0: 1988}`, `max_teacher_tokens_per_microbatch = 31808` (one microbatch) |
| Expression | `log1p` of restored counts; measured-support mask; teacher sees 1,988 measured addresses per cell, never q |
| Target blocks | one view: `sample_uniform_target_blocks(mask, production_seed=8813003, cell_indices=keys, sample_pass=0, view_index=0, mask_fraction=0.40, block_count=16)`, so the student sees about 1,193 addresses and predicts about 795 |
| Cell weights | 1.0 each |
| Seeds | `run_seed` 8113002; `update_index` 0 |
| EMA | presentation EMA with **proposed** `half_life_presentations = 22136` (see below) |

**Half-life.** 22,136 presentations is the value equivalent to the frozen V4 healthy-teacher momentum 0.996 per 128-cell update. It is a derived proposal that **the owner must confirm**. At 16 cells it gives momentum 0.99949912 (1 − m = 5.009e-4).

**Budget:** exactly **1** update, enforced three ways: journal horizon 1, a driver refusal for `update_index != 0`, and the authorization record. CPU only, 1 thread, deterministic algorithms on, at most 30 minutes wall clock and 8 GiB memory.

**Expected changes.** These are written down before the run; a mismatch stops the run and is reported as such.
- **Student (online) and predictor:** every element moves. PyTorch AdamW first applies decay (θ ← θ·(1 − lr·wd)), then the step. At step 1 the bias-corrected moments are m̂ = g and v̂ = g², so each element moves by −lr·g/(|g| + 1e-8): magnitude ≤ 1e-4, sign opposite to its gradient, plus decay of 1e-6·|θ|. A move larger than lr·(1 + wd·|θ|), plus float rounding, is a stop.
- **Adam state:** `step == 1` for every parameter, `exp_avg = 0.1·g` and `exp_avg_sq = 0.001·g²`. So `exp_avg_sq` must equal `0.1·exp_avg²` up to float rounding. This proves the moments are real and not fabricated.
- **Teacher (EMA):** before the update the teacher equals the student, so after it the teacher should be m·θ₀ + (1 − m)·θ_online,1. Its change is about 5.0e-4 × the student's change, so ≤ about 5.1e-8 per element. The runtime already requires `torch.equal` with this formula. The teacher must never hold a gradient. Teacher buffers, if any, do not change.
- **Loss:** recorded before and after. **No direction is required**: one step may not lower it, and lower loss would not be biology.
- **Geometry:** student and teacher cell and gene-token geometry at u0 and u1 (sentinel diagnostics), recorded only. The stop rules are the sentinel's existing failure-only rules: exactly constant cell states, or exact token collapse.

**Stop conditions.** Any one aborts without a commit and records a failed attempt in the pilot journal.
- Any source, data, contract, loaded-module or authorization mismatch.
- A q address (1672–1675) in the teacher's or student's packed IDs.
- Any non-finite loss, gradient or parameter.
- Any missing, non-finite or all-zero gradient (runtime gate).
- Optimizer step count not exactly +1.
- EMA equation mismatch.
- Adam moment inconsistency.
- A parameter change outside the first-step bound.
- Any teacher gradient.
- A sentinel `CollapseStop`.
- Any journal refusal.
- The wall-clock or memory budget exceeded.

**u1 checkpoint contents** (pilot journal, never the u0-only journal):

| Group | Contents |
|---|---|
| Model state | online, teacher and predictor state dicts |
| Optimizer | full AdamW state dict (real moments, step 1), named parameter layout, the structure digest (u0-equal) |
| Metadata | `completed_updates = 1`, `ema_updates = 1`, `presentations_seen = 16`, `next_update_index = 1`, seeds, journal bindings, `execution_authorized = false` / `training_authorized = false` as the runtime requires (the owner's pilot authorization is the separate record bound in the lock) |
| RNG | global CPU torch RNG state (dropout uses keyed Philox, but the global state is recorded too) |
| AMP | none on CPU (`amp_scaler_state = null`) |
| Batch manifest | rows, keys, operator plan, hidden-mask SHA-256, seeds, half-life and momentum |
| Update report | loss, gradient gate, maximum EMA error, microbatch plan |
| Proofs | PR224 guard completed receipt; persisted continuation proof |
| Sentinel record | as above |
| Environment | `sys.version`, `torch.__version__`, `torch.__config__.show()`, thread settings |

**M1 passes** when every prediction above holds and the u1 checkpoint is committed and verifies on a strict read. That is a **mechanics** pass only.

## 4. Milestone M2 — restart verification (separate milestone, separate authorization)

**Precondition:** M1 has passed and been independently reviewed.

**Schedule:** 3 updates from u0. Update *k* (0, 1, 2) uses SYNTH_A TRAIN rows [16k, 16k + 16) of the same row-index list (48 cells from 7 donors), with target blocks `sample_pass = k`, `update_index = k`, and everything else as in M1.

**Runs**, all in the same environment:

| Run | Description |
|---|---|
| C1 | uninterrupted u0 → u3 in one process |
| C2 | identical repeat of C1: determinism control |
| R | u0 → u1 in process A, persist through the pilot journal, then process A exits; process B uses `load_presentation_ema_continuation_checkpoint` + `restore_and_issue_presentation_ema_continuation_authority` and continues u1 → u3 |
| R′ (optional M2b) | process killed after `ATTEMPT_BEGIN` for u2, before the commit; journal `recover_interrupted_attempt`; resume from u1 to u3 |

**Same environment** means:
- the same machine and WSL kernel;
- the same Python, torch build string and BLAS/OpenMP libraries;
- the same commit and data ZIP;
- `torch.set_num_threads(1)`, OMP and MKL at 1 thread, and `torch.use_deterministic_algorithms(True)`;
- CPU only.

Both environment records must be identical.

**What must match for a bitwise restart claim** (R versus C1 at u2 and u3):
1. Every online, teacher and predictor tensor: `torch.equal`, with the same names, order, dtype and shape.
2. The optimizer state for every named parameter (step, `exp_avg`, `exp_avg_sq`) bit-for-bit, and the param-group fields equal.
3. The cursors (`next_update_index`, `presentations_seen`) and every EMA momentum value, compared as floats for equality.
4. Each update report: loss and maximum gradient compared as floats for equality; identical microbatch plans and hidden-mask SHA-256s.
5. The global torch RNG state bytes at each checkpoint.
6. A canonical tensor digest (SHA-256 over name-sorted raw tensor bytes) of the whole state.

**Not required to match:** checkpoint *file* bytes (zip metadata), timestamps, journal session IDs and wall-clock time.

**Interpretation rules:**
- **C1 must equal C2 bit for bit first.** If it does not, the environment is non-deterministic, and **no bitwise claim can be made**. Report the maximum absolute differences, downgrade to "numerically close", and investigate before any restart claim.
- **Negative controls must be detected.** Restoring u1 with one tensor element moved by one ULP, with `presentations_seen + 1` (a different EMA momentum), or with an off-by-one batch schedule must each produce a mismatch. This shows the comparison can detect errors.
- A pass supports **"bitwise restart on this environment for 3 DEV2048 updates"** only. It does not support other machines, GPU, AMP, longer horizons or biology.

**Budget:** at most 3 updates per run and 4 runs (C1, C2, R and the optional R′), all on CPU.

## 5. Order of work

1. Sol's independent review of #594 and #596 (the CI and custody guards).
2. Implement section 2 (journal lane, driver, non-executing tests) as a draft, then review it. **Still no training.**
3. Owner authorization for **M1 only** (section 6).
4. Execute M1, record it in the chronology, and review it independently.
5. Separate owner authorization for M2.
6. Execute M2, record it, and review it.

No milestone authorizes RT1–RT8, GPU, real RNA, the sealed controller, Stage4, target selection or a biological claim.

## 6. The owner authorization record (what you would sign)

The record is a JSON file committed append-only to the audit branch (#322) and mirrored on #460. Its SHA-256 is bound in the pilot journal lock. It must contain:
- `run_id` and milestone (`M1` or `M2`);
- the exact commit and driver blob;
- the contract SHA-256, data ZIP SHA-256 and premise-state blob;
- the model, optimizer and EMA configuration, including the confirmed half-life;
- seeds, the exact batch rows and the horizon;
- the environment pin and run directory;
- the date, owner identity and an expiry.

An external signed head (decision D1) is still open. Until then the record is hash-pinned but unsigned.
