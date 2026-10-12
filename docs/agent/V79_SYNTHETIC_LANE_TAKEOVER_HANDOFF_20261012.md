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

**Do not repeat audits before the exact heads/hashes recorded below unless a byte/head changed or a concrete contradiction is discovered. Audit only deltas.**

# 1. Current state

Q00-Q11 have already been realized exactly once on the locked Windows qualification environment and independently byte-audited. They must never be regenerated to repair later software. The first authorized engineering benchmark was consumed once and failed closed before fit 1 because the Windows RSS monitor used untyped Win32 ctypes signatures. That failure is immutable infrastructure evidence, not evidence about V2_CORE model quality, convergence, memory demand or runtime. PR #308 repaired that defect under RED→GREEN real Windows CI and now holds authority for exactly **one fresh engineering benchmark rerun** at exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`; that rerun has not yet been reported. Q00-Q11 qualification fitting and scoring remain OFF. Engineering work beyond the campaign runner/scorer reconciliation is on PR #306 at `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`, with Windows/Linux executor and scorer CI green, but physical scoring remains OFF.

# 2. Frozen scientific decisions

Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:
`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Included: quadratic depth, broad class, source, donor-within-source hierarchical/partial pooled.

Excluded: operator main, donor×class, source×class, arbitrary/free matrix or dataset identity.

Positive qualification family: lognormal. ZTNB is an unresolved challenger, not authority. Source is predictive/acquisition-source only; single-source estimands are undefined/unevaluable rather than zero.

Historical Bernoulli V2 qualification remains `NOT_QUALIFIED` because worst ESS was `361.8761303230284 < 400`; do not relax the threshold or resurrect it.

# 3. Contract V2 authority

Canonical file: `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`

SHA: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Other frozen authorities:
- pairing amendment `57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5`
- environment lock `5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782`
- generator/writer bundle `119add636cffdb1db3b58c44dce6a2c5eee245f85c773e5822735537ae8dfc16`

Frozen shape: 12 worlds, 44 genes/world, 1,056 fits, 292 gates, 260 hard statistical, 28 hard rule, 4 LIMIT, FWER .05, hard-gate alpha `.05/260`, first hard FAIL terminal, Q11 all-hard FAIL-class.

Exactly four LIMIT gates: Q01 det donor_SD; Q01 pos donor_SD; Q08 pos donor_SD; Q09 pos donor_SD.

Accepted contract bytes are Windows authority. Do not rewrite/round them for another platform.

# 4. Exact S174 authority

Physical repaired TRAIN substrate: `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Never reconstruct from the larger 50K corpus.

Hashes:
- shard authority `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- operator bridge `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- G500 cache `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- support mask `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`
- masked replay `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Resource rules: one count-shard CSR max, no global 4,726×41,238 CSR, no sparse vstack, one heavy fit at a time, 120-second inter-world settle.

Structural missingness is authoritative: unmeasured entries are not zeros.

# 5. Realization — never rerun

PR #295 realization head: `cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`

Frozen realization:
- root manifest `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- directory digest `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- runtime receipt `781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184`
- blinded index `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`

PR #297 byte audit:
- head `bb8923562144a0b19a6d80795adf727986893ded`
- 498-file ledger `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- audit receipt `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

Controller audit established one-to-one truth/blinded mapping, root/index/runtime/authorization binding, truth-array hashes, and Q10/Q11 paired semantics. Never regenerate Q00-Q11 because of a later bug.

# 6. Closed historical failure/audit chain

Do not repeat: #260, #261, #262, #264, #265, #279, #280, #283, #285, #286, #288, #290, #291, #293, #294, #295, #297, #299, #300, #301, #305, #306, #308 before the exact heads recorded here.

Critical historical traps:
1. #280 quasi-separation failure is not biology evidence.
2. structural missingness-as-zero bug was repaired in #288.
3. donor truth orientation is donor×gene.
4. TYPE-S needs named-gate dispatch despite `binomial_upper` encoding.
5. q005/q025/q975/q995 must be retained before chain disposal.
6. held-out fit summaries remain truth-blind; oracle is controller-only.
7. accepted Windows bytes must not be normalized for Linux.
8. old #300/#301 divergence was already reconciled on #305.
9. opaque IDs are not the security boundary; physical custody/import separation is.

# 7. Benchmark gate

Original executor head `2240fd82f1707399bb8b2b16d3d93fee23866067` had one benchmark authority. It was consumed once.

