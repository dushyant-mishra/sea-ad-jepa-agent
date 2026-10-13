# V79 V2_CORE first-opaque-world physical smoke at a61437ba: 88/88 COMPLETE through the production worker

Date: 2026-10-13 (UTC).

**Authority.** PR #317 controller comment `6137248929`: one staged physical smoke of exactly the first opaque world
(44 genes × 2 parts = 88 fits), through `run_v79_v2_core_qualification_world.py`, at the repaired head
`a61437ba284e9e75b0557157ad68e56eacd8f8fe`. The prior full-campaign authority at `559a1c10` is spent. Its custody
`48581e73…` and empty result directory were neither reused nor touched.

**Terminal.**
`FIRST_OPAQUE_WORLD_2AE1CB055FED_88_OF_88_COMPLETE_AT_A61437BA__PRIMARY_ONLY__0_DIVERGENCES__STOPPED_AFTER_WORLD__NO_SECOND_WORLD__SCORING_OFF__TRUTH_CLOSED__TRAINING_OFF__CONTROLLER_AUDIT_REQUIRED`

## 1. Preconditions (all passed before execution)

| check | result |
|---|---|
| checkout | Fresh detached `D:/jepa_wt_v79_qual_world1_a61437ba` at exact `a61437ba…`. `git status --porcelain` was empty before and after. The diff from `559a1c10` is 2 files: the world worker has one import moved from module scope into `_heldout_predictive`, plus tests. |
| runtime | `validate_runtime`: lock `5253ddca79c5…`, 31/31 packages, Windows, Python 3.11.17 (`v79-bayes`). JAX was not imported in the check process. |
| frozen package | The same `realized_worlds_v1`. 498/498 files byte-match ledger `4e65f213…`. No regeneration or mutation. |
| machine authorization | Controller side: `a3b79d537619615ef6b14fd983af07ed4622f964c1b479eca24ed6ae6fc2fc4a`. Its 1,056-record ledger came from the frozen `build_seed_ledger` and is **identical** to the `559a1c10` materialization; only the provenance fields differ. |
| fresh custody | Prepared at `a61437ba` into new paths. **`CUSTODY_RECEIPT_SHA256 = c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63`**. `executor_code_head` is `a61437ba`, `fit_count` 1056. Every run, scoring, truth and training flag is 0 or false. The blinded digest `76fe9e42…`, view `d5e9a464…` and sanitized authorization `1b24b7fc…` are unchanged. |
| fit-side firewall | PASS. 4 top-level entries and 148 blinded files. No Q labels, world identity, truth, root manifest, operator arrays, or scorer/gate modules. |
| first opaque world | **`2ae1cb055fed`**, taken from the custody queue only. It is the queue's first world and the lexically smallest opaque ID; the queue's world order is lexical, and its 88 fits sit contiguously at the queue start. No root mapping, Q label or truth was opened. |

## 2. Execution (once)

**Command:**
```
python scripts/v79/run_v79_v2_core_qualification_world.py D:/jepa_wt_v79_qual_world1_a61437ba \
  D:/jepa_v79_qualification_world1_a61437ba/fit_custody D:/jepa_v79_qualification_world1_a61437ba/result \
  c5116d6273f82fd3b3c5450b6bb8d701e03ef7d17ba6ada98eb5ff5aec906b63 2ae1cb055fed
```

- **Run:** 03:20:11Z → 03:55:34Z (2,123 s). Exit 0.
- **Worker output:** `{"opaque_world_id": "2ae1cb055fed", "completed": 88, "already_complete": false}`. stderr was empty.
- **Result directory:** exactly 88 fit receipts and 88 `donor_effect_draws_*.npz`. `HEAVY_FIT.lock` was released. No second world ran.

## 3. Results

**Prefix validation.** The runner's own frozen `completed_prefix(...)` validates **88**. Each receipt passes
`_validate_existing_receipt` (code SHA and seed checks included). The receipts match the queue items in order, and
all 44 genes have both parts.

**Diagnosis.** **COMPLETE 88**: detection 44, positive 44. NOT_DIAGNOSED 0.

**Recovery stages.** PRIMARY only on all 88. ESCALATION 0, EXTENSION 0.

**Sampling diagnostics:**

| measure | value |
|---|---|
| divergences | 0 (final), 0 (all attempts) |
| worst R-hat | 1.01 |
| worst bulk ESS | 603 |
| worst tail ESS | 425 |
| mean tree steps, by fit | 15.0 – 228.0 |

**Frozen settings, identical on every attempt:** 4 chains, 1000 warmup, 1000 draws, target_accept 0.9,
max_tree_depth 10, diagonal mass. The seeds equal the ledger on every attempt. Every receipt has `code_sha`
`a61437ba…` and contract `57e19295…`.

