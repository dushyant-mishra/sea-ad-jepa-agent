# V79 synthetic-dataset lane — canonical audit history

Date: 2026-10-12

This file is the durable controller/audit history for the V79 synthetic-dataset lane. Its purpose is to prevent repeated historical audits, accidental reopening of closed scientific decisions, and cross-lane contamination.

## Non-negotiable lane boundary

This branch is **synthetic/V79 only**. Target discovery is a separate lane. In particular, PR #298 is TD/G7 and must not be folded into this authority chain.

The synthetic lane follows:

`empirical TRAIN characterization -> model comparison/development -> freeze candidate -> fresh untouched synthetic qualification -> independent audit -> real posterior inference`

A failed confirmatory generation stays failed. Do not redesign against it and relabel it confirmatory. Any redesign requires a new development generation and a new untouched qualification generation.

## Current live topology

### PR #300 — campaign runner

- Branch: `feat/v79-v2-core-qualification-campaign-runner-20261012`
- Current audited head at consolidation: `7172b201b13c61634b84b85254bf4406959b2b57`
- Latest workflow at that head: `38271129785` — PASS
- Base executor authority: PR #299 head `2240fd82f1707399bb8b2b16d3d93fee23866067`
- Common scorer merge base: `8801bc236c5eb194628f8d588b43f43a5cde8da0`
- Current branch is 13 commits ahead of that merge base.

Important post-`8801bc23` additions include:

- score-ready 90/95/99 posterior quantiles;
- truth-blind held-out predictive summaries;
- 200 evenly spaced posterior predictive draws for descriptive metrics;
- 10 equal-width probability bins for detection calibration;
- 40-node Gauss-Hermite integration for new-donor positive predictive LPD;
- stricter held-out receipt validation;
- campaign-runner checkpoint/finalization hardening.

**Execution remains OFF.** A green engineering branch is not qualification-fit authority.

### PR #301 — controller scorer

- Branch: `feat/v79-v2-core-controller-scorer-20261012`
- Current audited head at consolidation: `fa1962eddfbb73ec95e5334288c83b324f8d97db`
- Base: old PR #300 head `8801bc236c5eb194628f8d588b43f43a5cde8da0`
- Current #301 is therefore **diverged** from current #300.

#301 carries the controller-only scorer lineage:

- frozen 292-gate authority;
- 260 hard statistical + 28 hard deterministic/rule + 4 LIMIT gates;
- controller truth loading and identified-parameter matching;
- exact frozen statistical kernels;
- TYPE-S and PPC named-gate dispatch;
- donor-SD floor derived from Contract V2 rather than caller injection;
- 90/95/99 absent-effect exclusion reporting;
- first-hard-fail terminal semantics;
- post-campaign scoring authorization / adjudication-receipt work.

Do **not** assume #301 contains #300's later held-out/campaign-runner fixes. Do not silently merge the branches. Port/rebase only after explicitly auditing overlapping `identified_summary` and scoring interfaces.

## Frozen authority chain

Treat these as closed historical entry points unless bytes/hashes change or a concrete contradiction is found:

| PR | Role | Controller conclusion |
|---|---|---|
| #260 | Bayesian/synthetic audit | historical audit authority |
| #261 | Bayesian/synthetic handoff | historical handoff authority |
| #262 | downstream factorial implementation | historical engineering |
| #264 | downstream factorial audit | historical audit authority |
| #265 | downstream factorial handoff | historical handoff authority |
| #279 | streaming/replay implementation | resource-safe exact-S174 path |
| #280 | first exact-S174 replay | **immutable failed-closed**; operator-within-source fixed-effect fit failed under quasi-separation/tiny ridge; do not reinterpret as biology |
| #283 | operator repair | lambda=1 primary; sensitivities 0.25/1/4; only operator-within-source columns penalized |
| #285 | completed exact-S174 replay | A-H completed; V2_CORE structure established |
| #286 | V2 qualification draft / structural missingness | draft authority; later superseded |
| #288 | mask-corrected S174 replay + V2 draft | structural missingness corrected; V2_CORE unchanged |
| #290 | final immutable V2 launch contract | final Contract V2 authority |
| #291 | world generator engineering | final generator head `f45ee034d9bd0c603da5783fed2cf09ee2b16f20`; engineering qualified only |
| #293 | generator hardening | integrated into #291 and closed redundant |
| #294 | deterministic physical writer | final source `fe3aac751e2b8d2e58d5cb4d35af74ad58c823df`; writer qualified |
| #295 | prospective realization authorization / realization record | head `cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`; Q00-Q11 realized exactly once; **do not regenerate** |
| #297 | realization audit freeze | head `bb8923562144a0b19a6d80795adf727986893ded`; 498-file ledger + exact controller evidence freeze |
| #299 | blinded qualification executor | head `2240fd82f1707399bb8b2b16d3d93fee23866067`; engineering-only executor qualified |
| #300 | campaign runner / custody | current fit-side engineering lineage; execution OFF |
| #301 | controller scorer | separate scoring lineage; execution OFF |

## Exact S174 authority

Physical repaired TRAIN substrate:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Never reconstruct it from the larger 50K corpus.

Authority facts:

- 4,726 cells
- 149 donors
- 42 operators
- 3 sources
- 3 broad classes
- 426 donor-class groups
- HVS: 3,072 cells / 62 donors
- NPH52: 246 / 19
- SEA_AD: 1,408 / 68

Hashes:

- S174 shard authority: `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- S174 operator bridge: `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- G500 cache: `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`

Resource rule: at most one count-shard CSR resident; no global 4,726x41,238 CSR; no sparse `vstack`; heavy-fit concurrency 1; settle 120 s.

## Historical Bayesian results — do not reopen casually

