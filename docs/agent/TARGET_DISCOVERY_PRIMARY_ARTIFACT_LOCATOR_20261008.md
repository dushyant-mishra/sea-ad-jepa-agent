# Target-discovery primary artifact locator — 2026-10-08

## Why this file exists

The takeover branch is a custody/navigation surface, not a complete mirror of every historical target-discovery branch. This locator tells the next agent exactly where primary evidence lives and, critically, records which previously missing Sept. 7 custody bytes have now been recovered.

Use these states:

- `PRESENT_IN_TAKEOVER` — directly available on PR #237 / this branch.
- `PRESENT_HISTORICAL_GIT_ONLY` — preserved on a historical Git branch/commit but not copied wholesale into PR #237.
- `PRESENT_LOCAL_ONLY` — physically mounted in the current ChatGPT environment and hash-bound, but not committed as a binary asset.
- `RECOVERED_CHAT_LOCAL__KEY_BYTES_IN_TAKEOVER` — historical package physically recovered, authenticated by exact historical hash, with authority-critical text bytes/checksum inventory copied into takeover custody.
- `REFERENCE_ONLY_NOT_RECOVERED` — exact historical identity is known but bytes have not yet been recovered.

For every old finding, use:

`defect/finding -> repair or primary recovery -> verification -> superseding/current conclusion`

Do not freeze an old RED audit as permanent truth, and do not accept later prose as a repair without primary evidence.

---

## 1. S174 HVS/SEA-AD feature-axis repair

**Status:** `PRESENT_HISTORICAL_GIT_ONLY` plus an older working snapshot in PR #237. Historical defect is **fixed and replayed**, not an open blocker.

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

**Interpretation:** defect discovered -> prospective physical rebuild frozen -> corrected cache built -> corrected replay performed. Use the live S174 branch for successor evidence beyond the older PR #237 snapshot.

---

## 2. TD34 / S149 panel genealogy — Sept. 7 primary package recovered

**Status:** `RECOVERED_CHAT_LOCAL__KEY_BYTES_IN_TAKEOVER`.

Historical audit branch:

`audit/td34-genealogy-s149-20261006`

Audit head:

`efa5c21db479f2feb78892356af3eef42c2886d2`

Audit file:

`docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

Historical TD34 closure:

`ff85f5bb18dc7d438113c3a5662856a360d2cd8f`

Historical anchors:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`
- `target_discovery/iterations/td34_state_geometry_globalrow/TD34_SUMMARY.csv`

### Recovered Sept. 7 package

Historical package:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Recovered chat-local path:

`/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

- bytes: `1664383`
- recovered SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- historical expected SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- verdict: `EXACT_MATCH`
- extracted files: `97`

Embedded handoff:

- archive path: `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.md`
- recovered SHA-256: `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`
- historical expected SHA-256: same
- verdict: `EXACT_MATCH`

Durable recovery records:

- `custody/target_discovery_20260907_recovered/README.md`
- `custody/target_discovery_20260907_recovered/RECOVERED_PACKAGE_SHA256_MANIFEST.csv`
- `docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md`

The binary ZIP remains chat-local because the connected GitHub write interface is text-only. Its exact byte count and SHA-256 are now durably recorded in Git.

### Original TD34 producer bytes: RECOVERED

Archive path:

`scripts/td_iteration34_state_geometry_globalrow.py`

Recovered SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

Historical audit-recorded SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

Verdict:

`PRIMARY_PRODUCER_BYTES_RECOVERED__EXACT_HASH_MATCH`

Durable takeover copy:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

The authentic producer establishes the exact panel-selection algorithm:

```python
states = np.load(SUP, allow_pickle=False)['states']
common = np.where((states == 1).all(0))[0]
ordered = np.array(
    sorted(common, key=lambda x: hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),
    dtype=np.int32,
)
panels = [ordered[i*512:(i+1)*512] for i in range(4)]
```

Therefore the four panels are deterministic slices of the all-state common-support address universe. The authentic producer does not select panel membership by outcome, pathology, covariance, observed cross-source agreement, expression magnitude, topology, or downstream target result.

### What is still pending for exact TD34 membership reconstruction

The producer reads:

`FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

That upstream support NPZ was **not found inside the recovered Sept. 7 ZIP**, and no standalone four-panel membership manifest was found by filename inspection.

So the old broad classification `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` is superseded, but exact membership vectors are not yet independently reproduced from takeover custody.

Current classification:

`PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`

Next closure action: recover/hash-bind the historical support NPZ or an authenticated equivalent containing the exact common-support address vector; reproduce the four 512-address vectors; hash them; compare them against downstream TD41 panel/pair artifacts.

Historical downstream TD41 ref:

`54f67f5cd5138c47311e95441b4895076ffb7bfc`

---

