# Target-discovery primary artifact locator — 2026-10-08

## Why this file exists

The prior takeover handoff correctly listed several target-discovery archaeology tasks, but it did **not** physically bundle every primary artifact into PR #237. A new agent therefore can search the takeover branch and incorrectly conclude that the requested files do not exist.

This locator separates four states:

- `PRESENT_IN_TAKEOVER` — directly available on PR #237 / its custody snapshot.
- `PRESENT_HISTORICAL_GIT_ONLY` — preserved in GitHub on a historical branch/commit but not copied into PR #237.
- `PRESENT_LOCAL_ONLY` — mounted under `/mnt/data` in the current ChatGPT environment and hash-bound, but deliberately not committed as large binary data.
- `REFERENCE_ONLY_NOT_RECOVERED` — known by exact historical name/hash but its bytes have not yet been recovered in this environment or PR #237.

Do not substitute a prose handoff for a primary artifact. Build defect -> repair -> verification -> supersession chains from the exact files/commits below.

---

## 1. S174 HVS/SEA-AD feature-axis repair

**Status:** `PRESENT_HISTORICAL_GIT_ONLY` plus an older working snapshot in PR #237.

Live repair branch:

`claude/s174-train-cache-rebuild-20261007`

Live branch head checked 2026-10-08:

`f88338713b173edb3acbc90662e607ce45b5878b`

Prospective rebuild-freeze commit:

`cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`

Primary freeze receipt:

`results/v77/S174_REBUILD_FREEZE_V1.json`

Corrected replay commit already recorded in takeover custody:

`46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`

Earlier S174 source head snapshotted into PR #237:

`750cb83c8c0535cc67a70d58b62db5607bd7d01e`

Snapshot root:

`custody/takeover_20261008/s174_working_snapshot/`

**Interpretation:** the historical HVS/SEA-AD feature-axis defect is not an open blocker. The correct chain is: defect discovered -> prospective physical rebuild frozen -> corrected cache built -> corrected replay performed. Use the live S174 branch for successor evidence after the older PR #237 snapshot.

---

## 2. TD34 / S149 panel genealogy

**Status:** audit is `PRESENT_HISTORICAL_GIT_ONLY`; original producer/panel manifests are `REFERENCE_ONLY_NOT_RECOVERED`.

Audit branch:

`audit/td34-genealogy-s149-20261006`

Audit head:

`efa5c21db479f2feb78892356af3eef42c2886d2`

Primary audit file:

`docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

Historical TD34 closure commit:

`ff85f5bb18dc7d438113c3a5662856a360d2cd8f`

Repository-resident historical anchors at that closure:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`
- `target_discovery/iterations/td34_state_geometry_globalrow/TD34_SUMMARY.csv`

Recorded TD34 producer-script SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

The audit found that repository authority preserved the script digest and summary, but **not** the original producer bytes, four exact 512-gene membership manifests, or enough primary provenance to reconstruct panel selection.

### Most specific missing-package lead

Historical package name:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Expected SHA-256:

`d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`

Expected embedded markdown SHA-256:

`5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`

**Current availability:** `REFERENCE_ONLY_NOT_RECOVERED`.

The ZIP is not among the ten currently mounted `/mnt/data` assets and is not bundled in PR #237. Therefore a new agent searching PR #237 is not expected to find it. Recover these exact bytes from older chat/library/local custody if possible and authenticate against the hashes above.

Historical downstream TD41 ref cited by the audit:

`54f67f5cd5138c47311e95441b4895076ffb7bfc`

`TD41S_PROSPECTIVE_FREEZE.md` says to use the same four deterministic 512-gene TD34 panels. That protects downstream pair sampling but does **not** repair missing upstream TD34 membership genealogy.

---

## 3. G2 / `PIPELINE_ARTEFACT_m`

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`; no later positive-control closure has yet been located by this handoff.

Same primary audit:

`audit/td34-genealogy-s149-20261006@efa5c21db479f2feb78892356af3eef42c2886d2`

`docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

Primary earlier full audit cited there:

commit `785a45972fed3ea896d2209058e2860ef115fc2d`

file `docs/agent/V74_MACHA_FULL_AUDIT_FINAL_20261003.md`

G2 successor audited there:

`claude/v74-g2-continuous-successor-20261002@03c0c48612860e4bd2f094ce54fdef9cde274490`

The checkpoint records `PIPELINE_ARTEFACT_m` as specified but not run under the required prospectively frozen positive-control discrimination design. Search newer history for a true successor before carrying this RED state forward, but do not treat a generic S102/G2 PASS label as supersession without the exact positive-control receipts and margins.

---

