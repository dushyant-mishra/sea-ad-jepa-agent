# V79 V2_CORE repaired engineering benchmark: single authorized rerun at 559a1c10 — COMPLETE, 4/4 fits

**Date:** 2026-10-12.

**Authority:**
- PR #308 controller ruling `6128881654`;
- execution instruction `6129078915`.

These authorize one fresh engineering-benchmark rerun on the repaired head only.

**Terminal:** `V2_CORE_ENGINEERING_BENCHMARK_RERUN_COMPLETE__4_OF_4_FITS__PROJECTED_1.52_H_WITHIN_72_H_CEILING__STOP_REQUIRED_FALSE__QUALIFICATION_FITS_OFF__SCORING_OFF__TRAINING_OFF__CONTROLLER_AUDIT_REQUIRED`

This was the one authorized physical attempt. It is now spent. Nothing downstream was run.

## Preconditions

All of these were recorded before anything was spent.

| check | result | record |
|---|---|---|
| checkout | fresh detached worktree `D:/jepa_wt_v79_benchmark_559a1c10`. `git rev-parse HEAD` = `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`. `git status --porcelain` empty. The diff versus PR #300 head `7172b201` is exactly the 3 repair files. | `record/PRELAUNCH_CHECKOUT.txt` |
| fresh directories | `D:/jepa_v79_engineering_benchmark_rerun_559a1c10/{engineering_package, fit_custody, result}`. None existed before prep. | same |
| old attempt untouched | `D:/jepa_v79_engineering_benchmark_2240fd82`: 643/643 output files are byte-identical to the frozen `OUTPUT_TREE_SHA256.txt` (evidence `b94367c6`). Its 10 `record/` files are byte-identical to their committed copies in `b94367c6`. | `record/OLD_ATTEMPT_UNTOUCHED_CHECK.txt`, `record/OLD_ATTEMPT_TREE_NOW.txt` |
| environment | Head's own `validate_runtime`: lock `5253ddca…`, 31/31 packages, Windows, Python 3.11.17. Run in a separate process. JAX was not imported. `XLA_FLAGS` and `JAX_PLATFORMS` were unset. | `record/PRELAUNCH_LOCK_CHECK.txt` |
| contention before launch | Windows load 12%, about 0.4 core in use across all processes. The two Python processes were idle IDE servers started the previous day. WSL load was 0.00 with no Python process. | `record/CONTENTION_CHECK.txt` |

## Step 1: prep — PASS (25 s)

**Command:**
```
python scripts/v79/prepare_v79_v2_core_engineering_benchmark.py D:/jepa_wt_v79_benchmark_559a1c10 \
  D:/jepa_v79_engineering_benchmark_rerun_559a1c10/engineering_package D:/jepa_v79_engineering_benchmark_rerun_559a1c10/fit_custody
```

**Prep receipt SHA-256** (`fit_custody/V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1.json`, not modified):
**`ee89a67ba3919a6593b2f20e4cc4030904e4032ef78c28438fecdab0cfed8170`**

**What the receipt records:**
- `executor_code_head` `559a1c10`;
- `execution_mode` ENGINEERING_BENCHMARK;
- `engineering_seed_root` 31999999;
- fit view `d5e9a464…`, root manifest `0dd2632b…`, blinded index `1021ccaf…`, digest `0d92183c…`;
- opaque world `2ae1cb055fed`, manifest `0b91416a…`.

These are identical to the deterministic prep of the failed attempt. The world was selected by opaque order only, never by Q label.

**Fit custody** holds only `blinded_fit_inputs/`, the fit-contract view and the prep receipt.

## Step 2: benchmark — COMPLETE, exit 0

The run took 74 s in total (17:40:27Z → 17:41:41Z).

**Command:**
```
python scripts/v79/run_v79_v2_core_benchmark.py D:/jepa_wt_v79_benchmark_559a1c10 \
  D:/jepa_v79_engineering_benchmark_rerun_559a1c10/fit_custody D:/jepa_v79_engineering_benchmark_rerun_559a1c10/result \
  ee89a67ba3919a6593b2f20e4cc4030904e4032ef78c28438fecdab0cfed8170
```

**Benchmark result receipt SHA-256** (`result/V79_V2_CORE_ENGINEERING_BENCHMARK_RECEIPT_V1.json`):
**`3774cecbc10266ed9205fe3bd8f161faf119ab83c3625783b484c2412477316d`**

**Runtime-environment receipt:**
- `V79_V2_CORE_FIT_RUNTIME_RECEIPT_V1`;
- lock `5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782`, 31/31 packages;
- Windows, Python 3.11.17 (`v79-bayes`).

**JAX-runtime receipt:**
- platform `cpu`;
- `jax_device_count` 4: `TFRT_CPU_0..3`;
- `jax_enable_x64` true;
- `jax_default_matmul_precision` highest.

### Per-fit results

Every fit used 4 chains, 1,000 warmup and 1,000 draws per chain, target_accept 0.9, max_tree_depth 10, diagonal mass, and was not extended.

