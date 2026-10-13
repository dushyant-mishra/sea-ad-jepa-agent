# V79 V2_CORE Q00–Q11 qualification campaign at 559a1c10: stopped before the first fit (implementation defect)

**Date:** 2026-10-13 (UTC).

**Authority:** PR #308 controller comment `6134273489`, authorizing one 1,056-fit Layer-A campaign at
`559a1c104c8f1f56d2c05509eecf6b9dc05846a5`.

**Terminal:** `V2_CORE_QUALIFICATION_CAMPAIGN_STOPPED_BEFORE_FIRST_FIT__WORLD_WORKER_IMPORTS_JAX_BEFORE_FROZEN_RUNTIME_CONFIGURATION__0_OF_1056_FITS__CUSTODY_AND_RESULT_PRESERVED__NO_RETRY__CONTROLLER_RULING_REQUIRED`

The campaign runner was invoked once. Its world worker refused before any fit because of a deterministic code defect
at the authorized head. Per the authority, this is an unhandled implementation failure: everything is preserved and
I stopped. Nothing was repaired or re-run.

## 1. Preconditions (all passed before anything was created)

| check | result | record |
|---|---|---|
| prior execution | **State A.** No `V79_V2_CORE_QUALIFICATION_CUSTODY_V1`, `…CAMPAIGN_RECEIPT_V1` or `…EXECUTION_AUTHORIZATION_V1` file exists anywhere on `D:` (full search, `.git` pruned), in `C:/Users/dushy`, or in WSL `/home`. | `record/PRIOR_EXECUTION_SEARCH_D.txt`, `record/PRELAUNCH_CHECKOUT.txt` |
| checkout | Fresh detached worktree `D:/jepa_wt_v79_qualification_559a1c10`. `git rev-parse HEAD` = `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`. `git status --porcelain` empty. Still clean afterwards. | `record/PRELAUNCH_CHECKOUT.txt` |
| runtime | `validate_runtime`: lock `5253ddca…`, 31/31 packages, Windows, Python 3.11.17 (`v79-bayes`). JAX was not imported in the check process. `XLA_FLAGS` and `JAX_PLATFORMS` were unset. | `record/PRELAUNCH_LOCK_CHECK.txt` |
| frozen package (`PACKAGE_DIR`) | `D:/jepa_wt_v79_qreal_cd6425b2/results/v79/v2_core_qualification/realized_worlds_v1`, the realization output, ignored by git. 498/498 files byte-match the frozen ledger `4e65f213…`. Root manifest `84949723…`. Directory digest `40458efe…`, computed with prep's own algorithm. Blinded index `8ea3e0cb…`. Runtime receipt `781d880a…`. No byte was modified. | §5 |
| frozen repo authorities at `559a1c10` | Contract V2 `57e19295…`. Audit-freeze receipt `6bd05349…`. Complete ledger `4e65f213…`. The pairing amendment `57d7478b…`, generator bundle `119add63…`, support mask `12ad275e…` and masked replay `caf2413c…` are bound in the realization authorization and manifests that this ledger covers. | — |
| contention | Windows load 11%, about 0.1 core in use. The 2 Python processes were idle IDE servers. WSL idle. | `record/CONTENTION_CHECK.txt` |

## 2. Machine-readable authorization (controller side, outside custody)

- **File:** `D:/jepa_v79_qualification_campaign_559a1c10/controller/V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1.json`.
- **SHA-256:** **`2ce50c1637c61f30e10169774a54afe71a3cf3deed3010aabb9afefd0cdffd4a`**.

**Content:**
- `schema` V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1;
- `qualification_campaign_authorized` true;
- `benchmark_controller_pass` true;
- contract `57e19295…`, blinded index `8ea3e0cb…`;
- `scoring_authorized` false, `training_authorized` false;
- provenance fields citing comment `6134273489`.

**Seed ledger:**
- `fit_seed_ledger` has 1,056 records (1,056 unique fit IDs).
- It was produced only by the frozen `scripts/v79/v79_v2_core_seed_ledger.build_seed_ledger` at `559a1c10`, using
  `record/materialize_execution_authorization.py`.
- The inputs were loaded exactly as `prepare()` loads them.
- No seed was typed, re-derived, reordered or edited.
- No world identity was printed. The root manifest stayed outside custody.

`prepare()` independently re-derived the ledger and accepted it. It wrote the sanitized copy into custody
(`1b24b7fc…`).

## 3. Custody preparation — PASS

**Command:**
```
python scripts/v79/prepare_v79_v2_core_qualification_campaign.py D:/jepa_wt_v79_qualification_559a1c10 \
  D:/jepa_wt_v79_qreal_cd6425b2/results/v79/v2_core_qualification/realized_worlds_v1 \
  D:/jepa_v79_qualification_campaign_559a1c10/controller/V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1.json \
  D:/jepa_v79_qualification_campaign_559a1c10/fit_custody
```

Exit 0, 02:35:36Z → 02:35:43Z.

**`CUSTODY_RECEIPT_SHA256` = `48581e7330020fd8c8e283fe95277bff6c9a585163c93920662d5fa9f6204d66`.**

**The receipt records:**
- `executor_code_head` 559a1c10;
- contract `57e19295…`, root `84949723…`, index `8ea3e0cb…`;
- blinded custody digest `76fe9e42…`;
- fit view `d5e9a464…`, authorization `1b24b7fc…`;
- `fit_count` 1056, `ppc_draws` 1000, `donor_draws_stored` 200;
- `qualification_fits_run` 0;
- `scoring_run`, `truth_accessed` and `training_authorized` all false.

