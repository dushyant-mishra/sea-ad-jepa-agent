# V79 synthetic-dataset lane — audited takeover handoff

Date: 2026-10-12

This handoff is for the **synthetic dataset / V79 controller-audit lane only**. It inherits the canonical historical audit ledger in:

- `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
- `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`

A future agent should read those two files first. They are intentionally written so closed audits do not have to be repeated.

## 1. Current state in one paragraph

The synthetic worlds are already generated exactly once, byte-audited, and frozen. The blinded V2_CORE fit executor and campaign-runner are engineered, but physical qualification fitting is still OFF. The controller scorer is also engineered on a separate branch, but scoring is OFF. The latest fit-side campaign branch (#300) and scorer branch (#301) diverged after common head `8801bc236c5eb194628f8d588b43f43a5cde8da0`; do not silently merge them. The next engineering task is to reconcile the scorer onto the latest campaign-runner interfaces while preserving the fit/truth firewall, then obtain explicit controller authority before any physical benchmark/qualification/scoring action.

## 2. Exact live heads at handoff

### Fit-side / campaign runner

PR #300

- branch: `feat/v79-v2-core-qualification-campaign-runner-20261012`
- head: `7172b201b13c61634b84b85254bf4406959b2b57`
- merge base with scorer: `8801bc236c5eb194628f8d588b43f43a5cde8da0`
- CI: run `38271129785` — PASS
- execution state: **HOLD / no qualification fit authority**

Important current behavior:

- all qualification fit records are opaque-world only;
- fit-side does not import controller truth/scorer modules;
- score-ready posterior summaries retain 90/95/99 interval endpoints;
- held-out predictive summaries are truth-blind and non-gating;
- new-donor positive predictive integration uses 40-node Gauss-Hermite;
- checkpoint resume is contiguous and hash/code/seed bound;
- final campaign receipt exists only after all 1,056 frozen fits are present and valid.

### Controller scorer

PR #301

- branch: `feat/v79-v2-core-controller-scorer-20261012`
- head: `fa1962eddfbb73ec95e5334288c83b324f8d97db`
- base: old #300 head `8801bc236c5eb194628f8d588b43f43a5cde8da0`
- scorer CI at current head: `38269425892` — PASS
- executor compatibility CI at current head: `38269425916` — PASS
- execution state: **HOLD / no scoring authority**

Scorer branch carries:

- controller truth loading;
- exact identification matching;
- donor truth orientation fixed as donor x gene;
- automatic frozen-gate evaluation;
- exact 292-gate binding;
- TYPE-S named-gate dispatch;
- 90/95/99 absent-effect exclusion reporting;
- donor-SD floor from Contract V2 authority;
- post-campaign scoring authorization and immutable adjudication-receipt work.

## 3. Branch divergence — first thing a takeover agent must respect

Current #300 is 13 commits ahead of the common merge base. Current #301 is 33 commits on its own scorer lineage.

Do not use a blind merge.

The overlapping files that require careful reconciliation include at least:

- `scripts/v79/v79_v2_core_identified_summary.py`
- `scripts/v79/v79_v2_core_score.py`
- scorer tests that assume the fit-summary schema

Recommended reconciliation method:

1. start from exact current #300 head;
2. port scorer-only files from #301 one logical unit at a time;
3. preserve the current #300 identified-summary quantiles and held-out schema;
4. run both executor and scorer suites on Windows and Linux;
5. verify the static fit-side trust-domain audit still proves no scorer/controller-truth import;
6. only after that create a new audited scorer-successor head.

Do not rewrite historical #301. Preserve it as evidence of how the scorer evolved.

## 4. Frozen scientific authority — do not rediscover

V2_CORE is already frozen as:

Detection:

`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:

`log(count) | count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Included:

- quadratic depth
- broad class
- source
- donor-within-source hierarchical/partial pooled

Excluded:

- operator main
- donor x class
- source x class
- arbitrary/free matrix or dataset identity

Do not re-open these choices merely because a downstream engineering test fails. A downstream bug is not new biological evidence.

## 5. Frozen qualification authority

Contract:

`results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json`

SHA:

`57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`

Frozen campaign:

- 12 worlds Q00-Q11
- 44 genes/world
- 1,056 fits
- 292 gates
- 260 hard statistical
- 28 hard deterministic/rule
- 4 LIMIT statistical
- first hard failure terminal
- Q11 all hard FAIL-class

Exactly four LIMIT gates:

- Q01 detection donor_SD
- Q01 positive donor_SD
- Q08 positive donor_SD
- Q09 positive donor_SD

## 6. Realization — never rerun

PR #295 realized Q00-Q11 exactly once on the locked Windows qualification environment.

Authority head:

`cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`

Frozen outputs:

- root manifest SHA: `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- world-set directory digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- runtime environment receipt: `781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184`
- blinded-fit index: `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`