**Flags on every receipt:**
- `execution_mode` QUALIFICATION;
- `benchmark_run` false;
- `qualification_fits_run` 1;
- **`scoring_run` false, `truth_accessed` false, `training_authorized` false**.

## 4. Runtime and resources — a finding for the controller

**Sampling only** (the NUTS attempt):

| measure | value |
|---|---|
| per-fit wall | mean 3.77 s, median 3.68 s, range 3.21–5.40 s; total 331.6 s |
| per-fit process CPU | mean 3.81 s, max 5.36 s |
| peak working set | max 1,359,056,896 bytes, median 1,090,107,392 bytes |

This matches the benchmark's 3.82 s.

**End to end.** The world took **2,123 s**, and **84% of it is outside sampling**:
- Per-fit end-to-end time is mean 24.2 s, median 24.5 s, range 7.9–119.8 s. Detection fits average about 34 s and
  positive fits about 16.5 s.
- The gap is the per-fit post-sampling work done before the receipt is written: posterior predictive checks
  (1,000 draws), held-out same-donor and new-donor predictive summaries (200 draws; new-donor with Gauss–Hermite 40),
  the identified posterior summaries, and writing the donor draws. Mean time from end of sampling to receipt: 21.3 s.
- The benchmark runner did not execute the held-out predictive path, so the frozen benchmark projection measured
  sampling only.

**Full-campaign projections:**
- **Frozen benchmark formula** (mean sampling wall × 1,056, plus frozen settle of 120 s × 12 worlds): **1.51 h**.
- **Naive extrapolation from this world's actual wall time** (12 × 2,123 s plus settle): **≈ 7.5 h**. This assumes
  the other worlds are similar in size.
- Both are far below the frozen 72 h ceiling. The real campaign is roughly 5× slower than the benchmark-based
  projection, but still about 10× under the ceiling.

**Machine load.** Machine CPU was mean 29.8% and max 41.4% of 16 logical CPUs (69 `typeperf` samples at 30 s). At
launch, a user Chrome process was using about 1.4 cores. I did not stop it; it is disclosed in
`record/CONTENTION_CHECK.txt`.

## 5. Confirmations

- No Q00–Q11 regeneration, and no frozen world byte modified.
- No seed modification; all seeds equal the controller-derived ledger.
- No sampler, prior, threshold or setting change.
- No selective, manual or repeated fit. The worker ran once.
- No second world.
- No scoring, no PR #306 scorer, no 292 gates, and no PASS/FAIL qualification terminal.
- No controller truth opened, and no opaque ID mapped to a Q label.
- No training.

**Note on what was read.** The receipts carry the frozen, truth-blind posterior summaries, PPC and held-out
diagnostics. I read only the convergence and resource fields listed above. No posterior was compared against
anything.

**Continuation, for the controller.** The 88 receipts form a valid contiguous prefix of the frozen 1,056 queue,
bound to custody `c5116d62…`. If continuation is authorized through the top-level runner with this same custody,
result directory and head, the runner validates and skips these 88. **STOP.**

## 6. Evidence in this directory

All copies are byte-exact; see `SOURCE_SHA256.txt`.

**`record/`:**
- preflight: `PRELAUNCH_CHECKOUT.txt`, `PRELAUNCH_LOCK_CHECK.txt`, `CONTENTION_CHECK.txt`;
- authorization: `materialize_execution_authorization.py`, `AUTHORIZATION_MATERIALIZATION_STDOUT.txt`;
- custody prep: `PREP_*`, `CUSTODY_RECEIPT_SHA256.txt`, `FIT_SIDE_FIREWALL_CHECK.txt`, `FIRST_OPAQUE_WORLD_DETERMINATION.json`;
- the run: `run_first_world.sh`, `WORLD_RUN_RECORD.txt`, `WORLD_STDOUT.json`, `WORLD_STDERR.txt`, `MACHINE_CPU_TYPEPERF.csv`;
- derived: `RESULT_VALIDATION_AND_DIAGNOSTICS.json`, `END_TO_END_TIMING.json`;
- `OUTPUT_TREE_SHA256.txt`.

**`OUTPUT_TREE_SHA256.txt`** (`4bf7eb1c…`) gives path, size and SHA-256 for all 325 files: the controller
authorization, 148 custody files and 176 result files.

**`receipts/`:**
- the custody receipt;
- the sanitized and controller-side authorizations;
- the fit contract view.

**`result/`:**
- all 88 fit receipts;
- all 88 donor-draw files (16.2 MB total).

The 132 blinded custody arrays (about 70 MB) are listed in the ledger, not committed. Their bytes stay at
`D:/jepa_v79_qualification_world1_a61437ba/fit_custody/`.