| fit ID | gene | part | final diagnosis | attempted stages | divergences | worst R-hat | worst bulk ESS | worst tail ESS | mean tree steps | wall s | process CPU s | peak working set (bytes) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `39250166781b6f2e7453baa4be7784cfa1768228157fe4c98dea5d603f3eb451` | 0 | positive | COMPLETE | PRIMARY only | 0 | 1.01 | 1184 | 1343 | 29.676 | 3.968 | 4.172 | 481,878,016 |
| `8b66d1cba6d5fa8d632212628a1a48b6664c312e0207ed0e0f2b4f2a829685cd` | 0 | detection | COMPLETE | PRIMARY only | 0 | 1.01 | 1559 | 2142 | 15.000 | 3.962 | 3.781 | 351,592,448 |
| `c5ed04a6830bf470413b623a0a8515c5b9f2f0da4d0a979e62877212be3d23d1` | 1 | detection | COMPLETE | PRIMARY only | 0 | 1.00 | 1687 | 2308 | 19.072 | 3.667 | 3.891 | 530,751,488 |
| `d09ff82bdab7549773c90d525c79e7691b25385ff3399cf8ee7fcb40b07cea63` | 1 | positive | COMPLETE | PRIMARY only | 0 | 1.01 | 1233 | 1588 | 26.368 | 3.674 | 3.797 | 513,769,472 |

Fit-record SHA-256s are in `SOURCE_SHA256.txt`.

### Across all four fits

- **Sampling:** divergences 0. Worst R-hat 1.01. Worst bulk ESS 1184. Worst tail ESS 1343. Mean tree steps 15.0–29.7 by fit.
- **Recovery:** no fit needed a recovery stage.
- **Timing:** total benchmark fit wall time 15.270 s; mean fit wall time 3.818 s.
- **Projected runtime** for all 1,056 qualification fits: **1.520 h**. This is the runner's frozen formula: 3.818 s × 1,056 fits = 1.120 h, plus the fit view's settle term between worlds, 0.400 h.
- **Frozen runtime ceiling:** 72 h.
- **`stop_required`:** false.

**Confirmed in the receipt and every fit record:**
- `qualification_fits_run = 0`;
- `scoring_run = false`;
- `truth_accessed = false`;
- `training_authorized = false`.

**Scope of what ran:**
- No Q00–Q11 qualification-world fit was run.
- Only the opaque engineering world `2ae1cb055fed`, at seed root 31999999, was fitted. It was never scored.
- No frozen realization byte was modified: prep wrote only into the fresh directories, and the checkout stayed clean.
- I did not open controller truth; the controller-side truth directories under `engineering_package/` are only hashed in `OUTPUT_TREE_SHA256.txt`.

## Disclosures

**1. Machine load during the timed window.** Machine CPU averaged 35% and peaked at 46% of 16 logical CPUs, over 13 five-second `typeperf` samples (`record/MACHINE_CPU_TYPEPERF.csv`).
- Each fit's own process CPU roughly equalled its wall time, about one core.
- Part of the remaining load was my concurrent light work for the TD lane: file copies, hashing small files, reading JSON. Part was ordinary background activity. I did not separate the two.
- The projection is about 47 times below the ceiling, so this cannot change the 72 h decision. The absolute per-fit timings may be slightly pessimistic.

**2. Scope of the projection.** The projection extrapolates 2 genes of one engineering world to 1,056 qualification fits, using the frozen formula. The qualification worlds may differ in size. The margin is large, but this is an estimate, not a measurement of the campaign.

**3. Status.** STOP. A successful benchmark does not authorize Q00–Q11 fitting, scoring, a real TRAIN posterior, factorial science, or training. Qualification launch requires a new controller audit and explicit authority.

## Evidence in this directory

All copies are byte-exact; see `SOURCE_SHA256.txt`.

- **`record/`** (run records):
  - `PRELAUNCH_CHECKOUT.txt`, `OLD_ATTEMPT_UNTOUCHED_CHECK.txt`, `OLD_ATTEMPT_TREE_NOW.txt`;
  - `PRELAUNCH_LOCK_CHECK.txt`, `CONTENTION_CHECK.txt`;
  - `PREP_RUN_RECORD.txt`, `PREP_STDOUT.json`, `PREP_STDERR.txt`, `PREP_RECEIPT_SHA256.txt`;
  - `run_benchmark_once.sh`, `BENCH_RUN_RECORD.txt`, `BENCH_STDOUT.json`, `BENCH_STDERR.txt`;
  - `MACHINE_CPU_TYPEPERF.csv`;
  - `FIT_DIAGNOSTICS_EXTRACT.txt`, a read-only derived extract;
  - `OUTPUT_TREE_SHA256.txt`: all 648 output files (package 496, custody 147, result 5).
- **`receipts/`** (receipts):
  - the prep receipt;
  - the fit-contract view;
  - the benchmark result receipt;
  - the 4 fit records.

The output trees remain in place at `D:/jepa_v79_engineering_benchmark_rerun_559a1c10/`, unmodified.
