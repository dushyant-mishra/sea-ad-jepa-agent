# V79 V2_CORE engineering benchmark: single authorized attempt, FAILED CLOSED before any fit

Date: 2026-10-12. Authority: PR #299 rulings 6119630554 and 6126798999 (one locked-Windows engineering benchmark
execution, seed root 31999999, 2 genes x 2 parts).

Terminal: `V2_CORE_ENGINEERING_BENCHMARK_FAILED_CLOSED__RESOURCE_MONITOR_REFUSED_BEFORE_FIRST_FIT__NO_FIT_RUN__CONTROLLER_AUDIT_REQUIRED__QUALIFICATION_FITS_OFF__SCORING_OFF__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

## Preconditions (all met before spending)

- **Contention** (`CONTENTION_CHECK.txt`):
  - Windows machine load 8%; top process about 0.38 core of 16 logical CPUs;
  - WSL load 0.02, 99.6% idle, no Python process. The TD equivalence run had finished.
- **Checkout:** fresh detached worktree `D:/jepa_wt_v79_benchmark_2240fd82` at exact `2240fd82f1707399bb8b2b16d3d93fee23866067`. `git status --porcelain` was empty before and after.
- **Environment** (`PRELAUNCH_LOCK_CHECK.txt`): the head's own `validate_runtime` matched lock `5253ddca…`, 31/31 packages, Windows, Python 3.11.17. JAX was not yet imported; `XLA_FLAGS` and `JAX_PLATFORMS` were unset.
- **Directories:** fresh, outside the repo, under `D:/jepa_v79_engineering_benchmark_2240fd82/`.

## Step 1: controller-side prep (PASS, 27 s)

| item | value |
|---|---|
| prep receipt | `b9f209c2f11b65804063695e71a7ea4ac7e60686b1a5d28ed4842db1fa4afb18` |
| fit-contract view | `d5e9a46425466996a00b1bc2152d9f958b08e535833bfaec83ece1435d8fa753` |
| engineering root manifest | `0dd2632bab43fe2df601c38ff06bd87be1fcfb3a948ec07b4b07934f394f0c9e` |
| blinded index | `1021ccaf0cecdffbeb2383f6a23b9f6162ad836b7a5d892dbf4faa23ebbf9244` |
| blinded directory digest | `0d92183cbcc4715fc82dabc74f4ebc23d5f05ac8ee3b3740df5701f9d6e6a7ca` |
| selected opaque world / manifest | `2ae1cb055fed` / `0b91416a8b504be57a2725e1ed3a0ca7382958772e99a453f48221de2641bb7d` |
| engineering seed root | 31999999 (not the qualification root) |
| fit IDs (gene x part) | four entries in the prep seed ledger: genes 0-1 x detection/positive |

The fit custody holds only `blinded_fit_inputs/`, the fit-contract view and the prep receipt. No controller root
manifest and no controller truth are present.

## Step 2: fit process (FAILED CLOSED after 3 s; no fit ran)

`run_v79_v2_core_benchmark.py` stopped at 15:03:09Z with exit code 1:

```
v79_v2_core_resource_monitor.ResourceMonitorRefused: GetProcessMemoryInfo failed
```

- **Where:** `_one_attempt` → `RM.ResourceMonitor().__enter__` → `_rss_bytes()`, at the first attempt of the first fit. This was **before** `run_nuts_attempt`, so no NUTS sampling ran.
- **What exists:** no fit record and no benchmark receipt. The `result/` directory exists and is empty, and the single-heavy-fit lock was released.
- **Counts:** benchmark fits completed 0. Qualification fits 0. Scoring 0. Q00–Q11 not accessed. Controller truth not opened by me; only hashed in `OUTPUT_TREE_SHA256.txt`.
- **Not produced:** per-fit wall time, RSS, CPU, R-hat, ESS, divergences, and the 72 h projection.
- **CPU sampler:** `MACHINE_CPU_TYPEPERF.csv` holds only its header, because the first 5 s sample came after the 3 s run.

## Diagnosis (read-only; not fixed; no retry)

`v79_v2_core_resource_monitor._rss_bytes()` (Windows branch) calls
`ctypes.windll.kernel32.GetCurrentProcess()` and `psapi.GetProcessMemoryInfo(h, …)` with no `restype`/`argtypes`.

On 64-bit Windows, ctypes then treats the returned pseudo-handle (-1) and the argument as a 32-bit C `int`, so the
handle `GetProcessMemoryInfo` receives is not the 64-bit `HANDLE(-1)` and the call fails.

The Windows CI (83/83) evidently never exercised the real `_rss_bytes()` path; the existing resource-monitor tests
did not reach it.

A remedy for the PR #299 lane:
- declare `GetCurrentProcess.restype = wintypes.HANDLE` and
  `GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]`;
- add a Windows-CI test that calls `_rss_bytes()` and `ResourceMonitor` unmocked.

Not applied here, per the ruling: no fix-and-continue.

## Observation for the controller

Opaque world IDs are `sha256("V2CORE|" + world_name)[:12]`
(`scripts/v79/generate_v79_v2_core_worlds.py:445`). They can be recomputed from the public Q labels by anyone who
reads the code. Blinding therefore rests on the fit-process firewall (no mapping import), not on ID secrecy. The
engineering world and the qualification world with the same label share an ID: `2ae1cb055fed` appears in both sets.
Their manifests and fit IDs differ.

## Evidence (byte-exact copies, this directory)

- `CONTENTION_CHECK.txt`, `PRELAUNCH_LOCK_CHECK.txt`
- `PREP_RUN_RECORD.txt`, `PREP_STDOUT.json`, `PREP_STDERR.txt`
- `BENCH_RUN_RECORD.txt`, `BENCH_STDOUT.json` (empty), `BENCH_STDERR.txt`
- `MACHINE_CPU_TYPEPERF.csv`
- `V79_V2_CORE_ENGINEERING_BENCHMARK_PREP_V1.json`, `V79_V2_CORE_FIT_CONTRACT_VIEW_V1.json`
- `OUTPUT_TREE_SHA256.txt`: SHA-256 of all 643 output files (engineering package 496, fit custody 147, result 0)

The output trees stay in place at `D:/jepa_v79_engineering_benchmark_2240fd82/`, unmodified.

STOP for controller audit. The single authorized execution is spent, failed closed; no rerun without a new ruling.
