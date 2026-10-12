# V79 synthetic-dataset lane — detailed audited takeover handoff

Date: 2026-10-12
Scope: **synthetic/V79 only**

This is the cold-start handoff for a new controller/agent. The purpose is to avoid repeating historical audits, reopening frozen scientific decisions because of engineering bugs, or crossing the fit/controller-truth firewall.

## 0. Cold-start protocol

Read, in order:

1. `docs/agent/V79_SYNTHETIC_LANE_CURRENT_POINTER.md`
2. `results/v79/synthetic_lane_audit/deltas/20261012T1720Z_ARCHIVAL_CONSOLIDATION_AND_TAKEOVER_V1.md`
3. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
4. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_CODE_DATA_RESULT_INDEX_20261012.csv`
5. this handoff
6. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md` only for deeper historical detail.

**Do not repeat audits before the exact heads/hashes recorded below unless a byte/head changed or a concrete contradiction is discovered.** Audit only deltas.

---

# 1. Current state in one paragraph

Q00-Q11 have already been realized exactly once on the locked Windows qualification environment and independently byte-audited. They must never be regenerated to repair later software. The first authorized engineering benchmark was consumed once and failed closed before fit 1 because the Windows RSS monitor used untyped Win32 ctypes signatures. That failure is immutable infrastructure evidence, not evidence about V2_CORE model quality, convergence, memory demand or runtime. PR #308 repaired that defect under RED→GREEN real Windows CI and now holds authority for exactly **one fresh engineering benchmark rerun** at exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`; that rerun has not yet been reported. Q00-Q11 qualification fitting and scoring remain OFF. Engineering work beyond the campaign runner/scorer reconciliation is on PR #306 at `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`, with Windows/Linux executor and scorer CI green, but physical scoring remains OFF.

---

# 2. Scientific decisions are frozen — do not reopen them because of downstream software failures

## V2_CORE

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
- donor × class
- source × class
- arbitrary/free matrix or dataset identity

Positive qualification family: lognormal.

ZTNB is an unresolved challenger, not qualification authority.

Source is a predictive/acquisition-source term only. Do not promote it to a universal/causal biological effect. Single-source estimands are undefined/unevaluable rather than zero.

Historical Bernoulli V2 qualification remains `NOT_QUALIFIED` because worst ESS was `361.8761303230284 < 400`; do not relax the threshold or resurrect it as authority.

---

# 3. Frozen Contract V2

Canonical file:

`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`

SHA-256:

`57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Other frozen authorities:
- Q10/Q11 pairing amendment `57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5`
- environment lock `5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782`
- generator/writer bundle `119add636cffdb1db3b58c44dce6a2c5eee245f85c773e5822735537ae8dfc16`

Frozen qualification shape:
- 12 worlds Q00-Q11
- 44 genes/world
- 2 parts/gene
- 1,056 fits
- 292 gates total
- 260 hard statistical
- 28 hard deterministic/rule
- 4 LIMIT statistical
- FWER 0.05
- hard statistical alpha `0.05 / 260`
- first hard FAIL terminal
- Q11 is all-hard FAIL-class stress world

Exactly four LIMIT gates:
- Q01 detection donor_SD
- Q01 positive donor_SD
- Q08 positive donor_SD
- Q09 positive donor_SD

Accepted contract bytes are Windows authority. Do not rewrite/round them to make another platform reproduce bytes.

---

# 4. Exact S174 / empirical authority

Physical repaired TRAIN substrate:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Never reconstruct this from the larger 50K corpus.

Key hashes:
- S174 shard authority `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- operator bridge `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- G500 cache `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- structural support mask `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`
- mask-corrected replay `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Resource rules:
- at most one count-shard CSR resident
- no global 4,726 × 41,238 CSR
- no sparse `vstack`
- one heavy fit at a time
- 120-second inter-world settle

Structural missingness is authoritative: unmeasured entries are not zeros and enter neither detection nor positive likelihood. Measured zeros remain real zeros.

---

# 5. Realization authority — never regenerate

PR #295 realization head:

`cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`

Frozen realized package:
- root manifest `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- directory digest `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- runtime receipt `781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184`
- blinded-fit index `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`

PR #297 realization audit freeze:
- head `bb8923562144a0b19a6d80795adf727986893ded`
- complete 498-file ledger `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- audit receipt `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

Controller audit established:
- 12/12 truth and blinded manifests one-to-one
- truth arrays hash-bound
- root binds index/runtime/authorization
- Q10/Q11 non-operator truth is byte-identical; Q11 alone adds frozen operator offsets
- observation arrays were intentionally not committed but are bound by the complete ledger

**Never regenerate Q00-Q11 because a later benchmark/fitter/scorer bug is found.**

---

# 6. Historical audit/failure chain that must not be repeated

Treat these as closed evidence unless exact bytes/heads change:

- #260 Bayesian/synthetic audit
- #261 Bayesian/synthetic handoff
- #262 downstream factorial implementation
- #264 downstream factorial audit
- #265 downstream factorial handoff
- #279 streaming/resource-safe replay
- #280 immutable failed-closed exact-S174 operator replay; quasi-separation under tiny ridge; do not reinterpret as biology
- #283 operator repair
- #285 completed exact-S174 A-H replay
- #286 V2 draft
- #288 mask-corrected replay; V2_CORE unchanged
- #290 final Contract V2
- #291 generator engineering
- #293 generator hardening integrated into #291
- #294 deterministic blinded writer
- #295 single realization
- #297 realization byte audit freeze
- #299 blinded V2_CORE executor
- #300 qualification campaign runner
- #301 historical scorer lineage
- #305 reconciled scorer/executor integration
- #306 controller scoring-orchestrator engineering
- #308 Windows monitor repair + one fresh benchmark rerun authority

Known historical traps:
1. structural missingness-as-zero bug — repaired prospectively in #288
2. donor truth orientation is donor × gene, not gene × donor
3. TYPE-S uses named-gate dispatch despite primitive `binomial_upper`
4. q005/q025/q975/q995 must be retained before chain disposal for 99/95% exclusion reporting
5. fit-side held-out metrics are truth-blind; oracle belongs only to controller scoring
6. accepted Windows contract/world bytes are not to be normalized for Linux
7. old #300/#301 divergence has already been reconciled on #305 — do not redo it
8. opaque IDs are not a secrecy boundary; firewall is physical custody/import separation

---

# 7. Benchmark history — critical current gate

## Spent failed attempt

Original executor head:

`2240fd82f1707399bb8b2b16d3d93fee23866067`

The one-shot authorization was consumed once.

Immutable evidence:
- branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`
- commit `b94367c6`
- path `docs/agent/V79_ENGINEERING_BENCHMARK_ATTEMPT_2240fd82_20261012/`

