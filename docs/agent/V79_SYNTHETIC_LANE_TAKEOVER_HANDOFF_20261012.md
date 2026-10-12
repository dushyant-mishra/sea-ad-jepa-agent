# V79 synthetic-dataset lane — audited takeover handoff

Date: 2026-10-12

This handoff is for the **synthetic dataset / V79 controller-audit lane only**. Read it together with:

- `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
- `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
- the newest files under `results/v79/synthetic_lane_audit/deltas/`
- `docs/agent/V79_SYNTHETIC_LANE_CURRENT_POINTER.md`

Do not repeat closed historical audits unless an authority byte/hash/head changes or a concrete contradiction is discovered.

## 1. Current state in one paragraph

Q00-Q11 are already realized exactly once, byte-audited, and frozen; world regeneration is forbidden. The first authorized engineering benchmark was consumed and failed closed before fit 1 because the Windows RSS monitor used an incorrectly typed Win32 process handle. That failure is immutable evidence, not evidence about V2_CORE biology, sampling or memory demand. The monitor bug has now been reproduced under a real Windows CI test, repaired, and requalified on PR #308. A fresh controller ruling authorizes exactly **one** new engineering benchmark attempt on the repaired PR #308 head only. Physical Q00-Q11 qualification fitting and scoring remain OFF. In parallel, the campaign runner/scorer lineages have been reconciled on #305 and the controller-only scoring orchestrator is being built on #306; its executor side is green with the monitor repair carried forward, while its scorer side is currently at an intentional TDD RED because `run_v79_v2_core_scoring.py` has not yet been implemented.

## 2. Benchmark failure, repair and current authority — read this first

### Historical spent attempt

Original executor / benchmark authority:

- PR #299 source head: `2240fd82f1707399bb8b2b16d3d93fee23866067`
- controller benchmark-only authorization: comment `6119596541`
- unit: Contract V2 engineering world only; seed root `31999999`; 2 genes x 2 parts; never scored

That single authorization was used once and is **SPENT**.

Result:

- failed after about 3 seconds
- failed before any model fit
- Q00-Q11 remained unfit
- scoring did not run
- failure point: first Windows RSS/resource-monitor call

Frozen failure evidence:

- branch: `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`
- commit: `b94367c6`
- path: `docs/agent/V79_ENGINEERING_BENCHMARK_ATTEMPT_2240fd82_20261012/`

Never delete, overwrite, reuse, mutate or reinterpret those outputs as a successful benchmark.

### Root cause

Historical `scripts/v79/v79_v2_core_resource_monitor.py` called:

- `GetCurrentProcess()` without declaring `restype = wintypes.HANDLE`
- `GetProcessMemoryInfo(...)` without typed argument declarations

On 64-bit Windows this allowed an invalid/truncated process handle and caused `GetProcessMemoryInfo failed` before fit 1.

### PR #308 repair

PR #308:

- branch: `fix/v79-windows-resource-monitor-20261012`
- base: exact #300 head `7172b201b13c61634b84b85254bf4406959b2b57`
- repaired head: `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`
- changed files exactly:
  1. `.github/workflows/v79-v2-core-qualification-executor.yml`
  2. `scripts/v79/v79_v2_core_resource_monitor.py`
  3. `tests/v79/test_v79_v2_core_resource_monitor_windows.py`

The repair declares:

- `GetCurrentProcess.argtypes = []`
- `GetCurrentProcess.restype = wintypes.HANDLE`
- `GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, POINTER(PMC), wintypes.DWORD]`
- `GetProcessMemoryInfo.restype = wintypes.BOOL`

TDD evidence:

- RED run `38280964089`: Windows reproduced the defect with **2 failed / 117 passed**; both unmocked monitor tests failed at `GetProcessMemoryInfo failed`. Ubuntu structural suite passed.
- GREEN run `38281216579`: Windows executor suite PASS including both real `_rss_bytes()` / `ResourceMonitor` tests; Ubuntu structural suite PASS; static fit-side trust-domain audit PASS on both.
- repair-only controller PASS: PR #308 comment `6128864889`

No sampler, model, prior, recovery rule, frozen contract, synthetic world, gate, or scoring logic changed.

### Fresh benchmark rerun authority

Controller ruling: PR #308 comment `6128881654`.

Exactly one fresh engineering benchmark rerun is authorized from:

`559a1c104c8f1f56d2c05509eecf6b9dc05846a5`

Conditions:

- clean checkout of that exact head
- actual locked Windows `v79-bayes` environment
- Contract V2 engineering seed root `31999999`
- 2 genes x 2 parts
- engineering world only; never scored
- frozen prep -> fit-only custody -> benchmark runner path
- **fresh package, custody and result directories only**
- old failed evidence at `b94367c6` is immutable and must not be reused
- if prep/execution fails closed: preserve evidence and STOP; no automatic second retry
- if projected qualification runtime exceeds 72 h: STOP; no setting changes

This authority does **not** authorize Q00-Q11 qualification fits or scoring.

## 3. Live engineering topology

### PR #300 — historical campaign-runner source lineage

- branch: `feat/v79-v2-core-qualification-campaign-runner-20261012`
- head: `7172b201b13c61634b84b85254bf4406959b2b57`
- historical CI: `38271129785` PASS
- execution state: no Q00-Q11 fit authority

Important campaign behavior already engineered:

- exact 1,056 opaque fit queue
- fit-side no controller truth/scorer imports
- 90/95/99 score-ready posterior summaries retained before chain disposal
- truth-blind held-out predictive summaries
- detection calibration: 10 fixed equal-width bins
- new-donor positive predictive LPD: exact 40-node Gauss-Hermite
- contiguous/hash/code/seed-bound resume
- final campaign receipt only after all 1,056 fit receipts validate

Do not execute the qualification campaign merely because this branch is green.

### PR #305 — reconciled scorer/executor integration baseline

- head: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`
- this supersedes the old operational #300/#301 divergence as the integration base
- before subsequent work, Windows/Linux executor and scorer suites were green and static trust-domain audits passed

Preserve historical #301 as evidence; do not restart reconciliation from scratch.

### PR #306 — active controller-scoring-orchestrator engineering

- branch: `feat/v79-v2-core-scoring-orchestrator-20261012`
- base: #305 head `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`
- current head after monitor repair forward-port: `33efb404caf81a47f976fb39f472c7537aed8f52`
- executor CI `38281486760`: **Windows PASS, Ubuntu PASS, static fit-side firewall PASS**
- exact PR #308 monitor repair + real Windows regression test are carried forward here

Completed scorer-side engineering on #306 includes:

- all five required non-gating descriptive families
- detection held-out log loss, predicted vs observed prevalence, and frozen 10-bin calibration aggregation
- controller-only planted held-out oracle
- frozen planted detection prevalence for the `<0.05` subset
- same-donor planted effects and 40-node Gauss-Hermite new-donor oracle integration
- Q11 operator perturbation handling on the controller side

Current #306 scorer state is intentionally RED under TDD:

- workflow run `38281486401`
- Linux scorer job failed during collection because `tests/v79/test_v79_v2_core_score_runner.py` imports missing module `run_v79_v2_core_scoring`
- this is a pre-existing next-feature RED, **not** a regression from the monitor repair

Next scorer engineering task: implement the controller-only physical scoring orchestrator under those tests. No physical scoring is authorized.

## 4. Frozen scientific authority — do not reopen because of engineering failures

Detection:

`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:

`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Included:

- quadratic depth
- broad class
- source
- donor-within-source hierarchical / partial pooled

Excluded:

- operator main
- donor x class
- source x class
- arbitrary/free matrix or dataset identity

A downstream engineering bug is not evidence to change this frozen biology/statistics decision.

Source remains a predictive/acquisition-source term only; do not make causal/universal source claims. Single-source estimands are undefined/unevaluable, never silently zero.

## 5. Frozen Contract V2 authority

Canonical contract:

`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`

SHA:

`57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Campaign:

- 12 worlds Q00-Q11
- 44 genes/world
- 1,056 fits
- 292 gates
- 260 hard statistical
- 28 hard deterministic/rule
- 4 LIMIT statistical
- FWER 0.05; alpha per hard statistical gate `0.05/260`
- first hard failure terminal
- Q11 all hard FAIL-class

Exactly four LIMIT gates:

- Q01 detection donor_SD
- Q01 positive donor_SD
- Q08 positive donor_SD
- Q09 positive donor_SD

Accepted contract bytes are Windows authority. Do not rewrite them to satisfy another platform.

## 6. World realization — never rerun

PR #295 realization authority head:

`cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`

Frozen realization:

- root manifest SHA `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- world-set directory digest `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- runtime environment receipt `781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184`
- blinded-fit index `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`