**Fit-side firewall — PASS** (`record/FIT_SIDE_FIREWALL_CHECK.txt`):
- **Top level:** custody holds exactly 4 entries: `blinded_fit_inputs`, the fit view, the authorization and the receipt.
- **Contents:** 148 files (16 JSON, 132 NPY) across 12 opaque worlds.
- **Per-world files:**
  - design arrays (class, donor, log_lib, source);
  - observations (train / same_donor / new_donor, detected and observed);
  - support mask;
  - blinded manifest.
- **Absent:** Q labels, world indices or names, controller truth, the root manifest, planted parameters, operator
  arrays, scorer or gate modules, pathology, rare-program and target-discovery content.
- **Token checks:** `operator` appears only in the frozen model's `excluded_terms`; `truth` only as
  `truth_accessed: false`.

## 4. Campaign run — FAILED CLOSED before the first fit

**Command** (invoked once; `record/run_campaign.sh`, `record/CAMPAIGN_RUN_RECORD.txt`):
```
python scripts/v79/run_v79_v2_core_qualification.py D:/jepa_wt_v79_qualification_559a1c10 \
  D:/jepa_v79_qualification_campaign_559a1c10/fit_custody D:/jepa_v79_qualification_campaign_559a1c10/result \
  48581e7330020fd8c8e283fe95277bff6c9a585163c93920662d5fa9f6204d66
```

It ran 02:37:12Z → 02:37:16Z and exited 1.

**Runner error:** `QualificationRunRefused: … world worker failed for opaque world 2ae1cb055fed with exit 1`.

**Worker error:** `v79_v2_core_runtime.RuntimeRefused: REFUSED V2_CORE runtime: JAX was imported before frozen runtime configuration`.

### Diagnosis

Full details are in `record/FAILURE_DIAGNOSIS.md`. It was established read-only by importing each worker dependency
in a fresh process with the checkout kept clean.

- `run_v79_v2_core_qualification_world.py` imports `v79_v2_core_fit_predictive` at module level (line 18).
- That module imports `v79_v2_core_fit_model`, which loads JAX and numpyro.
- So JAX is already in `sys.modules` when `execute_world` reaches the frozen guard
  `RT.configure_before_jax_import` (line 124). The guard correctly refuses.
- Of the 12 dependencies tested, only `fit_predictive` and `fit_model` load JAX at import time.
- The defect is deterministic: no process can reach a fit at this head.
- The benchmark runner imports neither module at load time, so the benchmark did not exercise this path.
- The import came with the held-out-predictive commits `8b252a0a` and `75a9b768` on the PR #300 lineage.

### State after the failure

- **Fits:** 0 of 1,056.
- **Result directory:** `D:/jepa_v79_qualification_campaign_559a1c10/result` exists and is empty. It contains no fit
  receipt, no campaign receipt and no `HEAVY_FIT.lock`; the worker refused before taking the lock.
- **Custody:** the receipt is still `48581e73…` and the blinded digest is still `76fe9e42…`. Nothing in custody was
  edited.
- **Checkout:** clean.
- **Runtime summary:** about 4 s wall time and no sampling, so there are no R-hat, ESS, divergence, recovery,
  per-fit runtime or peak-resource figures.

**Confirmed:**
- no world regeneration and no frozen byte modified;
- no seed modification;
- no selective, manual or repeated run;
- no scoring and no PR #306 scorer;
- no truth opened and no world ID mapped to a Q label;
- no training.

## 5. Status and what is needed (controller ruling)

**What is spent.** The single campaign invocation under `6134273489` failed closed. I will not re-invoke it.
- This is an implementation failure, not an ordinary interruption.
- Re-running the same command would fail identically.

**What a repair needs.** It is not mine to apply under this authority. In the repair lane:
1. move the `v79_v2_core_fit_predictive` import (and anything else that loads `v79_v2_core_fit_model`) inside
   `execute_world`, after `RT.configure_before_jax_import(...)` and `import jax`, the way `fit_model` is already
   imported there;
2. add a fresh-subprocess test that imports the world worker and asserts JAX is not loaded;
3. add an end-to-end subprocess test that drives `execute_world` through the runtime configuration on a minimal
   custody fixture.

**What any new campaign needs.** It requires a new controller authorization at the repaired head, with fresh custody
and result directories. This custody is bound to `executor_code_head 559a1c10`, and the runner refuses any other head.
These directories stay preserved as this attempt's evidence.

STOP.

## 6. Evidence in this directory

All copies are byte-exact; see `SOURCE_SHA256.txt`.

- **`record/`:** the run records, scripts, stdout/stderr, the firewall check, the diagnosis, and
  `OUTPUT_TREE_SHA256.txt`.
- **`OUTPUT_TREE_SHA256.txt`:** path, size and SHA-256 for all 149 files in `controller/`, `fit_custody/` and
  `result/`. The 132 blinded `.npy` arrays (about 70 MB) are listed there but not committed; their bytes stay at
  `D:/jepa_v79_qualification_campaign_559a1c10/fit_custody/`.
- **`receipts/`:**
  - the custody receipt;
  - the sanitized custody authorization;
  - the fit contract view;
  - the controller-side authorization with the 1,056-entry opaque fit ID → seed ledger. It holds no world identity.