Observed:
- prep PASS
- fit process failed after ~3 seconds
- failure occurred entering first `ResourceMonitor`
- exception `GetProcessMemoryInfo failed`
- no `run_nuts_attempt`
- 0 benchmark fits
- 0 qualification fits
- 0 scoring
- no R-hat/ESS/divergence/timing projection

Interpretation: infrastructure failure only.

## Repair

PR #308 exact head:

`559a1c104c8f1f56d2c05509eecf6b9dc05846a5`

Diff from #300 base is exactly 3 files:
1. `.github/workflows/v79-v2-core-qualification-executor.yml`
2. `scripts/v79/v79_v2_core_resource_monitor.py`
3. `tests/v79/test_v79_v2_core_resource_monitor_windows.py`

TDD:
- RED run `38280964089`: Windows reproduced `2 failed / 117 passed`
- GREEN run `38281216579`: Windows PASS including real monitor calls; Ubuntu PASS; fit firewall PASS

Controller comments:
- repair PASS `6128864889`
- fresh one-shot benchmark rerun authority `6128881654`
- exact Macha procedure `6129078915`

## Current benchmark authority

Exactly one fresh engineering benchmark rerun is authorized from exact #308 head `559a1c10...`.

Required semantics:
- locked Windows `v79-bayes`
- clean exact checkout
- fresh package/custody/result directories
- engineering seed root `31999999`
- 2 genes × 2 parts = 4 fits
- engineering world only
- never scored
- if anything fails: preserve evidence and STOP; no automatic second retry
- if projected full qualification runtime >72 h: STOP with no tuning
- if projection <=72 h: still STOP for controller audit

**At this handoff no fresh rerun result has been reported.**

---

# 8. Fit-side engineering lineage

PR #300 historical campaign-runner head:

`7172b201b13c61634b84b85254bf4406959b2b57`

Engineered properties already accepted structurally:
- opaque 1,056-fit queue
- exact Bernoulli detection + positive lognormal model
- contract-driven NUTS/recovery
- fit-only custody
- no controller truth/Q mapping/scorer imports
- world-serial fresh processes
- one-heavy-fit lock
- 120-second settle
- atomic contiguous-prefix checkpoint/resume
- code/hash/seed/manifest binding
- gate-ready identified summaries
- 90/95/99 interval endpoints retained
- truth-blind PPC
- compact donor-effect draws
- truth-blind same/new-donor held-out model metrics
- final campaign receipt only after all 1,056 valid fit records exist

Execution remains OFF until a successful benchmark is independently audited and a new qualification-execution authority is issued.