Immutable failed evidence:
- branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`
- commit `b94367c6`
- path `docs/agent/V79_ENGINEERING_BENCHMARK_ATTEMPT_2240fd82_20261012/`

Outcome: prep PASS, benchmark process failed before fit 1 on `GetProcessMemoryInfo`; 0 fits, 0 diagnostics, 0 runtime projection. Treat as infrastructure failure only.

PR #308 repair head: `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`

Diff is exactly monitor code, real Windows monitor regression test, and workflow wiring.

TDD:
- RED `38280964089`: real Windows failure reproduced, 2 failed / 117 passed
- GREEN `38281216579`: Windows PASS, Ubuntu PASS, fit firewall PASS

Controller comments:
- repair PASS `6128864889`
- fresh one-shot rerun authority `6128881654`
- canonical execution instructions `6129078915`

Exactly one fresh benchmark rerun is authorized at #308 head `559a1c10...`, locked Windows `v79-bayes`, fresh dirs, engineering seed `31999999`, 2 genes×2 parts, never scored. If anything fails, preserve evidence and STOP; no automatic second retry. If projected qualification runtime is >72h, STOP with no tuning. If <=72h, still STOP for controller audit.

At this handoff, no fresh rerun result has been reported.

# 8. Fit-side engineering

Historical #300 head: `7172b201b13c61634b84b85254bf4406959b2b57`

Accepted structural properties:
- opaque 1,056-fit queue
- exact Bernoulli + lognormal V2_CORE
- contract NUTS/recovery
- fit-only custody
- no truth/Q/scorer imports
- world-serial fresh processes
- one-heavy-fit lock
- 120s settle
- atomic contiguous resume
- code/hash/seed/manifest binding
- gate-ready identified summaries
- 90/95/99 endpoints
- truth-blind PPC and held-out predictive metrics
- compact donor draws
- final campaign receipt only after all 1,056 fit receipts validate

Qualification execution remains OFF until the repaired benchmark passes controller audit and a new explicit qualification authority is issued.

# 9. Controller scorer engineering

Historical #301 is evidence only. Do not resume reconciliation from it.

Preferred integration base: #305 `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`

Active #306 head: `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`

Verification:
- executor CI `38282050314`: Windows/Ubuntu PASS; fit firewall PASS
- scorer CI `38282050318`: Windows/Ubuntu PASS; scorer firewall PASS

Engineered pieces:
- truth loading/matching
- exact 292-gate evaluator
- first-hard-fail semantics
- absent-effect 90/95/99 reporting
- donor-SD floor from Contract V2
- five non-gating descriptive families
- calibration/prevalence summaries
- planted held-out oracle
- 40-node GH new-donor oracle
- Q11 operator perturbation handling
- scoring authorization/adjudication receipt primitives
- fit-ledger hash verification and write-once scoring-run primitives

Physical scoring remains OFF.

# 10. Trust-domain firewall

Fit side may see opaque ID, blinded index/manifest, src/donor/cls/log_lib, support, observations, sanitized fit contract and opaque seeds.

Fit side must not see Q labels/world index, planted truth, root mapping, operator identity, scorer modules or outcome gates.

Controller scoring is later and separate. Never use public Q10/Q11 opaque-ID knowledge for selection/order.

# 11. Local/project artifacts not promoted to V79 authority

The audit index inventories exact SHA/size for `WSL execution issue.txt`, `Status and Repair Plan.txt`, the large expression archive parts, `checkpoints.zip`, calibration bundle, `expression.zip`, the NPZ file and `t1_checkpoint_u0200.zip`.

They are available but intentionally not V79 authority. Do not use them unless provenance/lane relevance is explicitly established.

# 12. Next actions for the new agent

First unresolved external dependency: repaired benchmark result.

Check PR #308/comments newer than `6129078915`.

If no result exists: benchmark is still next physical gate; do not run qualification.

If a result exists: audit only that evidence. Require exact checkout `559a1c10...`, clean tree, fresh dirs, receipt hashes, exactly 4 fits, all recovery/diagnostic/resource fields, projected 1,056-fit runtime, qualification_fits=0, scoring=false, truth_accessed=false, and no Q00-Q11 fit. Any mismatch/failure => preserve and STOP. Successful <=72h benchmark still does not auto-authorize qualification; issue a separate authority only after audit.

Engineering dependency: if #306 advanced beyond `d4e10c82...`, audit only newer commits and both CI suites. Do not go back to #301.

# 13. Execution permissions

- regenerate Q00-Q11: **FORBIDDEN**
- repaired engineering benchmark: **ONE ATTEMPT AUTHORIZED at #308 `559a1c10...`; no result reported yet**
- Q00-Q11 qualification fits: **OFF**
- qualification scoring: **OFF**
- real TRAIN posterior: **OFF**
- factorial science: **OFF**
- TEST/Morabito/pathology: **OFF in this lane**
- target discovery: **SEPARATE LANE**
- JEPA training: **OFF**

# 14. Minimum takeover checklist

1. read pointer + newest delta + index + code/data/result locator;
2. check #308 for a new benchmark report;
3. check #306 for commits newer than `d4e10c82...`;
4. audit only those deltas;
5. never regenerate Q00-Q11;
6. preserve fit/controller-truth separation;
7. update #302 and this successor handoff after every material benchmark outcome, new authority/result, scorer milestone or new bug.