PR #297 independently froze the byte evidence:

- head: `bb8923562144a0b19a6d80795adf727986893ded`
- complete 498-file ledger SHA: `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- realization audit receipt SHA: `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

**Never regenerate the worlds to repair a later problem.**

## 7. Historical failures that are already understood

Do not spend a new session rediscovering these:

- PR #280 exact-S174 replay failed closed because operator-within-source fixed effects hit quasi-separation under the tiny ridge. This did not prove operator biology absent/present.
- structural missingness was previously encoded as zero; PR #288 fixed it using the support mask.
- accepted Contract V2 bytes are Windows authority; do not change them to make Linux arithmetic/digests agree.
- PR #295 initially exposed a stale top-level qualification whitelist after `authorization/` was added; the repair was deliberately narrow.
- authoritative donor-effect truth layout is donor x gene.
- TYPE-S needs named-gate dispatch despite primitive `binomial_upper` encoding.
- 95%/99% posterior interval endpoints must be retained before chain disposal.
- fit-side held-out predictive summaries must remain truth-blind; oracle comparison belongs in controller scoring.

## 8. Data/provenance authority

Exact repaired S174 TRAIN substrate:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Never reconstruct from the larger 50K corpus.

Key hashes:

- shard authority: `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`
- operator bridge: `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`
- G500 cache: `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`
- support mask: `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`
- masked replay: `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`

Resource discipline:

- one count-shard CSR resident maximum;
- no global 4,726 x 41,238 CSR;
- no sparse `vstack`;
- heavy fits concurrency 1;
- 120-second inter-world settle.

## 9. Local/project artifacts inventoried but not promoted to V79 authority

The audit index contains SHA256 + byte size for the current project/chat artifacts, including the large expression/calibration/checkpoint bundles. They were **not** copied into Git because provenance/lane relevance is not established and several are hundreds of MB. The index prevents a future agent from wasting time rediscovering them while also preventing accidental authority promotion.

See:

`results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`

## 10. What a future agent should do next

### First: audit only what changed after this handoff

Check live PR #300 and #301 heads. If unchanged from the heads above, do not repeat their historical audits.

If changed, compare only the delta from these recorded heads.

### Second: reconcile scorer lineage onto latest fit-side interfaces

Build a new successor branch from current #300 and port #301 scorer-only work carefully. The objective is one audited code lineage while preserving separate trust domains, not one runtime trust domain.

Required checks before declaring engineering complete:

- both Windows/Linux executor suites pass;
- both Windows/Linux scorer suites pass;
- exact 292 frozen gates are traversed;
- all 1,056 scored rows are required;
- all five descriptive metric families are required for final adjudication;
- fit-side static audit proves no `controller_truth` / scorer import;
- scoring authorization cannot exist without an exact complete campaign receipt + controller PASS;
- final adjudication receipt cannot authorize real posterior/factorial/training.

### Third: stop at the authority boundary

Do not run physical benchmark, qualification, scoring, real posterior or training just because engineering is green.

## 11. Current execution permissions

| Action | State |
|---|---|
| regenerate Q00-Q11 | **FORBIDDEN** |
| physical engineering benchmark | separate authority path only; do not infer from this handoff |
| physical qualification fits | **OFF** |
| qualification scoring | **OFF** |
| real TRAIN posterior | **OFF** |
| factorial science | **OFF** |
| TEST/Morabito/pathology | **OFF in this lane** |
| target discovery | **SEPARATE LANE** |
| JEPA training | **OFF** |

## 12. Fast takeover checklist

A new controller should be able to take over by doing only this:

1. read the audit-history markdown;
2. read the machine-readable audit index;
3. inspect live #300 head vs `7172b201...`;
4. inspect live #301 head vs `fa1962ed...`;
5. compare only any new delta;
6. reconcile scorer onto current fit-side lineage;
7. rerun structural CI;
8. request/issue the next explicit controller authority only after that audit.

Everything before those recorded heads is historical evidence unless a concrete inconsistency is discovered.