## 4. Nott ATAC + liftover + V64 custody

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`; raw external bytes are custody-referenced rather than bundled in PR #237.

Primary successor branch:

`chatgpt/v64-e2-single-source-successor-20260929`

Live branch head checked 2026-10-08:

`23255baaf81381d5c22c655a605642db27f2a173`

Earlier known custody checkpoint on that lineage:

`003ad549a158ebf44093d9771cb7c2aabd240d05`

Related contract branch:

`chatgpt/v64-nott-substrate-fit-contract-20260929`

known head:

`a6ecae6c31ba2083de72566fd336b187f7d59bfc`

Historical custody records on these branches preserve source URL/checksum identity for:

- Nott Table S5;
- microglia ATAC;
- neuron ATAC;
- oligodendrocyte ATAC;
- hg19->hg38 chain;
- hg38->hg19 chain.

The current live successor branch also contains NIH-CARD exact-control/liftOver audit history. Example current head artifact:

`results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

at `23255baaf81381d5c22c655a605642db27f2a173`.

Do not search only PR #237 for these V64 inputs/receipts. Check out or inspect the historical V64 successor branch directly, then build the exact source-file/checksum -> liftover-chain -> derived-result chain.

---

## 5. SCENIC+ / regulatory evidence

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`.

Two important historical branches still exist:

1. `agent-4/scenicplus-recovery-expansion-20260926`
   - head checked 2026-10-08: `5e3d1197749c6d2ac0b4015edea5c042b681af91`

2. `claude/v69-scenicplus-external-network-20261001`
   - head checked 2026-10-08: `d5b76230c1d2837dfbf643e205c5b2780831d8f9`

The V69 branch contains cisTarget/SCENIC+ external-network build and benchmark receipts; for example at the current head:

`results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json`

This branch is the place to reconstruct exact SCENIC+/cisTarget producer versions, motif/region universes, build receipts, inputs and exposure history. The earlier agent-4 branch is the recovery/expansion lineage and should be checked for primary pre-V69 artifacts not carried forward.

Do not treat SCENIC+ as a generic validation label: bind every target claim to the actual producer/version/input/region-universe receipt.

---

## 6. NIH-CARD Stage 3/4 and realism/control work

**Status:** design/audit branches are `PRESENT_HISTORICAL_GIT_ONLY`; an original Stage 3/4 execution-output package has **not yet been independently recovered by this handoff**.

Historical design branch:

`claude/v64-nihcard-e2-design-20260929`

head checked 2026-10-08:

`6d08386f9f996c8db6224a959ca93745669b27ee`

Related realism branch:

`claude/v64-nihcard-realism-design-20260929`

The current V64 single-source successor (`23255baaf81381d5c22c655a605642db27f2a173`) audits that realism lineage and records that Phase B / Stage 4 remained sealed at that point. The exact-control audit is:

`results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

Its audited realism merge tip is recorded as:

`aba071a450656553f923b601f379496dd2eefcf9`

and audited sampler commit:

`945ff4d4813f07c702dd8d37be0ecc5c251435f8`

Search subsequent NIH-CARD branches/commits for a genuine execution successor before concluding that the old sealed status is current. If original Stage 3/4 result bytes exist only in old chat/local custody, recover and hash-bind them; do not reconstruct them from summary prose.

---

## 7. Current local-only scientific/runtime assets

**Status:** `PRESENT_LOCAL_ONLY` under `/mnt/data`.

These are not the Sept. 7 target-discovery ZIP, but they are exact custody assets required elsewhere in the project:

| file | bytes | SHA-256 |
|---|---:|---|
| `WSL execution issue.txt` | 14,576 | `cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv` | 437 | `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` | 303,979,881 | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` |
| `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` | 303,979,880 | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` |
| `checkpoints.zip` | 71,356,460 | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` |
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | 410,278,055 | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` |
| `expression.zip` | 3,599,456 | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` |
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | 1,531,109 | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` |
| `t1_checkpoint_u0200.zip` | 233,729,581 | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` |
| `Status and Repair Plan.txt` | 5,233 | `cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56` |

The two 41K parts concatenate to:

- bytes: `607,959,761`
- SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Do not confuse these assets with the missing Sept. 7 target-discovery package.

---

## 8. Immediate new-agent search protocol

1. **Do not search PR #237 alone.** It is a takeover/custody surface, not a complete historical artifact mirror.
2. Start with this locator and inspect each exact branch/commit listed above.
3. For every old RED finding, construct a table: `defect -> repair commit -> verification artifact/run -> superseding conclusion`.
4. Mark a finding `FIXED` only if the repair and verification are primary artifacts, not because a later prose handoff says so.
5. Mark `REFERENCE_ONLY_NOT_RECOVERED` for the Sept. 7 ZIP until bytes matching `d0b883ff...` are physically recovered.
6. For TD34, do not upgrade or condemn the four panels until original producer bytes and membership manifests are recovered or a clearly new prospective experiment supersedes them.
7. For NIH-CARD, distinguish design/audit receipts from actual Stage 3/4 execution outputs.
8. For SCENIC+ and Nott, reconstruct source/input/build/liftover/exposure chains explicitly.

This locator is descriptive and non-authorizing. It does not authorize training, target freeze, Stage 4, TEST, Morabito use as pristine validation, or any protected execution.