Important scripts are indexed in:

`results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_CODE_DATA_RESULT_INDEX_20261012.csv`

---

# 9. Scorer/controller engineering lineage

Historical #301 is evidence only; do not resume from it.

Preferred integration base:

PR #305 head `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`

Active engineering:

PR #306 head `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`

Verification:
- executor CI `38282050314`: Windows PASS, Ubuntu PASS, fit firewall PASS
- scorer CI `38282050318`: Windows PASS, Ubuntu PASS, scorer firewall PASS

Current engineered scorer pieces include:
- controller truth loader/matching
- automatic frozen gate evaluator
- all 292 gates
- first-hard-fail semantics
- 90/95/99 absent-effect reporting
- donor-SD floor from Contract V2
- five required descriptive families, explicitly non-gating
- fixed detection calibration/prevalence summaries
- planted same/new-donor oracle
- 40-node GH oracle integration for new donors
- Q11 operator perturbation handling
- scoring authorization/adjudication receipt primitives
- fit-ledger hash verification / write-once scoring-run primitives

Physical scoring remains OFF. Do not create or execute a scoring authorization until a complete qualification campaign exists and has controller PASS.

---

# 10. Trust-domain firewall

Fit side may see:
- opaque world ID
- blinded manifest/index
- `src`, `donor`, `cls`, `log_lib`
- support mask
- train/same-donor/new-donor observations
- sanitized fit contract / opaque seeds

Fit side must not see:
- Q labels/world index
- planted truth
- controller root mapping
- operator identity
- scorer modules
- outcome gates

Controller scoring is a later physically separate domain and may open truth only after explicit post-campaign scoring authorization.

Never use public knowledge of Q10/Q11 opaque IDs to choose or order benchmark/campaign worlds.

---

# 11. Local/project artifacts visible in this chat but not V79 authority

These are inventoried by exact SHA/size in the audit index so a future agent does not waste time rediscovering them:

- `WSL execution issue.txt`
- `Status and Repair Plan.txt`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- expression archive parts 001/002
- `checkpoints.zip`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `expression.zip`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- `t1_checkpoint_u0200.zip`

They were intentionally **not** promoted to synthetic/V79 authority merely because they are available. Large binaries were not duplicated into Git. Use them only after provenance/lane relevance is explicitly established.

---

# 12. What the new agent should do next

## First unresolved external dependency: repaired benchmark result

Check PR #308 and recent PRs/comments for a new Macha/local Windows report after comment `6129078915`.

If no result exists:
- do not invent one
- do not run Q00-Q11 qualification
- benchmark remains the next physical gate

If a result exists:
- audit only that new evidence
- require exact checkout `559a1c10...`
- require clean worktree and fresh dirs
- verify prep/benchmark receipt hashes
- verify 4 fits exactly
- inspect every recovery stage, divergence, R-hat, ESS, wall/CPU/RSS
- inspect projected 1,056-fit runtime and `stop_required`
- verify qualification_fits=0, scoring=false, truth_accessed=false
- verify no Q00-Q11 world was fitted
- if any mismatch/failure: preserve evidence and STOP; no retry without new authority
- if successful and <=72 h: do not launch qualification automatically; issue a new explicit qualification authority only after controller audit

## Engineering dependency

If #306 advanced beyond `d4e10c82...`, audit only the newer commits and rerun/inspect both executor and scorer CI. Preserve trust-domain separation.

Do not go back to #301 and redo scorer reconciliation.

---

# 13. Explicit execution permissions at handoff

| Action | State |
|---|---|
| regenerate Q00-Q11 | **FORBIDDEN** |
| fresh repaired engineering benchmark | **ONE ATTEMPT AUTHORIZED at exact #308 head `559a1c10...`; no result reported yet** |
| Q00-Q11 qualification fits | **OFF** |
| qualification scoring | **OFF** |
| real TRAIN posterior | **OFF** |
| factorial science | **OFF** |
| TEST/Morabito/pathology | **OFF in this lane** |
| target discovery | **SEPARATE LANE** |
| JEPA training | **OFF** |

---

# 14. Minimum takeover checklist

A new agent should be able to take over without historical re-audit by doing only this:

1. read the current pointer and newest delta;
2. verify #308 live head against `559a1c10...` and look for a new benchmark report;
3. verify #306 live head against `d4e10c82...` and inspect only later commits;
4. use the code/data/result CSV to locate any needed script/result/authority;
5. keep Q00-Q11 realization immutable;
6. keep fit/controller-truth trust domains separate;
7. update #302/#303 after any material benchmark outcome, qualification authority/result, scorer milestone, or newly discovered bug.

Everything before these recorded heads is historical evidence unless a concrete inconsistency is found.