PR #297 byte-evidence freeze:

- head `bb8923562144a0b19a6d80795adf727986893ded`
- complete 498-file ledger SHA `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- realization audit receipt SHA `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

**Never regenerate Q00-Q11 to repair a later bug.**

## 7. Exact S174 / provenance authority

Physical repaired TRAIN substrate:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Never reconstruct from the larger 50K corpus.

Key hashes:

- shard authority `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- operator bridge `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- G500 cache `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- structural support mask `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`
- masked replay `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Resource discipline:

- at most one count-shard CSR resident
- no global 4,726 x 41,238 CSR
- no sparse `vstack`
- heavy-fit concurrency 1
- 120-second inter-world settle

## 8. Historical failures that must remain visible

Do not rediscover or erase these:

- PR #280 exact-S174 replay failed closed under operator-within-source quasi-separation/tiny ridge; this was not biological evidence about operator structure.
- structural missingness was previously encoded as zero; PR #288 corrected it with the support mask.
- accepted Contract V2 bytes are Windows authority.
- PR #295 had a stale `authorization/` whitelist; repaired narrowly.
- donor-effect truth orientation is donor x gene.
- TYPE-S requires named-gate dispatch despite `binomial_upper` primitive encoding.
- 95%/99% posterior endpoints must be retained before chain disposal.
- held-out fit summaries remain truth-blind; oracle comparison is controller-only.
- the first physical engineering benchmark attempt is now also a permanent failed-closed record at `b94367c6`; do not reinterpret it as model performance.

## 9. Current execution permissions

| Action | State |
|---|---|
| regenerate Q00-Q11 | **FORBIDDEN** |
| fresh engineering benchmark rerun | **AUTHORIZED ONCE ONLY at PR #308 head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`** |
| Q00-Q11 qualification fits | **OFF** |
| qualification scoring | **OFF** |
| real TRAIN posterior | **OFF** |
| factorial science | **OFF** |
| TEST/Morabito/pathology | **OFF in this lane** |
| target discovery | **SEPARATE LANE** |
| JEPA training | **OFF** |

## 10. What to do next

Two tracks may proceed without contaminating each other:

### A. Physical benchmark track

Use Macha/local Windows execution for the one authorized rerun only.

Required post-run report:

- exact executing checkout SHA (must equal `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`)
- prep receipt SHA
- engineering root manifest SHA
- blinded index SHA / blinded-directory digest
- selected opaque world manifest SHA
- all four fit-record SHAs and final diagnoses
- runtime environment receipt / JAX device receipt
- per-fit and total wall time / peak working set evidence
- projected full 1,056-fit qualification hours
- explicit confirmation Q00-Q11 qualification fits = 0 and scoring = false

If anything fails, preserve evidence and STOP. No second automatic retry.

### B. #306 scoring-orchestrator engineering track

Continue RED -> GREEN from `test_v79_v2_core_score_runner.py` by implementing `scripts/v79/run_v79_v2_core_scoring.py` only as far as frozen tests require.

The runner must eventually:

- require exact complete 1,056-fit campaign receipt
- verify each physical fit-record hash against the campaign ledger
- require separate post-campaign scoring authorization bound to campaign SHA, Contract V2, root manifest, blinded index, realization audit receipt and exact scorer Git head
- validate frozen blinded package hashes before using observations
- load controller truth only after authorization passes
- create exactly 1,056 controller-scored rows
- construct planted oracle held-out references
- evaluate exactly 292 frozen gates with first-hard-fail terminal semantics
- compute all five non-gating descriptive families
- write canonical/hash-bound scored rows, gate table, descriptive metrics and immutable adjudication receipt once only
- keep real-posterior/factorial/training authorities false

Do not physically score anything while engineering this runner.

## 11. Fast takeover checklist

A new controller should only need to:

1. read `V79_SYNTHETIC_LANE_CURRENT_POINTER.md`;
2. read the newest audit delta(s);
3. verify whether the one authorized PR #308 benchmark rerun has produced new evidence;
4. if yes, audit only that new evidence and issue no qualification authority unless benchmark result passes the frozen runtime/execution requirements;
5. check live #306 head against `33efb404caf81a47f976fb39f472c7537aed8f52` and inspect only newer deltas;
6. continue scorer-orchestrator TDD if needed;
7. update #302/#303 after every material new failure, fix, benchmark outcome, or authority ruling.

Everything earlier remains historical evidence unless a concrete inconsistency appears.