Detection/Bernoulli V2 ended **NOT_QUALIFIED** because worst ESS was `361.8761303230284`, below frozen minimum 400. Worst Rhat was `1.0050606796610788`; divergences 0. Do not resurrect V3 or relax the threshold to rescue it.

The older Gaussian/lognormal/ZTNB 18-fit campaign remains `UNADJUDICATED__METHODOLOGICAL_HOLD` and is not authority for V2_CORE.

## Mask-corrected replay conclusion

Structural missingness was real and was fixed in PR #288:

- support mask SHA: `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`
- 136,098 / 2,363,000 entries = 5.76% structurally unmeasured
- replay panel: 63,002 / 945,200 = 6.67%
- masked replay SHA: `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Likelihood uses only measured entries. Unmeasured values enter neither detection nor positive likelihood. Measured zero remains a real zero. All synthetic worlds include structural missingness.

A-H conclusions survived the correction.

## Frozen V2_CORE model

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

Positive-family qualification default: lognormal.

ZTNB remains an unresolved challenger, not qualification authority.

Source is a predictive/acquisition-source term only. Do not promote it to a causal or universal biological interpretation. Single-source estimands are undefined/unevaluable, never silently set to zero.

## Final Contract V2

Canonical contract:

`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`

SHA:

`57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Frozen structure:

- worlds: Q00-Q11
- genes/world: 44
- fits: 1,056
- gates: 292 total
- hard statistical: 260
- hard rule: 28
- LIMIT statistical: 4
- FWER: 0.05
- alpha per hard statistical gate: `0.05 / 260`
- first hard scientific failure is terminal
- Q11 all hard FAIL-class

Exactly four LIMIT gates:

- Q01 detection donor_SD
- Q01 positive donor_SD
- Q08 positive donor_SD
- Q09 positive donor_SD

## World realization authority

Frozen writer / environment authorities:

- pairing amendment: `57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5`
- env lock: `5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782`
- generator/writer bundle: `119add636cffdb1db3b58c44dce6a2c5eee245f85c773e5822735537ae8dfc16`
- realization authorization: `8a2140f8d8ae721f403871de4465db5f0f8caaf3ffa1be9ee71cff7f6d96bba9`

Locked-Windows realization result:

- root manifest: `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- directory digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- runtime receipt: `781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184`
- blinded-fit index: `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`
- world count: 12
- mode: `QUALIFICATION_TRUTH_FREEZE`

Realization audit freeze:

- complete 498-file ledger SHA: `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- realization audit receipt SHA: `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

Do not regenerate the worlds.

## Fit-side / scorer firewall

Fit-side may see only opaque world IDs and blinded inputs. It must not parse controller truth, Q labels, operator identity, or matrix identity.

Controller scoring is a separate trust domain and is not authorized merely because scorer code exists.

Qualification fitting, scoring, real posterior inference and training each require their own authority.

## Historical errors that must stay visible

1. **PR #280 failure** — a real failed-closed replay; do not erase or reinterpret it.
2. **Structural missingness bug** — old zeros included unmeasured entries; fixed prospectively in PR #288.
3. **Writer platform path issue** — canonical POSIX ledger paths were needed for portability.
4. **Linux/Windows world-set digest difference** — qualification world realization authority is Windows-locked; accepted Contract V2 bytes must not be rewritten to force cross-platform equality.
5. **Stale qualification whitelist in #295** — `authorization/` initially broke the no-world-artifact test. Repaired narrowly; `realized_worlds_v1` remains excluded.
6. **Donor truth orientation** — authoritative donor effects are `donor x gene`, not `gene x donor`.
7. **TYPE-S dispatch** — Contract V2 encodes TYPE_S_SOURCE using `binomial_upper`; scorer must dispatch by frozen gate name, not blindly by primitive test string.
8. **95/99% interval retention** — fit summaries must preserve q005/q025/q975/q995; otherwise absent-effect descriptive rates are unrecoverable after chain disposal.
9. **#300/#301 divergence** — current scorer branch does not contain the latest campaign-runner work.
10. **Accidental main-branch RED-test commit** — was detected and restored with lease; future work should always specify branch explicitly for GitHub contents writes.

## Local artifacts visible in the project/chat but not declared V79 authority

These were inventoried to prevent future rediscovery. They are **not automatically synthetic-lane authority** and large binaries were intentionally not duplicated into Git.

| File | bytes | SHA256 | note |
|---|---:|---|---|
| `WSL execution issue.txt` | 14,576 | `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e` | observation-operator / invariance / basis-stability design discussion |
| `Status and Repair Plan.txt` | 5,233 | `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56` | V5 dataset-first dimension-authority lane; separate |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv` | 437 | `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356` | local artifact |
| `...part001` | 303,979,881 | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` | local artifact |
| `...part002` | 303,979,880 | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` | local artifact |
| `checkpoints.zip` | 71,356,460 | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` | local artifact |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` | local artifact |
| `expression.zip` | 3,599,456 | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` | local artifact |
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | 1,531,109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` | local artifact |
| `t1_checkpoint_u0200.zip` | 233,729,581 | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` | local artifact |

## What is still OFF

- world regeneration
- qualification fits
- qualification scoring
- real TRAIN posterior
- factorial science
- TEST / Morabito / pathology in this lane
- target discovery in this lane
- JEPA training

## Takeover rule

A future controller should begin here, then inspect only:

1. PR #297 exact realization audit evidence;
2. current PR #300 head and CI;
3. current PR #301 scorer head and CI;
4. any new controller comment or authority created after this handoff.

Do **not** rerun the historical audit chain unless one of the authority bytes/hashes/heads changed, or a concrete contradiction is discovered. Historical failures remain evidence and must stay in the ledger.