## 3. G2 / `PIPELINE_ARTEFACT_m`

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`; old RED state must be checked against later successor history before being carried forward.

Primary Oct. 6 audit:

`audit/td34-genealogy-s149-20261006@efa5c21db479f2feb78892356af3eef42c2886d2`

`docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

Earlier full audit:

`785a45972fed3ea896d2209058e2860ef115fc2d`

`docs/agent/V74_MACHA_FULL_AUDIT_FINAL_20261003.md`

G2 successor inspected there:

`claude/v74-g2-continuous-successor-20261002@03c0c48612860e4bd2f094ce54fdef9cde274490`

The Oct. 6 checkpoint found the required prospectively frozen positive-control `PIPELINE_ARTEFACT_m` discrimination execution unrecovered at that time. Search later successor history for exact positive/negative control receipts and predefined margins. A generic S102/G2 PASS label is not by itself supersession.

---

## 4. Nott ATAC + liftover + V64 custody

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`; concrete Git starting point found.

Primary successor branch:

`chatgpt/v64-e2-single-source-successor-20260929`

Head checked 2026-10-08:

`23255baaf81381d5c22c655a605642db27f2a173`

Related contract branch:

`chatgpt/v64-nott-substrate-fit-contract-20260929@a6ecae6c31ba2083de72566fd336b187f7d59bfc`

Historical custody records on this lineage preserve identities for Nott Table S5, microglia/neuron/oligodendrocyte ATAC, and hg19<->hg38 liftover chains. Reconstruct exact source URL/checksum -> chain -> derived artifact -> exposure status rather than treating “Nott” as a generic validation label.

The V64 successor also contains NIH-CARD exact-control/liftOver audit history, including:

`results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

---

## 5. SCENIC+ / regulatory evidence

**Status:** `PRESENT_HISTORICAL_GIT_ONLY`.

Recovery/expansion lineage:

`agent-4/scenicplus-recovery-expansion-20260926@5e3d1197749c6d2ac0b4015edea5c042b681af91`

SCENIC+/cisTarget external-network lineage:

`claude/v69-scenicplus-external-network-20261001@d5b76230c1d2837dfbf643e205c5b2780831d8f9`

Example benchmark receipt:

`results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json`

Reconstruct producer/version, motif and region universes, input assets, build receipts, outputs and exposure history. Infrastructure/runtime commits alone are not scientific evidence.

---

## 6. NIH-CARD Stage 3/4 and realism/control work

**Status:** design/audit provenance is `PRESENT_HISTORICAL_GIT_ONLY`; original later Stage 3/4 execution-output package remains `REFERENCE_ONLY_NOT_RECOVERED` until physically located.

Design branch:

`claude/v64-nihcard-e2-design-20260929@6d08386f9f996c8db6224a959ca93745669b27ee`

Realism branch:

`claude/v64-nihcard-realism-design-20260929`

Current V64 successor:

`chatgpt/v64-e2-single-source-successor-20260929@23255baaf81381d5c22c655a605642db27f2a173`

Exact-control audit:

`results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

Audited realism merge tip recorded there:

`aba071a450656553f923b601f379496dd2eefcf9`

Audited sampler commit:

`945ff4d4813f07c702dd8d37be0ecc5c251435f8`

Do not confuse design/control receipts with actual Stage 3/4 biological execution output. Search later NIH-CARD branches and old custody for the exact execution package.

---

## 7. Local scientific/runtime assets

The environment also contains other hash-bound `/mnt/data` assets described in the earlier takeover documents. They are separate from the now-recovered Sept. 7 target-discovery ZIP.

The two 41K expression parts concatenate to SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Do not confuse those assets with the Sept. 7 custody package.

---

## 8. Immediate successor protocol

1. Read this locator and `docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md` before searching.
2. Do not search PR #237 alone for historical evidence; follow exact branch/commit pointers above.
3. For TD34, stop searching for the producer: it is recovered and hash-verified. Search instead for `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` or an authenticated equivalent support vector, then reconstruct exact four-panel membership.
4. For G2, search later successor history before carrying forward the Oct. 6 RED state.
5. For Nott/liftover, build the exact source/checksum -> liftover -> output -> exposure chain.
6. For SCENIC+, distinguish environment/runtime setup from scientific output custody.
7. For NIH-CARD, distinguish design/exact-control audits from actual Stage 3/4 execution bytes.
8. Re-adjudicate TD41->TD60 only after upstream provenance/substrate states are current.
9. Mark a defect `FIXED` only when repair plus verification are primary artifacts.
10. Preserve the boundaries below.

This locator is descriptive and non-authorizing. It does not authorize real-data training, target freeze, representation freeze, Stage A, Stage 4, TEST, Morabito use as pristine validation, production EMA selection, threshold tuning, or multimodal training.